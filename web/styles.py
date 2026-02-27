"""
PASIS Design System — BCG / Bain Professional Style
공유 CSS 및 UI 헬퍼 함수
"""

_CSS = """
/* ═══════════════════════════════════════════════════════════
   PASIS Design System  ·  BCG/Bain Professional Style
   Primary: #0B1F3A (Navy)  Accent: #E4002B (Red)
   ═══════════════════════════════════════════════════════════ */

/* ── Global ─────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] > .main {
  background: #F5F7FA;
}
.main .block-container {
  padding-top: 1.6rem;
  padding-bottom: 3rem;
  max-width: 1440px;
}

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #0B1F3A !important; }
section[data-testid="stSidebar"] > div { background: #0B1F3A !important; }
section[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
section[data-testid="stSidebar"] .stSelectbox > label,
section[data-testid="stSidebar"] .stMultiSelect > label,
section[data-testid="stSidebar"] .stSlider > label,
section[data-testid="stSidebar"] .stRadio > label {
  color: rgba(255,255,255,0.50) !important;
  font-size: 0.70rem !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stButton > button {
  background: #E4002B !important;
  color: white !important;
  border: none !important;
  font-weight: 700 !important;
}
section[data-testid="stSidebar"] hr {
  border-color: rgba(255,255,255,0.10) !important;
}

/* ── KPI / Metric Cards ──────────────────────────────────── */
div[data-testid="metric-container"] {
  background: #FFFFFF !important;
  border: 1px solid #E2E8F0 !important;
  border-top: 3px solid #E4002B !important;
  border-radius: 10px !important;
  padding: 18px 22px !important;
  box-shadow: 0 2px 8px rgba(11,31,58,0.05) !important;
}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] label,
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {
  font-size: 0.68rem !important;
  font-weight: 700 !important;
  letter-spacing: 1.3px !important;
  text-transform: uppercase !important;
  color: #6B7C93 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] > div {
  font-size: 1.65rem !important;
  font-weight: 800 !important;
  color: #0B1F3A !important;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: #E4002B !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 700 !important;
  font-size: 0.85rem !important;
  letter-spacing: 0.3px !important;
}
.stButton > button[kind="primary"]:hover {
  background: #C0001F !important;
  box-shadow: 0 4px 14px rgba(228,0,43,0.28) !important;
}
.stButton > button[kind="secondary"] {
  border: 1.5px solid #D1D9E6 !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  color: #0B1F3A !important;
  background: white !important;
}

/* ── Divider ─────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid #E2E8F0 !important; margin: 20px 0 !important; }

/* ── Expander ────────────────────────────────────────────── */
details[data-testid="stExpander"] {
  border: 1px solid #E2E8F0 !important;
  border-radius: 8px !important;
  background: white !important;
}
details[data-testid="stExpander"] summary {
  font-weight: 600 !important;
  color: #0B1F3A !important;
  font-size: 0.85rem !important;
}

/* ── DataFrame ───────────────────────────────────────────── */
div[data-testid="stDataFrame"] {
  border-radius: 8px !important;
  overflow: hidden !important;
  border: 1px solid #E2E8F0 !important;
}

/* ── Page Header ─────────────────────────────────────────── */
.pasis-page-header {
  background: linear-gradient(135deg, #0B1F3A 0%, #1A3560 100%);
  padding: 28px 32px 24px 32px;
  border-radius: 12px;
  margin-bottom: 28px;
  position: relative;
  overflow: hidden;
}
.pasis-page-header::after {
  content: '';
  position: absolute; top: 0; right: 0;
  width: 220px; height: 100%;
  background: linear-gradient(135deg, transparent 30%, rgba(228,0,43,0.07) 100%);
  pointer-events: none;
}
.pasis-page-header .eyebrow {
  font-size: 0.63rem; font-weight: 800; letter-spacing: 2.5px;
  text-transform: uppercase; color: rgba(255,255,255,0.45);
  margin-bottom: 8px;
}
.pasis-page-header h1 {
  font-size: 1.75rem; font-weight: 800; color: #FFFFFF;
  margin: 0 0 10px 0; line-height: 1.2; border: none !important;
}
.pasis-page-header p {
  font-size: 0.87rem; color: rgba(255,255,255,0.70);
  margin: 0 0 14px 0; line-height: 1.65; max-width: 680px;
}
.pasis-page-header .header-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.pasis-page-header .header-tag {
  background: rgba(255,255,255,0.10);
  border: 1px solid rgba(255,255,255,0.18);
  color: rgba(255,255,255,0.80);
  font-size: 0.67rem; font-weight: 700; letter-spacing: 0.5px;
  padding: 3px 10px; border-radius: 20px;
}

/* ── Section Title ───────────────────────────────────────── */
.pasis-section-title {
  font-size: 0.70rem; font-weight: 800; letter-spacing: 2px;
  text-transform: uppercase; color: #6B7C93;
  padding: 3px 0 3px 12px;
  border-left: 3px solid #E4002B;
  margin: 28px 0 16px 0;
  line-height: 1;
}

/* ── Scope Badges ────────────────────────────────────────── */
.scope-badge {
  display: inline-block; font-size: 0.63rem; font-weight: 800;
  letter-spacing: 1px; text-transform: uppercase;
  padding: 3px 9px; border-radius: 4px;
}
.scope-badge.market   { background: #FFF0F3; color: #C0001F; }
.scope-badge.tech     { background: #EEF2FB; color: #0B1F3A; }
.scope-badge.case     { background: #ECFBF4; color: #0A7B55; }
.scope-badge.policy   { background: #FFF8E8; color: #8A5A00; }

/* ── News Items ──────────────────────────────────────────── */
.news-item {
  background: white; border: 1px solid #E2E8F0;
  border-left-width: 4px; border-radius: 8px;
  padding: 14px 18px; margin-bottom: 10px;
}
.news-item .news-company-tag {
  display: inline-block; padding: 2px 9px; border-radius: 4px;
  font-size: 0.63rem; font-weight: 800; letter-spacing: 0.8px;
  color: white; margin-bottom: 8px; text-transform: uppercase;
}
.news-item .news-title {
  font-size: 0.92rem; font-weight: 700; color: #0B1F3A;
  line-height: 1.45; margin-bottom: 8px;
}
.news-item .news-meta { font-size: 0.75rem; color: #8A9BB0; }
.news-item .news-meta a { color: #E4002B !important; font-weight: 600; text-decoration: none; }

/* ── Player Profile Cards ────────────────────────────────── */
.player-profile-card {
  border-radius: 10px; padding: 14px 16px; margin-bottom: 8px;
  background: white; border: 1px solid #E2E8F0; border-top-width: 3px;
}
.player-profile-card .player-name {
  font-size: 0.88rem; font-weight: 800; color: #0B1F3A;
}
.player-profile-card .player-label { font-size: 0.68rem; color: #8A9BB0; margin: 3px 0 8px; }
.watch-tag {
  display: inline-block; background: #EEF2FF; color: #3730A3;
  padding: 2px 7px; border-radius: 4px;
  font-size: 0.62rem; font-weight: 700; margin: 2px 2px 0 0;
}

/* ── Weekly/Monthly Report Bodies ────────────────────────── */
.pasis-report-body {
  font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  font-size: 0.93rem; line-height: 1.8; color: #0B1F3A;
}
.pasis-report-body a { color: #E4002B; font-weight: 600; text-decoration: none; }
.pasis-report-body a:hover { text-decoration: underline; }
.pasis-monthly-body {
  font-family: -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
  font-size: 0.93rem; line-height: 1.8; color: #0B1F3A;
}
.pasis-monthly-body a { color: #0B1F3A; font-weight: 600; text-decoration: none; }

/* Weekly rpt- classes */
.rpt-section {
  background: #fff; border: 1px solid #E2E8F0;
  border-radius: 12px; padding: 24px 28px; margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(11,31,58,0.04);
}
.rpt-section-title {
  font-size: 1rem; font-weight: 800; color: #0B1F3A;
  border-left: 4px solid #E4002B; padding: 3px 0 3px 12px;
  background: linear-gradient(to right, #FFF0F3, transparent);
  margin-bottom: 16px;
}
.rpt-body { margin-bottom: 10px; }
.rpt-bullets { padding-left: 1.2rem; margin: 8px 0; }
.rpt-bullets li {
  padding: 8px 14px; margin-bottom: 8px;
  background: #F8F9FB; border-left: 3px solid #E4002B;
  border-radius: 0 6px 6px 0; list-style: none; margin-left: -1.2rem;
}
.rpt-company {
  border: 1px solid #E2E8F0; border-radius: 10px;
  padding: 16px 20px; margin-bottom: 14px; background: #FAFBFC;
}
.rpt-company-name {
  font-size: 1rem; font-weight: 800; color: #0B1F3A;
  margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #EEE;
}
.rpt-company-name a { color: #0B1F3A; }
.rpt-fact, .rpt-why, .rpt-lgu {
  padding: 6px 0 6px 12px; margin-bottom: 4px;
  font-size: 0.88rem; border-left: 2px solid transparent;
}
.rpt-fact { border-color: #8A9BB0; color: #3D4F6A; }
.rpt-why  { border-color: #0B1F3A; color: #0B1F3A; }
.rpt-lgu  { border-color: #E4002B; color: #C0001F; font-weight: 600; }
.rpt-trend {
  padding: 14px 18px; margin-bottom: 12px;
  border-radius: 8px; background: #F0F4FF; border-left: 3px solid #0B1F3A;
}
.rpt-trend-title {
  font-weight: 700; color: #0B1F3A; margin-bottom: 6px;
  display: flex; align-items: center; gap: 8px;
}
.rpt-badge {
  font-size: 0.67rem; font-weight: 700; padding: 2px 8px;
  border-radius: 10px; white-space: nowrap; background: #0B1F3A; color: white;
}
.rpt-badge.early, .rpt-badge.Early     { background: #D4881E; color: white; }
.rpt-badge.emerging, .rpt-badge.Emerging { background: #0B1F3A; color: white; }
.rpt-badge.mainstream, .rpt-badge.Mainstream { background: #0A7B55; color: white; }
.rpt-action { padding: 10px 16px; margin-bottom: 8px; border-radius: 8px; font-size: 0.88rem; }
.rpt-action--now   { background: #FFF0F3; border-left: 3px solid #E4002B; }
.rpt-action--short { background: #FFF8E8; border-left: 3px solid #D4881E; }
.rpt-action--mid   { background: #F0FFF8; border-left: 3px solid #0A7B55; }

/* Monthly mrpt- classes */
.mrpt-section {
  background: #fff; border: 1px solid #E2E8F0;
  border-radius: 12px; padding: 26px 30px; margin-bottom: 24px;
  box-shadow: 0 2px 10px rgba(11,31,58,0.05);
}
.mrpt-section-title {
  font-size: 1rem; font-weight: 800; color: #0B1F3A;
  border-left: 4px solid #0B1F3A; padding: 3px 0 3px 12px;
  background: linear-gradient(to right, #EEF2F8, transparent); margin-bottom: 18px;
}
.mrpt-body { margin-bottom: 10px; }
.mrpt-agenda {
  border: 1px solid #D1D9E6; border-radius: 10px;
  padding: 18px 22px; margin-bottom: 16px;
  background: #F8FAFD; border-left: 4px solid #0B1F3A;
}
.mrpt-agenda-title {
  font-size: 1rem; font-weight: 800; color: #0B1F3A;
  margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #DDE3EE;
}
.mrpt-issue, .mrpt-evidence, .mrpt-implication {
  padding: 7px 0 7px 14px; margin-bottom: 5px;
  font-size: 0.88rem; border-left: 2px solid transparent;
}
.mrpt-issue       { border-color: #8A9BB0; color: #3D4F6A; }
.mrpt-evidence    { border-color: #0B1F3A; color: #0B1F3A; }
.mrpt-implication { border-color: #E4002B; color: #C0001F; font-weight: 600; }
.mrpt-company {
  border: 1px solid #E2E8F0; border-radius: 10px;
  padding: 16px 20px; margin-bottom: 14px; background: #FAFBFC;
}
.mrpt-company-name {
  font-size: 1rem; font-weight: 800; color: #0B1F3A;
  margin-bottom: 10px; display: flex; align-items: center; gap: 10px;
}
.mrpt-company-name a { color: #0B1F3A; }
.mrpt-action-tag {
  font-size: 0.65rem; font-weight: 700; padding: 2px 9px;
  border-radius: 4px; white-space: nowrap;
}
.mrpt-action-tag.win     { background: #0A7B55; color: white; }
.mrpt-action-tag.watch   { background: #D4881E; color: white; }
.mrpt-action-tag.caution { background: #E4002B; color: white; }
.mrpt-tech-item {
  padding: 12px 16px; margin-bottom: 10px;
  border-radius: 8px; background: #F0F4FF;
  border-left: 3px solid #0B1F3A; font-size: 0.89rem;
}
.mrpt-badge {
  font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;
  white-space: nowrap; display: inline-block; margin-right: 6px;
  background: #0B1F3A; color: white;
}
.mrpt-badge.Early      { background: #D4881E; color: white; }
.mrpt-badge.Emerging   { background: #0B1F3A; color: white; }
.mrpt-badge.Mainstream { background: #0A7B55; color: white; }
.mrpt-action { padding: 12px 18px; margin-bottom: 10px; border-radius: 8px; font-size: 0.88rem; }
.mrpt-action--now   { background: #FFF0F3; border-left: 3px solid #E4002B; }
.mrpt-action--short { background: #FFF8E8; border-left: 3px solid #D4881E; }
.mrpt-action--mid   { background: #F0FFF8; border-left: 3px solid #0A7B55; }
"""

