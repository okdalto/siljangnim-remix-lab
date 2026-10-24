#version 150
in vec2 uv;
out vec4 fragColor;
out vec4 surfaceInfo;
uniform float timeline;
uniform int gridSize;
uniform sampler2D sourceImage;
uniform sampler2D photoImage;
uniform sampler2D resultImage;
uniform sampler2D labelAtlas;
uniform vec2 introTiming;
uniform float scanStart;
uniform float firstCell;
uniform float scanFinish;
uniform float motion[26];
uniform float filterMotion[81];
uniform float gatherMotion[28];
uniform float sourceScale[9];
uniform bool sourceChanging;
uniform float phaseTiming[20];
uniform vec4 cameraPose;
uniform float motionVisibility;
uniform vec4 preparedFilter;
uniform float preparedLayer;
uniform float labelOpacity;
uniform float introOpacity;

const float GAP=.95;
const float DETAILS=2.;
const float MELT_STRENGTH=.85;
const float WORK_LAYER=.95;
const float FILTER_HOVER=.32;
const float FAST_LAYER=.60;
float ease(float x){x=clamp(x,0.,1.);return x*x*x*(x*(x*6.-15.)+10.);}
float channelGray(){return ease((timeline-introTiming.y)/.12);}
float box(vec3 p,vec3 b){float r=.12*max(min(b.x,min(b.y,b.z)),0.);vec3 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.)-r;}
float smin(float a,float b,float k){float h=clamp(.5+.5*(b-a)/k,0.,1.);return mix(b,a,h)-k*h*(1.-h);}
vec3 sampleAt(vec2 cell){return texelFetch(sourceImage,ivec2(clamp(cell,0.,float(gridSize-1))),0).rgb;}
vec2 scanCell(float index){
    float width=float(gridSize-2),row=floor(index/width),col=mod(index,width);
    return vec2(col+1.,width-row);
}
float scanEndTime(){return scanFinish;}
vec2 scanState(){return vec2(motion[24],motion[25]);}
void take(inout vec4 best,float distance,vec3 color){if(distance<best.x)best=vec4(distance,color);}
vec3 initialFilterColor(vec2 tap,float weight){
    // RGB marks the three input components before channel decomposition.
    vec3 tint=tap.x<-.5?vec3(1.,.22,.18):(tap.x>.5?vec3(.20,.38,1.):vec3(.22,1.,.32));
    return tint*weight;
}
vec4 filterRack(vec3 p,vec3 center,float layer,float pitch,float enter){
    vec4 field=vec4(100.,0,0,0);
    for(int c=0;c<3;c++)for(int j=0;j<3;j++)for(int i=0;i<3;i++){
        vec2 tap=vec2(float(i)-1.,1.-float(j));
        vec3 position=center+vec3(tap*pitch,(1.-float(c))*layer);
        float coefficient=tap.x*(tap.y==0.?2.:1.);
        float weight=.22+.68*abs(coefficient)/2.;
        vec3 color=mix(initialFilterColor(tap,weight),vec3(weight),channelGray());
        take(field,box(p-position,vec3(pitch*.435,pitch*.435,.065)*enter),color);
    }
    return field;
}
// Symmetric soft union. Shifted exponentials avoid overflow and make the
// result independent of the order in which the nine boxes are evaluated.
void softAdd(inout vec4 field,inout float mass,float distance,vec3 color,float k){
    if(k<.00001){take(field,distance,color);mass=1.;return;}
    float nearest=min(field.x,distance);
    float oldWeight=exp(max((nearest-field.x)/k,-80.));
    float newWeight=exp(max((nearest-distance)/k,-80.));
    field=vec4(nearest,field.yzw*oldWeight+color*newWeight);
    mass=mass*oldWeight+newWeight;
}
vec4 softFinish(vec4 field,float mass,float k,float count,float normalize){
    if(k<.00001)return field;
    // Remove coincident-volume inflation continuously. Identical boxes reduce
    // to exactly the same SDF as one box at the end of the gathering motion.
    return vec4(field.x-k*log(max(mass,.000001))+k*log(count)*normalize,
                field.yzw/max(mass,.000001));
}
vec3 outputPoint(vec2 current){float n=float(gridSize);return vec3(6.5+(current.x-(n-1.)*.5)*5.76/n,(current.y-(n-1.)*.5)*5.76/n,0.);}
vec3 deliveryPoint(vec3 start,vec3 destination,float amount){
    // The eased arc stays outside the source slab instead of passing through it.
    return mix(start,destination,amount)+vec3(0,.9,.65)*sin(amount*3.14159265);
}
float outputValue(vec2 cell){return texelFetch(resultImage,ivec2(cell),0).r;}
float outputShade(vec2 cell){return .12+.82*outputValue(cell);}
// Nearest *existing* output cube, including a partially completed row.
// A missing nearest grid cell must never make the distance to older cells disappear.
vec4 storedOutput(vec3 p,float completed){
    float n=float(gridSize),w=n-2.,pitch=5.76/n;
    float count=clamp(completed,0.,w*w);
    float fullRows=floor(count/w),partial=mod(count,w);
    vec3 q=p-vec3(6.5,0,0);
    vec2 nearest=floor(q.xy/pitch+n*.5);
    vec4 best=vec4(100.,0,0,0);
    for(int part=0;part<2;part++){
        vec2 cell;
        if(part==0){
            if(fullRows<1.)continue;
            cell=clamp(nearest,vec2(1,w-fullRows+1.),vec2(w,w));
        }else{
            if(partial<1. || fullRows>=w)continue;
            float left=1.;
            float right=partial;
            cell=vec2(clamp(nearest.x,left,right),w-fullRows);
        }
        vec2 xy=(cell-(n-1.)*.5)*pitch;
        take(best,box(q-vec3(xy,0),vec3(pitch*.435,pitch*.435,.065)),vec3(outputShade(cell)));
    }
    return best;
}

