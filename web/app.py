"""
PASIS - Physical AI Strategic Intelligence System
메인 대시보드 (Streamlit)

실행: streamlit run web/app.py
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

# ── 페이지 설정 ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PASIS | Physical AI Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "PASIS v2.0 — LG Uplus Portfolio Strategy"},
)

# ── 디자인 시스템 주입 ──────────────────────────────────────────────────────
from web.styles import inject_global_css, section_title, plotly_layout, CHART_COLORS, SCOPE_COLORS
inject_global_css()

# ── DB 초기화 ────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="데이터베이스 초기화 중...")
def _init_db() -> None:
    from database.init_db import init_db
    init_db(seed_demo_data=True)

_init_db()


# ── 데이터 로딩 ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_kpis() -> dict:
    from database.init_db import get_session
    from database.queries import get_kpi_metrics
    with get_session() as session:
        return get_kpi_metrics(session)


@st.cache_data(ttl=300, show_spinner=False)
def load_signals(scope: str | None = None, days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope=scope, days_back=days_back)


@st.cache_data(ttl=300, show_spinner=False)
def load_timeline(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_timeline_data
    with get_session() as session:
        return get_timeline_data(session, days_back=days_back)


@st.cache_data(ttl=300, show_spinner=False)
def load_publishers() -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_top_publishers
    with get_session() as session:
        return get_top_publishers(session)


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 1.2rem 0; border-bottom:1px solid rgba(255,255,255,0.10); margin-bottom:1.2rem;">
      <div style="font-size:0.58rem;font-weight:800;letter-spacing:3px;
                  color:rgba(255,255,255,0.38);text-transform:uppercase;margin-bottom:6px;">
        LG Uplus Portfolio Strategy
      </div>
      <div style="font-size:1.1rem;font-weight:800;color:white;line-height:1.2;">
        PASIS
      </div>
      <div style="font-size:0.72rem;color:rgba(255,255,255,0.45);margin-top:2px;">
        Physical AI Intelligence
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.62rem;font-weight:800;letter-spacing:1.8px;
                color:rgba(255,255,255,0.38);text-transform:uppercase;margin-bottom:10px;">
      Navigation
    </div>
    """, unsafe_allow_html=True)

    st.page_link("app.py",                              label="Overview Dashboard",    icon="📊")
    st.page_link("pages/1_Market_Intelligence.py",      label="Market Intelligence",   icon="📈")
    st.page_link("pages/2_Technology_Radar.py",         label="Technology Radar",      icon="🔬")
    st.page_link("pages/3_Field_Intelligence.py",       label="Field Intelligence",    icon="🏭")
    st.page_link("pages/4_Policy_Monitor.py",           label="Policy Monitor",        icon="📜")
    st.page_link("pages/5_Key_Players.py",              label="Key Players",           icon="🏢")
    st.page_link("pages/6_Weekly_Brief.py",             label="Weekly Brief",          icon="📰")
    st.page_link("pages/7_Monthly_Review.py",           label="Monthly Review",        icon="📋")

    st.divider()

    st.markdown("""
    <div style="font-size:0.62rem;font-weight:800;letter-spacing:1.8px;
                color:rgba(255,255,255,0.38);text-transform:uppercase;margin-bottom:10px;">
      Pipeline
    </div>
    """, unsafe_allow_html=True)

    if st.button("데이터 수집 실행", use_container_width=True, type="primary"):
        with st.spinner("수집 중..."):
            try:
                from run_pipeline import run_once
                result = run_once()
                st.success(f"완료: {result.get('inserted', 0)}건 신규 저장")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"실행 오류: {e}")

    st.markdown("""
    <div style="font-size:0.62rem;font-weight:800;letter-spacing:1.8px;
                color:rgba(255,255,255,0.38);text-transform:uppercase;margin:16px 0 8px 0;">
      Period
    </div>
    """, unsafe_allow_html=True)
    days_back = st.selectbox("기간", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일",
                             label_visibility="collapsed")

    st.divider()
    from datetime import datetime
    st.caption(f"갱신: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ── 페이지 헤더 ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="pasis-page-header">
  <div class="eyebrow">LG UPLUS PORTFOLIO STRATEGY · PHYSICAL AI</div>
  <h1>Strategic Intelligence Overview</h1>
  <p>글로벌 Physical AI 시장의 핵심 신호를 실시간으로 수집·분석합니다.
     SEC 공시, arXiv 논문, 현장 사례, 정책 동향을 통합하여 LGU+ 전략팀에 선제적 인사이트를 제공합니다.</p>
  <div class="header-tags">
    <span class="header-tag">Market Intelligence</span>
    <span class="header-tag">Technology Radar</span>
    <span class="header-tag">Field Intelligence</span>
    <span class="header-tag">Policy Monitor</span>
    <span class="header-tag">Claude AI Analysis</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI 메트릭 ───────────────────────────────────────────────────────────────
kpis = load_kpis()
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("전체 신호", f"{kpis.get('total_signals', 0):,}건")
with col2:
    st.metric("이번 주 신규", f"{kpis.get('this_week', 0):,}건")
with col3:
    conf = kpis.get('avg_confidence', 0)
    st.metric("평균 신뢰도", f"{conf:.0%}")
with col4:
    st.metric("Market", f"{kpis.get('market', 0)}건")
with col5:
    st.metric("Tech", f"{kpis.get('tech', 0)}건")
with col6:
    st.metric("Case + Policy", f"{kpis.get('case', 0) + kpis.get('policy', 0)}건")

st.divider()

# ── 차트 ─────────────────────────────────────────────────────────────────────
import plotly.express as px
import plotly.graph_objects as go

from web.components.charts import (
    scope_distribution_chart,
    timeline_chart,
    publisher_bar_chart,
    confidence_histogram,
)

df_all       = load_signals(days_back=int(days_back))
df_timeline  = load_timeline(days_back=int(days_back))
df_publishers = load_publishers()

section_title("신호 분포 현황")
col_chart1, col_chart2 = st.columns([1, 2])
with col_chart1:
    fig = scope_distribution_chart(df_all)
    plotly_layout(fig, "스코프 분포")
    st.plotly_chart(fig, use_container_width=True)
with col_chart2:
    fig2 = timeline_chart(df_timeline)
    plotly_layout(fig2, "주간 수집 추이")
    st.plotly_chart(fig2, use_container_width=True)

col_chart3, col_chart4 = st.columns(2)
with col_chart3:
    fig3 = publisher_bar_chart(df_publishers)
    plotly_layout(fig3, "주요 출처")
    st.plotly_chart(fig3, use_container_width=True)
with col_chart4:
    fig4 = confidence_histogram(df_all)
    plotly_layout(fig4, "신뢰도 분포")
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── 최신 신호 피드 ────────────────────────────────────────────────────────────
from web.components.cards import signal_card, signal_card_compact

section_title("최신 Physical AI 신호")

if df_all.empty:
    st.info("수집된 데이터가 없습니다. 사이드바에서 '데이터 수집 실행'을 클릭하세요.")
else:
    col_vm, col_cnt = st.columns([3, 1])
    with col_vm:
        view_mode = st.radio(
            "보기 방식", ["아코디언", "목록"],
            horizontal=True, label_visibility="collapsed",
        )
    with col_cnt:
        n_show = st.selectbox("표시 건수", [10, 20, 50], index=1, label_visibility="collapsed")

    latest = df_all.head(n_show)
    if "아코디언" in view_mode:
        for _, row in latest.iterrows():
            signal_card(row.to_dict())
    else:
        for _, row in latest.iterrows():
            signal_card_compact(row.to_dict())

# ── 하단 ─────────────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("PASIS v2.0 · LG Uplus Portfolio Strategy Team")
with col_f2:
    st.caption("데이터 출처: SEC EDGAR, arXiv, RSS Feeds")
with col_f3:
    st.caption("분석 엔진: Claude claude-sonnet-4-6 (Anthropic)")