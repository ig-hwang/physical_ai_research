"""
Weekly Brief 페이지
Claude 생성 주간 전략 브리핑 뷰어 + 수동 생성 트리거
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Weekly Brief | PASIS", layout="wide")

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
def load_latest_report() -> dict | None:
    from database.init_db import get_session
    from database.queries import get_latest_weekly_report
    with get_session() as session:
        report = get_latest_weekly_report(session)
        if not report:
            return None
        return {
            "report_id":        report.report_id,
            "iso_week":         report.iso_week,
            "week_start":       report.week_start,
            "week_end":         report.week_end,
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
def load_signals_for_report(days_back: int = 90) -> list[dict]:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        df = get_signals_df(session, days_back=days_back)
        return [] if df.empty else df.to_dict("records")


def _generate_report() -> str:
    from pipeline.analyzer import StrategicAnalyzer
    from pipeline.scheduler import _generate_and_save_weekly_report
    signals = load_signals_for_report(days_back=90)
    if not signals:
        return "데이터 없음: 먼저 파이프라인을 실행하세요."
    analyzer = StrategicAnalyzer()
    _generate_and_save_weekly_report(analyzer, signals, force=True)
    return "생성 완료"


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("📰", "Weekly Brief")

    if st.button("주간 리포트 재생성", use_container_width=True, type="primary"):
        with st.spinner("Claude 분석 중... (30~90초)"):
            try:
                msg = _generate_report()
                st.success(msg)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"오류: {e}")

    st.divider()
    st.caption(
        "매주 월요일 09:00 KST 자동 생성\n"
        "수동 재생성도 가능합니다.\n\n"
        "**리포트 구성**\n"
        "- 이번 주 핵심 메시지\n"
        "- 기업별 주요 동향\n"
        "- 포착된 기술 트렌드\n"
        "- 시장 & 투자 흐름\n"
        "- LGU+ 전략 액션 아이템"
    )


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="주간 전략 브리핑 · CLAUDE AI ANALYSIS",
    title="Weekly Brief",
    description="수집된 전 스코프 신호를 Claude AI가 분석하여 LGU+ 전략팀 관점의 주간 브리핑을 생성합니다. "
                "핵심 메시지·기업 동향·기술 트렌드·전략 액션 아이템을 SCR 방법론 기반으로 정리합니다.",
    tags=["자동 생성", "Claude AI", "SCR 방법론", "LGU+ 전략", "매주 월요일"],
)

report = load_latest_report()

if not report:
    st.info("""
    **주간 리포트가 아직 없습니다.**

    사이드바의 **'주간 리포트 재생성'** 버튼을 클릭하거나,
    Airflow DAG `pasis_weekly_pipeline`을 실행하세요.
    """)
    st.stop()

# ── 메타 KPI ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("리포트 주차", report.get("iso_week", "N/A"))
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
section_title("브리핑 본문")
html_content = report.get("full_report_html", "")

if html_content and len(html_content) > 100:
    css, body = _extract_body(html_content)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(f'<div class="pasis-report-body">{body}</div>', unsafe_allow_html=True)
else:
    st.warning("리포트 내용이 없습니다. 사이드바에서 재생성해 주세요.")
    signals = load_signals_for_report(days_back=90)
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
        iso = report.get("iso_week", datetime.now().strftime("%Y-W%W"))
        full_html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LGU+ Physical AI Weekly Brief {iso}</title>
  <style>
    body {{
      font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
      font-size: 15px; line-height: 1.75; color: #0B1F3A;
      max-width: 960px; margin: 0 auto; padding: 2.5rem 2rem;
      background: #F5F7FA;
    }}
    h1 {{ font-size: 1.7rem; font-weight: 800; border-bottom: 3px solid #E4002B; padding-bottom: 10px; }}
    h2 {{
      font-size: 1.15rem; font-weight: 800; color: #0B1F3A;
      border-left: 4px solid #E4002B; padding: 4px 0 4px 12px;
      background: linear-gradient(to right, #FFF0F3, transparent);
      margin: 2rem 0 0.8rem 0;
    }}
    a {{ color: #E4002B; text-decoration: none; font-weight: 600; }}
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
    <h1>LGU+ Physical AI Weekly Brief</h1>
    <p>{iso} · 생성: {gen_str} · PASIS v2.0</p>
  </div>
  {html_content}
</body>
</html>"""
        st.download_button(
            "HTML 리포트 다운로드",
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
            "원본 신호 데이터 (JSON)",
            json.dumps(signals, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            f"pasis_signals_{datetime.now().strftime('%Y%m%d')}.json",
            "application/json",
            use_container_width=True,
        )
