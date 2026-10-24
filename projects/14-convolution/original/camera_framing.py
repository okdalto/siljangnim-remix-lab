"""Orthographic camera fitting from projected world-space box corners."""
import numpy as np

FORWARD=-np.array([13.,10.,18.]);FORWARD/=np.linalg.norm(FORWARD)
RIGHT=np.cross(FORWARD,[0,1,0]);RIGHT/=np.linalg.norm(RIGHT)
UP=np.cross(RIGHT,FORWARD)
BASIS=np.array([RIGHT,UP])
TARGET_MARGIN=.10
SAFE_MARGIN=.06
MIN_FRAMING=1.60


def project_boxes(boxes):
    """Project all eight AABB corners, using the equivalent absolute basis."""
    boxes=np.asarray(boxes,dtype=float).reshape(-1,6)
    centers=boxes[:,:3]@BASIS.T
    radii=boxes[:,3:]@np.abs(BASIS.T)
    return np.r_[np.min(centers-radii,axis=0),np.max(centers+radii,axis=0)]


def fit_camera(bounds,margin=TARGET_MARGIN,min_framing=MIN_FRAMING):
    center=(bounds[:2]+bounds[2:])*.5
    half_extent=np.max(bounds[2:]-bounds[:2])*.5
    framing=max(min_framing,half_extent/(1-2*margin))
    return np.r_[center@BASIS,framing]


def sample_camera_path(times,poses,t):
    """Quintic interpolation keeps position, velocity and acceleration continuous."""
    t=float(np.clip(t,times[0],times[-1]))
    step=times[1]-times[0]
    i=min(int(t/step),len(times)-2);u=(t-times[i])/step
    p0=poses[i];p1=poses[i+1]
    before=poses[max(i-1,0)];after=poses[min(i+2,len(poses)-1)]
    v0=(p1-before)*.5;v1=(after-p0)*.5
    a0=p1-2*p0+before;a1=after-2*p1+p0
    d=p1-p0-v0-.5*a0;e=v1-v0-a0;f=a1-a0
    b3=10*d-4*e+.5*f;b4=-15*d+7*e-f;b5=6*d-3*e+.5*f
    return p0+v0*u+.5*a0*u*u+b3*u**3+b4*u**4+b5*u**5


def margins(pose,bounds):
    center=BASIS@pose[:3]
    return np.r_[.5+(bounds[:2]-center)/(2*pose[3]),
                 .5-(bounds[2:]-center)/(2*pose[3])]
