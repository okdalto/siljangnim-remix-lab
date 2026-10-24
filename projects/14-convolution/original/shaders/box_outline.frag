#version 150
in vec2 uv;
out vec4 fragColor;
uniform sampler2D surfaceImage;
uniform float opacity;
void main(){
    vec2 texel=1./vec2(textureSize(surfaceImage,0));
    vec4 center=texture(surfaceImage,uv);
    float edge=0.;
    for(int axis=0;axis<2;axis++)for(int side=-1;side<=1;side+=2){
        vec2 stepUV=(axis==0?vec2(texel.x,0):vec2(0,texel.y))*.30*float(side);
        vec4 neighbor=texture(surfaceImage,uv+stepUV);
        float crease=length(center.xyz-neighbor.xyz);
        float silhouette=smoothstep(.001,.003,abs(center.w-neighbor.w));
        edge=max(edge,max(smoothstep(.18,.42,crease),silhouette));
    }
    // Only ink the surface side of an edge, keeping the stroke under a pixel.
    float alpha=center.w<.9999?edge*opacity:0.;
    fragColor=vec4(vec3(.94),alpha);
}
