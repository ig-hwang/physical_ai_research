"""
Market Signals 페이지
SEC 공시(10-K, 8-K), IR 보고서, M&A 신호
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Market Signals | PASIS", layout="wide")

st.markdown("""
<style>
  .scope-header { font-size:1.5rem; font-weight:800; color:#E4002B;
                  border-left:5px solid #E4002B; padding-left:12px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_market_signals(days_back: int = 90) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Market", days_back=days_back)


# ── 사이드바 필터 ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Market Signals 필터")
    days_back = st.selectbox("조회 기간", [7, 30, 90, 180], index=2,
                             format_func=lambda x: f"최근 {x}일")
    category_filter = st.multiselect(
        "카테고리",
        ["Annual Report", "Material Event", "IPO Filing", "Investment", "M&A"],
        default=[],
    )
    min_confidence = st.slider("최소 신뢰도", 0.0, 1.0, 0.6, step=0.05)

# ── 본문 ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="scope-header">Market Signals</p>', unsafe_allow_html=True)
st.caption("SEC 공시 (10-K, 8-K), IR 보고서, M&A · 대상: Tesla, NVIDIA, Amazon, Figure AI")

df = load_market_signals(int(days_back))

if df.empty:
    st.info("Market 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

# 필터 적용
if category_filter:
    df = df[df["category"].isin(category_filter)]
df = df[df["confidence_score"].fillna(0) >= min_confidence]

# ── KPI ───────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Market 신호 수", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("출처 수", f"{df['publisher'].nunique()}개")

st.divider()

# ── 카테고리별 분포 ────────────────────────────────────────────────────────────
import plotly.express as px
col_pie, col_bar = st.columns(2)
with col_pie:
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.pie(cat_counts, names="category", values="count",
                 hole=0.5, title="카테고리 분포",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_bar:
    pub_counts = df["publisher"].value_counts().head(8).reset_index()
    pub_counts.columns = ["publisher", "count"]
    fig2 = px.bar(pub_counts, x="count", y="publisher", orientation="h",
                  title="출처별 수집량",
                  color_discrete_sequence=["#E4002B"])
    fig2.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 신호 상세 카드 (출처 / 내용 요약 / 인사이트 3섹션) ────────────────────────
from web.components.cards import signal_card, signal_card_compact

st.markdown("### 수집 자료 상세")
st.caption("각 자료의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

view_mode = st.radio("보기 방식", ["카드 전체", "목록"], horizontal=True, label_visibility="collapsed")

for _, row in df.iterrows():
    if "카드" in view_mode:
        signal_card(row.to_dict())
    else:
        signal_card_compact(row.to_dict())

# ── 데이터 테이블 (다운로드) ───────────────────────────────────────────────────
st.divider()
with st.expander("전체 데이터 테이블 (CSV 다운로드)"):
    display_cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in display_cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("CSV 다운로드", csv, "market_signals.csv", "text/csv")