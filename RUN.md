# Crypto Bot – Binance + Telegram (created 2025-08-22T11:28:20.035835Z)

## 0) 중요 보안 안내
- `.env`는 **절대 커밋 금지** (이미 `.gitignore` 처리됨).
- 현재 `.env`는 **테스트넷용** 설정이며, 운영 키를 사용하려면 `BINANCE_TESTNET=false`로 변경하세요.
- 본 코드는 교육용 예제이며, 실제 자금 투입 전 충분한 테스트를 진행하세요.

## 1) 빠른 시작
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 또는 제공된 .env 사용 후 값 확인
python app.py
```

텔레그램에서 `/start` 후, **스캔** → **추천 전략** → **자동매매 시작** 순서로 사용합니다.

## 2) git 초기화 & push
```bash
git init
git add .
git commit -m "feat: initial crypto-bot with Telegram UI and strategies"
git remote add origin <YOUR_REMOTE_GIT_URL>
git push -u origin main
```

## 3) 주요 기능
- 상위 유동성 USDT 마켓 스캔 → 각 코인별 지표 분석 → **추천 매매법** 제시
- 여러 전략(SMA 크로스, RSI 역추세, 볼린저 돌파) 지원
- **자동매매 버튼**으로 시작/중지, 실시간 상태 알림(텔레그램)
- 스팟/선물 선택 가능(기본: 스팟, 옵션: USDT-M 선물)

## 4) 파일 구조
```
crypto-bot/
 ├─ app.py                  # Telegram 인터랙션 & 메인 루프
 ├─ config.py               # 환경변수 로딩
 ├─ exchange/
 │   └─ binance_client.py   # 스팟/선물 래퍼
 ├─ core/
 │   ├─ scanner.py          # 코인 선별 & 추천 생성
 │   ├─ trader.py           # 자동매매 엔진
 │   └─ indicators.py       # 지표 계산(RSI, SMA, BB, ATR 등)
 ├─ strategies/
 │   ├─ sma_crossover.py
 │   ├─ rsi_reversion.py
 │   └─ bb_breakout.py
 ├─ utils/
 │   └─ state.py            # 상태 저장/로드(JSON)
 ├─ RUN.md
 ├─ requirements.txt
 ├─ .env / .env.example
 └─ .gitignore
```

## 5) Docker (선택)
```bash
docker build -t crypto-bot .
docker run --env-file .env --name crypto-bot --restart=always crypto-bot
```

## 6) 제한/주의
- 선물 모드는 **추가 리스크**가 큽니다. 레버리지를 보수적으로 설정하세요.
- 네트워크/거래 거절/레이트리밋 발생 시 자동 리트라이 로직이 포함돼 있으나, 완벽하지 않을 수 있습니다.