"""Rebuild portable scenes using the archived production timing values."""
import json
from pathlib import Path
B = Path(__file__).resolve().parent
parameters = json.loads((B / 'parameters.json').read_text())
for topic, variants in parameters.items():
    for variant, uniforms in variants.items():
        scene = dict(version=2, backend='webgl2', script=dict(
            setup=(B/'setup.js').read_text(), render=(B/'render.js').read_text(), cleanup=''),
            inputs=['mouse'], timeline=dict(duration=20, loop=True), uniforms=uniforms)
        (B/topic/(variant+'.json')).write_text(json.dumps(scene, indent=2))
        if variant == 'effect':
            (B/topic/'project.md').write_text(
                '---\ntitle: PS1 Graphics — '+topic+'\nsiljangnim: 2\nbackend: webgl2\nassets: []\n---\n\n'
                '# PS1 Graphics — '+topic+'\n\n'
                'Educational WebGL2 experiment, not a full PS1 emulator. No external assets. '
                'Use Topic and Comparison controls; drag to orbit.\n\n## Scene\n\n```json\n'
                +json.dumps(scene, indent=2)+'\n```\n')
print('Rebuilt four projects and twelve scene variants.')
