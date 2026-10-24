#version 150
in vec2 uv;
out vec4 fragColor;
uniform sampler2D squareImage;
uniform float aspect;
void main(){
    vec2 squareUV=(uv-.5)*vec2(1.,aspect)+.5;
    if(squareUV.y>=0. && squareUV.y<=1.){
        fragColor=texture(squareImage,squareUV);
    }else{
        // Continue the existing dark background into the top/bottom margins.
        float edgeY=clamp(squareUV.y,0.,1.);
        vec2 st=vec2(squareUV.x,edgeY)*2.-1.;
        float background=mix(.035,.075,edgeY)*(1.-.12*dot(st,st));
        fragColor=vec4(vec3(background),1.);
    }
}
