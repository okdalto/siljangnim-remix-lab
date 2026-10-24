"""UI-free PyOpenGL convolution study on a padded 9:16 portrait canvas.

Space pause, R replay, 1–5 stages, arrows seek, Escape close.
Drop an image to replace the default dog photograph.
"""
from pathlib import Path
import argparse
import ctypes
import time
import math
from functools import lru_cache
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
from camera_framing import project_boxes,fit_camera,sample_camera_path,BASIS

ROOT = Path(__file__).resolve().parent
SIZE = 32
# Match the valid 30x30 output's visible front-face bounds to the 32x32 photo.
LOOP_RATIO=((SIZE-3)+2*.435)/SIZE
PIXELIZE_START, SPLIT_START = 1.1, 5.1
SCAN_START, FIRST_CELL, CELL_TIME = 7.3, 8.10, .004
DETAILED_CELLS = 2
SWEEP_RAMP=4.
SWEEP_BRAKE=2.8
LANDING_HOLD=.35
SWEEP_FIRST_CELL=.35
_SWEEP_TIME=np.linspace(0.,SWEEP_RAMP,4097)
_SWEEP_U=_SWEEP_TIME/SWEEP_RAMP
_SWEEP_EASE=_SWEEP_U**3*(_SWEEP_U*(_SWEEP_U*6-15)+10)
# Ease the logarithm of velocity, so the first few outputs also accelerate
# gradually instead of a large final rate overwhelming the initial slow rate.
_SWEEP_RATE=(1/SWEEP_FIRST_CELL)*np.exp(math.log(SWEEP_FIRST_CELL/CELL_TIME)*_SWEEP_EASE)
_SWEEP_COUNT=np.r_[0.,np.cumsum((_SWEEP_RATE[:-1]+_SWEEP_RATE[1:])*.5*np.diff(_SWEEP_TIME))]
_BRAKE_TIME=np.linspace(0.,SWEEP_BRAKE,4097)
_BRAKE_U=_BRAKE_TIME/SWEEP_BRAKE
_BRAKE_EASE=_BRAKE_U**3*(_BRAKE_U*(_BRAKE_U*6-15)+10)
_BRAKE_RATE=(1/CELL_TIME)*(1-_BRAKE_EASE)
_BRAKE_COUNT=np.r_[0.,np.cumsum((_BRAKE_RATE[:-1]+_BRAKE_RATE[1:])*.5*np.diff(_BRAKE_TIME))]
_SWEEP_TOTAL=(SIZE-2)**2-DETAILED_CELLS
SWEEP_CRUISE=(_SWEEP_TOTAL-_SWEEP_COUNT[-1]-_BRAKE_COUNT[-1])*CELL_TIME
SWEEP_BRAKE_START=SWEEP_RAMP+SWEEP_CRUISE
SWEEP_DURATION=SWEEP_BRAKE_START+SWEEP_BRAKE


def sweep_cells(elapsed):
    """Integrate acceleration, cruise, and a quintic brake to zero velocity."""
    elapsed=max(0.,elapsed)
    if elapsed<=SWEEP_RAMP:
        return float(np.interp(elapsed,_SWEEP_TIME,_SWEEP_COUNT))
    cruise=min(elapsed-SWEEP_RAMP,SWEEP_CRUISE)/CELL_TIME
    brake=float(np.interp(max(elapsed-SWEEP_BRAKE_START,0.),_BRAKE_TIME,_BRAKE_COUNT))
    return min(_SWEEP_TOTAL,float(_SWEEP_COUNT[-1])+cruise+brake)


SCAN_END = SCAN_START + DETAILED_CELLS*FIRST_CELL + SWEEP_DURATION
DURATION = SCAN_END + LANDING_HOLD + 6
LOOP_BLEND_START=SCAN_END+LANDING_HOLD+4.
LOOP_BLEND_DURATION=1.65
STAGES = [0., SPLIT_START+1.2, 3.5, SCAN_START+.4, SCAN_END+4]
# Shared CPU/GPU stage durations: pop, merge, spatial sum, RGB sum, delivery,
# filter travel, camera, split, filter entry, output framing.
PHASE_TIMING=np.array([1.65,.10,2.60,1.10,4.25,1.90,4.25,1.90,6.30,1.80,
                      7.70,.40,2.30,6.25,2.10,1.20,2.5,.85,6.15,2.10],dtype=np.float32)
MERGE_LOOP_START,MERGE_LOOP_END = SCAN_START+2.45,SCAN_START+6.20


def easing(x):
    x=min(1.,max(0.,x))
    return x*x*x*(x*(x*6-15)+10)


def sweep_motion_visibility(t,speed=.80):
    start=SCAN_START+DETAILED_CELLS*FIRST_CELL
    if t<start:return 1.
    if t>=SCAN_END:return 0.
    rate=float(np.interp(min(t-start,SWEEP_RAMP),_SWEEP_TIME,_SWEEP_RATE))
    interval=1/(rate*max(speed,.01))
    # Full motion above ~14 frames at 60 FPS; reduce it to nothing below 4–5.
    return easing((interval-.075)/(.24-.075))


def spring_response(x,damping):
    if x<=0:return 0.
    if x>=1:return 1.
    s=math.sqrt(1-damping*damping)
    y=1-math.exp(-damping*11*x)*(math.cos(11*s*x)+damping/s*math.sin(11*s*x))
    return y+(1-y)*easing((x-.78)/.22)


def motion_values(t):
    """Evaluate uniform springs once per frame, never per raymarch sample."""
    p=PHASE_TIMING
    state=min(scan_at(t),(SIZE-2)**2-.0001)
    index=math.floor(state)
    cycle=state-math.floor(state)
    sec=cycle*FIRST_CELL
    detail=index<DETAILED_CELLS
    merge=easing((sec-p[2])/p[3] if detail else (cycle-.30)/.23)
    travel=spring_response((sec-p[10])/p[11] if detail else (cycle-.78)/.22,.80)
    if not detail:
        # Once the explanatory geometry has faded, use the full cell interval
        # for the frame's travel so the braking tail does not twitch then wait.
        sweep_elapsed=t-SCAN_START-DETAILED_CELLS*FIRST_CELL
        landing_blend=easing((sweep_elapsed-SWEEP_RAMP)/.7)
        travel=travel*(1-landing_blend)+spring_response(cycle,.95)*landing_blend
    values=[spring_response((t-SPLIT_START)/p[15],.76),
            spring_response((sec-p[4])/p[5] if detail else (cycle-.57)/.15,.78),
            spring_response((sec-p[6])/p[7] if detail else (cycle-.66)/.12,.80),
            easing((sec-p[8])/p[9]) if detail else 0.,
            travel,
            spring_response((t-PIXELIZE_START)/1.2,.82),
            spring_response((t-p[16])/p[17],.82),
            spring_response(sec/.25 if detail else cycle/.15,.82),
            spring_response(merge/.52,.80),spring_response((merge-.65)/.35,.90),
            spring_response(sec/p[12],.90),spring_response((sec-p[13])/p[14],.90),
            spring_response((t-(SCAN_START+p[18]))/p[19],.90),
            spring_response((t-SCAN_END-LANDING_HOLD)/3.,.90),spring_response((t-SPLIT_START)/p[15],.90)]
    values += [spring_response((sec-order*p[1])/p[0] if detail else (cycle-order*.016)/.13,.68)
               for order in range(9)]
    return np.array(values+[index,cycle],dtype=np.float32)


