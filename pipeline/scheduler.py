"""
PASIS 주간 파이프라인 스케줄러
매주 월요일 오전 9시 (KST) 자동 실행

실행 방법:
  python pipeline/scheduler.py          # 상시 대기 데몬
  python run_pipeline.py --once         # 1회 즉시 실행
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from config import SCHEDULE_DAY, SCHEDULE_HOUR, SCHEDULE_TIMEZONE

log = logging.getLogger(__name__)


def run_weekly_pipeline() -> None:
    """
    주간 데이터 수집 → 분석 → 저장 → 리포트 생성 전체 파이프라인.
    Airflow 대체용 경량 스케줄러.
    """
    log.info(f"=== PASIS 주간 파이프라인 시작: {datetime.now().isoformat()} ===")

    try:
        from pipeline.scout import PhysicalAIScout
        from pipeline.analyzer import StrategicAnalyzer
        from pipeline.archivist import DataArchivist
        from database.init_db import get_session
        from database.models import WeeklyReport
        from database.queries import get_signals_df

        # Step 1: 데이터 수집
        log.info("[Step 1/4] 데이터 수집 시작")
        scout = PhysicalAIScout()
        raw_records = scout.run_all(days_back=14, save_raw=True)
        log.info(f"[Step 1/4] 수집 완료: {len(raw_records)}건")

        if not raw_records:
            log.warning("수집된 데이터가 없습니다. 파이프라인 중단.")
            return

        # Step 2: 전략 분석
        log.info("[Step 2/4] Claude 전략 분석 시작")
        analyzer = StrategicAnalyzer()
        analyzed_records = analyzer.analyze_batch(raw_records, save_processed=True)
        log.info(f"[Step 2/4] 분석 완료: {len(analyzed_records)}건")

        # Step 3: DB 저장
        log.info("[Step 3/4] DB 저장 시작")
        archivist = DataArchivist()
        ingestion_result = archivist.run_pipeline(analyzed_records)
        log.info(f"[Step 3/4] DB 저장: {ingestion_result}")

        # Step 4: 주간 리포트 생성
        log.info("[Step 4/4] 주간 리포트 생성 시작")
        _generate_and_save_weekly_report(analyzer, analyzed_records)
        log.info("[Step 4/4] 주간 리포트 생성 완료")

    except Exception as e:
        log.error(f"파이프라인 실행 오류: {e}", exc_info=True)
        raise

    log.info(f"=== PASIS 주간 파이프라인 완료: {datetime.now().isoformat()} ===")


def _generate_and_save_weekly_report(analyzer: object, signals: list[dict]) -> None:
    """주간 리포트 HTML 생성 후 DB 저장."""
    from datetime import timedelta
    from database.init_db import get_session
    from database.models import WeeklyReport
    from config import CLAUDE_MODEL
    from collections import Counter

    now = datetime.utcnow()
    # ISO 주 계산
    iso_year, iso_week, _ = now.isocalendar()
    iso_week_str = f"{iso_year}-W{iso_week:02d}"

    # 이번 주 월요일 ~ 일요일
    weekday = now.weekday()
    week_start = now - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    scope_counts = Counter(s.get("scope", "") for s in signals)

    html_report = analyzer.generate_weekly_report(signals)

    # Executive summary 추출 (앞 500자)
    exec_summary = html_report[:500] if html_report else ""

    with get_session() as session:
        # 동일 주 리포트가 있으면 업데이트
        existing = session.query(WeeklyReport).filter_by(iso_week=iso_week_str).first()
        if existing:
            existing.full_report_html = html_report
            existing.total_signals = len(signals)
            existing.market_signals = scope_counts.get("Market", 0)
            existing.tech_signals = scope_counts.get("Tech", 0)
            existing.case_signals = scope_counts.get("Case", 0)
            existing.policy_signals = scope_counts.get("Policy", 0)
            existing.generated_at = now
            log.info(f"주간 리포트 업데이트: {iso_week_str}")
        else:
            report = WeeklyReport(
                week_start=week_start,
                week_end=week_end,
                iso_week=iso_week_str,
                total_signals=len(signals),
                market_signals=scope_counts.get("Market", 0),
                tech_signals=scope_counts.get("Tech", 0),
                case_signals=scope_counts.get("Case", 0),
                policy_signals=scope_counts.get("Policy", 0),
                executive_summary=exec_summary,
                full_report_html=html_report,
                model_used=CLAUDE_MODEL,
                generated_at=now,
            )
            session.add(report)
            log.info(f"주간 리포트 신규 생성: {iso_week_str}")


def _on_job_executed(event: object) -> None:
    log.info(f"[Scheduler] 잡 성공: {getattr(event, 'job_id', '')}")


def _on_job_error(event: object) -> None:
    log.error(f"[Scheduler] 잡 실패: {getattr(event, 'job_id', '')} — {getattr(event, 'exception', '')}")


def start_scheduler() -> None:
    """APScheduler 시작 (블로킹 - 데몬 프로세스 용도)."""
    scheduler = BlockingScheduler(timezone=SCHEDULE_TIMEZONE)

    scheduler.add_listener(_on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    scheduler.add_job(
        run_weekly_pipeline,
        trigger=CronTrigger(
            day_of_week=SCHEDULE_DAY,
            hour=SCHEDULE_HOUR,
            minute=0,
            timezone=SCHEDULE_TIMEZONE,
        ),
        id="weekly_pipeline",
        name="PASIS 주간 Physical AI 파이프라인",
        replace_existing=True,
        misfire_grace_time=3600,  # 1시간 내 지연 허용
    )

    log.info(
        f"스케줄러 시작: 매주 {SCHEDULE_DAY} {SCHEDULE_HOUR}:00 {SCHEDULE_TIMEZONE}"
    )
    log.info("Ctrl+C로 종료")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("스케줄러 종료")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    start_scheduler()