vec4 scene(vec3 p){
    float n=float(gridSize),pitch=5.76/n;
    float split=ease((timeline-introTiming.y)/phaseTiming[15]);
    float splitMove=motion[0];
    float imageFront=GAP*splitMove+.065;
    vec2 state=scanState();
    float index=state.x,cycle=state.y;
    bool running=timeline>=scanStart && timeline<scanEndTime();
    bool detailed=index<DETAILS;
    float visibility=detailed?1.:motionVisibility;
    bool animate=detailed || visibility>.06;
    float seconds=cycle*firstCell;
    float merge=detailed?ease((seconds-phaseTiming[2])/phaseTiming[3]):ease((cycle-.30)/.23);
    float gather=detailed?ease((seconds-phaseTiming[4])/phaseTiming[5]):ease((cycle-.57)/.15);
    // Field normalization follows actual convergence, while positions may
    // overshoot slightly. This prevents a spring from inflating the final SDF.
    float gatherField=clamp(gatherMotion[27],0.,1.);
    // Only the two explanatory operations deliver a flying result cube.
    float deposit=detailed?ease((seconds-phaseTiming[8])/phaseTiming[9]):0.;
    float depositMove=motion[3];
    bool complete=detailed?deposit>=1.:(!animate || gather>=1.);
    float move=(detailed || animate)?motion[4]:0.;
    vec2 current=scanCell(index);
    vec2 next=scanCell(min(index+1.,(n-2.)*(n-2.)-1.));
    vec2 anchor=mix(current,next,move);
    vec3 windowCenter=vec3((current-(n-1.)*.5)*pitch,0.);
    vec3 destination=outputPoint(current);
    vec3 macro=vec3(-3.9,3.9,1.75);
    float outro=ease((timeline-scanEndTime()-.35)/3.);
    vec4 best=vec4(100.,0,0,0);

    // Original image and compact z-separated channel planes.
    for(int c=0;c<3;c++){
        float z=(1.-float(c))*GAP*splitMove;
        // Clear the old input from the loop's final composition as the camera
        // frames the output in exactly the opening photo's screen rectangle.
        vec3 q=p-vec3(-5.*outro,0,z);
        vec2 cell=clamp(floor(q.xy/pitch+n*.5),vec2(0),vec2(n-1.));
        vec2 xy=(cell-(n-1.)*.5)*pitch;
        vec3 rgb=sampleAt(cell);
        vec3 col=mix(rgb,vec3(rgb[c]),channelGray());
        float pixelize=ease((timeline-introTiming.x)/1.2);
        float pixelizeMove=motion[5];
        float d=box(q-vec3(xy,0),vec3(pitch*(.5-.065*pixelizeMove),pitch*(.5-.065*pixelizeMove),.065));
        if(timeline<introTiming.y){
            d=mix(box(q,vec3(2.88,2.88,.065)),d,pixelize);
            vec3 photo=texture(photoImage,clamp(q.xy/5.76+.5,0.,1.)).rgb;
            col=mix(photo,col,pixelize);
        }
        if(running && animate && sourceChanging && all(lessThanEqual(abs(cell-current),vec2(1)))){
            // This is the real source cell: remove it while its box travels.
            // Search the remaining patch and its four nearest outside strips,
            // so raymarching through a hole cannot skip neighboring geometry.
            vec4 local=vec4(100.,0,0,0);
            for(int j=0;j<3;j++)for(int i=0;i<3;i++){
                vec2 tap=vec2(float(i)-1.,1.-float(j));
                float scale=sourceScale[j*3+i];
                if(scale<=.001)continue;
                vec2 sourceCell=current+tap;
                vec2 position=(sourceCell-(n-1.)*.5)*pitch;
                float candidate=box(q-vec3(position,0),vec3(pitch*.435,pitch*.435,.065)*scale);
                take(local,candidate,vec3(sampleAt(sourceCell)[c]));
            }
            for(int side=0;side<4;side++){
                vec2 outside=cell;
                if(side==0)outside.x=current.x-2.;
                if(side==1)outside.x=current.x+2.;
                if(side==2)outside.y=current.y-2.;
                if(side==3)outside.y=current.y+2.;
                if(any(lessThan(outside,vec2(0)))||any(greaterThan(outside,vec2(n-1.))))continue;
                vec2 position=(outside-(n-1.)*.5)*pitch;
                float candidate=box(q-vec3(position,0),vec3(pitch*.435,pitch*.435,.065));
                take(local,candidate,vec3(sampleAt(outside)[c]));
            }
            d=local.x;col=local.yzw;
        }
        // Retire the source planes into the background as the final output takes focus.
        col*=1.-outro*.8;
        take(best,d,col);
        if(split<.0001)break;
    }

    // Raster output: top row first, each row always left to right.
    if(timeline>=scanStart){
        float completed=timeline>=scanEndTime()?(n-2.)*(n-2.):index+(complete?1.:0.);
        vec4 outputField=storedOutput(p,completed);
        take(best,outputField.x,outputField.yzw);
    }

    // Introduce the actual coefficients on a separate rack beside the image.
    // The working field takes ownership at scanStart with the same placement.
    if(timeline>=phaseTiming[16] && timeline<scanStart){
        float enter=motion[6];
        if(enter>.001){
            vec4 rack=filterRack(p,vec3(-3.5,2.2,1.99),GAP*splitMove,pitch,enter);
            take(best,rack.x,rack.yzw);
        }
    }
    // The next rack is already present during the preceding result's flight.
    // Its CPU trajectory starts entirely beyond the current camera frustum.
    if(preparedFilter.w>.5){
        vec4 rack=filterRack(p,preparedFilter.xyz,preparedLayer,pitch,1.);
        take(best,rack.x,rack.yzw);
    }

    // Every output follows the same sequence: staggered pop, simultaneous
    // multiply, direct 27-to-1 sum, deposit. First two are shown in macro.
    if(running && animate && !complete){
        // Once the sum is complete, render exactly ONE stable box.
        // Its dimensions converge to the stored cube before ownership changes.
        if(gather>=1.){
            vec3 sumCenter=detailed?macro:windowCenter+vec3(0,0,1.3);
            vec3 pos=deliveryPoint(sumCenter,destination,depositMove);
            vec3 bounds=vec3(pitch*.435,pitch*.435,.065);
            take(best,box(p-pos,bounds),vec3(outputShade(current)));
            return best;
        }
        // Keep the working field separate: its smooth union must not deform
        // the input planes or any previously deposited result cubes.
        vec3 homeLow=windowCenter-vec3(0,0,GAP);
        vec3 homeHigh=windowCenter+vec3(0,0,GAP);
        vec3 stageLow=detailed?min(macro-vec3(0,0,WORK_LAYER),vec3(-3.5,2.2,1.75-WORK_LAYER)):homeLow;
        vec3 stageHigh=detailed?macro+vec3(0,0,WORK_LAYER):windowCenter+vec3(0,0,imageFront+FILTER_HOVER+2.*FAST_LAYER*visibility);
        vec3 lo=min(homeLow,stageLow)-vec3(2.4,.85,.35);
        vec3 hi=max(homeHigh,stageHigh)+vec3(.85,.85,1.15);
        float bound=box(p-(lo+hi)*.5,(hi-lo)*.5);
        if(bound>.15){take(best,bound,vec3(0));return best;}
        vec4 work=vec4(100.,0,0,0);
        float workMass=0.;
        float gatherSoftness=MELT_STRENGTH*(detailed?.034:.026)*ease(gatherField/.16);
        for(int c=0;c<3;c++){
            vec3 homeCenter=windowCenter+vec3(0,0,(1.-float(c))*GAP);
            vec3 stageCenter=detailed?macro+vec3(0,0,(1.-float(c))*WORK_LAYER):windowCenter+vec3(0,0,imageFront+FILTER_HOVER+(2.-float(c))*FAST_LAYER*visibility);
            // One shared destination for all spatial taps AND all RGB channels.
            vec3 reduced=detailed?macro:windowCenter+vec3(0,0,imageFront+.20+.48*visibility);
            // Move the sampled image patch intact: do not spread its pixels.
            float spacing=pitch;
            for(int j=0;j<3;j++)for(int i=0;i<3;i++){
                vec2 tap=vec2(float(i)-1.,1.-float(j));
                float order=float(j*3+i);
                float pop=motion[15+j*3+i];
                vec3 home=homeCenter+vec3(tap*pitch,0);
                vec3 staged=stageCenter+vec3(tap*spacing,0);
                float gatherMove=gatherMotion[c*9+j*3+i];
                vec3 pos=mix(home,staged,pop);
                pos=mix(pos,reduced,gatherMove);
                pos=mix(pos,destination,depositMove);
                float halfSize=pitch*.435;
                float zSize=.065;
                float coefficient=tap.x*(tap.y==0.?2.:1.);
                int phaseIndex=(c*9+j*3+i)*3;
                float approach=filterMotion[phaseIndex];
                float contact=filterMotion[phaseIndex+1];
                float tapMerge=filterMotion[phaseIndex+2];
                // Keep a real surface gap until lateral registration is complete.
                float bulge=MELT_STRENGTH*sin(tapMerge*3.14159265)*(1.-gather);
                float nearGap=2.*zSize*(1.+.24*bulge)+.07;
                float gap=mix(.24,nearGap,approach);
                gap=mix(gap,0.,clamp(contact,0.,1.));
                // One smooth deformation envelope; no extra strand or oscillation.
                vec3 body=vec3(halfSize*(1.+.055*bulge),halfSize*(1.+.055*bulge),zSize*(1.+.24*bulge));
                // As the operation becomes unreadably fast, its working geometry
                // loses lift and scale; committed output cubes remain untouched.
                body*=visibility;
                gap*=visibility;
                vec3 q=p-pos;
                float a=box(q,body);
                float appear=motion[6];
                vec3 weightBody=body*appear;
                // Wait beside the working patch until multiplication is needed.
                // Approach above the pixels, then close the remaining z gap.
                vec3 parked=staged-vec3(.66*visibility,0,0);
                if(detailed){
                    vec3 intro=vec3(-3.5,2.2,1.75)+vec3(tap*pitch,(1.-float(c))*GAP*splitMove);
                    parked=mix(intro,parked,motion[10]);
                }
                vec3 filterCenter=mix(parked,pos,approach)+vec3(0,0,gap);
                float b=appear>.001?box(p-filterCenter,weightBody):100.;
                // A wider, early blend field makes a visible rounded neck before overlap.
                // It contracts back to the original silhouette before reduction/storage.
                float attraction=ease((tapMerge-.60)/.32);
                float settle=ease((tapMerge-.72)/.28);
                float softness=MELT_STRENGTH*halfSize*1.9*attraction*(1.-.67*settle)*(1.-gatherField)*visibility+.0001;
                float d=smin(a,b,softness);
                float blend=clamp(.5+.5*(a-b)/max(softness,.02),0.,1.);
                float intensity=sampleAt(current+tap)[c];
                float weight=.22+.68*abs(coefficient)/2.;
                float product=intensity*abs(coefficient)/2.;
                vec3 color=vec3(mix(intensity,weight,blend));
                // Preserve the source intensity during extraction and approach.
                // Show the product only as the two bodies finish joining.
                float productReveal=ease((tapMerge-.72)/.28);
                color=mix(color,vec3(product),productReveal);
                color=mix(color,vec3(outputShade(current)),clamp(gatherMove,0.,1.));
                softAdd(work,workMass,d,color,gatherSoftness*visibility);
            }
        }
        vec4 combined=softFinish(work,workMass,gatherSoftness*visibility,27.,ease((gatherField-.55)/.45));
        take(best,combined.x,combined.yzw);
    }
    return best;
}

