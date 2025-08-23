#!/bin/bash

# Crypto Bot - 모든 서비스 시작 스크립트
# Usage: ./start_all.sh

echo "🚀 Crypto Bot 서비스 시작 중..."
echo "================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
    return $?
}

# Function to kill process on port
kill_port() {
    echo "포트 $1에서 실행 중인 프로세스 종료 중..."
    lsof -i :$1 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
    sleep 1
}

# Check Python and Node
echo "1️⃣  환경 확인 중..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 및 Node.js 확인 완료${NC}"

# Check and load .env
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env 파일이 없습니다. .env.example을 복사하여 설정하세요.${NC}"
    exit 1
fi

# Load environment variables
source .env

# Display current mode
echo ""
echo "2️⃣  현재 설정:"
if [ "$BINANCE_TESTNET" = "true" ]; then
    echo -e "   네트워크: ${YELLOW}TESTNET${NC} (테스트넷)"
else
    echo -e "   네트워크: ${GREEN}MAINNET${NC} (메인넷) ⚠️  실제 자금 사용"
fi

if [ "$ENABLE_FUTURES" = "true" ]; then
    echo -e "   Futures: ${GREEN}활성화${NC}"
else
    echo -e "   Futures: ${YELLOW}비활성화${NC}"
fi

echo ""
echo "3️⃣  서비스 시작 중..."

# Kill existing processes
if check_port 5001; then
    echo "   기존 API 서버 종료 중..."
    kill_port 5001
fi

if check_port 3000; then
    echo "   기존 대시보드 종료 중..."
    kill_port 3000
fi

if check_port 3001; then
    echo "   기존 대시보드 (대체 포트) 종료 중..."
    kill_port 3001
fi

# Kill existing Python bots
echo "   기존 봇 프로세스 종료 중..."
pkill -f "python3 app.py" 2>/dev/null
pkill -f "python3 api_server.py" 2>/dev/null
sleep 2

# Start API Server
echo ""
echo "4️⃣  API 서버 시작 중 (포트 5001)..."
nohup python3 api_server.py > logs/api_server.log 2>&1 &
API_PID=$!
sleep 3

# Check if API server started
if check_port 5001; then
    echo -e "${GREEN}✅ API 서버 시작 완료 (PID: $API_PID)${NC}"
else
    echo -e "${RED}❌ API 서버 시작 실패${NC}"
    echo "   로그 확인: tail -f logs/api_server.log"
    exit 1
fi

# Start Main Trading Bot
echo ""
echo "5️⃣  메인 트레이딩 봇 시작 중..."
nohup python3 app.py > logs/trading_bot.log 2>&1 &
BOT_PID=$!
sleep 3

# Check if bot started
if ps -p $BOT_PID > /dev/null; then
    echo -e "${GREEN}✅ 트레이딩 봇 시작 완료 (PID: $BOT_PID)${NC}"
else
    echo -e "${RED}❌ 트레이딩 봇 시작 실패${NC}"
    echo "   로그 확인: tail -f logs/trading_bot.log"
    exit 1
fi

# Start Dashboard
echo ""
echo "6️⃣  대시보드 시작 중 (포트 3000/3001)..."
cd dashboard
nohup npm run dev > ../logs/dashboard.log 2>&1 &
DASH_PID=$!
cd ..
sleep 5

# Check which port dashboard is using
if check_port 3000; then
    DASH_PORT=3000
elif check_port 3001; then
    DASH_PORT=3001
else
    echo -e "${YELLOW}⚠️  대시보드가 시작되지 않았을 수 있습니다.${NC}"
    echo "   로그 확인: tail -f logs/dashboard.log"
    DASH_PORT="unknown"
fi

if [ "$DASH_PORT" != "unknown" ]; then
    echo -e "${GREEN}✅ 대시보드 시작 완료 (PID: $DASH_PID, 포트: $DASH_PORT)${NC}"
fi

# Save PIDs to file for stop script
echo "API_SERVER_PID=$API_PID" > .pids
echo "TRADING_BOT_PID=$BOT_PID" >> .pids
echo "DASHBOARD_PID=$DASH_PID" >> .pids

# Summary
echo ""
echo "================================"
echo -e "${GREEN}🎉 모든 서비스가 시작되었습니다!${NC}"
echo ""
echo "📊 서비스 상태:"
echo "   • API 서버: http://localhost:5001"
if [ "$DASH_PORT" != "unknown" ]; then
    echo "   • 대시보드: http://localhost:$DASH_PORT"
fi
echo "   • Telegram 봇: 활성화됨"
echo ""
echo "📱 Telegram 봇 사용법:"
echo "   1. Telegram에서 봇 검색"
echo "   2. /start 명령어 입력"
echo "   3. 메뉴 버튼으로 거래 시작"
echo ""
echo "📝 로그 확인:"
echo "   • API 서버: tail -f logs/api_server.log"
echo "   • 트레이딩 봇: tail -f logs/trading_bot.log"
echo "   • 대시보드: tail -f logs/dashboard.log"
echo ""
echo "🛑 서비스 중지: ./stop_all.sh"
echo "================================"

# Keep script running to monitor
echo ""
echo "서비스 모니터링 중... (Ctrl+C로 종료 - 서비스는 계속 실행됨)"
echo ""

# Trap Ctrl+C
trap 'echo ""; echo "스크립트를 종료합니다. 서비스는 백그라운드에서 계속 실행됩니다."; echo "서비스를 중지하려면 ./stop_all.sh 를 실행하세요."; exit 0' INT

# Monitor services
while true; do
    sleep 30
    
    # Check if services are still running
    if ! ps -p $API_PID > /dev/null; then
        echo -e "${RED}⚠️  API 서버가 중지되었습니다.${NC}"
    fi
    
    if ! ps -p $BOT_PID > /dev/null; then
        echo -e "${RED}⚠️  트레이딩 봇이 중지되었습니다.${NC}"
    fi
    
    if ! ps -p $DASH_PID > /dev/null; then
        echo -e "${YELLOW}⚠️  대시보드가 중지되었습니다.${NC}"
    fi
done