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

`.mid`는 음원 시간축 MIDI, `.quant.mid`는 양자화, `.musicxml`은 기보입니다.

분리가 덜 된 스템은 다른 악기 잔여가 음표로 붙을 수 있습니다. `--min-duration`을 키우거나 `--bpm`을 직접 넣으세요.

같은 음을 8분으로 반복하는 라인(앤티프리즈 인트로)은 `--bpm`과 `--grid 8`을 악보와 맞추세요. 조표는 베이스 음만으로 F#(♯6)이 잘 안 나와 `--key F#`이 필요합니다.

## 테스트 음원

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
