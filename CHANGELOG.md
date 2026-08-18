# Changelog

## Unreleased

웹 스튜디오: 픽스처 MIDI·출판 크롭 대조, 새 스템 업로드 후 전사 (`python scripts/serve_midi_viewer.py`).

정적 호스팅(보기 전용, 무료)과 Hugging Face Spaces Docker(휴대폰 업로드·CPU 전사). 유료 GPU/VM은 쓰지 않음. [docs/hosting.md](docs/hosting.md).

## 0.2.0 — 차트·PLAY·믹스 스템 채점

v0.1.0 이후 차트·PLAY·픽스처를 인쇄/스템에 맞추고 느린 테스트를 다시 돌린 상태.

- Antifreeze `PLAY` 126마디: 9–24 도돌이표, 25–볼타, 코러스 2회, 73–80 반복. 이 믹스에는 p.5 mm.60–64가 따로 없음.
- 있지 픽스처: `tests/fixtures/있지 - 자우림_bass_mixed.m4a` (믹스 잔여). `ijji_bass.m4a`는 `.gitignore`. 식별자는 `ijji`.
- 마디 리포트: `python scripts/report_bar_scores.py` → `out/listen/*_bars.txt` 와 `.compare.wav`.
- 하한: 있지 간주 chroma 0.55, IDMT 011 onset 0.79. 진리 피치는 하한 맞추려고 깎지 않음.
- 느린 테스트(`pytest -o addopts= -m slow`) 있지·Antifreeze·IDMT 통과. 탭 1.0이 목표는 아님.

## 0.1.0 — MVP 초안 (1차 구현 및 테스트 환경 구성)

첫 태그. 개인·비영리 베이스 스템 → MIDI / MusicXML 파이프라인의 초안과, 출판 탭으로 채점할 수 있는 테스트 뼈대를 고정한다.

### 파이프라인

- 분리된(또는 잔여가 있는) 베이스 스템을 입력으로 받는다. **소스 분리 자체는 범위 밖.**
- 기본 엔진은 torchcrepe f0(16 kHz / 10 ms, 없으면 librosa pYIN) + CREPE Notes 방식 분할.
- 옥타브는 STFT로 다시 고르고, 같은 음 반복은 저역 온셋·그리드로 쪼갠다.
- 출력: 성능 MIDI(`.mid`), 양자화 MIDI(`.quant.mid`), MusicXML, 미리듣기/비교 WAV.
- 브라우저 피아노롤: `python scripts/serve_midi_viewer.py`

의도적으로 넣지 않은 것: Basic Pitch 기본값, slap 스펙트럼 피크 재조율, 타이트 NMS로 8분을 붙이는 처리.

### 채점 진리 (출판 탭)

진리 피치는 차트 표(`BarSpec`)만 쓴다. 추측 근음은 채점하지 않는다.

| 곡 | 식별자 | 기보 | 연주 순 | 비고 |
|---|---|---|---|---|
| 자우림 「있지」 | `ijji` (잊지 아님) | 72마디, 반복 없음 | 72 | `--bpm 84 --grid 8 --key "F# minor"` |
| Antifreeze | `antifreeze` | 80마디 | 126 (9–24 반복, 25–볼타, 코러스 2회, 73–80 반복) | `--bpm 128 --grid 8 --key F#` |

- `lock=score`: 인쇄에서 읽은 음. `rhythm=hits`는 불규칙 필. `split8`은 한 마디에 두 코드×4 8분. `half_ee`는 2분 + 스타카토 8분 둘.
- `lock=approx` / `skip`: 탭이 아직 안 읽힌 마디. 타임라인만 유지.
- 있지 72마디·Antifreeze 80마디는 전부 score (마디 크롭으로 p.5 skip을 채움).

섹션별 테스트 + 전곡 통합. 한 번에 섞어 채점하지 않는다.

### 테스트 환경

```bash
pip install -e ".[dev]"
pytest                         # 빠른 레이아웃·단위 테스트 (addopts가 slow 제외)
pytest -o addopts= -m slow     # 스템 전사 (있지 / Antifreeze / IDMT)
python scripts/fetch_idmt_bass.py   # IDMT-SMT-Bass (재배포하지 않음)
python scripts/crop_score_bars.py   # 출판 악보 마디 크롭
```

- 빠른 테스트: 차트 연속성, 스냅샷, 크롭 파일, MIDI 뷰어 페이지.
- 느린 테스트: 실제 스템 전사 후 섹션별 exact/chroma 하한.
- 마디 크롭: `tests/fixtures/score_crops/{ijji,antifreeze}/mNNN.png` (코드·TAB이 한 장에 보이게 상하 패딩).
- 차트 제작 절차: [docs/chart-verification.md](docs/chart-verification.md). 에이전트는 [AGENTS.md](AGENTS.md)에서 참조한다.
- 팀 공유 픽스처: [tests/fixtures/README.md](tests/fixtures/README.md) (악보 PDF·마디 크롭·믹스 스템).

### 품질 목표

MIDI가 스템처럼 들려야 한다. 인쇄 레이아웃이 “맞다”는 것은 pytest 통과가 아니라, 잠근 마디가 출판 악보와 같다는 뜻이다.
