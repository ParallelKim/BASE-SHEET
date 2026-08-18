# 출판 탭 검증 차트 제작

채점 진리(`BarSpec`)를 출판 베이스 악보에서 읽는 절차다. pytest가 초록이라고 인쇄와 같다는 뜻이 아니다. 잠근 마디가 악보와 같을 때만 진리다.

이 문서는 「있지」·Antifreeze에서 쓴 방법을 고정한다. 차트를 고치거나 곡을 추가할 때 따른다.

## 목적

- 전사 MIDI를 **섹션별로** 출판 탭 피치와 대조한다.
- 추측 근음은 채점하지 않는다. 안 읽힌 마디는 빈 타임라인(`skip`)으로 둔다.
- 한 곡을 한 점수로 섞어 채점하지 않는다.

## 산출물

| 역할 | 경로 |
|---|---|
| 리듬 확장 (단일 소스) | `tests/chart_table.py` (`BarSpec`, `spec_hits`) |
| 있지 기보 72마디 | `tests/ijji_chart.py` |
| Antifreeze 기보 80마디 | `tests/antifreeze_chart.py` |
| 차트만 펼침 (피치 발명 금지) | `tests/ijji_truth.py`, `tests/antifreeze_truth.py` |
| 연속성·스냅샷·히트 수 | `tests/test_chart_layout.py` |
| 마디 크롭 | `tests/fixtures/score_crops/{ijji,antifreeze}/mNNN.png` |
| 페이지 렌더 | `tests/fixtures/score_crops/{ijji,antifreeze}/pages/pN.png` |
| 크롭 박스 | `tests/fixtures/score_crops/manifest.json` |
| 크롭 스크립트 | `scripts/crop_score_bars.py` |
| 스템 vs 차트 마디 리포트 | `scripts/report_bar_scores.py` |

식별자 `ijji`는 자우림 **「있지」**다. 「잊지」가 아니다. `ijji*` 파일명을 바꾸지 않는다.

## 원칙

1. **기보 마디 하나 = `BarSpec` 하나.** `written`은 1부터 연속. 반복·볼타는 `PLAY`(1-based 기보 번호 나열)로만 펼친다.
2. **진리 파일은 차트를 펼치기만 한다.** 피치를 여기서 만들지 않는다.
3. **읽지 못하면 잠그지 않는다.** `lock=approx`이면 `rhythm=skip`, `pitches=()`. 루프 근음을 짐작해 넣지 않는다.
4. **이미 잠근 차트도 틀린다.** OCR·비전·패딩 크롭으로 넣은 값은 인쇄 번호가 보이는 크롭으로 다시 본다.
5. **TAB 비전/OCR은 신뢰하지 않는다.** 줄 혼동, 두 단을 한 마디로 읽기, 프렛 `2`/`5` 오인이 잦다.

## 절차

### 1. 마디 크롭

```bash
python scripts/crop_score_bars.py
# 기본 PDF: tests/fixtures/ijji_bass_score.pdf, Antifreeze_bass_score.pdf
```

각 `mNNN.png`는 기보 한 마디다. 코드·가사·베이스 오선·TAB이 한 장에 들어가게 상하를 넉넉히 자른다. 파일명의 `NNN`은 **인쇄된 마디 번호**와 같아야 한다.

페이지 전체(`pages/pN.png`)도 같이 둔다. 단의 코드 진행·볼타·더블 바를 볼 때 쓴다.

### 2. 번호가 맞는지 확인

인쇄 숫자가 보이는 크롭으로 파일명을 검증한다. 있지 예: m001, m013, m025, m045, m049, m053, m061. Antifreeze 예: m001, m017, m033, m044(p.4 시작).

번호가 어긋나면 차트 전체를 밀어서 고치지 말고, 크롭 스크립트의 단(system) 수부터 고친다.

### 3. 페이지로 뼈대, 크롭으로 필

