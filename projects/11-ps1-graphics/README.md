# 11 · 무엇이 레트로 게임을 레트로답게 보이게 할까요?

2026-10-16 제작한 PS1 그래픽스 쇼츠 네 편의 실행 프로젝트와 공통 연구소 복도 비교 장면 소스입니다. WebGL2로 선택한 PS1 렌더링 제약을 재현하는 교육용 실험이며, PS1 전체 에뮬레이터는 아닙니다.

## 실장님에서 바로 실행

아래 문서 하나를 내려받아 실장님 에이전트에게 **“이 project.md를 프로젝트로 가져와 실행해 줘”**라고 요청하세요. `project_import_md`로 가져올 수 있습니다. 네 실험은 외부 에셋, Python, 유료 API 없이 실행됩니다.

| 쇼츠 | 가져올 문서 | 비교 내용 |
| --- | --- | --- |
| 바닥은 왜 출렁일까? | [affine/project.md](affine/project.md) | 원근 보정 → affine UV → 삼각형 세분화 |
| 모서리는 왜 떨릴까? | [jitter/project.md](jitter/project.md) | 부드러운 좌표 → 정수 격자 스냅 |
| 면의 앞뒤는 왜 뒤집힐까? | [depth/project.md](depth/project.md) | 깊이 버퍼 → 면 단위 정렬, 추가 near-plane 실험 |
| 거친 질감은 어떻게 만들어질까? | [pixels/project.md](pixels/project.md) | 폴리곤 수, 정점 조명, 색 양자화·디더링, 샘플링·해상도 |

**Topic**으로 주제, **Comparison**으로 기본/제약/완화 또는 다음 제약을 고릅니다. 일부 변화는 타임라인 재생 중 순차 적용됩니다. 마우스를 누르고 드래그하면 카메라를 움직입니다. 영상 합성용 장면이어서 화면 위아래에 자막 여백이 있습니다. 세 번째 비교가 모든 주제에서 해결책을 의미하지는 않습니다.

각 폴더의 `clean.json`, `effect.json`, `fix.json`은 촬영 조건별 scene입니다. `setup.js`는 공통 셰이더·기하·절차적 텍스처, `render.js`는 주제별 카메라·그리기 코드입니다. 수정 후 Python 3.11 이상에서 다음 명령으로 문서를 다시 만드세요. 추가 Python 패키지는 필요 없습니다.

```sh
cd projects/11-ps1-graphics
python3 build_scenes.py
```

`parameters.json`에는 최종 제작에서 저장한 조건별 전환 시점이 있습니다. 로컬 영상 계획이나 유료 음성 캐시 없이 빌드할 수 있도록 분리했습니다.

## 공통 연구소 복도 + 캐릭터 비교

네 편 도입과 마지막 얼굴 클로즈업에서 사용한 복도·카메라·효과 소스도 보관합니다. 왼쪽 기본 렌더링과 오른쪽 PS1 제약은 **같은 모델, 텍스처, 카메라, 시간**을 사용합니다. 기본 쪽도 원본 저폴리곤 캐릭터입니다. 현대 고밀도 모델과 비교하는 장면이 아닙니다.

