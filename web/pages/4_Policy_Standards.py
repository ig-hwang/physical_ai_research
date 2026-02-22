"""
Policy / Standards 페이지
EU AI Act, NIST AI RMF, IFR 등 규제/표준 동향
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Policy/Standards | PASIS", layout="wide")

st.markdown("""
<style>
  .scope-header { font-size:1.5rem; font-weight:800; color:#F5A623;
                  border-left:5px solid #F5A623; padding-left:12px; }
  .regulation-box {
    background:#FFF8E1; border-left:4px solid #F5A623;
    padding:1rem; border-radius:6px; margin:0.5rem 0;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_policy_signals(days_back: int = 180) -> pd.DataFrame:
    from database.init_db import get_session
    from database.queries import get_signals_df
    with get_session() as session:
        return get_signals_df(session, scope="Policy", days_back=days_back)


# ── 사이드바 ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Policy/Standards 필터")
    days_back = st.selectbox("조회 기간", [30, 90, 180, 365], index=2,
                             format_func=lambda x: f"최근 {x}일")
    region_filter = st.multiselect(
        "지역",
        ["EU", "US", "KR", "Global"],
        default=[],
        help="출처명 기준 필터 (EU Official Journal, NIST 등)",
    )

# ── 본문 ──────────────────────────────────────────────────────────────────────
st.markdown('<p class="scope-header">Policy / Standards</p>', unsafe_allow_html=True)
st.caption("EU AI Act, NIST AI RMF, IFR · Physical AI 고위험 분류, 규제 타임라인")

df = load_policy_signals(int(days_back))

if df.empty:
    st.info("Policy 스코프 신호 없음. 파이프라인을 실행하세요.")
    st.stop()

# 지역 필터 (publisher 기반 간이 적용)
if region_filter:
    region_keywords = {"EU": ["EU", "europe", "eur-lex"], "US": ["NIST", "US", "federal"],
                       "KR": ["KISA", "과기부", "방통위"], "Global": ["IFR", "ISO", "ITU"]}
    mask = df["publisher"].str.lower().apply(
        lambda p: any(
            kw.lower() in (p or "").lower()
            for r in region_filter
            for kw in region_keywords.get(r, [])
        )
    )
    filtered = df[mask]
    df = filtered if not filtered.empty else df

# ── KPI ───────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("규제/표준 신호", f"{len(df)}건")
col2.metric("평균 신뢰도", f"{df['confidence_score'].mean():.0%}" if not df.empty else "N/A")
col3.metric("발행 기관", f"{df['publisher'].nunique()}개")

st.divider()

# ── 규제/표준 자료 (출처 / 내용 요약 / 인사이트 카드) ─────────────────────────
from web.components.cards import signal_card, signal_card_compact

st.markdown("### 수집 자료 상세")
st.caption("각 규제/표준 문서의 출처 · 내용 요약 · LGU+ 전략 인사이트를 확인하세요.")

view_mode = st.radio("보기 방식", ["카드 전체", "목록"], horizontal=True, label_visibility="collapsed")

if "published_at" in df.columns and not df.empty:
    df_sorted = df.sort_values("published_at")
    for _, row in df_sorted.iterrows():
        if "카드" in view_mode:
            signal_card(row.to_dict())
        else:
            signal_card_compact(row.to_dict())

st.divider()

# ── 카테고리 분포 ──────────────────────────────────────────────────────────────
col_cat, col_pub = st.columns(2)
with col_cat:
    st.markdown("### 규제 유형 분포")
    cat_counts = df["category"].value_counts().reset_index()
    cat_counts.columns = ["category", "count"]
    fig = px.bar(
        cat_counts, x="category", y="count",
        color_discrete_sequence=["#F5A623"],
        labels={"category": "유형", "count": "건수"},
    )
    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_pub:
    st.markdown("### 발행 기관별")
    pub_counts = df["publisher"].value_counts().reset_index()
    pub_counts.columns = ["publisher", "count"]
    fig2 = px.pie(
        pub_counts, names="publisher", values="count",
        color_discrete_sequence=px.colors.qualitative.Antique,
    )
    fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig2, use_container_width=True)

# ── 다운로드 ───────────────────────────────────────────────────────────────────
with st.expander("전체 데이터 (CSV)"):
    display_cols = ["title", "category", "publisher", "published_at", "confidence_score", "source_url"]
    display_df = df[[c for c in display_cols if c in df.columns]]
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("CSV 다운로드", csv, "policy_standards.csv", "text/csv")
