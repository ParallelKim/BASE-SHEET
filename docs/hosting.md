# 스튜디오 호스팅

모바일에서 있지·Antifreeze MIDI와 출판 마디 크롭을 보려면 **정적 사이트**를 올립니다. Firebase Hosting 또는 Vercel이 맞습니다.

전사는 torchcrepe가 수분 걸립니다. Firebase/Vercel 서버리스 제한 안에 넣지 않습니다. 새 스템을 올리려면 로컬에서 `python scripts/serve_midi_viewer.py` 를 켜세요.

## 정적 산출물

배포 전에 (Firebase `predeploy`·Vercel `buildCommand`가 대신 실행):

```bash
python3 scripts/build_studio_static.py
```

| 경로 | 내용 |
|---|---|
| `web/index.html` | 스튜디오 UI |
| `web/data/catalog.json` | 곡 목록·PLAY·크롭 URL |
| `web/data/*.mid` | 성능·양자화 MIDI (git에 포함) |
| `web/score_crops/` | 출판 마디 PNG (`tests/fixtures/score_crops/` 복사, git 제외) |

로컬에서 정적 미리보기:

```bash
python3 scripts/build_studio_static.py
python3 -m http.server 8080 --directory web
# http://127.0.0.1:8080/
```

API가 있는 로컬 서버(`serve_midi_viewer.py`)는 `/api/catalog`를 쓰고, 없으면 `data/catalog.json`으로 넘어갑니다.

## Vercel (추천: Git 연동)

1. [Vercel](https://vercel.com/)에서 GitHub 저장소 `ParallelKim/BASE-SHEET`를 Import.
2. Framework Preset는 Other. `vercel.json`이 `python3 scripts/build_studio_static.py` → `web/` 을 지정합니다.
3. Deploy. 주소는 `https://<이름>.vercel.app`.

CLI:

```bash
npx -y vercel@latest
```

프로덕션: `npx -y vercel@latest --prod`.

## Firebase Hosting

프로젝트 ID는 `.firebaserc`의 `default`입니다. 기본값은 `base-sheet`이니, 본인 프로젝트로 바꾸세요.

```bash
npx -y firebase-tools@latest login
npx -y firebase-tools@latest use --add
npx -y firebase-tools@latest deploy --only hosting
```

주소는 `https://<project-id>.web.app` 또는 `https://<project-id>.firebaseapp.com`.

새 프로젝트를 만들 때:

```bash
npx -y firebase-tools@latest projects:create <project-id> --display-name "BASE-SHEET"
npx -y firebase-tools@latest use <project-id>
npx -y firebase-tools@latest deploy --only hosting
```

`<project-id>`는 6–30자, 소문자·숫자·하이픈, 전역 고유여야 합니다.

## 올리지 않는 것

- 스템 m4a, IDMT wav, `out/` 미리듣기 WAV
- 업로드/전사 API (로컬 서버 전용)