def filter_motion_values(t):
    """Stagger individual weights while keeping each XY/Z approach synchronized."""
    state=min(scan_at(t),(SIZE-2)**2-.0001)
    index=math.floor(state);cycle=state-index
    detail=index<DETAILED_CELLS
    sec=cycle*FIRST_CELL
    values=[]
    for channel in range(3):
        for order in range(9):
            if detail:
                delay=order*.045+channel*.018
                merge=easing((sec-PHASE_TIMING[2]-delay)/PHASE_TIMING[3])
            else:
                delay=order*.003+channel*.001
                merge=easing((cycle-.30-delay)/.23)
            values.extend((spring_response(merge/.52,.80),
                           spring_response((merge-.65)/.35,.90),merge))
    return np.asarray(values,dtype=np.float32)


def gather_motion_values(t):
    """Delay each contribution, then converge all 27 into the same pixel."""
    state=min(scan_at(t),(SIZE-2)**2-.0001)
    index=math.floor(state);cycle=state-index
    detail=index<DETAILED_CELLS
    sec=cycle*FIRST_CELL
    values=[]
    for channel in range(3):
        for order in range(9):
            if detail:
                delay=order*.035+channel*.012
                phase=(sec-PHASE_TIMING[4]-delay)/(PHASE_TIMING[5]-.304)
            else:
                delay=order*.003+channel*.001
                phase=(cycle-.57-delay)/(.15-.026)
            values.append(spring_response(phase,.78))
    return np.asarray(values+[min(values)],dtype=np.float32)


def source_scale_values(t,speed=.80):
    """Vacate extracted pixels, then regrow their source cells after departure."""
    if t<SCAN_START or t>=SCAN_END:return np.ones(9,dtype=np.float32)
    m=motion_values(t)
    detail=m[24]<DETAILED_CELLS
    if not detail and sweep_motion_visibility(t,speed)<=.06:
        return np.ones(9,dtype=np.float32)
    cycle=float(m[25]);sec=cycle*FIRST_CELL
    result=[]
    for order in range(9):
        if m[15+order]<=.001:scale=1.
        elif detail:
            elapsed=sec-order*float(PHASE_TIMING[1])
            scale=spring_response((elapsed-float(PHASE_TIMING[0])-.08)/.50,.82)
        else:
            elapsed=cycle-order*.016
            scale=spring_response((elapsed-.13-.02)/.12,.82)
        result.append(scale)
    return np.asarray(result,dtype=np.float32)


def merge_loop_time(clock):
    span=MERGE_LOOP_END-MERGE_LOOP_START
    # Hold briefly on the separate and joined shapes for comparison.
    phase=clock%(span+.80)
    return MERGE_LOOP_START+float(np.clip(phase-.25,0,span))


def kernel(axis):
    k = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=np.float32)
    return k if axis == 0 else k.T


def sobel(image):
    windows = np.lib.stride_tricks.sliding_window_view(image,(3,3),axis=(0,1))
    gradients = [np.einsum('xycij,ij->xyc',windows,kernel(a)) for a in range(2)]
    gx, gy = [g @ np.array([.2126,.7152,.0722]) for g in gradients]
    return gradients, np.clip(np.hypot(gx,gy)/4,0,1)


def load_image(path, size=SIZE):
    with Image.open(path) as image:
        square = ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'),
                              (size,size),Image.Resampling.LANCZOS)
        return np.ascontiguousarray(np.asarray(square)[::-1],dtype=np.float32)/255


def scan_at(t):
    s = max(t-SCAN_START,0)
    return min(s/FIRST_CELL if s < DETAILED_CELLS*FIRST_CELL else DETAILED_CELLS+sweep_cells(s-DETAILED_CELLS*FIRST_CELL),
               (SIZE-2)**2)


def scan_cell(index):
    width=SIZE-2
    row,column=divmod(index,width)
    return column+1,width-row


def label_opacity(t):
    start=float(PHASE_TIMING[16]+PHASE_TIMING[17])+.1
    return easing((t-start)/.4)*(1-easing((t-(SPLIT_START-.45))/.4))


