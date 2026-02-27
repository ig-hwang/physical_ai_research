"""
Monthly Review 페이지 (Bain 스타일)
Claude 생성 월간 전략 리뷰 뷰어 + 수동 생성 트리거
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Monthly Review | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand
inject_global_css()


def _extract_body(html: str) -> tuple[str, str]:
    """HTML에서 <style> CSS와 body 콘텐츠를 분리."""
    import re
    html = html.strip()
    style_match = re.search(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
    css = style_match.group(1) if style_match else ""
    if html.startswith(("<!DOCTYPE", "<html", "<!doctype")):
        body_open = re.search(r"<body[^>]*>", html, re.IGNORECASE)
        if body_open:
            body = html[body_open.end():]
            body_close = re.search(r"</body>", body, re.IGNORECASE)
            if body_close:
                body = body[:body_close.start()]
        else:
            body = html
    else:
        body = html
    return css, body.strip()


@st.cache_data(ttl=300)
def load_latest_monthly_report() -> dict | None:
    from database.init_db import get_session, get_engine
    from database.models import Base
    try:
        from database.models import MonthlyReport
    except ImportError:
        return None
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        report = (
            session.query(MonthlyReport)
            .order_by(MonthlyReport.month_start.desc())
            .first()
        )
        if not report:
            return None
        return {
            "report_id":        report.report_id,
            "month_key":        report.month_key,
            "month_start":      report.month_start,
            "month_end":        report.month_end,
            "total_signals":    report.total_signals,
            "market_signals":   report.market_signals,
            "tech_signals":     report.tech_signals,
            "case_signals":     report.case_signals,
            "policy_signals":   report.policy_signals,
            "full_report_html": report.full_report_html,
            "generated_at":     report.generated_at,
            "model_used":       report.model_used,
        }


@st.cache_data(ttl=300)
def load_signals_for_report(days_back: int = 31) -> list[dict]:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        df = get_signals_df(session, days_back=days_back)
        return [] if df.empty else df.to_dict("records")


def _generate_report() -> str:
    """월간 리포트 즉시 생성 후 DB 저장."""
    import calendar
    from datetime import datetime
    from collections import Counter
    from pipeline.analyzer import StrategicAnalyzer
    from database.init_db import get_session, get_engine
    from database.models import Base, MonthlyReport
    from config import CLAUDE_MODEL

    Base.metadata.create_all(get_engine())

    signals = load_signals_for_report(days_back=31)
    if not signals:
        return "데이터 없음: 먼저 파이프라인을 실행하세요."

    analyzer = StrategicAnalyzer()
    html_report = analyzer.generate_monthly_report(signals)

    now = datetime.utcnow()
    month_key   = f"{now.year}-{now.month:02d}"
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day    = calendar.monthrange(now.year, now.month)[1]
    month_end   = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)
    scope_counts = Counter(s.get("scope", "") for s in signals)

    with get_session() as session:
        existing = session.query(MonthlyReport).filter_by(month_key=month_key).first()
        if existing:
            session.delete(existing)
            session.flush()
        report = MonthlyReport(
            month_key=month_key,
            month_start=month_start,
            month_end=month_end,
            total_signals=len(signals),
            market_signals=scope_counts.get("Market", 0),
            tech_signals=scope_counts.get("Tech", 0),
            case_signals=scope_counts.get("Case", 0),
            policy_signals=scope_counts.get("Policy", 0),
            full_report_html=html_report,
            model_used=CLAUDE_MODEL,
            generated_at=now,
        )
        session.add(report)
    return "생성 완료"


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("📋", "Monthly Review")

    if st.button("월간 리포트 재생성", use_container_width=True, type="primary"):
        with st.spinner("Claude 분석 중... (60~120초)"):
            try:
                msg = _generate_report()
                st.success(msg)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    st.divider()
    st.caption(
        "매월 1일 자동 생성 예정\n"
        "수동 재생성도 가능합니다.\n\n"
        "**리포트 구성 (Bain 스타일)**\n"
        "- Executive Summary\n"
        "- Key Agendas 분석\n"
        "- Competitive Intelligence\n"
        "- Technology Radar\n"
        "- Capital Flow 분석\n"
        "- LGU+ Strategic Positioning"
    )


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="월간 전략 리뷰 · BAIN STYLE · CLAUDE AI ANALYSIS",
    title="Monthly Review",
    description="한 달간 수집된 전 스코프 신호를 Bain & Company SCR 방법론으로 분석합니다. "
                "시장 아젠다·경쟁 동향·기술 성숙도·자본 흐름·전략 포지셔닝을 통합하여 월간 전략 리뷰를 제공합니다.",
    tags=["Bain Style", "SCR 방법론", "월간 분석", "Claude AI", "전략 포지셔닝"],
)

report = load_latest_monthly_report()

if not report:
    st.info("""
    **월간 리포트가 아직 없습니다.**

    사이드바의 **'월간 리포트 재생성'** 버튼을 클릭하여 생성하세요.
    """)
    st.stop()

# ── 메타 KPI ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("리포트 월", report.get("month_key", "N/A"))
c2.metric("전체 신호", f"{report.get('total_signals', 0)}건")
c3.metric("Market", f"{report.get('market_signals', 0)}건")
c4.metric("Tech", f"{report.get('tech_signals', 0)}건")
c5.metric("Case + Policy",
          f"{report.get('case_signals', 0) + report.get('policy_signals', 0)}건")

gen_at  = report.get("generated_at")
gen_str = gen_at.strftime("%Y-%m-%d %H:%M") if hasattr(gen_at, "strftime") else str(gen_at)
st.caption(f"생성: {gen_str}  ·  모델: {report.get('model_used', 'N/A')}")

st.divider()

# ── 리포트 본문 ───────────────────────────────────────────────────────────────
section_title("월간 전략 리뷰 본문")
html_content = report.get("full_report_html", "")

if html_content and len(html_content) > 100:
    css, body = _extract_body(html_content)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(f'<div class="pasis-monthly-body">{body}</div>', unsafe_allow_html=True)
else:
    st.warning("리포트 내용이 없습니다. 사이드바에서 재생성해 주세요.")
    signals = load_signals_for_report(days_back=31)
    if signals:
        from web.components.cards import signal_card
        section_title("수집 신호 목록 (리포트 대체)")
        for s in signals[:15]:
            signal_card(s)

st.divider()

# ── 다운로드 ──────────────────────────────────────────────────────────────────
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    if html_content:
        month_key = report.get("month_key", datetime.now().strftime("%Y-%m"))
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LGU+ Physical AI Monthly Review {month_key}</title>
  <style>
    body {{
      font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
      font-size: 15px; line-height: 1.75; color: #0B1F3A;
      max-width: 980px; margin: 0 auto; padding: 2.5rem 2rem;
      background: #F5F7FA;
    }}
    h1 {{ font-size: 1.7rem; font-weight: 800; border-bottom: 3px solid #0B1F3A; padding-bottom: 10px; }}
    h2 {{
      font-size: 1.15rem; font-weight: 800; color: #0B1F3A;
      border-left: 4px solid #0B1F3A; padding: 4px 0 4px 12px;
      background: linear-gradient(to right, #EEF2F8, transparent);
      margin: 2rem 0 0.8rem 0;
    }}
    a {{ color: #0B1F3A; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
    .report-header {{
      background: linear-gradient(135deg, #0B1F3A 0%, #1A3560 100%);
      color: white; padding: 1.5rem 2rem;
      border-radius: 8px; margin-bottom: 1.5rem;
    }}
    .report-header h1 {{ color: white; border-bottom: none; padding-bottom: 0; margin: 0 0 4px 0; }}
    .report-header p {{ margin: 0; opacity: 0.70; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="report-header">
    <h1>LGU+ Physical AI Monthly Review</h1>
    <p>{month_key} · 생성: {gen_str} · PASIS v2.0</p>
  </div>
  {html_content}
</body>
</html>"""
        st.download_button(
            "HTML 리포트 다운로드",
            full_html.encode("utf-8"),
            f"pasis_monthly_{month_key}.html",
            "text/html",
            use_container_width=True,
        )
with col_dl2:
    signals = load_signals_for_report(days_back=31)
    if signals:
        import json
        st.download_button(
            "원본 신호 데이터 (JSON)",
            json.dumps(signals, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            f"pasis_signals_{datetime.now().strftime('%Y%m')}.json",
            "application/json",
            use_container_width=True,
        )