# BASE-SHEET

분리된(또는 분리 잔여가 있는) 베이스 스템을 MIDI와 MusicXML 악보로 바꿉니다. 개인 악보 제작용이며 수익화하지 않습니다.

저장소 전체를 복제하지 않고, CREPE Notes·BassLift·Basic Pitch/NeuralNote·music21에서 **후처리 알고리즘만** 가져옵니다. 출처는 [THIRD_PARTY.md](THIRD_PARTY.md)를 보세요.

현재 태그는 **v0.2.0** — 차트·PLAY·믹스 스템 채점. 범위와 한계는 [CHANGELOG.md](CHANGELOG.md)를 보세요. v0.1.0은 MVP 초안입니다.

## 설치

Python 3.10–3.12, ffmpeg(m4a 등).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

선택:

- `pip install torchcrepe` — 저음 f0 (없으면 librosa pYIN)
- `pip install basic-pitch` — `--engine basic-pitch`
- `pip install git+https://github.com/CPJKU/madmom.git` — 반복음 온셋 (없으면 librosa)

## 사용

```bash
python -m base_sheet path/to/bass.wav -o ./out
python -m base_sheet path/to/bass.m4a -o ./out --bpm 96 --grid 16
python -m base_sheet path/to/bass.m4a -o ./out --engine basic-pitch --snap-key --key "E minor"
```

기본 엔진은 **torchcrepe f0**(없으면 pYIN, 프레임을 E1 주기 기준으로 잡음) + CREPE Notes 분할입니다. 같은 음 반복은 저역 온셋과 박자 그리드의 RMS 재공격으로 쪼개고, 각 음의 옥타브는 스펙트럼의 f/2f로 다시 고릅니다. Basic Pitch는 `--engine basic-pitch`로만 쓰세요.

`.mid`는 음원 시간축 MIDI, `.quant.mid`는 양자화, `.musicxml`은 기보입니다. 같이 `.preview.wav`(MIDI를 베이스 톤으로 합성)와 `.compare.wav`(왼쪽=스템, 오른쪽=MIDI)가 나옵니다.

## 결과 확인

**듣기** — 스템과 같은지 보려면 `.compare.wav`를 헤드폰으로 재생하세요. 왼쪽이 원본 베이스, 오른쪽이 분석 MIDI입니다. MIDI만 들으려면 `.preview.wav` 또는 DAW/VLC에 `.mid`를 넣으세요. (GM 일렉트릭 베이스, 프로그램 33)

브라우저에서 출판 크롭과 MIDI를 같이 보고, 새 스템을 올려 전사합니다 (모바일 터치 가능):

```bash
python scripts/serve_midi_viewer.py
# http://127.0.0.1:8765/   (기본 0.0.0.0:8765)
# 보기: 있지 / Antifreeze 성능·양자화 MIDI + 기보 마디 크롭
# 올리기: wav/mp3/m4a 업로드 → 서버에서 파이프라인 실행
```

공개 주소에서 보기·올리기·변환까지 하려면 무료 Hugging Face Space(Docker CPU)를 씁니다. 느려도 됩니다. Vercel은 보기만. 절차는 [docs/hosting.md](docs/hosting.md).

```bash
docker build -t base-sheet-studio . && docker run --rm -p 7860:7860 base-sheet-studio
```

**악보** — `.musicxml`을 [MuseScore](https://musescore.org/)에서 엽니다. GarageBand/Logic/Guitar Pro도 MusicXML·MIDI를 읽습니다. 출판 탭과 비교할 때는 양자화 파일(`.quant.mid`, `.musicxml`)을 보세요. 스템과 음이 같은지는 양자화 전 `.mid` / `.preview.wav`가 맞습니다.

출판 악보를 마디 단위 이미지로 보려면 (코드·가사·TAB이 한 장에 들어가게 상하를 넉넉히 자릅니다):

```bash
python scripts/crop_score_bars.py
# tests/fixtures/score_crops/ijji/m016.png
# tests/fixtures/score_crops/antifreeze/m042.png
```

채점 진리를 인쇄에서 읽는 절차는 [docs/chart-verification.md](docs/chart-verification.md). 에이전트는 [AGENTS.md](AGENTS.md). 공유 픽스처 목록은 [tests/fixtures/README.md](tests/fixtures/README.md).

```bash
python -m base_sheet tests/fixtures/Antifreeze_bass_mixed.m4a -o ./out --bpm 128 --grid 8 --key F#
python -m base_sheet "tests/fixtures/있지 - 자우림_bass_mixed.m4a" -o ./out --bpm 84 --grid 8 --key "F# minor"
# out/*.preview.wav  out/*.compare.wav(L=스템 R=MIDI)  out/*.musicxml
python scripts/report_bar_scores.py   # 출판 탭과 마디별 대조, out/listen/
```

두 픽스처 스템은 킥·다른 저음이 섞일 수 있습니다. 소스 분리는 하지 않습니다. 잔여가 음표로 붙으면 `--min-duration`을 키우거나 `--bpm`을 직접 넣으세요.

같은 음을 8분으로 반복하는 라인(앤티프리즈 인트로)은 `--bpm`과 `--grid 8`을 악보와 맞추세요. 조표는 베이스 음만으로 F#(♯6)이 잘 안 나와 `--key F#`이 필요합니다.

## 공개 평가셋 (악보가 없을 때)

BassLift·NeuralNote는 베이스 스템 픽스처를 넣지 않습니다. Basic Pitch 테스트 음원은 vocadito(보컬)입니다.

베이스 A2M용으로 공개된 건 Fraunhofer **IDMT-SMT-Bass-Single-Track** (17곡 DI, onset/offset/pitch XML, CC BY-NC-ND 4.0)입니다. 음원은 재배포하지 않고 받을 때만 씁니다.

```bash
python scripts/fetch_idmt_bass.py
pytest -o addopts= -m slow tests/test_idmt.py
```

픽스처 스템은 믹스 잔여가 있는 베이스입니다. 악보는 `tests/fixtures/*_bass_score.pdf`.

```bash
pytest                         # 빠른 테스트 (slow 제외)
pytest -o addopts= -m slow     # 있지 / Antifreeze / IDMT 스템
```

## CLI

| 옵션 | 기본 | 의미 |
|---|---|---|
| `--engine` | `crepe` | `crepe` 또는 `basic-pitch` |
| `--bpm` | 자동 | 템포 투표 생략 |
| `--grid` | `8` | `8` `16` `8t` `16t` |
| `--key` | 추정 | 예: `F#`, `Em` |
| `--snap-key` | off | 조성에 피치 스냅 (E 제자리표 곡은 끄기) |
| `--min-duration` | 0.05 | 짧은 음 제거(초) |
| `--no-preview` | off | WAV 미리듣기/비교 생략 |