캐릭터는 [PSX Style Teen — swickster](https://swickster.itch.io/psx-style-teen)입니다. 제작자 안내는 “Free to use in commercial projects. Credit is appreciated!”입니다. 원본 파일의 독립적인 재배포 조건은 명시되어 있지 않아 FBX·텍스처·모델이 포함된 scene은 Git에 넣지 않았습니다. 제작자 페이지에서 직접 다운로드하고 다음과 같이 연결하세요.

1. 내려받은 RAR을 풀어 `assets/PSXStyleTeen/PS1Teen1.fbx`와 `assets/PSXStyleTeen/PS1Teen_Diffuse.png`를 배치합니다.
2. Node.js 20 이상과 Python 3.11 이상에서 실행합니다.

```sh
npm ci
node import-teen.mjs
python3 build_lab.py
```

3. 생성된 `output/lab-teen.md`를 실장님에 가져오면 승인된 12초 전체 비교를 볼 수 있습니다. `output/lab-intro.md`는 세로 영상 도입, `output/lab-portrait.md`는 얼굴 클로즈업 비교입니다. 영상의 자막·음성은 포함하지 않습니다.

`import-teen.mjs`는 FBX를 펼친 삼각형으로 변환하고 팔 자세를 내립니다. 원본 법선은 유지합니다. 모델 배율은 최종 승인된 0.8입니다. `lab_setup.js`는 자체 제작 복도·문·타일·조명 텍스처이며 외부 이미지를 사용하지 않습니다. 세 `lab_*render.js` 파일은 실제 최종 장면의 카메라·구도를 보존합니다. 생성된 파일에는 모델 데이터가 포함되므로 공개 저장소에 다시 올리기 전에 에셋 조건을 확인하세요.

## 기술적 범위

- Affine은 보간 방식이고 warping은 그 결과입니다. UV×clip.w와 clip.w의 보간 뒤 나눗셈으로 기본 원근 보정을 상쇄합니다. 바닥 2개 삼각형과 12×12 분할을 비교합니다.
- Jitter 실험은 96×72 격자로 현상을 확대합니다. PS1의 고정 해상도라는 뜻이 아니며 GTE 고정소수점 계산 전체를 구현하지 않았습니다.
- Depth 실험은 변환된 삼각형 중심 깊이로 정렬합니다. 교차하는 면을 단일 순서로 해결하지 못하는 경우를 보여 줍니다. 실제 게임별 ordering 구현은 다양합니다.
- Near-plane의 전체 삼각형 버리기/클리핑 비교는 추가 실험입니다. 최종 쇼츠 본문에서는 제외했습니다. 실제 PS1의 모든 클리핑 방법이나 GPU 크기 제한을 재현하지 않습니다.
- Low-poly와 Gouraud는 별개입니다. Dithering은 최종 색 정밀도 감소 전 반복 오프셋을 넣는 예시이며 GPU의 모든 primitive별 규칙을 구현하지 않았습니다.
- Nearest 샘플링과 내부 저해상도도 별개입니다. 복도는 오른쪽 192×240 렌더 타깃과 160×200 정점 격자를 사용합니다. 이는 설명용 설정입니다. CRT 효과는 없습니다.

## 보관 범위와 검증

실행 scene, 셰이더, 복도 제작 코드, 모델 연결 과정과 최종 조건을 보관합니다. 최종 MP4, 유료 내레이션, 개인 Drive 정보, 제작 캐시와 폐기한 인물 시안은 포함하지 않습니다. 영상 편집 전체를 자동 제작하는 패키지가 아니라 쇼츠에서 사용한 실험의 재현용 아카이브입니다.

원본 네 문서는 제작 과정에서 실장님 재가져오기·실행·캡처로 확인했습니다. 이 공개본의 빌드·구조 검증 범위는 [verification.json](verification.json)을 참고하세요.

## English / credits

Four importable, asset-free Siljangnim WebGL2 experiments explaining selected PS1 rendering constraints. Run `python3 build_scenes.py` to rebuild them. The laboratory intro and face comparison sources are included; acquire Swickster's model separately, run `npm ci`, `node import-teen.mjs`, then `python3 build_lab.py`. Import a generated document from `output/`. No commercial narration or third-party character files are redistributed.

Authored source: GPL-3.0-or-later (repository LICENSE). Three.js 0.185.0: MIT, installed separately. Swickster's model retains its author's terms, not this repository's GPL.

Technical references: [PSX-SPX GPU](https://psx-spx.consoledev.net/graphicsprocessingunitgpu/), [GTE](https://psx-spx.consoledev.net/geometrytransformationenginegte/). These references informed the original educational implementation; they are not bundled assets.
