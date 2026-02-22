#!/usr/bin/env bash
# PASIS 시작 스크립트
# 사용법:
#   ./run.sh web      # 웹 대시보드 실행
#   ./run.sh pipeline # 파이프라인 1회 실행
#   ./run.sh daemon   # 스케줄러 데몬 시작
#   ./run.sh init     # DB 초기화 + 데모 데이터

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# .env 로드
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

MODE="${1:-web}"

check_deps() {
  if ! python -c "import streamlit" 2>/dev/null; then
    echo "[ERROR] 패키지 미설치. 설치 중..."
    pip install -r requirements.txt
  fi
}

case "$MODE" in
  web)
    echo "[PASIS] 웹 대시보드 시작 → http://localhost:8501"
    check_deps
    streamlit run web/app.py \
      --server.port 8501 \
      --server.headless true \
      --browser.gatherUsageStats false
    ;;
  pipeline)
    echo "[PASIS] 파이프라인 1회 실행"
    check_deps
    python run_pipeline.py --once
    ;;
  daemon)
    echo "[PASIS] 스케줄러 데몬 시작 (매주 월요일 09:00 KST)"
    check_deps
    python run_pipeline.py --daemon
    ;;
  init)
    echo "[PASIS] DB 초기화 + 데모 데이터 시딩"
    check_deps
    python run_pipeline.py --init
    ;;
  *)
    echo "사용법: ./run.sh [web|pipeline|daemon|init]"
    exit 1
    ;;
esac