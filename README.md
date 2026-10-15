# Siljangnim Remix Lab

**쇼츠에서 본 실험을 내려받아 직접 바꿔 보세요.**

실장님 리믹스 쇼츠 01–09의 실행 코드와 입력 자료입니다. 영상의 설명용 애니메이션 대신, 실제 결과를 계산한 실험을 모았습니다. Python과 FFmpeg로 실행하며 API 키, 유료 음성 서비스, GPU는 필요하지 않습니다. 각 프로젝트의 README에서 실행 명령과 모델의 제한을 확인하세요.

[Download ZIP](https://github.com/okdalto/siljangnim-remix-lab/archive/refs/heads/main.zip) · [Siljangnim](https://github.com/okdalto/siljangnim)

## 시작하기

Python 3.11 또는 3.12와 FFmpeg(ffprobe 포함)를 먼저 설치하세요. FFmpeg는 시스템 PATH에 있어야 합니다.

```sh
git clone https://github.com/okdalto/siljangnim-remix-lab.git
cd siljangnim-remix-lab
python3 -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

| 번호 | 프로젝트 | 바꿔 볼 것 |
| --- | --- | --- |
| 01 | [낙서 × 관절](projects/01-doodle-walker) | 모터 설정과 이동 거리 목표 |
| 02 | [흔들리는 의자](projects/02-chair-search) | 발 위치와 점점 무거워지는 상자 |
| 03 | [도시 × 핀볼](projects/03-city-pinball) | 건물 경계와 반발 |
| 04 | [작은 도미노 × 거대한 도미노](projects/04-domino-amplifier) | 크기 비율과 간격 |
| 05 | [목소리 × 롤러코스터](projects/05-voice-coaster) | 목소리의 끝음과 발사 비거리 |
| 06 | [미로 × 성장](projects/06-maze-growth) | 미로 seed와 가지 탐색 |
| 07 | [책상 물건 × 테트리스](projects/07-object-tetris-photo) | 물건 순서와 배치 |
| 08 | [다리 × 보강](projects/08-bridge-repair) | 부재, 하중, 보강 위치 |
| 09 | [음악 × 손글씨](projects/09-music-type-collision) | 드럼 에너지와 스프링 |

각 폴더에서 README의 명령을 실행하면 결과 영상/수치가 생성됩니다. 물리 실험은 단순화된 모델이며, 실제 구조물 설계나 현실의 롤러코스터 안전성을 검증하지 않습니다. 플랫폼·라이브러리 차이로 부동소수점 결과가 조금 달라질 수 있습니다.

02는 동일한 상자 여섯 개를 점점 무겁게 쌓으며 다리 설계 18개를 비교합니다. 05는 목소리의 pitch를 실제로 변형하고 다시 측정해, 레일 끝에서 날아가는 카트의 비거리를 비교합니다. 공개 기본 입력은 직접 합성한 모음이며 영상의 George 음성은 포함하지 않습니다.

## English

Download and remix the actual experiments featured in the Siljangnim Shorts series. Each numbered folder includes source code, inputs and run instructions. These are executable experiments, not narrated-video templates. Python 3.11/3.12 and FFmpeg are required; no API keys or paid services are needed. Start with the installation commands above, then follow the README in your chosen project.

The models are deliberately simplified. See each project's documented assumptions and any differences between bundled sample inputs and the published video. Episode 05 now edits and remeasures audio to compare launch distances. Its bundled synthetic input differs from the local George sample used in the video.

## License and credits

Project-authored source code is licensed under GPL-3.0-or-later; see [LICENSE](LICENSE). Third-party libraries and input assets retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and project-specific notices. Generated input imagery is identified as such. The commercial narration service, credentials, browser profiles and video-production caches are not part of this repository.

Create with words and remix freely. Your creative coding studio, **siljangnim**.

## Verification

```sh
python scripts/check_environment.py
python scripts/verify_all.py
```

The second command reruns all nine experiments, renders their outputs and fully decodes every generated MP4. It can take several minutes and writes `verification-report.json`. The initial nine-project check used a fresh HTTPS clone on 2026-10-15. The current report also reruns the revised chair load and audio launch experiments locally using the pinned requirements on macOS/Python3.12. The music-type browser viewer was also opened, played and visually checked. This is not a claim of testing every OS.
