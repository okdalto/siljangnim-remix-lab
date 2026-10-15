"""Fast dependency/asset check; does not substitute for running experiments."""
import importlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for module in ['numpy','PIL','pymunk','scipy','librosa','soundfile','cv2']:
 importlib.import_module(module)
for tool in ['ffmpeg','ffprobe']:
 assert shutil.which(tool),f'Install {tool} and add it to PATH'
projects=sorted((root/'projects').iterdir())
assert len(projects)==9
for folder in projects:
 assert (folder/'README.md').is_file(),folder
print('Dependencies and nine project READMEs verified. Run each README command to reproduce results.')