// Captions lie on the same world XY planes as the image and filter grids.
// Invert their projected basis so both glyph axes inherit the quarter view.
float caption(vec2 st,vec3 anchor,float width,float row,vec3 right,vec3 up){
    vec3 delta=anchor-cameraPose.xyz;
    vec2 projected=vec2(dot(delta,right),dot(delta,up));
    mat2 plane=mat2(vec2(right.x,up.x),vec2(right.y,up.y));
    vec2 local=inverse(plane)*(st*cameraPose.w-projected);
    vec2 point=local/vec2(width,width/4.)+.5;
    if(any(lessThan(point,vec2(0)))||any(greaterThan(point,vec2(1))))return 0.;
    return texture(labelAtlas,vec2(point.x,(1.-row)*.5+point.y*.5)).r;
}

void main(){
    vec2 st=uv*2.-1.;
    vec3 offset=vec3(13.,10.,18.);
    vec3 forward=normalize(-offset),right=normalize(cross(forward,vec3(0,1,0))),up=cross(right,forward);
    vec2 state=scanState();
    float seconds=state.y*firstCell;
    bool detailed=timeline>=scanStart && state.x<DETAILS;
    vec3 focus=cameraPose.xyz;
    float framing=cameraPose.w;
    vec3 ro=offset+focus+right*st.x*framing+up*st.y*framing;
    vec3 rd=forward;
    vec3 color=vec3(mix(.035,.075,uv.y));
    float t=0.;bool hit=false;vec4 mat;
    vec3 surfaceNormal=vec3(0);
    for(int i=0;i<155;i++){
        mat=scene(ro+rd*t);
        if(mat.x<.0015){hit=true;break;}
        t+=max(mat.x*.68,.0006);
        if(t>47.)break;
    }
    if(hit){
        vec3 p=ro+rd*t;vec2 e=vec2(.002,0);
        vec3 normal=normalize(vec3(scene(p+e.xyy).x-scene(p-e.xyy).x,scene(p+e.yxy).x-scene(p-e.yxy).x,scene(p+e.yyx).x-scene(p-e.yyx).x));
        surfaceNormal=normal;
        vec3 light=normalize(vec3(-3,8,14));
        float diffuse=max(dot(normal,light),0.);
        float spec=pow(max(dot(normal,normalize(light-rd)),0.),48.);
        float ao=clamp(scene(p+normal*.06).x/.06,.6,1.);
        color=mat.yzw*(.5+.5*diffuse)*ao+spec*.075;
        color+=pow(1.-max(dot(normal,-rd),0.),4.)*.04;
    }
    color*=1.-.12*dot(st,st);
    color=mix(vec3(mix(.035,.075,uv.y)),color,introOpacity);
    if(labelOpacity>.001){
        float imageLabel=caption(st,vec3(0,-3.55,0),1.45,0.,right,up);
        float filterLabel=caption(st,vec3(-3.5,1.55,1.99),1.20,1.,right,up);
        color=mix(color,vec3(.68),max(imageLabel,filterLabel)*labelOpacity);
    }
    gl_FragDepth=hit?clamp(t/47.,0.,1.):1.;
    surfaceInfo=vec4(surfaceNormal*.5+.5,gl_FragDepth);
    fragColor=vec4(color,1.);
}
