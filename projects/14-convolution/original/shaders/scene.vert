#version 150
in vec2 position;
out vec2 uv;
void main() { uv=position*.5+.5; gl_Position=vec4(position,0,1); }