# Plotly 공통 색상 팔레트
CHART_COLORS = ["#0B1F3A", "#E4002B", "#0A7B55", "#D4881E", "#1A5FAD", "#6B21A8", "#0E7490"]
SCOPE_COLORS = {
    "Market": "#E4002B",
    "Tech": "#0B1F3A",
    "Case": "#0A7B55",
    "Policy": "#D4881E",
}


def inject_global_css() -> None:
    """전역 디자인 시스템 CSS를 주입합니다."""
    import streamlit as st
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, description: str, tags: list[str] | None = None) -> None:
    """BCG/Bain 스타일 페이지 헤더를 렌더링합니다."""
    import streamlit as st
    tags = tags or []
    tags_html = "".join(f'<span class="header-tag">{t}</span>' for t in tags)
    st.markdown(f"""
    <div class="pasis-page-header">
      <div class="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{description}</p>
      <div class="header-tags">{tags_html}</div>
    </div>
    """, unsafe_allow_html=True)


def section_title(text: str) -> None:
    """섹션 구분 타이틀을 렌더링합니다."""
    import streamlit as st
    st.markdown(f'<div class="pasis-section-title">{text}</div>', unsafe_allow_html=True)


def sidebar_brand(page_icon: str, page_name: str) -> None:
    """사이드바 상단 PASIS 브랜드 헤더를 렌더링합니다."""
    import streamlit as st
    st.markdown(f"""
    <div style="padding:1rem 0 1rem 0; border-bottom:1px solid rgba(255,255,255,0.10); margin-bottom:1.2rem;">
      <div style="font-size:0.58rem;font-weight:800;letter-spacing:3px;
                  color:rgba(255,255,255,0.38);text-transform:uppercase;margin-bottom:4px;">
        PASIS Intelligence
      </div>
      <div style="font-size:1rem;font-weight:800;color:white;line-height:1.2;">
        {page_icon}&nbsp; {page_name}
      </div>
    </div>
    """, unsafe_allow_html=True)


def plotly_layout(fig, title: str = "") -> object:
    """Plotly 차트에 일관된 전문 레이아웃을 적용합니다."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#0B1F3A", family="sans-serif"), x=0, xref="paper"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="sans-serif", size=12, color="#3D4F6A"),
        margin=dict(l=4, r=4, t=36 if title else 10, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            font=dict(size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        ),
        xaxis=dict(gridcolor="#F0F0F4", linecolor="#E2E8F0", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#F0F0F4", linecolor="#E2E8F0", tickfont=dict(size=11)),
    )
    return fig
