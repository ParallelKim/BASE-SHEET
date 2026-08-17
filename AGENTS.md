# BASE-SHEET 에이전트

개인·비영리 베이스 스템 → MIDI / MusicXML. 품질 기준은 **MIDI가 스템처럼 들리는 것**이다. 소스 분리는 범위 밖이다.

사용자 대면 설명은 한국어.

## 검증 차트

출판 탭으로 채점 진리를 만들거나 고칠 때는 **[docs/chart-verification.md](docs/chart-verification.md)** 를 따른다.

요약: 기보 마디 하나 = `BarSpec` 하나. 크롭(`tests/fixtures/score_crops/`)으로 읽고, 못 읽으면 `skip`. 추측 근음은 채점하지 않는다. 이미 잠근 차트도 인쇄 번호가 보이는 크롭으로 다시 본다. 진리 파일은 차트를 펼치기만 한다.

## 파이프라인

- 패키지: `src/base_sheet/`. 기본 엔진은 torchcrepe(16 kHz / 10 ms, viterbi). Basic Pitch는 기본값이 아니다.
- slap 스펙트럼 피크 재조율, 타이트 NMS, Antifreeze 8분을 붙이는 처리를 다시 넣지 않는다.
- 있지: `--bpm 84 --grid 8 --key "F# minor"`. 식별자 `ijji` = 「있지」(잊지 아님). `ijji*` 이름을 바꾸지 않는다.
- Antifreeze: `--bpm 128 --grid 8 --key F#`. PLAY는 126 연주 마디 (`tests/antifreeze_chart.py`).
- 두 픽스처 스템은 믹스 잔여(킥·다른 저음)가 있다. 소스 분리·킥 게이트를 넣지 않는다.
- 마디 오차: `python scripts/report_bar_scores.py`.
- 웹 스튜디오: `python scripts/serve_midi_viewer.py` (크롭 대조 + 음원 업로드).

## 저장소

커밋함: 출판 악보 PDF, 마디 크롭, Antifreeze 스템, 있지 믹스 스템(`있지 - 자우림_bass_mixed.m4a`), [docs/chart-verification.md](docs/chart-verification.md).

커밋하지 않음: `ijji_bass.m4a` (`.gitignore` 로컬 이름), IDMT wav (CC BY-NC-ND 재배포 금지).

섹션별 테스트와 전곡 통합을 유지한다. 한 점수로 섞지 않는다. 차트만 바꾼 뒤 느린 스템 하한을 맞추려고 진리 피치를 깎지 않는다. 느린 테스트는 `pytest -o addopts= -m slow` (`addopts`가 `-m 'not slow'`).