1. `pages/pN.png`로 그 페이지의 코드 진행, 8분/온음, 반복괄호, 더블 바를 적는다.
2. 필·슬라이드·쉼이 있는 마디는 `mNNN.png`를 연다.
3. 페이지 개요와 개별 크롭이 다르면 **인쇄 번호가 보이는 쪽**을 이긴다.

### 4. 한 마디를 읽는 우선순위

겹치면 위가 이긴다.

1. **인쇄 마디 번호** — 이 파일이 그 마디인지.
2. **코드 심볼** (보컬 위). 한 마디에 코드가 둘이면 리듬도 둘(`split8` / `pair` / `half_ee`).
3. **TAB 프렛 + 줄.** 4현은 위부터 G–D–A–E. E현 2 = F#1(30), A현 5 = D2(38), E현 5 = A1(33), E현 0 = E1(28).
4. **베이스 오선 음.** TAB과 오선이 다르면 오선 음 + 코드를 쓰고, TAB 줄 오인을 의심한다.
5. 가사·볼타 괄호·더블 바는 **어느 단인지** 가리는 데만 쓴다. 피치를 만들지 않는다.

은음(grace)·고스트(`x`)는 채점 온셋에 넣지 않는다. 슬라이드 도착음은 넣는다.

### 5. 크롭 패딩 함정

상하 패딩이 커서 **위·아래 단이 같이 들어온다.** 비전/OCR이 이웃 마디를 본 마디라고 단정한다.

- 파일명 마디와 **인쇄 숫자**가 다르면 이웃이다. 쓰지 않는다.
- 한 크롭에 8분 페달과 필 스태프가 같이 있으면, 본선(보통 위 베이스 단)만 잠근다. `<2x>` 반음 스태프는 채점 라인이 아니다.
- 가사가 그 섹션과 안 맞으면 (예: 드라이브 가사가 코다 크롭에 보임) 단이 섞인 것이다.

### 6. 리듬을 고른다

`tests/chart_table.py`의 `rhythm`만 쓴다. 새 패턴이 반복되면 리듬을 추가하고, 한 마디뿐이면 `hits`다.

| rhythm | 인쇄 | 히트 |
|---|---|---|
| `rest` | 온쉼표 | 없음 |
| `eight` | 같은 음 8분 ×8 | 8 |
| `split8` | 음 A 8분 ×4, 음 B 8분 ×4 | 8 |
| `half_ee` | 2분 A, 스타카토 8분 B 둘, 4박 쉼 | 3 |
| `pair` | 2분 A + 2분 B | 2 |
| `whole` | 온음표 | 1 |
| `half` | 2분 하나 (나머지 쉼) | 1 |
| `hits` | 불규칙 필. `events=(eighth, dur_eighths, pitch)` , 8분 격자 0–8 | `events` 길이 |
| `skip` | 미읽음. `lock=approx`만 | 없음 |

있지 버스(13–15 등)는 `pair`가 아니라 `half_ee`다. 드라이브(45–60)는 마디당 코드 하나가 아니라 `split8`(또는 그 마디의 `hits` 필)다.

`hits`의 `eighth`는 그 마디 안 8분 위치(0–7.x), `dur_eighths`는 길이. 쉼은 이벤트를 안 넣는다.

### 7. lock과 스냅샷

- `lock=score`: 위 우선순위로 읽은 음. 채점한다.
- `lock=approx` + `skip`: 아직 못 읽음. 자리만 유지.

`LOCK_SNAPSHOT`에 잠근 마디의 `(rhythm, pitches)`를 넣는다. 스냅샷을 고치려면 **그 마디 크롭을 다시 연다.** 테스트만 맞추려고 스냅샷을 바꾸지 않는다.

`tests/test_chart_layout.py`: 기보가 1..N 연속인지, 스냅샷이 차트와 같은지, truth==chart인지, 섹션이 타임라인을 나누는지, 히트 수가 인쇄와 같은지.

### 8. 이미 잠근 값을 다시 본다

