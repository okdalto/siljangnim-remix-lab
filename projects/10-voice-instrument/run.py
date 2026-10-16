"""Portable version of the Short's 16-section acoustic duct model (GPL-3.0+)."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import write
from scipy.linalg import solve_banded
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent
SR = 24000
F0 = 80.8533319339
OPEN, CLOSE, LOWPASS = .4034024367889455, .2679836752422151, 13827.623043745323


def transfer(z, hz):
    """Volume-flow ratio: rigid circular sections, pressure-release outlet."""
    hz = np.asarray(hz)
    k = 2*np.pi*hz/343 - 1j*z[-1]*np.sqrt(np.maximum(hz, 1)/1000)
    cs, sn = np.cos(k*z[0]/16), 1j*np.sin(k*z[0]/16)
    a = np.ones(len(hz), complex)
    b = np.zeros(len(hz), complex)
    c, d = b.copy(), a.copy()
    for area in np.exp(z[1:17])*1e-4:
        a,b,c,d = a*cs+b*sn*area, a*sn/area+b*cs, c*cs+d*sn*area, c*sn/area+d*cs
    return 1/d


def finite_element(z, hz, cells=1024):
    """Independent linear 1D FEM assembly, equivalent to the DOLFINx weak form.

    Integral A p' v' - k² A p v dx; unit inlet flux and p(L)=0.
    No FEniCSx runtime is needed for this small tridiagonal system.
    """
    assert cells % 16 == 0
    dx = z[0]/cells
    areas = np.repeat(np.exp(z[1:17])*1e-4, cells//16)
    stiffness, mass = areas/dx, areas*dx/6
    kd = np.r_[stiffness[0], stiffness[:-1]+stiffness[1:]]
    md = 2*np.r_[mass[0], mass[:-1]+mass[1:]]
    rhs = np.zeros(cells); rhs[0] = 1
    result = []
    for f in hz:
        k = 2*np.pi*f/343 - 1j*z[-1]*np.sqrt(max(f,1)/1000)
        off = -stiffness[:-1] - k*k*mass[:-1]
        ab = np.zeros((3,cells),complex)
        ab[0,1:] = off; ab[1] = kd-k*k*md; ab[2,:-1] = off
        p = solve_banded((1,1), ab, rhs)
        result.append(areas[-1]*p[-1]/dx)
    return np.array(result)


def pulse(n, f0):
    phase = np.mod(np.arange(n)*f0/SR,1)
    q = np.zeros(n)
    a = phase < OPEN; b = (phase >= OPEN)&(phase < OPEN+CLOSE)
    q[a] = .5*(1-np.cos(np.pi*phase[a]/OPEN))
    q[b] = np.cos(np.pi*(phase[b]-OPEN)/(2*CLOSE))
    return q


def synth(z, duration=2.32, f0=F0):
    n = round(duration*SR); nf = 2**int(np.ceil(np.log2(n+SR)))
    hz = np.fft.rfftfreq(nf,1/SR)
    q = pulse(n,f0); q[:1200] *= np.linspace(0,1,1200)
    spectrum = np.fft.rfft(q,nf)/(1+1j*hz/LOWPASS)
    y = np.fft.irfft(spectrum*transfer(z,hz)*1j*2*np.pi*hz*np.exp(-(hz/6500)**8),nf)[:n]
    y -= y.mean(); y *= .115/max(np.sqrt(np.mean(y*y)),1e-12)
    y[:1200] *= np.linspace(0,1,1200); y[-1200:] *= np.linspace(1,0,1200)
    return y*min(1,.88/max(abs(y)))


def save(path,y):
    write(path,SR,np.round(y*32767).astype(np.int16))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,default=ROOT/'output')
    p.add_argument('--pitch',type=float,default=F0)
    p.add_argument('--fit',action='store_true',help='Refit the supplied measured spectral target')
    args = p.parse_args()
    if not 45 <= args.pitch <= 300: p.error('pitch must be 45–300 Hz')
    args.out.mkdir(parents=True,exist_ok=True)
    trace=json.loads((ROOT/'data/search-trace.json').read_text())
    initial=np.array(trace['states'][0]['parameters']); final=np.array(trace['final_parameters'])
    if args.fit:
        target=json.loads((ROOT/'data/target.json').read_text())
        hz=np.array(target['frequency_hz']); db=np.array(target['transfer_db'])
        def objective(z):
            err=20*np.log10(np.maximum(abs(transfer(z,hz)),1e-12))-db
            err-=err.mean()
            return np.r_[err/10,.035*np.diff(z[1:17],2)]
        fit=least_squares(objective,initial,bounds=(np.r_[.14,np.full(16,np.log(.05)),.2],np.r_[.32,np.full(16,np.log(20)),16]),max_nfev=240)
        final=fit.x  # A fresh one-start fit, not a claim to reproduce the seven-start optimum.
    hz=np.arange(80.,4001.,10.)
    h=transfer(final,hz); fem=finite_element(final,hz)
    error=float(np.max(abs(20*np.log10(abs(fem/h)))))
    assert error<.1, error
    before=synth(initial,f0=args.pitch); after=synth(final,f0=args.pitch)
    assert np.isfinite(after).all() and np.sqrt(np.mean((before-after)**2))>.01
    save(args.out/'initial.wav',before);save(args.out/'final.wav',after)
    save(args.out/'comparison.wav',np.r_[before,np.zeros(int(.7*SR)),after])
    np.savetxt(args.out/'response.csv',np.c_[hz,abs(h),abs(fem)],delimiter=',',header='Hz,TMM_magnitude,FEM_magnitude',comments='')
    report={'parameters':final.tolist(),'length_mm':float(final[0]*1000),'section_inner_diameter_mm':(2*np.sqrt(np.exp(final[1:17])*100/np.pi)).tolist(),'fem_tmm_max_db_80_4000':error,'pitch_hz':args.pitch,'sample_rate':SR,'seconds_per_sample':len(after)/SR,'source':'Analytic continuous pulse, no recorded voice mixed in','fit':args.fit}
    (args.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
