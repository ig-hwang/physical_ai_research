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

  /* ── 리포트 공통 래퍼 ─────────────────────────────────── */
  .pasis-report-body {
    font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    font-size: 0.94rem; line-height: 1.8; color: #1A1A2E;
  }
  .pasis-report-body a { color: #E4002B; font-weight: 600; text-decoration: none; }
  .pasis-report-body a:hover { text-decoration: underline; }
  .pasis-report-body strong { color: #1A1A2E; }
  .pasis-report-body ul { padding-left: 1.2rem; }
  .pasis-report-body li { margin-bottom: 0.35rem; }

  /* ── 섹션 카드 ───────────────────────────────────────── */
  .rpt-section {
    background: #ffffff; border: 1px solid #E8ECF0;
    border-radius: 12px; padding: 22px 26px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  .rpt-section-title {
    font-size: 1.1rem; font-weight: 800; color: #1A1A2E;
    border-left: 4px solid #E4002B; padding: 3px 0 3px 12px;
    background: linear-gradient(to right, #FFF0F0, transparent);
    margin-bottom: 16px;
  }
  .rpt-body { margin-bottom: 10px; }
  .rpt-bullets { padding-left: 1.2rem; margin: 8px 0; }
  .rpt-bullets li {
    padding: 8px 14px; margin-bottom: 8px;
    background: #F8F9FB; border-left: 3px solid #E4002B;
    border-radius: 0 6px 6px 0; list-style: none;
    margin-left: -1.2rem;
  }

  /* ── 기업별 동향 ─────────────────────────────────────── */
  .rpt-company {
    border: 1px solid #E8ECF0; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 14px;
    background: #FAFBFC;
  }
  .rpt-company-name {
    font-size: 1rem; font-weight: 800; color: #1A1A2E;
    margin-bottom: 10px; padding-bottom: 8px;
    border-bottom: 1px solid #EEE;
  }
  .rpt-company-name a { color: #1A1A2E; }
  .rpt-fact, .rpt-why, .rpt-lgu {
    padding: 6px 0 6px 12px; margin-bottom: 4px;
    font-size: 0.88rem; border-left: 2px solid transparent;
  }
  .rpt-fact { border-color: #888; color: #333; }
  .rpt-why  { border-color: #1A1AEA; color: #1A1A2E; }
  .rpt-lgu  { border-color: #E4002B; color: #C00020; font-weight: 600; }

  /* ── 기술 트렌드 ─────────────────────────────────────── */
  .rpt-trend {
    padding: 14px 18px; margin-bottom: 12px;
    border-radius: 8px; background: #F0F0FF;
    border-left: 3px solid #1A1AEA;
  }
  .rpt-trend-title {
    font-weight: 700; color: #1A1A2E; margin-bottom: 6px;
    display: flex; align-items: center; gap: 8px;
  }
  .rpt-badge {
    font-size: 0.68rem; font-weight: 700; padding: 1px 8px;
    border-radius: 10px; white-space: nowrap;
    background: #1A1AEA; color: white;
  }
  .rpt-badge.early   { background: #F5A623; color: white; }
  .rpt-badge.emerging{ background: #1A1AEA; color: white; }
  .rpt-badge.mainstream { background: #00A651; color: white; }

  /* ── LGU+ 액션 아이템 ────────────────────────────────── */
  .rpt-action {
    padding: 10px 16px; margin-bottom: 8px;
    border-radius: 8px; font-size: 0.88rem;
  }
  .rpt-action--now   { background: #FFF0F0; border-left: 3px solid #E4002B; }
  .rpt-action--short { background: #FFF8E1; border-left: 3px solid #F5A623; }
  .rpt-action--mid   { background: #F0FFF5; border-left: 3px solid #00A651; }
</style>
""", unsafe_allow_html=True)


def _extract_body(html: str) -> tuple[str, str]:
    """
    HTML에서 <style> CSS와 body 콘텐츠를 분리.
    - Full HTML 문서(<!DOCTYPE ...>): <style>과 <body> 내용 추출
    - HTML 조각(fragment): 그대로 body로 사용
    - </body> 없이 잘린 경우도 처리
    """
    import re
    html = html.strip()

    # <style> 블록 추출 (있는 경우)
    style_match = re.search(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
    css = style_match.group(1) if style_match else ""

    # Full HTML 문서인 경우 <body> 이후 내용 추출 (</body> 없어도 동작)
    if html.startswith(("<!DOCTYPE", "<html", "<!doctype")):
        body_open = re.search(r"<body[^>]*>", html, re.IGNORECASE)
        if body_open:
            body = html[body_open.end():]
            # </body> 있으면 그 앞까지만
            body_close = re.search(r"</body>", body, re.IGNORECASE)
            if body_close:
                body = body[:body_close.start()]
        else:
            body = html
    else:
        # 이미 fragment
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
    st.caption(
        "매주 월요일 09:00 KST 자동 생성\n"
        "수동 재생성도 가능합니다.\n\n"
        "📌 **리포트 포함 내용**\n"
        "- 이번 주 핵심 메시지\n"
        "- 기업별 주요 동향\n"
        "- 포착된 기술 트렌드\n"
        "- 시장 & 투자 흐름\n"
        "- LGU+ 전략 액션 아이템"
    )


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
    css, body = _extract_body(html_content)
    # Claude 자체 CSS가 있으면 함께 주입 (없어도 pasis-report-body CSS가 커버)
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(
        f'<div class="pasis-report-body">{body}</div>',
        unsafe_allow_html=True,
    )
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
    body {{
      font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
      font-size: 15px; line-height: 1.75; color: #1A1A2E;
      max-width: 960px; margin: 0 auto; padding: 2.5rem 2rem;
      background: #FAFBFC;
    }}
    h1 {{ font-size: 1.7rem; font-weight: 800; border-bottom: 3px solid #E4002B; padding-bottom: 10px; }}
    h2 {{
      font-size: 1.15rem; font-weight: 800; color: #1A1A2E;
      border-left: 4px solid #E4002B; padding: 4px 0 4px 12px;
      background: linear-gradient(to right, #FFF0F0, transparent);
      margin: 2rem 0 0.8rem 0;
    }}
    h3 {{ font-size: 1rem; font-weight: 700; color: #333; margin: 1.2rem 0 0.4rem 0; }}
    a {{ color: #E4002B; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
    ul {{ padding-left: 1.3rem; }}
    li {{ margin-bottom: 0.4rem; }}
    table {{ width: 100%; border-collapse: collapse; margin: 0.8rem 0; }}
    th {{ background: #1A1A2E; color: white; padding: 8px 12px; font-size: 0.85rem; }}
    td {{ padding: 8px 12px; border-bottom: 1px solid #EEE; font-size: 0.88rem; }}
    tr:nth-child(even) td {{ background: #F9F9F9; }}
    .report-header {{
      background: #1A1A2E; color: white; padding: 1.5rem 2rem;
      border-radius: 8px; margin-bottom: 1.5rem;
    }}
    .report-header h1 {{ color: white; border-bottom: none; padding-bottom: 0; margin: 0 0 4px 0; }}
    .report-header p {{ margin: 0; opacity: 0.75; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="report-header">
    <h1>LGU+ Physical AI 전략 브리핑</h1>
    <p>{iso} · 생성: {gen_str} · PASIS v1.0</p>
  </div>
  {html_content}
</body>
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