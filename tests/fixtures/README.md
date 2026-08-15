# 테스트 픽스처 (팀 공유)

채점·크롭·지침은 저장소에 둔다. 클론하면 악보와 마디 조각을 바로 볼 수 있다.

## 커밋하는 것

| 파일 | 내용 |
|---|---|
| `ijji_bass_score.pdf` | 자우림 「있지」 출판 베이스 악보 (akbobada) |
| `Antifreeze_bass_score.pdf` | Antifreeze 출판 베이스 악보 |
| `Antifreeze_bass_mixed.m4a` | Antifreeze 미리 분리한 베이스 스템 |
| `score_crops/ijji/m001.png` … `m072.png` | 있지 기보 마디 크롭 |
| `score_crops/antifreeze/m001.png` … `m080.png` | Antifreeze 기보 마디 크롭 |
| `score_crops/*/pages/pN.png` | 페이지 전체 |
| `score_crops/manifest.json` | 크롭 박스 |

차트 표는 `tests/ijji_chart.py`, `tests/antifreeze_chart.py`. 읽는 절차는 [docs/chart-verification.md](../../docs/chart-verification.md). 에이전트는 [AGENTS.md](../../AGENTS.md).

```bash
python scripts/crop_score_bars.py
```

## 커밋하지 않는 것

- `ijji_bass.m4a` — 있지 스템 (`.gitignore`). 로컬에 두면 느린 테스트가 쓴다.
- `idmt-smt-bass/` — IDMT-SMT-Bass는 CC BY-NC-ND라 재배포하지 않는다. `python scripts/fetch_idmt_bass.py`.
