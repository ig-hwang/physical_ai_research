"""
Market Intelligence 페이지
SEC 공시(10-K, 8-K), IR 보고서, M&A 신호 — 재무·자본 시장 동향
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Market Intelligence | PASIS", layout="wide")

from web.styles import inject_global_css, page_header, section_title, sidebar_brand, plotly_layout, CHART_COLORS
inject_global_css()


@st.cache_data(ttl=300)
def load_market_signals(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Market", days_back=days_back)


# ── 사이드바 ─────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_brand("📈", "Market Intelligence")
    days_back = st.selectbox("PERIOD", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "CATEGORY",
        ["Annual Report", "Material Event", "IPO Filing", "Investment", "M&A"],
        default=[],
    )
    min_confidence = st.slider("MIN CONFIDENCE", 0.0, 1.0, 0.6, step=0.05)


# ── 헤더 ─────────────────────────────────────────────────────────────────────
page_header(
    eyebrow="MARKET SCOPE · SEC / IR / M&A",
    title="Market Intelligence",
    description="Tesla, NVIDIA, Amazon 등 주요 기업의 SEC 공시(10-K·8-K), IR 보고서, M&A 동향을 수집합니다. "
                "재무 공시에서 Physical AI 전략 방향성과 투자 의도를 독해하여 선제적 시장 인사이트를 제공합니다.",
    tags=["SEC 10-K / 8-K", "IR Reports", "M&A Signals", "Tesla", "NVIDIA", "Amazon"],
)

df = load_market_signals(int(days_back))

if df.empty:
    st.info("Market 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

if category_filter:
    df = df[df["category"].isin(category_filter)]
df = df[df["confidence_score"].fillna(0) >= min_confidence]

# ── KPI ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("수집 신호", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("출처 수", f"{df['publisher'].nunique()}개")
col4.metric("카테고리 수", f"{df['category'].nunique()}개")

st.divider()

# ── 차트 ─────────────────────────────────────────────────────────────────────
section_title("공시 유형 분석")
col_pie, col_bar = st.columns(2)

with col_pie:
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.pie(
        cat_counts, names="category", values="count",
        hole=0.52,
        color_discrete_sequence=CHART_COLORS,
    )
    plotly_layout(fig, "카테고리 분포")
    fig.update_traces(textposition="outside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

with col_bar:
    pub_counts = df["publisher"].value_counts().head(8).reset_index()
    pub_counts.columns = ["publisher", "count"]
    fig2 = px.bar(
        pub_counts, x="count", y="publisher", orientation="h",
        color_discrete_sequence=["#E4002B"],
    )
    plotly_layout(fig2, "출처별 수집량 (Top 8)")
    fig2.update_layout(yaxis=dict(categoryorder="total ascending"))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 신호 상세 ─────────────────────────────────────────────────────────────────
section_title("수집 자료 상세")
st.caption("각 공시·IR 자료의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

from web.components.cards import signal_card, signal_card_compact
view_mode = st.radio("보기", ["카드", "목록"], horizontal=True, label_visibility="collapsed")

for _, row in df.iterrows():
    if "카드" in view_mode:
        signal_card(row.to_dict())
    else:
        signal_card_compact(row.to_dict())

st.divider()
with st.expander("전체 데이터 (CSV 다운로드)"):
    cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    st.download_button("CSV 다운로드", display_df.to_csv(index=False, encoding="utf-8-sig"),
                       "market_intelligence.csv", "text/csv")