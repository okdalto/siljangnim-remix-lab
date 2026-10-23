# 13 · 보로노이와 들로네 / Voronoi and Delaunay

쇼츠에서 사용한 점·영역·삼각형과 3D 조각 실험을 실장님에서 직접 실행하고 바꿔 보세요.

## 실장님에서 바로 실행

1. 이 저장소를 [ZIP](https://github.com/okdalto/siljangnim-remix-lab/archive/refs/heads/main.zip)으로 받거나 clone합니다.
2. **[project.md](project.md)**를 [실장님](https://github.com/okdalto/siljangnim) 에이전트에게 주고 “이 프로젝트를 가져와서 실행해 줘”라고 요청합니다.
3. `Study`에서 네 가지 실험을 선택합니다. `Pause`로 멈추고 `Restart`로 다시 시작합니다.

장면 코드, 라이브러리, 필요한 수치 데이터가 문서 안에 포함됩니다. 실장님 외 별도 설치, API 키, 유료 서비스, CDN 다운로드가 필요 없습니다. gzip 데이터 해제에 브라우저 DecompressionStream을 사용하므로 최신 Chrome/Edge/Safari 기반 실장님을 사용하세요.

| Study | 동작 | 바꿔 볼 것 |
| --- | --- | --- |
| Voronoi & Delaunay | 움직이는 점으로 매 프레임 실제 d3-delaunay 계산 | 점 개수, seed, 영역·연결선·점 표시, 영역 밝기 |
| Ballet points | 영상에서 추출한 추적점을 재생하며 삼각분할을 다시 계산 | 연결선·점 표시, 일시정지 |
| 3D Voronoi | x/y/z 공간을 나눈 볼록 다면체 36개 | 분리 간격, 카메라 회전·확대 |
| Wall physics | cannon-es로 64개 조각과 공의 충돌을 실시간 계산 | 균일/집중 seed 배치, 재시작, 카메라 |

3D 화면에서는 드래그로 회전, 휠로 확대합니다. 2D 점 개수·seed는 첫 번째 Study에만 적용됩니다. 발레는 기존 추적 데이터이며 실시간 카메라 분석이 아닙니다. 3D 형상은 사전 계산되어 있고, 벽의 충돌·중력은 실행할 때 계산합니다. 벽은 9초까지 진행한 뒤 멈춥니다. 재시작하려면 Restart를 누르세요.

## 원리와 모델의 범위

- **2D**: d3-delaunay 6.0.4가 Delaunay 삼각형과 [0,1]²로 자른 Voronoi 영역을 계산합니다. 임의로 가까운 두 점을 연결한 그림이 아닙니다. 네 점이 같은 원에 놓이는 순간 삼각분할이 유일하지 않을 수 있습니다.
- **발레**: 쇼츠용 Comfy/Seedance 생성 영상에서 OpenCV Canny·경계 검출·Lucas–Kanade 추적으로 얻은 193프레임/24fps 추적점과 실루엣입니다. 원본 영상, 음성, API 요청·키는 포함하지 않습니다. 점 좌표는 0.1픽셀 단위로 저장합니다. 화면의 선은 Delaunay를 실루엣으로 잘라 표시한 것으로, 경계 제약 삼각분할(constrained Delaunay)은 아닙니다.
- **3D**: SciPy HalfspaceIntersection으로 각 점과 나머지 점 사이의 수직 이등분 평면을 교차하고 상자로 자릅니다. ConvexHull로 면을 구성하고 같은 평면의 면들을 합칩니다. 정육면체 셀 부피의 합은 8입니다.
- **벽**: 미리 분할한 Voronoi 조각을 고정해 두었다가 공이 닿기 직전 모두 해제합니다. 응력으로 균열이 생기는 재료 파괴 모델은 아닙니다. 64개 조각, 밀도 10, 공 질량 8·반지름 0.32·초기 속도 (0,4,0), 중력 9.81, 내부 시간 간격 1/480초입니다. 공은 첫 충돌 전까지 높이를 유지하도록 힘을 받습니다. 두 배치의 크기·총 질량·공 조건은 같고 36개 seed 위치만 달라집니다. 저속 기기에서는 안정성을 위해 시뮬레이션 시간이 실제 시간보다 느리게 흐를 수 있습니다.

이것은 쇼츠의 계산을 조절해 보는 실행 예제입니다. 내레이션·자막·편집 타임라인·완성 MP4는 포함하지 않습니다.

## 소스 수정과 검증

Node.js 20+에서 별도 npm 설치 없이:

```sh
cd projects/13-voronoi-delaunay
node verify.cjs
node build.cjs
```

`setup.js`와 `render.js`는 실장님 렌더러, `core.cjs`는 테스트와 장면이 함께 사용하는 물리 모델입니다. `build.cjs`는 vendor와 gzip 수치 데이터를 넣어 `project.md`와 `scene.json`을 만듭니다. 브라우저 빌드에서 cannon-es의 Node perf_hooks 참조만 globalThis.performance로 치환합니다. 원본 vendor는 수정하지 않습니다.

검증은 90프레임의 Voronoi 면적 합/최근접 조건, 1,800개 최근접 질의, 3D 부피, 두 벽의 각 540프레임 충돌·유한 좌표·정착 속도를 확인합니다. 결과는 `verification.json`입니다.

### 3D 형상·물리 기록 재생성 (선택)

Python 3.11/3.12에서:

```sh
python3 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python geometry.py
python merge.py
node physics.cjs
node build.cjs
```

`geometry.py`의 seed나 점 배치를 바꾸면 새로운 벽/입체를 만들 수 있습니다. `physics.cjs`는 원본 쇼츠와 같은 조건의 60fps 운동 기록을 `data/`에 씁니다. 장면은 이 기록을 재생하지 않고 `core.cjs`로 직접 계산합니다. `export2d.cjs`는 원본 2D 설명 장면의 수치 데이터를 재생성합니다.

### 내 영상의 점으로 바꾸기 (선택)

검정 배경의 영상을 준비한 뒤:

```sh
python extract_video.py my-video.mp4
node build.cjs
```

이 명령은 `data/ballet.json`을 교체합니다. 필요하면 `--crop x0 y0 x1 y1`, `--threshold 18`, `--floor-cut 430`을 사용하세요. floor-cut은 432×546으로 리사이즈한 뒤의 y값입니다. 원본 쇼츠는 crop `139 452 641 1085`, floor-cut `430`을 사용했습니다. 단순 명도 마스크이므로 복잡한 배경·여러 사람·검정 옷에는 다른 segmentation이 필요합니다. 입력 영상의 가로세로 비율도 432:546 crop에 맞추면 왜곡을 줄일 수 있습니다.

## 출처와 라이선스

작성한 소스: 저장소의 GPL-3.0-or-later. 번들 라이브러리는 각 라이선스를 유지합니다.

- [d3-delaunay 6.0.4](https://github.com/d3/d3-delaunay): ISC, Observable/Mapbox. Delaunator ISC, robust-predicates Unlicense 관련 고지도 vendor/에 포함.
- [cannon-es 0.20.0](https://github.com/pmndrs/cannon-es): MIT, vendor/CANNON-LICENSE.
- SciPy 1.14.1 / NumPy 2.1.3: BSD-3-Clause, OpenCV-Python 4.10.0.84: Apache-2.0; 별도 설치.
- `data/ballet.json`: 생성 영상에서 추출한 수치 데이터. 실제 무용수를 촬영한 영상이나 사람의 모션캡처로 소개하지 않습니다.

## English

Import **project.md** into Siljangnim and choose a Study. Everything required for the scene is embedded: no API keys, paid service, package installation or CDN fetch. The four studies cover moving 2D Voronoi/Delaunay, tracked ballet points, precomputed 3D cells, and live cannon-es wall dynamics. Drag/scroll to orbit/zoom in 3D.

The ballet data derives from generated footage. The wall uses pre-cut pieces with supports removed before impact, not stress-driven fracture. Geometry is precomputed with SciPy; physics is live. Run `node verify.cjs` for numerical checks and `node build.cjs` to rebuild the importable scene. Optional Python commands above regenerate geometry or extract tracked points from your own dark-background video. Narration, paid-service recordings and production caches are excluded.
