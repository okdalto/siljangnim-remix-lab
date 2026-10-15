"""Re-run all experiments and decode generated videos. Requires FFmpeg."""
import concurrent.futures,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JOBS={
'01-doodle-walker':[['search.py'],['render_clean.py']],
'02-chair-search':[['run.py'],['clean_results.py']],
'03-city-pinball':[['build.py']],
'04-domino-amplifier':[['search.py'],['render.py']],
'05-voice-coaster':[['run.py'],['render.py']],
'06-maze-growth':[['build.py'],['render_exit.py']],
'07-object-tetris-photo':[['make.py']],
'08-bridge-repair':[['run.py'],['clean_results.py']],
'09-music-type-collision':[['run.py','--render']]}
def run(item):
 name,commands=item;folder=ROOT/'projects'/name
 for args in commands:
  result=subprocess.run([sys.executable,*args],cwd=folder,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  if result.returncode:raise RuntimeError(name+' failed:\n'+result.stdout[-4000:])
 videos=sorted(folder.rglob('*.mp4'))
 assert videos,name+' produced no video'
 for p in videos:subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
 print(name,'PASS',len(videos),'decoded videos',flush=True)
 return {'project':name,'commands':commands,'decoded_videos':len(videos),'status':'pass'}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,JOBS.items()))
(ROOT/'verification-report.json').write_text(json.dumps(results,indent=2)+'\n')
