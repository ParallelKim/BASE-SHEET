# 스튜디오 호스팅

개인용입니다. 휴대폰에서 보기·올리기·변환까지 하려면 **무료 CPU 컨테이너**가 맞고, 느려도 됩니다.

추천: **Hugging Face Spaces**(Docker, CPU basic, 카드 없음). 같은 주소에서 MIDI 보기와 업로드 전사를 합니다. 잠들면 첫 접속이 느리고, 전사는 CPU라 곡당 수분~십몇 분 걸릴 수 있습니다.

노트북만 켜 두고 쓸 거면 Cloudflare 터널도 됩니다. Vercel/Firebase는 보기 전용(정적)입니다.

## Hugging Face Spaces (휴대폰 변환)

1. [huggingface.co](https://huggingface.co/) 계정 (무료).
2. **New Space** → SDK **Docker** → Hardware **CPU basic** → **Private** (올린 스템이 공개되지 않게).
3. GitHub `ParallelKim/BASE-SHEET` 를 연결하거나, 이 저장소의 `Dockerfile` 이 있는 브랜치를 가리킵니다.
4. 빌드가 끝날 때까지 기다립니다 (torch CPU 이미지, 처음엔 꽤 걸림).
5. Space URL을 휴대폰 브라우저에서 엽니다. 올리기 탭 → wav/mp3/m4a → 완료되면 보기 탭에서 MIDI와 `.preview.wav` / `.compare.wav`.

로컬에서 같은 이미지를 시험:

```bash
docker build -t base-sheet-studio .
docker run --rm -p 7860:7860 base-sheet-studio
# http://127.0.0.1:7860/
```

Space가 잠긴 뒤에는 첫 요청이 깨우는 데 몇 분 걸릴 수 있습니다. 전사 중에는 화면을 유지하세요 (폴링이 Space를 깨워 둡니다). 재시작되면 올린 작업은 사라집니다. 남기고 싶은 MIDI는 로컬 `web/data/` 에 넣고 다시 배포하세요.

## 노트북 + 터널 (계정 없이)

```bash
python scripts/serve_midi_viewer.py --no-open
npx -y cloudflared tunnel --url http://127.0.0.1:8765
```

나온 `https://….trycloudflare.com` 을 폰에서 엽니다. 노트북이 켜져 있는 동안만 됩니다.

## 보기만 (Vercel / Firebase, 무료)

업로드는 없습니다. 있지·Antifreeze MIDI와 크롭만 공개합니다.

```bash
python3 scripts/build_studio_static.py
npx -y vercel@latest
```

Firebase Hosting: `npx -y firebase-tools@latest deploy --only hosting`. `.firebaserc` 의 `default` 는 본인 프로젝트 ID로 바꾸세요.

## 정적 산출물

```bash
python3 scripts/build_studio_static.py
```

| 경로 | 내용 |
|---|---|
| `web/index.html` | 스튜디오 UI |
| `web/data/*.mid` | 성능·양자화 MIDI |
| `web/score_crops/` | 출판 마디 PNG (빌드 때 복사, git 제외) |

## 올리지 않는 것

- Vercel/Firebase Function 에 torchcrepe (번들·시간·업로드 크기)
- 유료 GPU / 상시 VM
- IDMT wav, `out/` 미리듣기 WAV를 정적 호스팅에 올리기
