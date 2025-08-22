# Phase 2 & Phase 3 완성 가이드

## ✅ 완료된 작업

### Phase 2: 안정화
1. **로깅 시스템 개선** (`utils/logger.py`)
   - 구조화된 JSON 로깅
   - Supabase 연동
   - 민감 정보 마스킹
   - 로그 파일 로테이션

2. **에러 처리 강화**
   - 전역 예외 처리
   - 자동 재시도 로직
   - Supabase 알림 시스템

3. **테스트 시스템**
   - pytest 기반 단위 테스트
   - 지표 테스트 (`tests/test_indicators.py`)
   - 전략 테스트 (`tests/test_strategies.py`)

### Phase 3: 고도화
1. **Supabase 통합**
   - 데이터베이스 스키마 생성 (`supabase/migrations/001_initial_schema.sql`)
   - Python 클라이언트 (`core/supabase_client.py`)
   - 실시간 구독 지원

2. **WebSocket 실시간 데이터** (`core/websocket_manager.py`)
   - Binance WebSocket 연동
   - 실시간 가격 스트리밍
   - 자동 재연결 처리

3. **백테스팅 엔진** (`backtesting/engine.py`)
   - 과거 데이터 백테스팅
   - 성과 분석
   - Supabase 결과 저장

4. **포트폴리오 매니저** (`core/portfolio_manager.py`)
   - 다중 전략 관리
   - 자금 배분
   - 리밸런싱

5. **Next.js 대시보드** (부분 완성)
   - 프로젝트 초기화 완료
   - Supabase 연동 설정
   - Vercel 배포 설정

## 🚀 시작하기

### 1. Supabase 테이블 생성
```bash
# Supabase 대시보드에서 SQL Editor 열기
# supabase/migrations/001_initial_schema.sql 내용 복사하여 실행
```

### 2. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 테스트 실행
```bash
pytest tests/
```

### 4. 대시보드 실행
```bash
cd dashboard
npm install
npm run dev
```

## 📝 남은 작업 (대시보드 완성)

### 1. 메인 대시보드 페이지 (`dashboard/app/page.tsx`)
```tsx
// 다음 컴포넌트들을 구현해야 합니다:
- PerformanceChart: 수익률 차트
- PositionTable: 실시간 포지션 테이블
- StrategyCards: 전략별 성과 카드
- AlertList: 최근 알림 목록
```

### 2. 거래 내역 페이지 (`dashboard/app/trades/page.tsx`)
```tsx
// 거래 내역 테이블과 필터링
```

### 3. 백테스팅 페이지 (`dashboard/app/backtest/page.tsx`)
```tsx
// 백테스팅 설정 및 결과 표시
```

### 4. 설정 페이지 (`dashboard/app/settings/page.tsx`)
```tsx
// 전략 설정 및 파라미터 조정
```

## 🔧 주요 기능 사용법

### 로깅 시스템
```python
from utils.logger import logger

# 다양한 로그 레벨
logger.info("정보 메시지", module="trader")
logger.error("에러 발생", module="scanner", exc_info=True)
logger.log_trade("EXECUTED", "BTCUSDT", "BUY", 45000, 0.01)
```

### Supabase 연동
```python
from core.supabase_client import supabase_manager

# 포지션 생성
position_id = await supabase_manager.create_position({
    "symbol": "BTCUSDT",
    "side": "BUY",
    "entry_price": 45000,
    "entry_quantity": 0.01
})

# 성과 조회
performance = await supabase_manager.get_performance_history(days=30)
```

### WebSocket 실시간 데이터
```python
from core.websocket_manager import BinanceWebSocketManager

ws_manager = BinanceWebSocketManager(testnet=True)

# 실시간 가격 구독
await ws_manager.subscribe_ticker("BTCUSDT", on_price_update)
await ws_manager.subscribe_kline("BTCUSDT", "15m", on_candle_close)
```

### 백테스팅
```python
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.sma_crossover import sma_crossover_signal

config = BacktestConfig(
    initial_capital=10000,
    commission_rate=0.001,
    stop_loss_pct=0.02
)

engine = BacktestEngine(config)
results = engine.run(
    data=historical_data,
    strategy_func=sma_crossover_signal,
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

### 포트폴리오 관리
```python
from core.portfolio_manager import PortfolioManager

portfolio = PortfolioManager(total_capital=10000, binance_client=spot)
await portfolio.initialize()
await portfolio.start_monitoring(["BTCUSDT", "ETHUSDT"], "15m")
```

## 🚀 Vercel 배포

1. Vercel 계정 생성 (https://vercel.com)

2. 프로젝트 연결
```bash
cd dashboard
npx vercel
```

3. 환경 변수 설정 (Vercel 대시보드에서)
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

4. 배포
```bash
vercel --prod
```

## 📊 모니터링

### Supabase 대시보드
- 테이블 데이터 확인
- 실시간 로그 모니터링
- 성과 분석

### 로컬 로그 파일
```bash
# 시스템 로그
tail -f logs/system.log

# 거래 로그
tail -f logs/trades.log

# 에러 로그
tail -f logs/errors.log
```

## 🔐 보안 주의사항

1. **API 키 관리**
   - `.env` 파일은 절대 커밋하지 마세요
   - 프로덕션에서는 환경 변수 사용

2. **Supabase RLS**
   - Row Level Security 정책 검토
   - 프로덕션 전 권한 설정 강화

3. **Rate Limiting**
   - Binance API 한도 준수
   - WebSocket 연결 수 제한

## 🐛 트러블슈팅

### Supabase 연결 실패
```python
# 연결 상태 확인
health = await supabase_manager.health_check()
```

### WebSocket 재연결
```python
# 자동 재연결 설정됨 (max_reconnect_attempts=10)
# 수동 재연결
await ws_manager.close_all()
await ws_manager.subscribe_ticker("BTCUSDT", callback)
```

### 테스트 실패
```bash
# 상세 로그와 함께 테스트
pytest -v --log-cli-level=DEBUG
```

## 📚 추가 개발 제안

1. **머신러닝 전략**
   - TensorFlow/PyTorch 통합
   - 가격 예측 모델
   - 강화학습 에이전트

2. **고급 리스크 관리**
   - Value at Risk (VaR)
   - 몬테카를로 시뮬레이션
   - 포트폴리오 최적화

3. **소셜 트레이딩**
   - 전략 공유 플랫폼
   - 성과 리더보드
   - 복사 거래

4. **모바일 앱**
   - React Native 앱
   - 푸시 알림
   - 원격 제어

## 💡 팁

- 테스트넷에서 충분히 테스트 후 실전 적용
- 작은 금액으로 시작하여 점진적으로 증가
- 모든 거래 로그 보관 (세금 신고용)
- 정기적인 백업 및 모니터링

## 📞 지원

문제가 있으시면 다음을 확인하세요:
- Supabase 로그 테이블
- 로컬 로그 파일
- pytest 테스트 결과

---

**Phase 2 & 3 구현 완료!** 🎉

이제 안정적인 자동매매 시스템과 웹 대시보드를 갖춘 완전한 암호화폐 트레이딩 봇을 사용할 수 있습니다.