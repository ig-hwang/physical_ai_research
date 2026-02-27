"""
Policy Monitor 페이지
EU AI Act, NIST AI RMF, IFR 등 규제·표준 동향 — Physical AI 컴플라이언스 리스크
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Policy Monitor | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand, plotly_layout, CHART_COLORS
inject_global_css()


@st.cache_data(ttl=300)
def load_policy_signals(days_back: int = 180) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Policy", days_back=days_back)


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("📜", "Policy Monitor")
    days_back = st.selectbox("PERIOD", [30, 90, 180, 365], index=2,
                             format_func=lambda x: f"최근 {x}일")
    region_filter = st.multiselect(
        "REGION",
        ["EU", "US", "KR", "Global"],
        default=[],
        help="출처명 기준 필터 (EU Official Journal, NIST 등)",
    )


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="POLICY SCOPE · REGULATION / STANDARD",
    title="Policy Monitor",
    description="EU AI Act, NIST AI RMF, IFR 등 글로벌 규제·표준 동향을 모니터링합니다. "
                "Physical AI의 고위험 시스템 분류 기준과 컴플라이언스 타임라인은 사업 진입 전략의 핵심 변수입니다.",
    tags=["EU AI Act", "NIST AI RMF", "IFR", "High-Risk AI", "Safety Standards"],
)

df = load_policy_signals(int(days_back))

if df.empty:
    st.info("Policy 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

# 지역 필터
if region_filter:
    region_keywords = {
        "EU": ["EU", "europe", "eur-lex"],
        "US": ["NIST", "US", "federal"],
        "KR": ["KISA", "과기부", "방통위"],
        "Global": ["IFR", "ISO", "ITU"],
    }
    mask = df["publisher"].str.lower().apply(
        lambda p: any(
            kw.lower() in (p or "").lower()
            for r in region_filter
            for kw in region_keywords.get(r, [])
        )
    )
    filtered = df[mask]
    df = filtered if not filtered.empty else df

# ── KPI ──────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("규제/표준 신호", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("발행 기관", f"{df['publisher'].nunique()}개")

st.divider()

# ── 신호 상세 ─────────────────────────────────────────────────────────────────
section_title("규제·표준 동향 상세")
st.caption("각 규제·표준 문서의 출처 · 내용 요약 · LGU+ 컴플라이언스 인사이트를 확인하세요.")

from web.components.cards import signal_card, signal_card_compact
view_mode = st.radio("보기", ["카드", "목록"], horizontal=True, label_visibility="collapsed")

if "published_at" in df.columns and not df.empty:
    df_sorted = df.sort_values("published_at")
    for _, row in df_sorted.iterrows():
        if "카드" in view_mode:
            signal_card(row.to_dict())
        else:
            signal_card_compact(row.to_dict())

st.divider()

# ── 분포 차트 ─────────────────────────────────────────────────────────────────
section_title("규제 유형 분석")
col_cat, col_pub = st.columns(2)

with col_cat:
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(
        cat_counts, x="category", y="count",
        color_discrete_sequence=["#D4881E"],
        labels={"category": "유형", "count": "건수"},
    )
    plotly_layout(fig, "규제 유형 분포")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_pub:
    pub_counts = df["publisher"].value_counts().reset_index()
    pub_counts.columns = ["publisher", "count"]
    fig2 = px.pie(
        pub_counts, names="publisher", values="count",
        hole=0.4,
        color_discrete_sequence=CHART_COLORS,
    )
    plotly_layout(fig2, "발행 기관별 비중")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
with st.expander("전체 데이터 (CSV 다운로드)"):
    cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    st.download_button("CSV 다운로드", display_df.to_csv(index=False, encoding="utf-8-sig"),
                       "policy_monitor.csv", "text/csv")
