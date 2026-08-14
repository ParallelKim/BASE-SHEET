# BASE-SHEET

분리된(또는 분리 잔여가 있는) 베이스 스템을 MIDI와 MusicXML 악보로 바꿉니다. 개인 악보 제작용이며 수익화하지 않습니다.

저장소 전체를 복제하지 않고, CREPE Notes·BassLift·Basic Pitch/NeuralNote·music21에서 **후처리 알고리즘만** 가져옵니다. 출처는 [THIRD_PARTY.md](THIRD_PARTY.md)를 보세요.

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

**악보** — `.musicxml`을 [MuseScore](https://musescore.org/)에서 엽니다. GarageBand/Logic/Guitar Pro도 MusicXML·MIDI를 읽습니다. 출판 탭과 비교할 때는 양자화 파일(`.quant.mid`, `.musicxml`)을 보세요. 스템과 음이 같은지는 양자화 전 `.mid` / `.preview.wav`가 맞습니다.

```bash
python -m base_sheet tests/fixtures/Antifreeze_bass_mixed.m4a -o ./out --bpm 128 --grid 8 --key F#
# out/Antifreeze_bass_mixed.preview.wav
# out/Antifreeze_bass_mixed.compare.wav   ← L=stem R=MIDI
# out/Antifreeze_bass_mixed.musicxml      ← MuseScore
```


분리가 덜 된 스템은 다른 악기 잔여가 음표로 붙을 수 있습니다. `--min-duration`을 키우거나 `--bpm`을 직접 넣으세요.

같은 음을 8분으로 반복하는 라인(앤티프리즈 인트로)은 `--bpm`과 `--grid 8`을 악보와 맞추세요. 조표는 베이스 음만으로 F#(♯6)이 잘 안 나와 `--key F#`이 필요합니다.

## 공개 평가셋 (악보가 없을 때)

BassLift·NeuralNote는 베이스 스템 픽스처를 넣지 않습니다. Basic Pitch 테스트 음원은 vocadito(보컬)입니다.

베이스 A2M용으로 공개된 건 Fraunhofer **IDMT-SMT-Bass-Single-Track** (17곡 DI, onset/offset/pitch XML, CC BY-NC-ND 4.0)입니다. 음원은 재배포하지 않고 받을 때만 씁니다.

```bash
python scripts/fetch_idmt_bass.py
pytest tests/test_idmt.py -m slow
```


`tests/fixtures/Antifreeze_bass_mixed.m4a` — 미리 분리한 베이스. 출판 악보는 `tests/fixtures/Antifreeze_bass_score.pdf`.

```bash
python -m base_sheet tests/fixtures/Antifreeze_bass_mixed.m4a -o ./out --bpm 128 --grid 8 --key F#
pytest
pytest -m slow
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
