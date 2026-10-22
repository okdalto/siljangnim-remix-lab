# 12 · KD-tree × Simplex noise

쇼츠의 움직이는 3D 공간 분할을 직접 바꿔 보는 실장님 프로젝트입니다. 사진에 높이를 준 것이 아니라 **1,024개의 3D 점을 x → y → z 축으로 반복 분할**합니다. 기본 depth 9에서 512개 영역이 생깁니다.

## 실장님에서 실행

1. 이 저장소를 ZIP으로 내려받거나 clone합니다.
2. 이 폴더의 **[project.md](project.md)**를 실장님 에이전트에게 전달하고 “이 프로젝트를 가져와서 실행해 줘”라고 요청합니다.
3. 드래그로 회전하고 휠로 확대합니다. Depth, Noise speed, Damping, Seed를 바꾸거나 Blocks / Plates를 선택해 보세요.

project.md에 코드와 Simplex noise 구현이 모두 들어 있습니다. 별도 에셋, Python, Node.js, API 키, 유료 서비스 또는 CDN 연결 없이 실행됩니다. 실장님 자체는 별도로 설치해야 합니다: https://github.com/okdalto/siljangnim

- **Depth**: 2–9, 영역 개수 4–512.
- **Noise speed**: 0은 시뮬레이션 정지, 1은 기본 속도. 카메라 회전은 별개입니다.
- **Damping**: 점의 관성을 감쇠하는 정도.
- **Show every cell**: 내부가 보이도록 생략한 조각까지 표시.
- **Exact median boundaries**: 표시용 스프링을 끄고 현재 점의 정확한 중앙값 분할 표시.

## 계산과 표시의 차이

simplex-noise의 4D 함수에 x/y/z와 시간을 넣어 목표 위치를 만듭니다. 점은 질량 1, 강성 12의 스프링으로 목표를 따라갑니다. 기본 감쇠는 임계 감쇠입니다. 매 프레임 실제 점으로 KD-tree를 다시 만듭니다.

점의 정렬 순서가 바뀌면 정확한 중앙값 경계는 갑자기 바뀔 수 있습니다. 기본 모드에서는 계층별 분할 비율에도 스프링을 적용합니다. 이 **표시용 경계는 정확한 중앙값보다 늦게 따라가며, 항상 해당 점들을 정확히 분류하는 검색 트리는 아닙니다.** 공유 경계로 재구성하므로 전체 영역의 빈틈 없는 분할과 부피 8은 유지합니다. Exact 옵션은 실제 중앙값 분할입니다. KD-tree 검색 검증에는 표시용 경계를 사용하지 않습니다.

실장님 장면은 쇼츠와 같은 알고리즘·색감을 사용하는 실시간 포트입니다. 쇼츠의 고정 카메라, 내레이션, 자막, 프레임별 연출은 포함하지 않습니다. 낮은 FPS에서는 안정성을 위해 시뮬레이션 시간이 느려질 수 있습니다.

## 네 단계 브라우저 실험

이 폴더에서 다음을 실행한 뒤 http://127.0.0.1:8774/ 를 엽니다.

```sh
python3 -m http.server 8774 --bind 127.0.0.1 --directory browser
```

1. 데이터 점 → 2D KD-tree와 최근접 검색 (화면 클릭으로 질의점 변경)
2. Simplex noise로 점 밀도를 바꾼 2D 패턴
3. 실제 x/y/z 분할과 z 단면
4. 같은 공간을 블록·얇은 판·모서리로 표현

이 네 단계는 원래의 정적 인터랙티브 연구입니다. 움직이는 관성 기반 3D 버전은 project.md에 있습니다. 브라우저 연구의 Three.js 및 noise 라이브러리도 로컬에 포함되어 있습니다.

## 소스 수정 및 검증

Node.js 20 이상에서 (npm 설치 불필요):

```sh
node verify.mjs
node build.mjs
```

`simulation.mjs`가 실제 운동과 분할, `setup.js` / `render.js`가 실장님 렌더러입니다. `build.mjs`는 이 파일들과 vendor의 noise 코드를 묶어 `scene.json`과 `project.md`를 재생성합니다. 테스트는 440개 최근접 검색을 전수 검색과 비교하고, 240개 움직이는 프레임의 결정성·부피·유효 범위, 정확한 분할 모드와 depth 변경을 확인합니다.

## 출처와 라이선스

- KD-tree / 스프링 / 실장님 포트: 이 프로젝트에서 작성, GPL-3.0-or-later (저장소 LICENSE).
- [simplex-noise.js 4.0.3](https://github.com/jwagner/simplex-noise.js): Jonas Wagner, MIT. 원본 구현과 라이선스는 vendor/에 있습니다.
- [Three.js r170](https://github.com/mrdoob/three.js/tree/r170): MIT. browser/vendor/에 포함되며 네 단계 브라우저 연구에서 사용합니다. 실장님 장면은 자체 WebGL2 도구를 사용합니다.

## English

Import **project.md** into Siljangnim. It is self-contained and needs no API key, asset download, Python or Node installation. Orbit with the mouse and adjust depth, noise speed, damping, seed and display style. Actual 3D points follow time-varying simplex-noise targets through damped springs; a median KD-tree is rebuilt on x/y/z every frame.

Default displayed split ratios are spring-smoothed and deliberately lag exact median boundaries; they are a visual partition, not an exact point-classification tree. Switch on **Exact median boundaries** to compare. The browser folder contains the original four static interactive studies. This is a live port of the Short's algorithm, not the narrated video timeline. Run `node verify.mjs` to validate geometry, nearest-neighbor queries and animated partitions; `node build.mjs` rebuilds the importable document.
