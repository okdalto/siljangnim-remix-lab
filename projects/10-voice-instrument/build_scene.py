"""Build a network-free Siljangnim document with geometry and computed audio."""
import json
import numpy as np
from run import ROOT,F0,OPEN,CLOSE,LOWPASS,transfer

def main():
    trace=json.loads((ROOT/'data/search-trace.json').read_text())
    states=[s['parameters'] for s in trace['states']]+[trace['final_parameters']]
    # Steady-state Fourier series of the same analytic pulse used by run.py.
    phase=np.arange(8192)/8192; q=np.zeros(8192)
    a=phase<OPEN;b=(phase>=OPEN)&(phase<OPEN+CLOSE)
    q[a]=.5*(1-np.cos(np.pi*phase[a]/OPEN));q[b]=np.cos(np.pi*(phase[b]-OPEN)/(2*CLOSE))
    hz=np.arange(1,149)*F0
    base=np.fft.rfft(q)[1:149]/8192/(1+1j*hz/LOWPASS)*1j*2*np.pi*hz*np.exp(-(hz/6500)**8)
    waves=[]
    for z in states:
        coeff=base*transfer(np.array(z),hz)
        coeff*=.115/np.sqrt(2*np.sum(abs(coeff)**2))
        waves.append([np.r_[0,2*coeff.real].tolist(),np.r_[0,-2*coeff.imag].tolist()])
    setup='const STATES='+json.dumps(states)+';\nconst WAVES='+json.dumps(waves)+';\n'+(ROOT/'scene-setup.js').read_text()
    scene={'version':2,'backend':'webgl2','script':{'setup':setup,'render':(ROOT/'scene-render.js').read_text(),'cleanup':"window.removeEventListener('pointerdown',ctx.state.unlock);if(ctx.state.audio)ctx.state.audio.close();"},'uniforms':{'u_candidate':{'type':'int','value':len(states)-1,'min':0,'max':len(states)-1,'step':1,'label':'Computed candidate'},'u_sound':{'type':'bool','value':True,'label':'Sound'}},'inputs':[]}
    md='# Voice to instrument — Siljangnim Remix Lab 10\n\nImport this document in Siljangnim, click the viewer to enable sound, and change Computed candidate. Geometry and audio coefficients come from the same 16-section transfer matrix. No external assets or API needed. Search states are precomputed; audio is a continuous analytic pulse through each candidate. See README for Python refitting and FEM verification.\n\n## Scene\n```json\n'+json.dumps(scene,ensure_ascii=False,indent=2)+'\n```\n'
    (ROOT/'project.md').write_text(md)
    print('Built project.md:',len(states),'candidates')

if __name__=='__main__':main()