def scene_envelopes(t,m=None,speed=.80):
    """World AABBs of the actual shader boxes; hidden prefetch racks are excluded."""
    if m is None:m=motion_values(t)
    p=PHASE_TIMING;pitch=5.76/SIZE
    index=int(m[24]);cycle=float(m[25]);sec=cycle*FIRST_CELL
    detail=index<DETAILED_CELLS
    running=SCAN_START<=t<SCAN_END
    visibility=1. if detail else sweep_motion_visibility(t,speed)
    animate=detail or visibility>.06
    gather=easing((sec-p[4])/p[5] if detail else (cycle-.57)/.15)
    deposit=easing((sec-p[8])/p[9]) if detail else 0.
    complete=deposit>=1. if detail else not animate or gather>=1.
    context=[];work=[]
    def add(collection,center,half):
        collection.append(np.r_[center,np.broadcast_to(half,(3,))])
    outro=easing((t-SCAN_END-LANDING_HOLD)/3.)
    edge=2.88
    for c in range(3):
        add(context,[-5*outro,0,(1-c)*.95*m[0]],[edge,edge,.065])
        if m[0]==0:break
    # Use the same visibility and scale as the shader, including caption fades.
    if PHASE_TIMING[16]<=t<SCAN_START and m[6]>.001:
        for c in range(3):
            add(context,[-3.5,2.2,1.99+(1-c)*.95*m[0]],
                [pitch*(1+.435*m[6]),pitch*(1+.435*m[6]),.065*m[6]])
            if m[0]==0:break
    if label_opacity(t)>.001:
        add(context,[0,-3.55,0],[1.45/2,1.45/8,0])
        add(context,[-3.5,1.55,1.99],[1.20/2,1.20/8,0])
    completed=900 if t>=SCAN_END else index+int(complete) if running else 0
    full_rows,partial=divmod(completed,SIZE-2)
    def output_rect(x0,x1,y0,y1):
        lo=np.array([6.5+(x0-15.5)*pitch,(y0-15.5)*pitch,0.])
        hi=np.array([6.5+(x1-15.5)*pitch,(y1-15.5)*pitch,0.])
        add(context,(lo+hi)*.5,(hi-lo)*.5+[pitch*.435,pitch*.435,.065])
    if full_rows:output_rect(1,30,31-full_rows,30)
    if partial:output_rect(1,partial,30-full_rows,30-full_rows)
    if running and animate and not complete:
        x,y=scan_cell(index)
        window=np.array([(x-15.5)*pitch,(y-15.5)*pitch,0.])
        destination=window+[6.5,0,0]
        macro=np.array([-3.9,3.9,1.75])
        if gather>=1.:
            center=macro if detail else window+[0,0,1.3]
            amount=float(m[3])
            position=center*(1-amount)+destination*amount+np.array([0,.9,.65])*math.sin(amount*math.pi)
            add(work,position,[pitch*.435,pitch*.435,.065])
        else:
            filters=filter_motion_values(t).reshape(3,9,3)
            gather_values=gather_motion_values(t)
            gathers=gather_values[:27].reshape(3,9)
            field=float(np.clip(gather_values[27],0,1))
            gather_pad=.85*(.034 if detail else .026)*easing(field/.16)*math.log(27)*(1-easing((field-.55)/.45))
            front=.95*float(m[0])+.065
            for c in range(3):
                home_center=window+[0,0,(1-c)*.95]
                stage=macro+[0,0,(1-c)*.95] if detail else window+[0,0,front+.32+(2-c)*.60*visibility]
                reduced=macro if detail else window+[0,0,front+.20+.48*visibility]
                for order in range(9):
                    j,i=divmod(order,3);tap=np.array([i-1,1-j,0.])*pitch
                    staged=stage+tap
                    pop=float(m[15+order]);converge=float(gathers[c,order])
                    pos=(home_center+tap)*(1-pop)+staged*pop
                    pos=pos*(1-converge)+reduced*converge
                    pos=pos*(1-m[3])+destination*m[3]
                    approach,contact,merge=filters[c,order]
                    bulge=.85*math.sin(merge*math.pi)*(1-gather)
                    body=np.array([pitch*.435*(1+.055*bulge)]*2+[.065*(1+.24*bulge)])*visibility
                    gap=(.24*(1-approach)+(2*.065*(1+.24*bulge)+.07)*approach)*(1-np.clip(contact,0,1))*visibility
                    parked=staged-[.66*visibility,0,0]
                    if detail:
                        intro=np.array([-3.5,2.2,1.75])+tap+[0,0,(1-c)*.95*m[0]]
                        parked=intro*(1-m[10])+parked*m[10]
                    weight=parked*(1-approach)+pos*approach+[0,0,gap]
                    attraction=easing((merge-.60)/.32)
                    settle=easing((merge-.72)/.28)
                    pair_pad=(.85*pitch*.435*1.9*attraction*(1-.67*settle)*(1-field)*visibility+.0001)/4
                    pad=pair_pad+gather_pad*visibility+.002
                    add(work,pos,body+pad)
                    add(work,weight,body*float(m[6])+pad)
    context.extend(work)
    return np.asarray(context).reshape(-1,6),np.asarray(work).reshape(-1,6)


def framing_bounds(t,m=None,speed=.80):
    """Return projected context and work bounds for fitting and audit."""
    context,work=scene_envelopes(t,m,speed)
    return project_boxes(context),project_boxes(work) if len(work) else None


def framing_subject(t,m=None,speed=.80):
    """Visible subjects: active work in close-ups, output in the final shot."""
    if t>=SCAN_END:
        context,_=scene_envelopes(t,m,speed)
        return project_boxes([box for box in context if box[0]>3.])
    context,work=framing_bounds(t,m,speed)
    return work if work is not None else context


@lru_cache(maxsize=1)
def closing_bounds():
    shift=BASIS@(np.array([6.5,0,.065])-LOOP_RATIO*np.array([0,0,.065]))
    return framing_bounds(0.)[0]*LOOP_RATIO+np.r_[shift,shift]


def camera_target(t,m=None,speed=.80):
    """Fit visible subjects for geometric diagnostics."""
    if m is None:m=motion_values(t)
    return fit_camera(framing_subject(t,m,speed))


def shot_transition(t,start,end):
    return easing((t-start)/(end-start))


@lru_cache(maxsize=4)
def camera_path(speed,phase_signature):
    """Fixed shots joined only at scene boundaries, with no spring tracking."""
    times=np.arange(int(np.ceil(DURATION*120))+1)/120.
    def union_bounds(items):
        items=np.asarray(items)
        return np.r_[items[:,:2].min(axis=0),items[:,2:].max(axis=0)]
    opening=fit_camera(framing_bounds(0.)[0],margin=.12)
    intro=fit_camera(union_bounds([framing_bounds(t)[0]
        for t in np.linspace(float(PHASE_TIMING[16])+.01,SCAN_START,181)]))
    macro=fit_camera(union_bounds([framing_bounds(t)[1]
        for t in np.linspace(SCAN_START+2.3,SCAN_START+6.15,241)]))
    overview=fit_camera(union_bounds([framing_bounds(t,speed=speed)[0]
        for t in np.linspace(SCAN_START+DETAILED_CELLS*FIRST_CELL,SCAN_END,301)]))
    intro[3]*=1.07
    macro[3]*=1.20
    overview[3]*=1.12
    closing=fit_camera(closing_bounds(),margin=.12)
    poses=np.tile(opening,(len(times),1))
    def transition(start,end,source,target):
        weights=np.array([shot_transition(t,start,end) for t in times])
        active=times>=start
        poses[active]=source+(target-source)*weights[active,None]
    transition(float(PHASE_TIMING[16]),4.7,opening,intro)
    previous=intro
    for index in range(DETAILED_CELLS):
        start=SCAN_START+index*FIRST_CELL
        transition(start,start+2.3,previous,macro)
        transition(start+6.15,start+FIRST_CELL,macro,overview)
        previous=overview
    transition(SCAN_END+LANDING_HOLD,SCAN_END+LANDING_HOLD+3.4,overview,closing)
    return times,poses


class CameraRig:
    """Fixed scene compositions with slow, non-overshooting transitions."""
    def __init__(self,speed=.80):
        self.times,self.poses=camera_path(speed,tuple(float(v) for v in PHASE_TIMING))

    def sample(self,t):
        return sample_camera_path(self.times,self.poses,t)


