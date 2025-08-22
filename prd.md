# 암호화폐 자동매매 봇 PRD (Product Requirements Document)

## 📋 목차
1. [제품 개요](#1-제품-개요)
2. [목표 및 비전](#2-목표-및-비전)
3. [핵심 기능](#3-핵심-기능)
4. [기술 아키텍처](#4-기술-아키텍처)
5. [상세 기능 명세](#5-상세-기능-명세)
6. [매매 전략](#6-매매-전략)
7. [리스크 관리](#7-리스크-관리)
8. [사용자 인터페이스](#8-사용자-인터페이스)
9. [설정 및 환경변수](#9-설정-및-환경변수)
10. [API 명세](#10-api-명세)
11. [보안 고려사항](#11-보안-고려사항)
12. [성능 요구사항](#12-성능-요구사항)
13. [모니터링 및 로깅](#13-모니터링-및-로깅)
14. [배포 및 운영](#14-배포-및-운영)
15. [테스트 전략](#15-테스트-전략)
16. [로드맵](#16-로드맵)

---

## 1. 제품 개요

### 1.1 제품명
**Crypto Trading Bot** - 지능형 암호화폐 자동매매 시스템

### 1.2 제품 설명
바이낸스 거래소 API와 텔레그램 봇을 활용한 자동화된 암호화폐 매매 시스템으로, 다양한 기술적 지표를 기반으로 매매 기회를 포착하고 리스크를 관리합니다.

### 1.3 대상 사용자
- 암호화폐 트레이더 (초급~중급)
- 자동매매 시스템을 구축하고자 하는 개인 투자자
- 24시간 시장 모니터링이 필요한 트레이더

### 1.4 핵심 가치
- **자동화**: 24시간 무중단 시장 모니터링 및 매매
- **리스크 관리**: ATR 기반 손절/익절 자동 설정
- **사용자 친화성**: 텔레그램을 통한 간편한 제어
- **확장성**: 새로운 전략 추가 용이한 모듈형 구조

---

## 2. 목표 및 비전

### 2.1 단기 목표 (1-3개월)
- ✅ 기본 자동매매 시스템 구축
- ✅ 3가지 핵심 전략 구현
- ✅ 텔레그램 봇 인터페이스 구현
- 🔄 테스트넷 검증 완료
- 🔄 실전 베타 테스트

### 2.2 중기 목표 (3-6개월)
- 📅 웹소켓 기반 실시간 데이터 처리
- 📅 백테스팅 엔진 구축
- 📅 포트폴리오 매니저 추가
- 📅 웹 대시보드 개발
- 📅 멀티 거래소 지원

### 2.3 장기 비전 (6-12개월)
- 📅 머신러닝 기반 전략 최적화
- 📅 소셜 트레이딩 기능
- 📅 모바일 앱 개발
- 📅 SaaS 서비스 전환

---

## 3. 핵심 기능

### 3.1 시장 스캐닝 및 분석
- **실시간 시장 모니터링**: 상위 유동성 코인 추적
- **기술적 분석**: EMA, RSI, ADX, 볼린저 밴드 등 다양한 지표 활용
- **스코어링 시스템**: 각 코인의 매매 매력도 점수화
- **자동 추천**: 시장 상황에 맞는 최적 전략 제안

### 3.2 자동매매 실행
- **전략 기반 매매**: 사전 정의된 전략에 따른 자동 주문
- **포지션 관리**: 동시 포지션 제한 및 자금 관리
- **주문 타입**: 시장가, 지정가 주문 지원
- **자동 재시도**: 네트워크 오류 시 자동 재연결 및 재시도

### 3.3 리스크 관리
- **ATR 기반 손익 관리**: 변동성에 따른 동적 손절/익절
- **포지션 사이징**: 계좌 잔고 대비 적정 포지션 크기 계산
- **최대 손실 제한**: 일일/주간 최대 손실 한도 설정
- **긴급 정지**: 비정상 상황 시 자동 거래 중단

### 3.4 사용자 인터페이스
- **텔레그램 봇**: 모바일 친화적 제어 인터페이스
- **실시간 알림**: 매매 신호, 포지션 변동, 손익 알림
- **대화형 명령**: 간편한 설정 변경 및 상태 조회

---

## 4. 기술 아키텍처

### 4.1 시스템 구성도
```
┌─────────────────────────────────────────────────────────┐
│                     사용자 인터페이스                      │
│                    (Telegram Bot)                       │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      메인 애플리케이션                     │
│                        (app.py)                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Scanner  │  │  Trader  │  │Strategies│  │  State   ││
│  │  Module  │  │  Module  │  │  Module  │  │ Manager  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      거래소 연동 계층                      │
│                   (Binance Client)                      │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                      외부 서비스                          │
│         Binance API          Telegram API               │
└─────────────────────────────────────────────────────────┘
```

### 4.2 디렉토리 구조
```
crypto-bot/
├── app.py                      # 메인 애플리케이션
├── config.py                   # 설정 관리
├── requirements.txt            # 패키지 의존성
├── .env                        # 환경 변수 (git 제외)
├── .gitignore                  # Git 제외 파일
│
├── core/                       # 핵심 비즈니스 로직
│   ├── __init__.py
│   ├── scanner.py              # 시장 스캐닝 및 분석
│   ├── trader.py               # 자동매매 실행 엔진
│   └── indicators.py           # 기술적 지표 계산
│
├── strategies/                 # 매매 전략 모듈
│   ├── __init__.py
│   ├── sma_crossover.py        # SMA 크로스오버 전략
│   ├── rsi_reversion.py        # RSI 역추세 전략
│   └── bb_breakout.py          # 볼린저 밴드 돌파 전략
│
├── exchange/                   # 거래소 연동
│   ├── __init__.py
│   └── binance_client.py       # 바이낸스 API 클라이언트
│
├── utils/                      # 유틸리티
│   ├── __init__.py
│   ├── state.py                # 상태 관리
│   └── logger.py               # 로깅 유틸리티
│
├── tests/                      # 테스트 코드
│   ├── test_indicators.py
│   ├── test_strategies.py
│   └── test_trader.py
│
└── docs/                       # 문서
    ├── setup.md                # 설치 가이드
    └── api.md                  # API 문서
```

### 4.3 기술 스택
- **언어**: Python 3.9+
- **프레임워크**: python-telegram-bot, ccxt
- **데이터 분석**: pandas, numpy, ta-lib
- **API 클라이언트**: python-binance
- **상태 관리**: JSON 파일 기반
- **로깅**: Python logging module

---

## 5. 상세 기능 명세

### 5.1 시장 스캐닝 기능

#### 5.1.1 코인 선별 프로세스
1. **유동성 필터링**
   - 24시간 거래대금 상위 50개 코인 선택
   - USDT 마켓만 대상
   - 최소 거래량 임계값 적용

2. **기술적 분석**
   - 15분봉 데이터 수집 (최근 100봉)
   - 다중 지표 계산 및 분석
   - 각 지표별 점수 산정

3. **스코어링 알고리즘**
   ```python
   score = (
       trend_score * 0.3 +      # 추세 강도
       volatility_score * 0.2 +  # 변동성 점수
       momentum_score * 0.25 +   # 모멘텀
       volume_score * 0.25       # 거래량
   )
   ```

4. **추천 생성**
   - Top 5 코인 선정
   - 각 코인별 최적 전략 매칭
   - 리스크 레벨 평가

### 5.2 자동매매 실행

#### 5.2.1 매매 프로세스
```
시작 → 시장 스캔 → 신호 감지 → 포지션 확인 → 주문 실행 → 모니터링 → 청산/익절/손절
```

#### 5.2.2 주문 관리
- **진입 조건**: 전략별 신호 + 리스크 체크
- **청산 조건**: 반대 신호 / 손절 / 익절 도달
- **부분 체결 처리**: 미체결 수량 자동 취소 및 재주문
- **슬리피지 관리**: 최대 허용 슬리피지 설정

### 5.3 포지션 관리

#### 5.3.1 포지션 추적
```json
{
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry_price": 45000,
    "quantity": 0.01,
    "stop_loss": 44100,
    "take_profit": 46350,
    "entry_time": "2024-01-20T10:30:00Z",
    "pnl": 150,
    "status": "OPEN"
}
```

#### 5.3.2 동시 포지션 제한
- 최대 동시 포지션: 설정 가능 (기본값: 1)
- 포지션당 최대 자금: 전체 자금의 10%
- 상관관계 체크: 유사 자산 중복 방지

---

## 6. 매매 전략

### 6.1 SMA Crossover (추세 추종)
```python
전략 로직:
- 매수: SMA(20) > SMA(50) 크로스
- 매도: SMA(20) < SMA(50) 크로스
- 필터: ADX > 20 (추세 강도)
- 적합 시장: 명확한 추세 시장
```

### 6.2 RSI Reversion (역추세)
```python
전략 로직:
- 매수: RSI < 30 (과매도)
- 매도: RSI > 70 (과매수)
- 필터: 볼륨 > 평균 볼륨 * 1.5
- 적합 시장: 횡보/박스권 시장
```

### 6.3 Bollinger Breakout (변동성 돌파)
```python
전략 로직:
- 매수: 가격 > 상단 밴드 & 이전 스퀴즈
- 매도: 가격 < 하단 밴드 & 이전 스퀴즈
- 필터: 볼린저 밴드 폭 > 임계값
- 적합 시장: 변동성 확대 시점
```

### 6.4 전략 선택 알고리즘
```python
def select_strategy(market_condition):
    if trend_strength > 0.7:
        return "sma_crossover"
    elif volatility < 0.3:
        return "bb_breakout"
    elif rsi_extreme:
        return "rsi_reversion"
    else:
        return "default"
```

---

## 7. 리스크 관리

### 7.1 손절/익절 설정

#### 7.1.1 ATR 기반 동적 설정
```python
stop_loss = entry_price - (ATR * STOP_LOSS_ATR_MULTIPLIER)
take_profit = entry_price + (ATR * TAKE_PROFIT_ATR_MULTIPLIER)
```

#### 7.1.2 리스크 파라미터
- **최대 손실률**: 포지션당 2%
- **리스크/리워드 비율**: 최소 1:2
- **트레일링 스탑**: 이익 10% 이상 시 활성화

### 7.2 자금 관리

#### 7.2.1 Kelly Criterion 적용
```python
position_size = account_balance * kelly_fraction * confidence_level
```

#### 7.2.2 포지션 사이징 규칙
- 최소 거래 금액: 10 USDT
- 최대 거래 금액: 계좌의 10%
- 분할 매수: 3단계 분할 진입 옵션

### 7.3 비상 상황 대응

#### 7.3.1 자동 정지 조건
- 일일 손실 5% 초과
- 연속 3회 손절
- API 연결 실패 5분 지속
- 비정상 가격 움직임 감지 (±10% 급변)

#### 7.3.2 복구 프로세스
1. 모든 열린 포지션 청산
2. 자동매매 일시 정지
3. 관리자 알림 발송
4. 시스템 상태 점검 후 수동 재시작

---

## 8. 사용자 인터페이스

### 8.1 텔레그램 봇 명령어

#### 8.1.1 기본 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/start` | 봇 시작 및 메뉴 표시 | `/start` |
| `/help` | 도움말 표시 | `/help` |
| `/status` | 현재 상태 조회 | `/status` |
| `/balance` | 계좌 잔고 조회 | `/balance` |

#### 8.1.2 거래 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/scan` | 시장 스캔 실행 | `/scan` |
| `/trade [on/off]` | 자동매매 시작/중지 | `/trade on` |
| `/positions` | 열린 포지션 조회 | `/positions` |
| `/close [symbol]` | 특정 포지션 청산 | `/close BTCUSDT` |

#### 8.1.3 설정 명령어
| 명령어 | 설명 | 예시 |
|--------|------|------|
| `/set [param] [value]` | 파라미터 설정 | `/set symbol ETHUSDT` |
| `/strategy [name]` | 전략 변경 | `/strategy rsi_reversion` |
| `/risk [level]` | 리스크 레벨 설정 | `/risk conservative` |
| `/config` | 현재 설정 확인 | `/config` |

### 8.2 인라인 키보드

#### 8.2.1 메인 메뉴
```
┌─────────────────────────┐
│ 📊 시장 스캔             │
├─────────────────────────┤
│ ▶️ 자동매매 시작         │
├─────────────────────────┤
│ ⏹️ 자동매매 중지         │
├─────────────────────────┤
│ 📈 포지션 확인           │
├─────────────────────────┤
│ ⚙️ 설정                 │
└─────────────────────────┘
```

#### 8.2.2 설정 메뉴
```
┌─────────────────────────┐
│ 🪙 심볼 변경             │
├─────────────────────────┤
│ 📐 전략 선택             │
├─────────────────────────┤
│ ⚠️ 리스크 관리           │
├─────────────────────────┤
│ 🔙 메인 메뉴             │
└─────────────────────────┘
```

### 8.3 알림 메시지

#### 8.3.1 거래 알림
```
🟢 매수 신호 발생
━━━━━━━━━━━━━
심볼: BTCUSDT
전략: SMA Crossover
가격: $45,230
수량: 0.01 BTC
━━━━━━━━━━━━━
손절: $44,100 (-2.5%)
익절: $46,800 (+3.5%)
```

#### 8.3.2 손익 알림
```
💰 포지션 청산
━━━━━━━━━━━━━
심볼: ETHUSDT
손익: +$125.50 (+5.2%)
보유 시간: 3시간 45분
━━━━━━━━━━━━━
누적 손익: +$450.30
승률: 65% (13/20)
```

---

## 9. 설정 및 환경변수

### 9.1 필수 환경변수

```bash
# API Keys
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Trading Configuration
SYMBOL=BTCUSDT                  # 거래 심볼
TIMEFRAME=15m                    # 봉 주기
TRADE_USDT=50                    # 1회 거래 금액
MAX_OPEN_POSITIONS=1             # 최대 동시 포지션

# Risk Management
STOP_LOSS_ATR=2.0                # 손절 ATR 배수
TAKE_PROFIT_ATR=3.0              # 익절 ATR 배수
MAX_DAILY_LOSS_PERCENT=5         # 일일 최대 손실률

# System Configuration
ENABLE_TESTNET=false             # 테스트넷 사용 여부
ENABLE_FUTURES=false             # 선물 거래 활성화
LOG_LEVEL=INFO                   # 로그 레벨
```

### 9.2 선택적 설정

```bash
# Strategy Parameters
SMA_FAST_PERIOD=20               # 빠른 이평선 기간
SMA_SLOW_PERIOD=50               # 느린 이평선 기간
RSI_PERIOD=14                    # RSI 기간
RSI_OVERSOLD=30                  # RSI 과매도 기준
RSI_OVERBOUGHT=70                # RSI 과매수 기준
BB_PERIOD=20                     # 볼린저 밴드 기간
BB_STD_DEV=2.0                   # 볼린저 밴드 표준편차

# Advanced Settings
ENABLE_TRAILING_STOP=true        # 트레일링 스탑 사용
TRAILING_STOP_PERCENT=2.0        # 트레일링 스탑 비율
ENABLE_PARTIAL_CLOSE=false       # 부분 청산 사용
PARTIAL_CLOSE_PERCENT=50         # 부분 청산 비율
```

### 9.3 리스크 레벨 프리셋

#### Conservative (보수적)
```bash
TRADE_USDT=30
STOP_LOSS_ATR=1.5
TAKE_PROFIT_ATR=2.0
MAX_OPEN_POSITIONS=1
```

#### Moderate (중간)
```bash
TRADE_USDT=50
STOP_LOSS_ATR=2.0
TAKE_PROFIT_ATR=3.0
MAX_OPEN_POSITIONS=2
```

#### Aggressive (공격적)
```bash
TRADE_USDT=100
STOP_LOSS_ATR=2.5
TAKE_PROFIT_ATR=4.0
MAX_OPEN_POSITIONS=3
```

---

## 10. API 명세

### 10.1 내부 API

#### 10.1.1 Scanner API
```python
class Scanner:
    def scan_market() -> List[Dict]:
        """시장 스캔 및 분석"""
        return [
            {
                "symbol": "BTCUSDT",
                "score": 85,
                "indicators": {...},
                "recommended_strategy": "sma_crossover"
            }
        ]
    
    def get_top_coins(limit: int = 5) -> List[str]:
        """상위 코인 목록 반환"""
        
    def analyze_coin(symbol: str) -> Dict:
        """특정 코인 상세 분석"""
```

#### 10.1.2 Trader API
```python
class Trader:
    def start_trading() -> None:
        """자동매매 시작"""
        
    def stop_trading() -> None:
        """자동매매 중지"""
        
    def execute_trade(signal: Dict) -> Dict:
        """거래 실행"""
        return {
            "order_id": "123456",
            "status": "FILLED",
            "executed_price": 45230,
            "executed_qty": 0.01
        }
    
    def close_position(symbol: str) -> Dict:
        """포지션 청산"""
```

### 10.2 외부 API 연동

#### 10.2.1 Binance API 엔드포인트
- **시장 데이터**: `/api/v3/klines`
- **계좌 정보**: `/api/v3/account`
- **주문 실행**: `/api/v3/order`
- **포지션 조회**: `/fapi/v2/positionRisk` (선물)

#### 10.2.2 Telegram Bot API
- **메시지 전송**: `sendMessage`
- **인라인 키보드**: `InlineKeyboardMarkup`
- **콜백 처리**: `CallbackQueryHandler`

---

## 11. 보안 고려사항

### 11.1 API 키 보안
- **.env 파일 암호화**: 프로덕션 환경에서 암호화
- **권한 제한**: 거래 권한만 부여, 출금 권한 제외
- **IP 화이트리스트**: 특정 IP만 API 접근 허용
- **키 로테이션**: 정기적인 API 키 갱신

### 11.2 통신 보안
- **HTTPS 전용**: 모든 API 통신 SSL/TLS 암호화
- **메시지 검증**: HMAC 서명 검증
- **Rate Limiting**: API 호출 제한 준수

### 11.3 봇 보안
- **사용자 인증**: 텔레그램 user_id 화이트리스트
- **명령어 권한**: 관리자/일반 사용자 구분
- **입력 검증**: 모든 사용자 입력 sanitization

### 11.4 시스템 보안
- **로그 마스킹**: 민감 정보 로그 제외
- **에러 처리**: 상세 에러 정보 숨김
- **백업**: 상태 파일 정기 백업

---

## 12. 성능 요구사항

### 12.1 응답 시간
- **API 응답**: < 100ms (p95)
- **시장 스캔**: < 5초
- **주문 실행**: < 500ms
- **봇 명령 처리**: < 2초

### 12.2 처리량
- **동시 처리**: 10개 심볼 동시 모니터링
- **초당 거래**: 5 TPS (Transactions Per Second)
- **메시지 처리**: 100 메시지/분

### 12.3 가용성
- **목표 가동률**: 99.9% (월간)
- **최대 다운타임**: 43분/월
- **자동 복구**: 5분 이내

### 12.4 리소스 사용
- **메모리**: < 512MB
- **CPU**: < 25% (평균)
- **네트워크**: < 100MB/일
- **디스크**: < 1GB (로그 포함)

---

## 13. 모니터링 및 로깅

### 13.1 로깅 전략

#### 13.1.1 로그 레벨
```python
CRITICAL: 시스템 중단 위험
ERROR: 거래 실패, API 오류
WARNING: 비정상 상황, 높은 슬리피지
INFO: 거래 실행, 포지션 변경
DEBUG: 상세 실행 흐름
```

#### 13.1.2 로그 포맷
```
[2024-01-20 10:30:45] [INFO] [trader] Order executed: BTCUSDT BUY 0.01 @ 45230
```

### 13.2 모니터링 지표

#### 13.2.1 시스템 메트릭
- CPU/메모리 사용률
- API 응답 시간
- 에러율
- 네트워크 지연

#### 13.2.2 비즈니스 메트릭
- 총 거래 횟수
- 승률
- 누적 손익
- 평균 보유 시간
- 최대 드로다운

### 13.3 알림 설정

#### 13.3.1 긴급 알림
- 시스템 다운
- API 키 만료
- 대량 손실 발생
- 비정상 거래 패턴

#### 13.3.2 일반 알림
- 일일 거래 요약
- 주간 성과 리포트
- 시스템 상태 점검

---

## 14. 배포 및 운영

### 14.1 배포 환경

#### 14.1.1 개발 환경
```bash
# 로컬 개발
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

#### 14.1.2 테스트 환경
```bash
# Binance Testnet
ENABLE_TESTNET=true
BINANCE_TESTNET_API_KEY=test_key
BINANCE_TESTNET_API_SECRET=test_secret
```

#### 14.1.3 프로덕션 환경
```bash
# Docker 배포
docker build -t crypto-bot .
docker run -d --name crypto-bot \
  --env-file .env.production \
  --restart unless-stopped \
  crypto-bot
```

### 14.2 CI/CD 파이프라인

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    steps:
      - Test
      - Build
      - Deploy to VPS
      - Health Check
```

### 14.3 운영 체크리스트

#### 14.3.1 일일 점검
- [ ] 시스템 상태 확인
- [ ] 에러 로그 검토
- [ ] 거래 성과 확인
- [ ] API 한도 확인

#### 14.3.2 주간 점검
- [ ] 성과 분석 리포트
- [ ] 전략 파라미터 검토
- [ ] 시스템 업데이트 확인
- [ ] 백업 상태 확인

#### 14.3.3 월간 점검
- [ ] 전략 백테스팅
- [ ] 리스크 파라미터 재조정
- [ ] API 키 로테이션
- [ ] 시스템 최적화

---

## 15. 테스트 전략

### 15.1 단위 테스트
```python
# tests/test_indicators.py
def test_rsi_calculation():
    """RSI 계산 정확도 테스트"""
    
def test_sma_crossover():
    """SMA 크로스오버 신호 테스트"""
```

### 15.2 통합 테스트
```python
# tests/test_integration.py
def test_order_execution_flow():
    """주문 실행 전체 플로우 테스트"""
    
def test_risk_management():
    """리스크 관리 시스템 테스트"""
```

### 15.3 백테스팅
```python
# 과거 데이터 기반 전략 검증
backtest_config = {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 10000,
    "commission": 0.001
}
```

### 15.4 페이퍼 트레이딩
- **기간**: 최소 2주
- **환경**: Binance Testnet
- **검증 항목**: 
  - 주문 실행 정확도
  - 슬리피지 측정
  - 에러 처리
  - 성과 측정

---

## 16. 로드맵

### Phase 1: MVP (완료)
- [x] 기본 봇 구조 구현
- [x] 3가지 전략 구현
- [x] 텔레그램 인터페이스
- [x] 리스크 관리 기본 기능

### Phase 2: 안정화 (진행중)
- [ ] 테스트넷 검증 (진행 중)
- [ ] 에러 처리 강화
- [ ] 로깅 시스템 개선
- [ ] 성능 최적화

### Phase 3: 고도화 (2024 Q2)
- [ ] 웹소켓 실시간 데이터
- [ ] 백테스팅 엔진
- [ ] 웹 대시보드
- [ ] 멀티 전략 포트폴리오

### Phase 4: 확장 (2024 Q3)
- [ ] 머신러닝 전략
- [ ] 소셜 트레이딩