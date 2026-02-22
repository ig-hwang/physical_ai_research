"""
PASIS 파이프라인 엔트리포인트
사용법:
  python run_pipeline.py          # 1회 실행 (--once 기본)
  python run_pipeline.py --once   # 즉시 1회 실행
  python run_pipeline.py --daemon # 스케줄러 데몬 시작
  python run_pipeline.py --init   # DB 초기화만 (데모 데이터 시딩)
"""
import argparse
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pasis_pipeline.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("run_pipeline")


def run_once() -> dict:
    """
    데이터 수집 → 분석 → DB 저장 → 주간 리포트 생성 1회 실행.
    Returns: 수행 결과 summary dict
    """
    log.info("=== PASIS 파이프라인 1회 실행 시작 ===")

    from pipeline.scout import PhysicalAIScout
    from pipeline.analyzer import StrategicAnalyzer
    from pipeline.archivist import DataArchivist
    from pipeline.scheduler import _generate_and_save_weekly_report

    result = {"inserted": 0, "updated": 0, "errors": [], "total_collected": 0}

    # Step 1: 수집
    try:
        scout = PhysicalAIScout()
        raw_records = scout.run_all(days_back=14, save_raw=True)
        result["total_collected"] = len(raw_records)
        log.info(f"Step 1 완료: {len(raw_records)}건 수집")
    except Exception as e:
        log.error(f"Step 1 수집 오류: {e}")
        result["errors"].append(f"수집: {e}")
        return result

    if not raw_records:
        log.warning("수집 결과 없음. 파이프라인 중단.")
        return result

    # Step 2: 분석
    try:
        analyzer = StrategicAnalyzer()
        analyzed_records = analyzer.analyze_batch(raw_records, save_processed=True)
        log.info(f"Step 2 완료: {len(analyzed_records)}건 분석")
    except Exception as e:
        log.error(f"Step 2 분석 오류: {e}")
        analyzed_records = raw_records  # 분석 실패 시 원본 사용
        result["errors"].append(f"분석: {e}")

    # Step 3: DB 저장
    try:
        archivist = DataArchivist()
        ingest_result = archivist.run_pipeline(analyzed_records)
        result["inserted"] = ingest_result.get("rows_inserted", 0)
        result["updated"] = ingest_result.get("rows_updated", 0)
        result["errors"].extend(ingest_result.get("errors", []))
        log.info(f"Step 3 완료: 신규={result['inserted']}, 갱신={result['updated']}")
    except Exception as e:
        log.error(f"Step 3 저장 오류: {e}")
        result["errors"].append(f"저장: {e}")

    # Step 4: 주간 리포트
    try:
        _generate_and_save_weekly_report(analyzer, analyzed_records)
        log.info("Step 4 완료: 주간 리포트 생성")
    except Exception as e:
        log.error(f"Step 4 리포트 오류: {e}")
        result["errors"].append(f"리포트: {e}")

    log.info(f"=== PASIS 파이프라인 완료: {result} ===")
    return result


def init_db_only() -> None:
    """DB 초기화 + 데모 데이터 시딩만 실행."""
    from database.init_db import init_db
    init_db(seed_demo_data=True)
    log.info("DB 초기화 및 데모 데이터 시딩 완료.")


def main() -> None:
    parser = argparse.ArgumentParser(description="PASIS 파이프라인 실행기")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true", default=True,
                       help="1회 즉시 실행 (기본값)")
    group.add_argument("--daemon", action="store_true",
                       help="스케줄러 데몬 모드 (주간 자동 실행)")
    group.add_argument("--init", action="store_true",
                       help="DB 초기화만 실행")
    args = parser.parse_args()

    # DB 항상 초기화 (테이블 없으면 생성)
    from database.init_db import init_db
    init_db(seed_demo_data=False)

    if args.init:
        from database.init_db import init_db as full_init
        full_init(seed_demo_data=True)
    elif args.daemon:
        from pipeline.scheduler import start_scheduler
        start_scheduler()
    else:
        result = run_once()
        log.info(f"실행 결과: {result}")


if __name__ == "__main__":
    main()