def self_test():
    # Absolute-basis extents must equal explicit projection of all eight corners.
    corners=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)])
    for box in ([2.,-1.,.5,.0783,.0783,.065],[-3.5,2.2,1.99,.26,.26,.95]):
        points=(np.array(box[:3])+corners*np.array(box[3:]))@BASIS.T
        expected=np.r_[points.min(axis=0),points.max(axis=0)]
        assert np.allclose(project_boxes([box]),expected)
    assert len(scene_envelopes(0.)[0])==1
    assert len(scene_envelopes(float(PHASE_TIMING[16])-.01)[0])==1
    assert len(scene_envelopes(float(PHASE_TIMING[16])+.1)[0])==2
    rig=CameraRig()
    assert np.allclose(rig.sample(0)[:3],rig.sample(float(PHASE_TIMING[16]))[:3])
    assert np.allclose(rig.sample(0),rig.sample(1.5))
    image = np.full((SIZE,SIZE,3),.5,dtype=np.float32)
    _, out = sobel(image)
    assert np.allclose(out,0)
    image[:,:SIZE//2] = 0
    image[:,SIZE//2:] = 1
    gradients, out = sobel(image)
    assert np.allclose(gradients[0][:,SIZE//2-2:SIZE//2],4)
    assert np.allclose(gradients[1],0)
    assert np.allclose(out[:,SIZE//2-2:SIZE//2],1)
    gradients, out = sobel(image.transpose(1,0,2))
    assert np.allclose(gradients[0],0)
    assert np.allclose(gradients[1][SIZE//2-2:SIZE//2],4)
    assert out.shape == (SIZE-2,SIZE-2)
    assert scan_at(SCAN_START)==0 and np.isclose(scan_at(SCAN_START+FIRST_CELL),1)
    assert abs(scan_at(SCAN_END)-(SIZE-2)**2)<1e-4
    assert np.isclose(scan_at(SCAN_START+DETAILED_CELLS*FIRST_CELL),DETAILED_CELLS)
    positions=[scan_cell(i) for i in range((SIZE-2)**2)]
    assert positions[0]==(1,SIZE-2) and positions[1]==(2,SIZE-2)
    assert positions[SIZE-2]==(1,SIZE-3)
    assert len(set(positions))==(SIZE-2)**2
    assert all((b==(a[0]+1,a[1])) if a[0]<SIZE-2 else b==(1,a[1]-1)
               for a,b in zip(positions,positions[1:]))
    assert np.isclose(sweep_cells(SWEEP_DURATION),(SIZE-2)**2-DETAILED_CELLS)
    assert np.isclose(sweep_cells(.0001)/.0001,1/SWEEP_FIRST_CELL,rtol=1e-4)
    assert np.isclose((sweep_cells(SWEEP_RAMP+.0001)-sweep_cells(SWEEP_RAMP))/.0001,1/CELL_TIME)
    assert SWEEP_CRUISE>0 and _BRAKE_RATE[-1]==0.
    assert np.all(np.diff(_BRAKE_RATE)<=1e-10)
    assert abs((sweep_cells(SWEEP_DURATION)-sweep_cells(SWEEP_DURATION-.001))/.001)<.001
    assert sweep_cells(SWEEP_DURATION+1)==sweep_cells(SWEEP_DURATION)
    assert motion_values(SCAN_END+LANDING_HOLD*.5)[13]==0.
    assert LOOP_BLEND_START>SCAN_END+LANDING_HOLD+3.
    assert LOOP_BLEND_START+LOOP_BLEND_DURATION<DURATION
    assert easing((DURATION-LOOP_BLEND_START)/LOOP_BLEND_DURATION)==1.
    assert np.all(np.diff([sweep_cells(t) for t in np.linspace(0,SWEEP_DURATION,1000)])>0)
    visibility=[sweep_motion_visibility(SCAN_START+DETAILED_CELLS*FIRST_CELL+t)
                for t in np.linspace(0,SWEEP_DURATION,1000)]
    assert visibility[0]==1. and visibility[-1]==0.
    assert np.all(np.diff(visibility)<=1e-10)
    rig=CameraRig()
    start=rig.sample(SCAN_START+.7)
    rig.sample(SCAN_START+2.)
    assert np.array_equal(start,rig.sample(SCAN_START+.7))
    assert np.linalg.norm(start[:3]-camera_target(SCAN_START+.7)[:3])>.01
    # Every convolution holds one identical pose from multiplication to sum.
    for index in range(DETAILED_CELLS):
        held=[rig.sample(SCAN_START+index*FIRST_CELL+sec)
              for sec in np.linspace(2.31,6.14,121)]
        assert np.max(np.abs(np.asarray(held)-held[0]))<1e-12
    sweep=[rig.sample(t) for t in np.linspace(SCAN_START+DETAILED_CELLS*FIRST_CELL+.01,
                                             SCAN_END+LANDING_HOLD-.01,121)]
    assert np.max(np.abs(np.asarray(sweep)-sweep[0]))<1e-9
    # Loop framing: all four front-face corners coincide in view space.
    opening=rig.sample(0.)
    closing=rig.sample(DURATION)
    from camera_framing import margins
    critical=[0.,3.9,SPLIT_START+.6,SCAN_START+.9,SCAN_START+4.8,
              SCAN_START+PHASE_TIMING[8]+.18,SCAN_START+FIRST_CELL+.9,SCAN_END,DURATION]
    for t in critical:
        view_margins=margins(rig.sample(float(t)),framing_subject(float(t)))
        assert view_margins.min()>=.06-1e-6
    # Velocity and acceleration must also join continuously between path samples.
    knot=round((SCAN_START+PHASE_TIMING[8]+.3)*120)/120
    eps=1e-4
    before2,before,at,after,after2=[rig.sample(knot+i*eps) for i in (-2,-1,0,1,2)]
    assert np.linalg.norm((at-before)/eps-(after-at)/eps)<.1
    assert np.linalg.norm((at-2*before+before2)/eps**2-(after2-2*after+at)/eps**2)<1.
    forward=-np.array([13.,10.,18.]);forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    basis=np.array([right,up])
    for x,y in ((-1,-1),(-1,1),(1,-1),(1,1)):
        first=np.array([2.88*x,2.88*y,.065])
        last=np.array([6.5+2.88*LOOP_RATIO*x,2.88*LOOP_RATIO*y,.065])
        a=basis@(first-opening[:3])/opening[3]
        b=basis@(last-closing[:3])/closing[3]
        assert np.allclose(a,b,atol=1e-6)
    staggered=filter_motion_values(SCAN_START+3.15).reshape(3,9,3)
    assert staggered[0,0,2]>staggered[0,-1,2]
    assert np.all(np.diff(staggered[:,:,2],axis=1)<=0)
    assert np.all(np.diff(staggered[:,:,2],axis=0)<=0)
    assert np.allclose(filter_motion_values(SCAN_START+float(PHASE_TIMING[4]))[2::3],1.)
    gathered=gather_motion_values(SCAN_START+float(PHASE_TIMING[4])+.25)[:27].reshape(3,9)
    assert gathered[0,0]>gathered[-1,-1]
    assert gathered[-1,-1]==0.
    gather_end=SCAN_START+float(PHASE_TIMING[4]+PHASE_TIMING[5])
    assert np.allclose(gather_motion_values(gather_end),1.,atol=1e-6)
    assert PHASE_TIMING[8]>PHASE_TIMING[4]+PHASE_TIMING[5]
    departing=source_scale_values(SCAN_START+.4)
    assert departing[0]==0. and departing[-1]==1.
    rebuilding=source_scale_values(SCAN_START+float(PHASE_TIMING[0])+.20)
    assert 0.<rebuilding[0]<1. and rebuilding[-1]==0.
    assert np.allclose(source_scale_values(SCAN_START+3.2),1.)
    assert np.allclose(source_scale_values(0.),1.)
    # Before contact closes, even the bulged surfaces must remain separated.
    for sec in np.linspace(float(PHASE_TIMING[2]),float(PHASE_TIMING[2]+PHASE_TIMING[3]),301):
        m=motion_values(SCAN_START+sec)
        merge=easing((sec-PHASE_TIMING[2])/PHASE_TIMING[3])
        half_depth=.065*(1+.24*.85*math.sin(merge*math.pi))
        near_gap=2*half_depth+.07
        center_gap=(.24*(1-float(m[8]))+near_gap*float(m[8]))*(1-float(np.clip(m[9],0,1)))
        if merge<=.65:assert center_gap-2*half_depth>.068
        if m[9]>0:assert np.isclose(m[8],1.)
    # A new rack must start fully outside the view and reach the exact position
    # used by the following operation before ownership switches at its boundary.
    for index in range(DETAILED_CELLS):
        prepare_start=SCAN_START+index*FIRST_CELL+float(PHASE_TIMING[8])+.25
        rack,layer=prepared_filter(prepare_start,rig)
        pose=rig.sample(prepare_start)
        forward=-np.array([13.,10.,18.]);forward/=np.linalg.norm(forward)
        right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right)
        # Include all channel layers and the full 3x3 patch extent.
        rightmost=np.dot(rack[:3]-pose[:3],right)+abs(right[2])*layer+abs(right[0])*.27+.1
        assert rightmost < -pose[3]
        end=SCAN_START+(index+1)*FIRST_CELL-1e-5
        prepared,_=prepared_filter(end,rig)
        if index==0:expected=np.array([-3.5,2.2,1.99])
        else:
            x,y=scan_cell(index+1)
            expected=np.array([(x-15.5)*.18-.66,(y-15.5)*.18,2.175])
        assert np.allclose(prepared[:3],expected,atol=1e-5)
    # Check actual 3x3 RGB products against the vectorized response at several positions.
    dog=load_image(ROOT/'assets/dog.jpg')
    gradients,_=sobel(dog)
    for x,y in [positions[0],positions[1],positions[30],positions[-1]]:
        for axis in range(2):
            expected=np.sum(dog[y-1:y+2,x-1:x+2]*kernel(axis)[...,None],axis=(0,1))
            assert np.allclose(gradients[axis][y-1,x-1],expected,atol=1e-6)
    assert load_image(ROOT/'assets/dog.jpg').shape == (SIZE,SIZE,3)
    print('PASS: Sobel, raster order, acceleration, camera, filter preparation/continuity, pre-contact surface clearance')


def label_atlas():
    """Tracked technical monospace captions, rendered once at high resolution."""
    atlas=Image.new('L',(256,128))
    draw=ImageDraw.Draw(atlas)
    try:
        font=ImageFont.truetype('DejaVuSansMono.ttf',40)
    except OSError:
        font=ImageFont.load_default(size=40)
    for row,label in enumerate(('IMAGE','FILTER')):
        advances=[draw.textlength(letter,font=font)+9 for letter in label]
        x=(256-(sum(advances)-9))/2
        for letter,advance in zip(label,advances):
            draw.text((x,row*64+32),letter,font=font,fill=255,anchor='lm')
            x+=advance
    return np.ascontiguousarray(np.asarray(atlas)[::-1])


def footprint_vertices(t,m,pose):
    """Project the three flat 3x3 outlines into the current camera's view."""
    if t<SPLIT_START+1.2 or t>=SCAN_END+.6:return np.empty((0,3),dtype=np.float32)
    index=min(int(m[24]),(SIZE-2)**2-1)
    cell=np.array(scan_cell(index),dtype=float)
    following=np.array(scan_cell(min(index+1,(SIZE-2)**2-1)),dtype=float)
    cell+=(following-cell)*float(m[4])
    center=(cell-(SIZE-1)*.5)*(5.76/SIZE)
    offset=np.array([13.,10.,18.])
    forward=-offset/np.linalg.norm(offset)
    right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    corners=np.array([[-1,-1],[1,-1],[1,1],[-1,1]])*(1.5*5.76/SIZE)
    result=[]
    for channel in range(3):
        for edge in range(4):
            for corner in (edge,(edge+1)%4):
                world=np.r_[center+corners[corner],(1-channel)*.95*float(m[0])+.077]
                delta=world-pose[:3]
                depth=np.dot(delta-offset,forward)/47.
                result.append([np.dot(delta,right)/pose[3],np.dot(delta,up)/pose[3],depth*2-1])
    return np.asarray(result,dtype=np.float32)


def prepared_filter(t,camera):
    """Create the next explanatory rack outside the camera during delivery."""
    state=scan_at(t)
    index=int(state)
    if index>=DETAILED_CELLS:return np.zeros(4,dtype=np.float32),.95
    start=SCAN_START+index*FIRST_CELL+float(PHASE_TIMING[8])+.25
    if t<start:return np.zeros(4,dtype=np.float32),.95
    pose=camera.sample(start)
    forward=-np.array([13.,10.,18.]);forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,1,0]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    origin=pose[:3]-right*(pose[3]+1.6)+up*.25
    if index+1<DETAILED_CELLS:
        target=np.array([-3.5,2.2,1.99]);layer=.95
    else:
        x,y=scan_cell(index+1)
        target=np.array([(x-15.5)*.18-.66,(y-15.5)*.18,.95+.065+.32+.60+.24])
        layer=.60
    amount=spring_response((t-start)/1.5,.90)
    position=origin*(1-amount)+target*amount
    return np.array([*position,1.],dtype=np.float32),layer


class Explorer:
    def __init__(self,args):
        import glfw
        from OpenGL import GL
        from OpenGL.GL.shaders import compileProgram,compileShader
        self.glfw,self.gl = glfw,GL
        if not glfw.init():
            raise RuntimeError('GLFW could not initialize a display.')
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR,3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR,2)
        glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT,True)
        glfw.window_hint(glfw.DECORATED,False)
        glfw.window_hint(glfw.RESIZABLE,False)
        if args.capture: glfw.window_hint(glfw.VISIBLE,False)
        monitor=glfw.get_primary_monitor()
        mode=glfw.get_video_mode(monitor)
        window_height=min(960,max(320,(mode.size.height-100)//16*16))
        window_width=window_height*9//16
        self.window = glfw.create_window(window_width,window_height,'Convolution',None,None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError('OpenGL 3.2 core is required.')
        glfw.set_window_pos(self.window,max(0,(mode.size.width-window_width)//2),
                            max(30,(mode.size.height-window_height)//2))
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        self.program=GL.glCreateProgram()
        scene_shaders=[compileShader((ROOT/'shaders/scene.vert').read_text(),GL.GL_VERTEX_SHADER),
                       compileShader((ROOT/'shaders/scene.frag').read_text(),GL.GL_FRAGMENT_SHADER)]
        for shader in scene_shaders:GL.glAttachShader(self.program,shader)
        GL.glBindFragDataLocation(self.program,0,'fragColor')
        GL.glBindFragDataLocation(self.program,1,'surfaceInfo')
        GL.glLinkProgram(self.program)
        if not GL.glGetProgramiv(self.program,GL.GL_LINK_STATUS):
            raise RuntimeError(GL.glGetProgramInfoLog(self.program).decode())
        for shader in scene_shaders:GL.glDeleteShader(shader)
        self.line_program=compileProgram(
            compileShader((ROOT/'shaders/outline.vert').read_text(),GL.GL_VERTEX_SHADER),
            compileShader((ROOT/'shaders/outline.frag').read_text(),GL.GL_FRAGMENT_SHADER),validate=False)
        self.composite_program=compileProgram(
            compileShader((ROOT/'shaders/scene.vert').read_text(),GL.GL_VERTEX_SHADER),
            compileShader((ROOT/'shaders/composite.frag').read_text(),GL.GL_FRAGMENT_SHADER),validate=False)
        self.box_outline_program=compileProgram(
            compileShader((ROOT/'shaders/scene.vert').read_text(),GL.GL_VERTEX_SHADER),
            compileShader((ROOT/'shaders/box_outline.frag').read_text(),GL.GL_FRAGMENT_SHADER),validate=False)
        self.portrait_program=compileProgram(
            compileShader((ROOT/'shaders/scene.vert').read_text(),GL.GL_VERTEX_SHADER),
            compileShader((ROOT/'shaders/portrait.frag').read_text(),GL.GL_FRAGMENT_SHADER),validate=False)
        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)
        self.vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER,self.vbo)
        vertices = np.array([-1,-1,3,-1,-1,3],dtype=np.float32)
        GL.glBufferData(GL.GL_ARRAY_BUFFER,vertices.nbytes,vertices,GL.GL_STATIC_DRAW)
        loc = GL.glGetAttribLocation(self.program,'position')
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc,2,GL.GL_FLOAT,False,0,ctypes.c_void_p(0))
        self.composite_vao=GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.composite_vao)
        loc=GL.glGetAttribLocation(self.composite_program,'position')
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc,2,GL.GL_FLOAT,False,0,ctypes.c_void_p(0))
        self.box_outline_vao=GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.box_outline_vao)
        loc=GL.glGetAttribLocation(self.box_outline_program,'position')
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc,2,GL.GL_FLOAT,False,0,ctypes.c_void_p(0))
        self.portrait_vao=GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.portrait_vao)
        loc=GL.glGetAttribLocation(self.portrait_program,'position')
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc,2,GL.GL_FLOAT,False,0,ctypes.c_void_p(0))
        self.line_vao=GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.line_vao)
        self.line_vbo=GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER,self.line_vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER,24*3*4,None,GL.GL_STREAM_DRAW)
        loc=GL.glGetAttribLocation(self.line_program,'position')
        GL.glEnableVertexAttribArray(loc)
        GL.glVertexAttribPointer(loc,3,GL.GL_FLOAT,False,0,ctypes.c_void_p(0))
        self.textures = GL.glGenTextures(4)
        self.locations = {name:GL.glGetUniformLocation(self.program,name) for name in
            ('timeline','gridSize','sourceImage','photoImage','resultImage',
             'scanStart','firstCell','scanFinish','motion[0]','phaseTiming[0]',
             'introTiming','labelAtlas','preparedFilter','preparedLayer','labelOpacity','introOpacity',
             'filterMotion[0]','gatherMotion[0]','sourceScale[0]','sourceChanging')}
        self.locations['cameraPose']=GL.glGetUniformLocation(self.program,'cameraPose')
        self.locations['motionVisibility']=GL.glGetUniformLocation(self.program,'motionVisibility')
        # The driver trims unused trailing elements from GLSL uniform arrays.
        # Upload only the linked active range, especially on the Metal backend.
        self.phase_count=next(int(size) for name,size,_ in
            (GL.glGetActiveUniform(self.program,i) for i in range(GL.glGetProgramiv(self.program,GL.GL_ACTIVE_UNIFORMS)))
            if name in (b'phaseTiming[0]','phaseTiming[0]'))
        self.camera=CameraRig(args.speed)
        self.load(args.image or ROOT/'assets/dog.jpg')
        GL.glBindTexture(GL.GL_TEXTURE_2D,int(self.textures[3]))
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_R8,256,128,0,GL.GL_RED,GL.GL_UNSIGNED_BYTE,label_atlas())
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_LINEAR)
        for param in (GL.GL_TEXTURE_WRAP_S,GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_CLAMP_TO_EDGE)
        self.t,self.playing = args.time,not args.paused
        self.first_pass=True
        self.opening_cached=False
        self.loop_merge,self.loop_clock = args.loop_merge,0.
        if self.loop_merge:self.t=MERGE_LOOP_START
        self.speed = args.speed
        glfw.set_key_callback(self.window,self.key)
        glfw.set_drop_callback(self.window,self.drop)
        # Raymarch at logical resolution rather than 4x as many Retina pixels.
        self.render_size = args.resolution
        self.fbo = GL.glGenFramebuffers(1)
        self.color = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.color)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA8,self.render_size,self.render_size,
                        0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,None)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT0,
                                 GL.GL_TEXTURE_2D,self.color,0)
        self.surface=GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.surface)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA16F,self.render_size,self.render_size,
                        0,GL.GL_RGBA,GL.GL_FLOAT,None)
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_LINEAR)
        for param in (GL.GL_TEXTURE_WRAP_S,GL.GL_TEXTURE_WRAP_T):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_CLAMP_TO_EDGE)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT1,GL.GL_TEXTURE_2D,self.surface,0)
        self.depth=GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.depth)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_DEPTH_COMPONENT24,self.render_size,self.render_size,
                        0,GL.GL_DEPTH_COMPONENT,GL.GL_UNSIGNED_INT,None)
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_NEAREST)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_DEPTH_ATTACHMENT,GL.GL_TEXTURE_2D,self.depth,0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)!=GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError('Incomplete render framebuffer')
        self.line_fbo=GL.glGenFramebuffers(1)
        self.line_color=GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.line_color)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA8,self.render_size,self.render_size,
                        0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,None)
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_LINEAR)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.line_fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT0,GL.GL_TEXTURE_2D,self.line_color,0)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_DEPTH_ATTACHMENT,GL.GL_TEXTURE_2D,self.depth,0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)!=GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError('Incomplete outline framebuffer')
        self.loop_fbo=GL.glGenFramebuffers(1)
        self.loop_texture=GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.loop_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA8,self.render_size,self.render_size,
                        0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,None)
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_LINEAR)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.loop_fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT0,GL.GL_TEXTURE_2D,self.loop_texture,0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)!=GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError('Incomplete loop framebuffer')
        self.presentation_size=(self.render_size,round(self.render_size*16/9))
        self.presentation_fbo=GL.glGenFramebuffers(1)
        self.presentation_texture=GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D,self.presentation_texture)
        GL.glTexImage2D(GL.GL_TEXTURE_2D,0,GL.GL_RGBA8,*self.presentation_size,
                        0,GL.GL_RGBA,GL.GL_UNSIGNED_BYTE,None)
        for param in (GL.GL_TEXTURE_MIN_FILTER,GL.GL_TEXTURE_MAG_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D,param,GL.GL_LINEAR)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,self.presentation_fbo)
        GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,GL.GL_COLOR_ATTACHMENT0,GL.GL_TEXTURE_2D,self.presentation_texture,0)
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER)!=GL.GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError('Incomplete portrait framebuffer')
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER,0)
        self.cache_opening_frame()
        print('OpenGL:',GL.glGetString(GL.GL_VERSION).decode(),flush=True)

    def cache_opening_frame(self):
        """Cache the fully visible opening for a pixel-exact loop crossfade."""
        saved_t,saved_pass=self.t,self.first_pass
        self.t,self.first_pass=.95,False
        self.render()
        gl=self.gl
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER,self.fbo)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER,self.loop_fbo)
        s=self.render_size
        gl.glBlitFramebuffer(0,0,s,s,0,0,s,s,gl.GL_COLOR_BUFFER_BIT,gl.GL_NEAREST)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0)
        self.opening_cached=True
        self.t,self.first_pass=saved_t,saved_pass

    def load(self,path):
        gl = self.gl
        self.image = load_image(path)
        _,output = sobel(self.image)
        padded = np.zeros_like(self.image)
        padded[1:-1,1:-1] = output[...,None]
        for texture,data in zip(self.textures,(self.image,load_image(path,512),padded)):
            gl.glBindTexture(gl.GL_TEXTURE_2D,int(texture))
            h,w = data.shape[:2]
            gl.glTexImage2D(gl.GL_TEXTURE_2D,0,gl.GL_RGB32F,w,h,0,gl.GL_RGB,
                            gl.GL_FLOAT,np.ascontiguousarray(data))
            for param in (gl.GL_TEXTURE_MIN_FILTER,gl.GL_TEXTURE_MAG_FILTER):
                gl.glTexParameteri(gl.GL_TEXTURE_2D,param,gl.GL_LINEAR)
            for param in (gl.GL_TEXTURE_WRAP_S,gl.GL_TEXTURE_WRAP_T):
                gl.glTexParameteri(gl.GL_TEXTURE_2D,param,gl.GL_CLAMP_TO_EDGE)
        print('Image:',path,flush=True)

    def key(self,window,key,scancode,action,mods):
        g = self.glfw
        if action not in (g.PRESS,g.REPEAT): return
        if key==g.KEY_ESCAPE: g.set_window_should_close(window,True)
        elif key==g.KEY_SPACE: self.playing=not self.playing
        elif key==g.KEY_R:
            self.loop_clock=0.
            self.first_pass=True
            self.t,self.playing=(MERGE_LOOP_START if self.loop_merge else 0.),True
        elif g.KEY_1<=key<=g.KEY_5:
            self.loop_merge=False
            self.t=STAGES[key-g.KEY_1]
        elif key in (g.KEY_RIGHT,g.KEY_LEFT):
            delta=1 if key==g.KEY_RIGHT else -1
            if self.loop_merge:self.loop_clock=max(0.,self.loop_clock+delta)
            else:self.t=float(np.clip(self.t+delta,0,DURATION))

    def drop(self,window,paths):
        try:
            self.load(paths[0])
            self.t=0.
            self.first_pass=True
            self.opening_cached=False
            self.cache_opening_frame()
        except (OSError,ValueError) as error:
            print('Cannot load image:',error)

    def render(self):
        gl,g = self.gl,self.glfw
        fw,fh = g.get_framebuffer_size(self.window)
        if not fw or not fh: return
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.fbo)
        gl.glDrawBuffers(2,[gl.GL_COLOR_ATTACHMENT0,gl.GL_COLOR_ATTACHMENT1])
        gl.glViewport(0,0,self.render_size,self.render_size)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glDepthFunc(gl.GL_ALWAYS)
        gl.glDepthMask(gl.GL_TRUE)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        gl.glUseProgram(self.program)
        gl.glBindVertexArray(self.vao)
        gl.glUniform1f(self.locations['timeline'],self.t)
        gl.glUniform1f(self.locations['introOpacity'],easing(self.t/.85) if self.first_pass else 1.)
        gl.glUniform2f(self.locations['introTiming'],PIXELIZE_START,SPLIT_START)
        gl.glUniform1i(self.locations['gridSize'],SIZE)
        movements=motion_values(float(np.float32(self.t)))
        pose=self.camera.sample(self.t).astype(np.float32)
        gl.glUniform1fv(self.locations['motion[0]'],26,movements)
        gl.glUniform1fv(self.locations['filterMotion[0]'],81,filter_motion_values(float(np.float32(self.t))))
        gl.glUniform1fv(self.locations['gatherMotion[0]'],28,gather_motion_values(float(np.float32(self.t))))
        source_scales=source_scale_values(self.t,self.speed)
        gl.glUniform1fv(self.locations['sourceScale[0]'],9,source_scales)
        gl.glUniform1i(self.locations['sourceChanging'],int(np.any(np.abs(source_scales-1.)>.001)))
        gl.glUniform1fv(self.locations['phaseTiming[0]'],self.phase_count,PHASE_TIMING[:self.phase_count])
        gl.glUniform4fv(self.locations['cameraPose'],1,pose)
        prepared,layer=prepared_filter(self.t,self.camera)
        gl.glUniform4fv(self.locations['preparedFilter'],1,prepared)
        gl.glUniform1f(self.locations['preparedLayer'],layer)
        label_alpha=label_opacity(self.t)
        gl.glUniform1f(self.locations['labelOpacity'],label_alpha)
        gl.glUniform1f(self.locations['motionVisibility'],sweep_motion_visibility(self.t,self.speed))
        for name,value in [('scanStart',SCAN_START),('firstCell',FIRST_CELL),('scanFinish',SCAN_END)]:
            gl.glUniform1f(self.locations[name],value)
        for unit,(name,texture) in enumerate(zip(
                ('sourceImage','photoImage','resultImage','labelAtlas'),self.textures)):
            gl.glActiveTexture(gl.GL_TEXTURE0+unit)
            gl.glBindTexture(gl.GL_TEXTURE_2D,int(texture))
            gl.glUniform1i(self.locations[name],unit)
        gl.glDrawArrays(gl.GL_TRIANGLES,0,3)
        self.render_outlines(movements,pose)
        self.render_loop_blend()
        self.render_portrait()
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER,self.presentation_fbo)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER,0)
        gl.glBlitFramebuffer(0,0,*self.presentation_size,0,0,fw,fh,
                             gl.GL_COLOR_BUFFER_BIT,gl.GL_LINEAR)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,0)

    def render_outlines(self,movements,pose):
        gl=self.gl
        vertices=footprint_vertices(self.t,movements,pose)
        if self.t<PIXELIZE_START:
            gl.glDisable(gl.GL_DEPTH_TEST)
            return
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.line_fbo)
        gl.glClearColor(0,0,0,0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glDepthFunc(gl.GL_LEQUAL)
        gl.glDepthMask(gl.GL_FALSE)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA,gl.GL_ONE_MINUS_SRC_ALPHA,gl.GL_ONE,gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glUseProgram(self.box_outline_program)
        gl.glBindVertexArray(self.box_outline_vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D,self.surface)
        gl.glUniform1i(gl.glGetUniformLocation(self.box_outline_program,'surfaceImage'),0)
        gl.glUniform1f(gl.glGetUniformLocation(self.box_outline_program,'opacity'),.72*easing((self.t-PIXELIZE_START)/1.2))
        gl.glDrawArrays(gl.GL_TRIANGLES,0,3)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LINE_SMOOTH)
        gl.glLineWidth(1.)
        gl.glUseProgram(self.line_program)
        gl.glUniform1f(gl.glGetUniformLocation(self.line_program,'opacity'),
                       .85*easing((self.t-SPLIT_START-1.2)/.45)*(1-easing((self.t-SCAN_END)/.6)))
        gl.glBindVertexArray(self.line_vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER,self.line_vbo)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER,0,vertices.nbytes,vertices)
        gl.glDrawArrays(gl.GL_LINES,0,len(vertices))
        gl.glDisable(gl.GL_LINE_SMOOTH)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.fbo)
        gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glUseProgram(self.composite_program)
        gl.glBindVertexArray(self.composite_vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D,self.line_color)
        gl.glUniform1i(gl.glGetUniformLocation(self.composite_program,'outlineImage'),0)
        gl.glUniform1f(gl.glGetUniformLocation(self.composite_program,'layerOpacity'),1.)
        gl.glBlendFunc(gl.GL_ONE,gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDrawArrays(gl.GL_TRIANGLES,0,3)
        gl.glDisable(gl.GL_BLEND)
        gl.glDepthMask(gl.GL_TRUE)

    def render_loop_blend(self):
        alpha=easing((self.t-LOOP_BLEND_START)/LOOP_BLEND_DURATION)
        if not self.opening_cached or alpha<=0:return
        gl=self.gl
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.fbo)
        gl.glDrawBuffer(gl.GL_COLOR_ATTACHMENT0)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_ONE,gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glUseProgram(self.composite_program)
        gl.glBindVertexArray(self.composite_vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D,self.loop_texture)
        gl.glUniform1i(gl.glGetUniformLocation(self.composite_program,'outlineImage'),0)
        gl.glUniform1f(gl.glGetUniformLocation(self.composite_program,'layerOpacity'),alpha)
        gl.glDrawArrays(gl.GL_TRIANGLES,0,3)
        gl.glDisable(gl.GL_BLEND)

    def render_portrait(self):
        gl=self.gl
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.presentation_fbo)
        gl.glViewport(0,0,*self.presentation_size)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(self.portrait_program)
        gl.glBindVertexArray(self.portrait_vao)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D,self.color)
        gl.glUniform1i(gl.glGetUniformLocation(self.portrait_program,'squareImage'),0)
        gl.glUniform1f(gl.glGetUniformLocation(self.portrait_program,'aspect'),self.presentation_size[1]/self.presentation_size[0])
        gl.glDrawArrays(gl.GL_TRIANGLES,0,3)

    def run(self,args):
        gl,g = self.gl,self.glfw
        try:
            if args.capture:
                self.render()
                gl.glBindFramebuffer(gl.GL_FRAMEBUFFER,self.presentation_fbo)
                w,h=self.presentation_size
                raw=gl.glReadPixels(0,0,w,h,gl.GL_RGBA,gl.GL_UNSIGNED_BYTE)
                Image.frombytes('RGBA',(w,h),raw).transpose(
                    Image.Transpose.FLIP_TOP_BOTTOM).save(args.capture)
                print(f'Captured {args.capture} at {self.t:.2f}s')
                return
            previous=time.monotonic()
            frames=[]
            while not g.window_should_close(self.window):
                now=time.monotonic()
                dt=now-previous
                if self.playing:
                    if self.loop_merge:
                        self.loop_clock+=dt*self.speed
                        self.t=merge_loop_time(self.loop_clock)
                    else:
                        next_t=self.t+dt*self.speed
                        if next_t>=DURATION:self.first_pass=False
                        self.t=next_t%DURATION
                previous=now
                self.render()
                g.swap_buffers(self.window)
                g.poll_events()
                if args.benchmark:
                    frames.append(time.monotonic()-now)
                    if len(frames)>=120:
                        print(f'120 frames: {1/np.mean(frames):.1f} FPS',flush=True)
                        break
        finally:
            gl.glDeleteTextures([*map(int,self.textures),int(self.color),int(self.depth),int(self.line_color),int(self.surface),int(self.loop_texture),int(self.presentation_texture)])
            gl.glDeleteFramebuffers(4,[self.fbo,self.line_fbo,self.loop_fbo,self.presentation_fbo])
            gl.glDeleteBuffers(2,[self.vbo,self.line_vbo])
            gl.glDeleteVertexArrays(5,[self.vao,self.line_vao,self.composite_vao,self.box_outline_vao,self.portrait_vao])
            gl.glDeleteProgram(self.program)
            gl.glDeleteProgram(self.line_program)
            gl.glDeleteProgram(self.composite_program)
            gl.glDeleteProgram(self.box_outline_program)
            gl.glDeleteProgram(self.portrait_program)
            g.destroy_window(self.window)
            g.terminate()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path)
    parser.add_argument('--time',type=float,default=0.)
    parser.add_argument('--speed',type=float,default=.80)
    parser.add_argument('--resolution',type=int,default=720)
    parser.add_argument('--paused',action='store_true')
    parser.add_argument('--capture',type=Path)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--benchmark',action='store_true')
    parser.add_argument('--loop-merge',action='store_true',help='Repeat only the enlarged merging interval')
    args=parser.parse_args()
    if args.resolution<128: parser.error('--resolution must be at least 128')
    args.time=min(DURATION,max(0,args.time))
    if args.self_test: self_test()
    else: Explorer(args).run(args)


if __name__=='__main__': main()
