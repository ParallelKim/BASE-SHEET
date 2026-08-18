# 스튜디오 호스팅

토이 프로젝트는 **돈을 내지 않는 구성**이 맞습니다. torchcrepe 전사는 수분·수 GB라 공짜 상시 서버에 올리기 어렵습니다.

권장:

| 무엇을 | 어디서 | 비용 |
|---|---|---|
| 있지·Antifreeze 보기 | Vercel / Firebase / GitHub Pages 정적 사이트 | 무료 |
| 새 스템 업로드 → 미리듣기 | 노트북에서 스튜디오 + (필요할 때만) 터널 | 무료 |

카드를 넣고 Cloud Run/Fly/Vercel Pro를 쓰는 건 이 규모에 맞지 않습니다.

## 1. 공개 보기 (정적, 무료)

```bash
python3 scripts/build_studio_static.py
```

| 경로 | 내용 |
|---|---|
| `web/index.html` | 스튜디오 UI |
| `web/data/catalog.json` | 곡 목록·PLAY·크롭 URL |
| `web/data/*.mid` | 성능·양자화 MIDI (git에 포함) |
| `web/score_crops/` | 출판 마디 PNG (`tests/fixtures/score_crops/` 복사, git 제외) |

가장 손쉬운 무료 배포는 **Vercel Hobby**입니다. GitHub 저장소를 Import하면 `vercel.json`이 빌드(`python3 scripts/build_studio_static.py` → `web/`)를 합니다. 주소는 `https://<이름>.vercel.app`.

```bash
npx -y vercel@latest
```

Firebase Hosting도 무료 한도 안에서 됩니다. `.firebaserc`의 `default`는 `base-sheet`이니 본인 프로젝트로 바꾸세요.

```bash
npx -y firebase-tools@latest login
npx -y firebase-tools@latest use --add
npx -y firebase-tools@latest deploy --only hosting
```

주소는 `https://<project-id>.web.app`.

로컬에서 정적만 미리보기:

```bash
python3 scripts/build_studio_static.py
python3 -m http.server 8080 --directory web
```

이 주소에서는 올리기가 꺼집니다. `/api`가 없으면 `data/catalog.json`만 씁니다.

## 2. 업로드 → 미리듣기 (로컬, 무료)

전사는 본인 머신에서 돌립니다. 품질(torchcrepe)과 비용이 같이 해결됩니다.

```bash
python scripts/serve_midi_viewer.py
# http://127.0.0.1:8765/
```

같은 Wi‑Fi의 휴대폰이면 `http://<노트북 LAN IP>:8765/` 로도 됩니다.

휴대폰·외부망에서 쓰려면 **Cloudflare 빠른 터널**(계정·카드 없음):

```bash
python scripts/serve_midi_viewer.py --no-open
npx -y cloudflared tunnel --url http://127.0.0.1:8765
```

나온 `https://….trycloudflare.com` 을 휴대폰 브라우저에 엽니다. 노트북이 켜져 있는 동안만 동작합니다. 새 곡을 자주 공개하려면 로컬에서 전사한 `.mid`를 `web/data/`에 넣고 정적 사이트를 다시 배포하면 됩니다.

## 쓰지 않는 것

- Vercel/Firebase Function에 torchcrepe를 넣기 (번들·시간·업로드 크기)
- GPU/상시 VM 유료 플랜
- 스템 m4a, IDMT wav, `out/` 미리듣기 WAV를 정적 호스팅에 올리기
