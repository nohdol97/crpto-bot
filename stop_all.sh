#!/bin/bash

# Crypto Bot - 모든 서비스 중지 스크립트
# Usage: ./stop_all.sh

echo "🛑 Crypto Bot 서비스 중지 중..."
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
    lsof -i :$1 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
}

# Load PIDs if file exists
if [ -f .pids ]; then
    source .pids
    echo "저장된 PID 파일을 찾았습니다."
fi

echo ""
echo "1️⃣  API 서버 중지 중..."
# Try saved PID first
if [ ! -z "$API_SERVER_PID" ] && ps -p $API_SERVER_PID > /dev/null 2>&1; then
    kill -9 $API_SERVER_PID 2>/dev/null
    echo -e "${GREEN}✅ API 서버 중지됨 (PID: $API_SERVER_PID)${NC}"
else
    # Fallback to port-based killing
    if check_port 5001; then
        kill_port 5001
        echo -e "${GREEN}✅ API 서버 중지됨 (포트 5001)${NC}"
    else
        echo -e "${YELLOW}ℹ️  API 서버가 실행 중이지 않습니다.${NC}"
    fi
fi

# Also kill by process name
pkill -f "python3 api_server.py" 2>/dev/null

echo ""
echo "2️⃣  트레이딩 봇 중지 중..."
# Try saved PID first
if [ ! -z "$TRADING_BOT_PID" ] && ps -p $TRADING_BOT_PID > /dev/null 2>&1; then
    kill -9 $TRADING_BOT_PID 2>/dev/null
    echo -e "${GREEN}✅ 트레이딩 봇 중지됨 (PID: $TRADING_BOT_PID)${NC}"
else
    # Fallback to process name
    if pgrep -f "python3 app.py" > /dev/null; then
        pkill -f "python3 app.py"
        echo -e "${GREEN}✅ 트레이딩 봇 중지됨${NC}"
    else
        echo -e "${YELLOW}ℹ️  트레이딩 봇이 실행 중이지 않습니다.${NC}"
    fi
fi

echo ""
echo "3️⃣  대시보드 중지 중..."
# Try saved PID first
if [ ! -z "$DASHBOARD_PID" ] && ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    kill -9 $DASHBOARD_PID 2>/dev/null
    echo -e "${GREEN}✅ 대시보드 중지됨 (PID: $DASHBOARD_PID)${NC}"
else
    # Fallback to port-based killing
    if check_port 3000; then
        kill_port 3000
        echo -e "${GREEN}✅ 대시보드 중지됨 (포트 3000)${NC}"
    elif check_port 3001; then
        kill_port 3001
        echo -e "${GREEN}✅ 대시보드 중지됨 (포트 3001)${NC}"
    else
        echo -e "${YELLOW}ℹ️  대시보드가 실행 중이지 않습니다.${NC}"
    fi
fi

# Kill any remaining Next.js processes
pkill -f "next dev" 2>/dev/null

echo ""
echo "4️⃣  잔여 프로세스 정리 중..."
# Clean up any remaining Python processes related to our bot
pkill -f "python3.*crypto-bot" 2>/dev/null

# Remove PID file
if [ -f .pids ]; then
    rm .pids
    echo "PID 파일 삭제됨"
fi

echo ""
echo "================================"
echo -e "${GREEN}✅ 모든 서비스가 중지되었습니다.${NC}"
echo ""
echo "서비스를 다시 시작하려면: ./start_all.sh"
echo "================================"