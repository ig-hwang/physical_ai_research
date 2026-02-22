"""
주간 전략 브리핑 리포트 페이지
Claude 생성 HTML 리포트 뷰어 + 수동 생성 트리거
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
import streamlit as st

st.set_page_config(page_title="주간 리포트 | PASIS", layout="wide")

st.markdown("""
<style>
  .report-title {
    font-size: 1.6rem; font-weight: 800; color: #1A1A2E;
    border-left: 5px solid #E4002B; padding-left: 14px;
    margin-bottom: 0.4rem;
  }
  .section-h2 {
    font-size: 1.15rem; font-weight: 800; color: #1A1A2E;
    border-bottom: 2px solid #E4002B; padding-bottom: 5px;
    margin: 1.4rem 0 0.7rem 0;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_latest_report() -> dict | None:
    from database.init_db import get_session
    from database.queries import get_latest_weekly_report
    with get_session() as session:
        report = get_latest_weekly_report(session)
        if not report:
            return None
        return {
            "report_id":      report.report_id,
            "iso_week":       report.iso_week,
            "week_start":     report.week_start,
            "week_end":       report.week_end,
            "total_signals":  report.total_signals,
            "market_signals": report.market_signals,
            "tech_signals":   report.tech_signals,
            "case_signals":   report.case_signals,
            "policy_signals": report.policy_signals,
            "full_report_html": report.full_report_html,
            "generated_at":   report.generated_at,
            "model_used":     report.model_used,
        }


@st.cache_data(ttl=300)
def load_signals_for_report(days_back: int = 90) -> list[dict]:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        df = get_signals_df(session, days_back=days_back)
        if df.empty:
            return []
        return df.to_dict("records")


def _generate_report() -> str:
    """즉시 주간 리포트 생성 후 DB 저장."""
    from pipeline.analyzer import StrategicAnalyzer
    from pipeline.scheduler import _generate_and_save_weekly_report

    signals = load_signals_for_report(days_back=90)
    if not signals:
        return "데이터 없음: 먼저 파이프라인을 실행하세요."

    analyzer = StrategicAnalyzer()
    _generate_and_save_weekly_report(analyzer, signals)
    return "생성 완료"


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 리포트 관리")

    if st.button("주간 리포트 재생성", use_container_width=True, type="primary"):
        with st.spinner("Claude가 분석 중... (30~90초)"):
            try:
                msg = _generate_report()
                st.success(msg)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    st.divider()
    st.caption("매주 월요일 09:00 KST 자동 생성\n수동 재생성도 가능합니다.")


# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown('<p class="report-title">주간 Physical AI 전략 브리핑</p>', unsafe_allow_html=True)

report = load_latest_report()

if not report:
    st.info("""
    **주간 리포트가 아직 없습니다.**

    사이드바의 **'주간 리포트 재생성'** 버튼을 클릭하거나,
    Airflow DAG `pasis_weekly_pipeline` 을 실행하세요.
    """)
    st.stop()

# ── 메타 KPI ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("리포트 주차", report.get("iso_week", "N/A"))
c2.metric("전체 신호", f"{report.get('total_signals', 0)}건")
c3.metric("Market", f"{report.get('market_signals', 0)}건")
c4.metric("Tech", f"{report.get('tech_signals', 0)}건")
c5.metric("Case + Policy",
          f"{report.get('case_signals', 0) + report.get('policy_signals', 0)}건")

gen_at = report.get("generated_at")
gen_str = gen_at.strftime("%Y-%m-%d %H:%M") if hasattr(gen_at, "strftime") else str(gen_at)
st.caption(f"생성: {gen_str}  ·  모델: {report.get('model_used', 'N/A')}")

st.divider()

# ── 리포트 본문 ───────────────────────────────────────────────────────────────
html_content = report.get("full_report_html", "")

if html_content and len(html_content) > 100:
    # components.html 대신 st.markdown으로 렌더링 (스크롤 제한 없음)
    st.markdown(html_content, unsafe_allow_html=True)
else:
    st.warning("리포트 내용이 없습니다. 사이드바에서 재생성해 주세요.")
    signals = load_signals_for_report(days_back=90)
    if signals:
        from web.components.cards import signal_card
        st.markdown("### 수집 신호 목록 (리포트 대체)")
        for s in signals[:15]:
            signal_card(s)

st.divider()

# ── 다운로드 ──────────────────────────────────────────────────────────────────
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    if html_content:
        iso = report.get("iso_week", datetime.now().strftime("%Y-W%W"))
        # 다운로드용 완전한 HTML 문서
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LGU+ Physical AI 전략 브리핑 {iso}</title>
  <style>
    body {{ font-family: -apple-system, 'Malgun Gothic', sans-serif;
           line-height: 1.7; color: #1A1A2E;
           max-width: 960px; margin: 0 auto; padding: 2rem; }}
    h1, h2, h3 {{ color: #1A1A2E; }}
    h2 {{ border-bottom: 2px solid #E4002B; padding-bottom: 6px; }}
  </style>
</head>
<body>{html_content}</body>
</html>"""
        st.download_button(
            "📄 HTML 리포트 다운로드",
            full_html.encode("utf-8"),
            f"pasis_weekly_{iso}.html",
            "text/html",
            use_container_width=True,
        )
with col_dl2:
    signals = load_signals_for_report(days_back=90)
    if signals:
        import json
        st.download_button(
            "📊 원본 신호 데이터 (JSON)",
            json.dumps(signals, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            f"pasis_signals_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json",
            use_container_width=True,
        )