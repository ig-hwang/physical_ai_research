"""
PASIS Chart Components - Plotly 기반 시각화 모듈
모든 차트는 Streamlit st.plotly_chart()와 호환.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objects import Figure

# ── Color Palette (LG Uplus Brand) ────────────────────────────────────────────
SCOPE_COLORS = {
    "Market": "#E4002B",   # LG Red
    "Tech": "#1A1AEA",     # Electric Blue
    "Case": "#00A651",     # Green
    "Policy": "#F5A623",   # Amber
}

CHART_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Pretendard, -apple-system, sans-serif", size=13),
    margin=dict(l=0, r=0, t=40, b=0),
)


def scope_distribution_chart(df: pd.DataFrame) -> Figure:
    """스코프별 신호 분포 도넛 차트."""
    if df.empty:
        return _empty_fig("데이터 없음")

    counts = df["scope"].value_counts().reset_index()
    counts.columns = ["scope", "count"]

    fig = px.pie(
        counts,
        names="scope",
        values="count",
        hole=0.55,
        color="scope",
        color_discrete_map=SCOPE_COLORS,
        title="스코프별 신호 분포",
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>%{value}건 (%{percent})<extra></extra>",
    )
    fig.update_layout(**CHART_THEME, showlegend=True, legend=dict(orientation="h", y=-0.1))
    return fig


def timeline_chart(df: pd.DataFrame) -> Figure:
    """주별 신호 수집량 추이 라인 차트."""
    if df.empty:
        return _empty_fig("데이터 없음")

    # df 컬럼: week, scope, count
    if "week" not in df.columns:
        return _empty_fig("타임라인 데이터 없음")

    fig = px.line(
        df,
        x="week",
        y="count",
        color="scope",
        color_discrete_map=SCOPE_COLORS,
        markers=True,
        title="주간 신호 수집 추이",
        labels={"week": "주", "count": "건수", "scope": "스코프"},
    )
    fig.update_traces(line_width=2.5, marker_size=7)
    fig.update_xaxes(tickformat="%Y-%m-%d", tickangle=-30)
    fig.update_layout(**CHART_THEME)
    return fig


def publisher_bar_chart(df: pd.DataFrame) -> Figure:
    """퍼블리셔별 수집 건수 수평 막대 차트."""
    if df.empty:
        return _empty_fig("데이터 없음")

    df_sorted = df.sort_values("count", ascending=True).tail(10)
    fig = px.bar(
        df_sorted,
        x="count",
        y="publisher",
        orientation="h",
        title="주요 출처별 수집량",
        labels={"count": "건수", "publisher": "출처"},
        color="count",
        color_continuous_scale=["#FFC0CB", "#E4002B"],
    )
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False)
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>%{x}건<extra></extra>"
    )
    return fig


def confidence_histogram(df: pd.DataFrame) -> Figure:
    """신뢰도 점수 분포 히스토그램."""
    if df.empty or "confidence_score" not in df.columns:
        return _empty_fig("데이터 없음")

    valid = df["confidence_score"].dropna()
    if valid.empty:
        return _empty_fig("신뢰도 데이터 없음")

    fig = px.histogram(
        valid,
        nbins=10,
        title="신뢰도 점수 분포",
        labels={"value": "신뢰도 점수", "count": "건수"},
        color_discrete_sequence=["#1A1AEA"],
        range_x=[0, 1],
    )
    fig.update_layout(**CHART_THEME)
    fig.update_traces(hovertemplate="신뢰도: %{x:.2f}<br>%{y}건<extra></extra>")
    return fig


def keyword_frequency_chart(df: pd.DataFrame, top_n: int = 15) -> Figure:
    """
    제목/요약에서 전략 키워드 빈도 막대 차트.
    df 컬럼: keyword, count
    """
    if df.empty:
        return _empty_fig("키워드 데이터 없음")

    df_top = df.nlargest(top_n, "count")
    fig = px.bar(
        df_top,
        x="count",
        y="keyword",
        orientation="h",
        title=f"Top {top_n} 전략 키워드",
        labels={"count": "언급 건수", "keyword": "키워드"},
        color="count",
        color_continuous_scale=["#B3D4F5", "#1A1AEA"],
    )
    fig.update_layout(**CHART_THEME, coloraxis_showscale=False)
    return fig


def category_treemap(df: pd.DataFrame) -> Figure:
    """스코프 > 카테고리 트리맵."""
    if df.empty:
        return _empty_fig("데이터 없음")

    grouped = (
        df.groupby(["scope", "category"])
        .size()
        .reset_index(name="count")
    )
    grouped["scope"] = grouped["scope"].fillna("Unknown")
    grouped["category"] = grouped["category"].fillna("기타")

    fig = px.treemap(
        grouped,
        path=["scope", "category"],
        values="count",
        color="scope",
        color_discrete_map=SCOPE_COLORS,
        title="Scope > Category 트리맵",
    )
    fig.update_layout(**CHART_THEME)
    return fig


def _empty_fig(message: str) -> Figure:
    """빈 데이터용 빈 Figure."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#999"),
    )
    fig.update_layout(**CHART_THEME)
    return fig