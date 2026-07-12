#!/bin/bash

# [①사유]: 시스템 자동 부팅 및 환경 무결성 확보.
# [②방어 기제 #102, #212]: 부팅 전 통합 테스트(pytest) 강제 수행.

# 1. 환경 설정 (경로 및 가상환경)
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PYTHON_CMD="python3"

# 2. 필수 디렉토리 존재 확인
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
fi

# 3. [방어 기제 #102] 부팅 전 무결성 검증 (통합 테스트)
echo "--- System Integrity Check: Running Integration Tests ---"
$PYTHON_CMD -m pytest "$PROJECT_ROOT/tests/integration_tests.py"
if [ $? -ne 0 ]; then
    echo "CRITICAL: Integration tests failed. Bot will not start."
    exit 1
fi
echo "--- Integration Tests Passed: Booting Strategy Bot ---"

# 4. 부팅 (백그라운드 실행 및 로그 분리)
# 비정상 종료 시 재시작을 위한 루프 적용 (선택 사항)
echo "--- Bot started at $(date) ---"
nohup $PYTHON_CMD -u "$PROJECT_ROOT/main.py" > "$LOG_DIR/system_$(date +%Y%m%d).log" 2>&1 &

echo "Bot is running in background. Logs are directed to $LOG_DIR"

