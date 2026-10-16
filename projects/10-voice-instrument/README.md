# 10 · 목소리에 맞춰 악기 모양을 바꾸면

쇼츠에서 사용한 **16개 원통 구간으로 된 공명관**의 최종 형상과 실제 탐색 후보를 공개합니다. 실장님에서 후보를 바꾸면 관의 모양과 계산한 소리가 함께 바뀝니다. 브라우저 체험에는 Python, GPU, API 키가 필요 없습니다.

## 실장님에서 바로 실행

1. 이 저장소를 내려받고 [project.md](project.md)를 실장님 에이전트에게 전달하세요.
2. **“이 project.md를 프로젝트로 가져와서 실행해 줘”**라고 요청하세요. 에이전트는 `project_import_md`로 문서 전체를 가져옵니다.
3. 뷰어의 악기를 한 번 클릭해 소리를 켜세요. 브라우저의 자동 재생 제한 때문에 클릭이 필요합니다.
4. **Computed candidate** 슬라이더를 왼쪽부터 오른쪽으로 움직여 보세요. 마지막 값 13이 쇼츠의 최종 형상입니다. **Sound**로 음소거할 수 있습니다.

관 내부의 단면을 옆에서 본 모습입니다. 표시된 길이와 반지름은 같은 축척을 사용합니다. 14개 후보는 실제 최적화 과정에서 저장한 형상이며, 브라우저에서 새 최적화를 하는 것은 아닙니다. 소리는 같은 연속 진동원을 각 형상의 음향 모델에 통과시켜 계산한 정상상태 소리입니다. 후보를 바꿀 때 클릭 잡음을 줄이기 위해 짧게 crossfade합니다.

## Python으로 다시 계산하고 바꾸기

Python 3.11/3.12에서 이 폴더로 이동해 실행하세요. FFmpeg는 필요 없습니다.

```sh
python3 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python run.py
```

`output/comparison.wav`는 초기 관 → 0.7초 간격 → 최종 관 순서입니다. `initial.wav`와 `final.wav`는 각각 2.32초입니다. `results.json`에는 길이·내경·검증 오차, `response.csv`에는 주파수 응답을 저장합니다. 전부 로컬에서 새로 계산합니다.

```sh
python run.py --pitch 110       # 동일한 관에 다른 기본 주파수의 진동원을 넣기
python run.py --fit             # 공개된 목표 스펙트럼에 관 형상 다시 맞추기
python build_scene.py           # 공개 데이터로 실장님 문서 다시 생성
```

`--fit`은 초기 후보에서 시작하는 단일 최적화입니다. 영상의 여러 초기값 탐색을 그대로 반복하지 않으며, 새 결과는 `output/results.json`에 저장됩니다. 브라우저에도 새 결과를 넣으려면 그 파일의 `parameters`를 `data/search-trace.json`의 `final_parameters`에 복사한 뒤 `build_scene.py`를 실행하고 새 문서를 가져오세요. 기본 공개 파일은 저절로 덮어쓰지 않습니다.

## 쇼츠와 공개본의 관계

- 최종 관 길이 **195.768819 mm**, 16개 구간. 내경 약 2.52–50.44 mm.
- `data/search-trace.json`: 쇼츠에 사용한 실제 탐색 후보와 최종 파라미터. 각 파라미터는 `[길이(m), log(단면적 cm²) × 16, 1 kHz 감쇠계수(Np/m)]`입니다.
- `data/target.json`: 길게 낸 모음에서 분석한 목표 스펙트럼과 formant 수치. 성우 원본 파형은 포함하지 않습니다.
- `samples/short-final-tube.wav`: 쇼츠에서 사용한 **FEniCSx/DOLFINx 계산 결과**. 분석한 pitch·진폭 변화를 따른 합성 진동원으로 만든 소리이며, 성우 녹음을 관에 통과시킨 파일이 아닙니다.
- 실장님과 `run.py`의 기본 체험은 차이를 비교하기 쉽도록 **고정 pitch 80.8533 Hz**를 사용합니다. 따라서 쇼츠의 미세한 pitch·진폭 변화와 완전히 같지는 않습니다.
- `run.py`는 NumPy/SciPy transfer matrix와 독립적인 1D linear FEM을 구현합니다. FEM은 원래 DOLFINx에서 사용한 약형과 같은 식을 직접 조립합니다. 공개 기본 실행이 FEniCSx를 호출한다고 주장하지 않습니다.

모델은 강체 벽, 1D 관, 열린 출구의 압력 0, 주파수별 경험적 감쇠를 가정합니다. 실제 제작·리드·재료·출구 방사 임피던스는 검증하지 않았습니다. 이 형상만 프린트해서 불면 성우와 같은 소리가 난다는 의미는 아닙니다.

## English

Import the entire `project.md` into Siljangnim using `project_import_md`, click the viewer once to enable audio, then change **Computed candidate**. The final slider value (13) is the Short's final bore. **Sound** mutes playback. No assets, network requests, credentials or Python installation are required for the viewer.

The viewer shows measured-scale bore profiles and synthesized steady-state audio for 14 computed candidates. It replays the saved search; it does not optimize a new voice in the browser. The Python commands above regenerate audio, optionally change excitation pitch, refit the supplied spectral target, and independently compare transfer matrices with a 1024-element linear FEM. A new single-start fit may differ from the published multi-start result.

The bundled Short sample is synthesized FEniCSx output, not a commercial voice recording. The portable demo uses a fixed-pitch analytic excitation, so it intentionally differs from the Short's pitch/envelope trajectory. This is a 1D acoustic research model, not a fabrication-ready instrument or a guarantee of matching a human voice when blown.

## Credits / license

Project source and authored numeric data: GPL-3.0-or-later, see the repository license. NumPy and SciPy: BSD licenses. Original research pipeline: [Praat](https://www.fon.hum.uva.nl/praat/) / [Parselmouth](https://github.com/YannickJadoul/Parselmouth) for voice analysis and [FEniCSx](https://fenicsproject.org/) / DOLFINx for the FEM solve. Those libraries are not vendored or required by the browser demo. Commercial Brian/George recordings, credentials, model weights and production caches are excluded.
