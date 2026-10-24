#version 150
in vec2 uv;
uniform sampler2D outlineImage;
uniform float layerOpacity;
out vec4 fragColor;
void main(){fragColor=texture(outlineImage,uv)*layerOpacity;}
