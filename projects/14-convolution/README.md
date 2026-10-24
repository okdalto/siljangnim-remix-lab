# 14 · Convolution / 컨볼루션

쇼츠의 강아지 사진으로 필터 연산을 직접 바꿔 보세요.

## 실장님에서 원본 3D 실행

1. 저장소를 clone하거나 [ZIP으로 다운로드](https://github.com/okdalto/siljangnim-remix-lab/archive/refs/heads/main.zip)합니다.
2. [project.md](project.md)를 실장님 에이전트에게 주고 **“이 프로젝트의 Scene을 가져와 실행해 줘”**라고 요청합니다. 가져오기 뒤 이전 화면이 남으면 `scene.json` 전체를 `scene_write`로 적용합니다.
3. 사진 → 픽셀 박스 → RGB 분리 → 필터 곱셈 → 27개 값 합산 → 결과 스캔이 원본 3D 장면으로 재생됩니다.

**2D 체험판을 대체한 원본 3D WebGL2 이식판입니다.** 둥근 SDF 박스, 합산의 smooth union, 깊이 가림, 외곽선, 원본 카메라 경로를 유지했습니다. MP4를 재생하는 것이 아니라 매 프레임 원본 GLSL로 3D 형상을 렌더링합니다.

| 조작 | 기능 |
| --- | --- |
| Playback speed | 원본 시간의 재생 배속, 기본 0.8 |
| Pause / Restart | 일시정지 / 처음부터 |
| Source time / seek | 사진 0.95, RGB 6.5, 곱셈 10.5, 합산 13.1, 스캔 27, 결과 34.97초로 탐색 |
| View | 원본 애니메이션 또는 Blur / Sharpen / Laplacian 결과 비교 |
| Raymarch resolution | 느리면 256으로, 선명하게 보려면 720~1080으로 조절 |

필터 비교에서는 쇼츠처럼 같은 위치의 박스를 유지하고 색만 바꿉니다. `Original 3D animation`으로 돌아오면 Sobel 애니메이션을 계속합니다. 브라우저의 float 렌더 타깃과 DecompressionStream을 지원하는 최신 실장님이 필요합니다. 이미지와 모션 데이터가 모두 문서에 들어 있어 추가 설치·CDN·API 키는 필요 없습니다.

Python 원본이 계산하던 카메라·스프링·필터 준비 동작은 **240Hz로 샘플링한 수치 데이터**입니다. 셰이더는 이 값을 사용해 실시간으로 형상을 계산하며, 필터 출력은 JS에서 실제 계산합니다. 재생 속도는 바꿀 수 있지만 스프링 상수나 카메라 경로를 수정하면 `bake_motion.py`로 데이터를 다시 만들어야 합니다. 렌더 해상도와 GPU에 따라 프레임 속도가 달라집니다. WebGL에서는 원본 GL_LINE_SMOOTH 대신 브라우저의 선 래스터화를 사용하므로 얇은 선은 미세하게 다를 수 있습니다. 전체 원본 반복 타임라인을 제공하며 쇼츠의 내레이션·자막·Manim 타이틀·문장별 재편집은 포함하지 않습니다.

## 쇼츠의 원본 3D 애니메이션

Python 3.11/3.12, OpenGL 3.2 이상, GUI 디스플레이가 필요합니다. 소프트웨어 렌더러 성능은 보장하지 않습니다.

```sh
cd projects/14-convolution/original
python3 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python convolution.py
```

사진 → RGB 분리 → 필터 곱셈 → 27개 값 합산 → Sobel 결과 애니메이션입니다. Space로 멈춤, R로 재시작, 1–5로 단계 이동, 방향키로 탐색합니다. 다른 사진은 `python convolution.py --image my-photo.png` 또는 창에 드롭합니다. Mac 전용 폰트 경로를 제거하고 Pillow 기본 폰트 fallback을 넣었습니다. 원본 설명과 자세한 조작은 [original/README.md](original/README.md)를 참고하세요. 쇼츠의 편집 속도·Manim 타이틀·마지막 필터 비교 편집은 이 원본 반복 타임라인에 포함되지 않습니다.

## 계산과 수정

32×32 RGB 입력, 3×3 필터, stride 1, valid 영역만 계산하므로 결과는 30×30입니다. sRGB 수치를 선형광 변환 없이 사용합니다.

- Identity: 중앙 픽셀 그대로.
- Blur: 주변 9개 RGB 값의 평균.
- Sharpen: 중앙 ×5에서 상하좌우를 뺍니다.
- Sobel: Gx/Gy를 RGB별 계산 후 `.2126R + .7152G + .0722B`로 합쳐 `sqrt(Gx² + Gy²)/4`를 표시합니다. 아래 계수 표와 Sum RGB는 **Gx**이고 최종 출력은 **Gx와 Gy 둘 다** 사용합니다.
- Laplacian: 중앙 ×8에서 주변 8개를 뺀 휘도 응답의 절댓값.

최종 표시만 [0,1]로 제한하며 음수 계수와 원래 합계는 보존합니다. 표의 Blur 계수는 가독성을 위해 0.11로 표시되지만 계산은 정확한 1/9입니다. 엄밀히는 커널을 뒤집지 않는 cross-correlation입니다. 대칭 필터는 convolution과 같고 Sobel은 부호가 뒤집혀도 최종 magnitude가 같습니다.

`core.cjs`가 실제 필터 계산이며 `setup.js`, `render.js`는 원본 3D의 WebGL2 렌더러입니다. `data.json`은 위→아래 행 순서입니다. OpenGL 원본의 아래→위 텍스처 배열을 변환했습니다.

```sh
# Node.js 20+, npm 설치 불필요
node build.cjs
node verify.cjs
# 선택: 원본 모션 데이터 재생성 (Python 환경 필요)
python bake_motion.py
python verify_motion.py
node build.cjs
# 원본 Python 환경에서 수치/카메라 검사
python original/convolution.py --self-test
# 선택: 다른 이미지로 실장님 입력 교체
python prepare_data.py my-photo.png
python bake_motion.py --image my-photo.png
node build.cjs
node verify.cjs
```

검증은 NumPy 참조 출력 13,500개와 JS 결과, 상수·계단 입력, identity 필터의 좌표 정렬을 확인합니다. `verification.json`에 수치 오차가 기록됩니다. 사용자 이미지로 재배포할 때는 그 이미지의 권리를 확인하고 아래 기본 사진의 고지와 구분하세요.

## 사진과 라이선스

소스: 저장소 GPL-3.0-or-later. 기본 사진과 그 파생 데이터는 별도 **CC BY 3.0**입니다.

**Golden Retriever Hund Dog.JPG**, Kintaiyo — [Wikimedia Commons 원본](https://commons.wikimedia.org/wiki/File:Golden_Retriever_Hund_Dog.JPG), [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). 원본 사진 `original/assets/dog.jpg` 포함. 중앙 crop, 32×32 축소, RGB 분리, 필터 연산 및 수치 데이터 변환을 적용했습니다. 저자가 이 프로젝트를 보증한다는 의미는 아닙니다. 별도 설치 라이브러리는 NumPy (BSD-3-Clause), Pillow (HPND), PyOpenGL (BSD), GLFW (zlib/libpng)입니다.

## English

Import **project.md** and apply its Scene (or **scene.json**) in Siljangnim. This is the original **3D SDF animation**, not the earlier 2D study or a prerecorded video. Original GLSL geometry, RGB separation, multiplication, soft-union gathering, camera paths, depth and outlines run in WebGL2. Original Python CPU motion is sampled at 240 Hz; rebuild with `bake_motion.py` after changing motion rules. Play/pause, seek and adjust resolution; View switches to fixed-geometry filter comparisons.

No Python or external downloads are required to run the embedded scene. Python is optional for regenerating data or running the original desktop renderer in **original/**. The narrated Shorts edit is not included. Thin-line antialiasing can differ between desktop OpenGL and WebGL. See the photo's CC BY 3.0 attribution above; code is GPL-3.0-or-later.
