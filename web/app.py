"""
PASIS - Physical AI Strategic Intelligence System
메인 대시보드 (Streamlit)

실행: streamlit run web/app.py
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (pages/에서 database, pipeline 임포트 가능)
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

# ── 페이지 설정 (가장 첫 번째 Streamlit 명령) ─────────────────────────────────
st.set_page_config(
    page_title="PASIS | Physical AI Intelligence",
    page_icon="assets/favicon.png" if (_ROOT / "web/assets/favicon.png").exists() else "robot",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/",
        "About": "PASIS v1.0 — LG Uplus Portfolio Strategy",
    },
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* 전체 배경 */
  .main { background-color: #F8F9FB; }

  /* 헤더 */
  .pasis-header {
    padding: 1.2rem 0 0.8rem 0;
    border-bottom: 3px solid #E4002B;
    margin-bottom: 1.5rem;
  }
  .pasis-title {
    font-size: 1.8rem; font-weight: 800;
    color: #1A1A2E; margin: 0;
  }
  .pasis-subtitle {
    font-size: 0.9rem; color: #666; margin: 0;
  }

  /* KPI 카드 */
  div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #E8E8E8;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }

  /* 사이드바 */
  section[data-testid="stSidebar"] {
    background: #1A1A2E;
    color: white;
  }
  section[data-testid="stSidebar"] * {
    color: white !important;
  }
  section[data-testid="stSidebar"] .stCheckbox label {
    color: #DDD !important;
  }

  /* 섹션 제목 */
  .section-title {
    font-size: 1.1rem; font-weight: 700;
    color: #1A1A2E; margin: 1.2rem 0 0.5rem 0;
    padding-left: 8px;
    border-left: 4px solid #E4002B;
  }

  /* 최신 신호 테이블 */
  .signal-row { border-bottom: 1px solid #F0F0F0; padding: 0.5rem 0; }

  /* 하단 여백 */
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── DB 초기화 ─────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="데이터베이스 초기화 중...")
def _init_db() -> None:
    from database.init_db import init_db
    init_db(seed_demo_data=True)


_init_db()


# ── 데이터 로딩 (TTL 5분 캐시) ──────────────────────────────────────────────
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


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0 0.5rem 0; border-bottom:1px solid #333;">
      <div style="font-size:1.1rem;font-weight:800;letter-spacing:1px;">PASIS</div>
      <div style="font-size:0.7rem;color:#AAA;">Physical AI Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 네비게이션")
    st.page_link("app.py", label="대시보드", icon="📈")
    st.page_link("pages/1_Market_Signals.py", label="Market Signals", icon="🏦")
    st.page_link("pages/2_Tech_Frontier.py", label="Tech Frontier", icon="🔬")
    st.page_link("pages/3_Real_World_Cases.py", label="Real-world Cases", icon="🏭")
    st.page_link("pages/4_Policy_Standards.py", label="Policy/Standards", icon="📜")
    st.page_link("pages/5_Weekly_Report.py", label="주간 리포트", icon="📰")

    st.divider()
    st.markdown("### 파이프라인")
    if st.button("지금 수집 실행", use_container_width=True, type="primary"):
        with st.spinner("데이터 수집 중..."):
            try:
                from run_pipeline import run_once
                result = run_once()
                st.success(f"완료: {result.get('inserted', 0)}건 신규 저장")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"실행 오류: {e}")

    st.markdown("### 조회 기간")
    days_back = st.selectbox("기간", [7, 30, 90, 180], index=2, format_func=lambda x: f"최근 {x}일")

    st.divider()
    from datetime import datetime
    st.caption(f"마지막 갱신: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pasis-header">
  <p class="pasis-title">Physical AI Strategic Intelligence</p>
  <p class="pasis-subtitle">LG Uplus Portfolio Strategy · Global Physical AI Market Monitor</p>
</div>
""", unsafe_allow_html=True)

# ── KPI 메트릭 ────────────────────────────────────────────────────────────────
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

# ── 차트 행 1 ──────────────────────────────────────────────────────────────────
from web.components.charts import (
    scope_distribution_chart,
    timeline_chart,
    publisher_bar_chart,
    confidence_histogram,
)

df_all = load_signals(days_back=int(days_back))
df_timeline = load_timeline(days_back=int(days_back))
df_publishers = load_publishers()

col_chart1, col_chart2 = st.columns([1, 2])
with col_chart1:
    st.markdown('<p class="section-title">스코프 분포</p>', unsafe_allow_html=True)
    st.plotly_chart(scope_distribution_chart(df_all), use_container_width=True)

with col_chart2:
    st.markdown('<p class="section-title">주간 수집 추이</p>', unsafe_allow_html=True)
    st.plotly_chart(timeline_chart(df_timeline), use_container_width=True)

# ── 차트 행 2 ──────────────────────────────────────────────────────────────────
col_chart3, col_chart4 = st.columns(2)
with col_chart3:
    st.markdown('<p class="section-title">주요 출처</p>', unsafe_allow_html=True)
    st.plotly_chart(publisher_bar_chart(df_publishers), use_container_width=True)

with col_chart4:
    st.markdown('<p class="section-title">신뢰도 분포</p>', unsafe_allow_html=True)
    st.plotly_chart(confidence_histogram(df_all), use_container_width=True)

st.divider()

# ── 최신 신호 피드 ─────────────────────────────────────────────────────────────
from web.components.cards import signal_card, signal_card_compact, render_scope_badge

st.markdown('<p class="section-title">최신 Physical AI 신호</p>', unsafe_allow_html=True)

if df_all.empty:
    st.info("수집된 데이터가 없습니다. 사이드바에서 '지금 수집 실행'을 클릭하세요.")
else:
    col_vm, col_cnt = st.columns([3, 1])
    with col_vm:
        view_mode = st.radio(
            "보기 방식",
            ["아코디언 (제목 훑고 클릭)", "목록 (압축)"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with col_cnt:
        n_show = st.selectbox("표시 건수", [10, 20, 50], index=1, label_visibility="collapsed")

    latest = df_all.head(n_show)

    if "아코디언" in view_mode:
        for _, row in latest.iterrows():
            signal_card(row.to_dict())
    else:
        st.markdown("""
        <div style="padding:8px 14px;background:#F5F5F5;border-radius:6px 6px 0 0;
                    font-size:0.75rem;font-weight:700;color:#888;display:flex;gap:10px;">
          <span style="width:90px;">스코프</span>
          <span style="flex:1;">제목</span>
          <span style="width:120px;">출처</span>
          <span style="width:80px;">날짜</span>
          <span style="width:70px;">신뢰도</span>
        </div>
        """, unsafe_allow_html=True)
        for _, row in latest.iterrows():
            signal_card_compact(row.to_dict())

# ── 하단 정보 ─────────────────────────────────────────────────────────────────
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.caption("PASIS v1.0 · LG Uplus Portfolio Strategy Team")
with col_f2:
    st.caption("데이터 출처: SEC EDGAR, arXiv, RSS Feeds")
with col_f3:
    st.caption("분석 엔진: Claude claude-sonnet-4-6 (Anthropic)")