OCR로 채운 필·루프는 특히 다시 본다. 이 프로젝트에서 실제로 틀린 예:

- 있지 버스 `pair`(2분+2분) → 인쇄는 2분 + 8분 둘 + 쉼 (`half_ee`).
- 있지 드라이브 한 마디 한 코드 → 인쇄는 두 코드×4 8분. 51마디 Bm은 F#m\|E.
- 있지 28·32·48·52 필을 같은 패턴으로 묶음. 32 마지막은 A가 아니라 E0.
- 있지 코다 62 F# → A 페달. 64·66은 A then E2.
- Antifreeze p.5 skip을 “안 읽힘”으로 둔 마디가 2~4 8분+쉼 또는 온음표 아웃트로.
- 70·73·75·79 OCR 근음이 인쇄와 다름. 79의 `0-0-2`는 C# 온음표.

고친 뒤에는 `LOCK_SNAPSHOT`과 섹션 히트 수 테스트를 같이 갱신한다.

### 9. 커밋 범위

커밋하지 않는다: `ijji_bass.m4a`(로컬 이름), IDMT wav (재배포 금지).
커밋한다: 출판 악보 PDF, 마디 크롭, 이 문서, `Antifreeze_bass_mixed.m4a`, `있지 - 자우림_bass_mixed.m4a`.

```bash
pytest                         # addopts가 slow 제외
pytest -o addopts= -m slow     # 스템 전사
python scripts/report_bar_scores.py
```

스템 전사는 차트 잠금 다음에 돌린다. 차트만 바꾸고 하한을 맞추려고 피치를 깎지 않는다.

## MIDI (4현 표준)

있지: F#1=30 D2=38 A1=33 E1=28 B1=35 G#1=32 E2=40 A2=45 G#2=44 C#2=37 F#2=42 G2=43 B2=47 C#3=49 D3=50.

Antifreeze: B1=35 C#2=37 F#1=30 E1=28 A#1=34 G#1=32 D#2=39.

CLI: 있지 `--bpm 84 --grid 8 --key "F# minor"` (인쇄 ♩=83). Antifreeze `--bpm 128 --grid 8 --key F#`.

## PLAY (연주 순)

있지: 1–72, 반복 없음. 테스트 섹션 이름 `coda_a`/`coda_b`는 61–72 구간일 뿐, 악보 코다 점프가 아니다.

Antifreeze 126마디 (`Antifreeze_bass_mixed.m4a`):

- 1–8 인트로
- 9–24, 9–24 (`|: ` m.9, `:|` m.24)
- 25–42 (1st ending), 25–39 + 43 (2nd ending; `|: ` m.25)
- 44–47 페달 1회
- 48–59 두 번 (6 cycles)
- 65–72 브레이크다운. 이 믹스에는 p.5 mm.60–64 필 엔딩이 따로 없음
- 73–80, 73–80 (아웃트로 반복)

인쇄 반복 기호를 펼친 뒤 **스템 마디 근음·길이로 확인**한다. 하한을 맞추려고 PLAY 마디를 만들지 않는다. `PLAY_SNAPSHOT_PREFIX` / `PLAY_SNAPSHOT_VOLTA2`가 앞부분을 얼린다.

## 하지 말 것

- 안 읽은 필 피치를 만들기
- 추측 근음을 `lock=score`로 두기
- 전곡을 한 점수로 합쳐 하한만 맞추기
- `ijji*` 이름을 「잊지」 쪽으로 바꾸기
- `ijji_bass.m4a`·IDMT를 커밋하기. 믹스 스템 `있지 - 자우림_bass_mixed.m4a`는 이미 픽스처다.
- 파이프라인 기본값을 Basic Pitch로 두기, slap 스펙트럼 피크 재조율, 타이트 NMS, Antifreeze 8분을 붙이기
- 크롭 비전 캡션의 옥타브(A-string 0 = A2 같은 말)를 그대로 믿기. A현 개방은 A1=33이다.
