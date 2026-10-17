import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="서울 기온 분석", page_icon="🌡️", layout="wide")

# ========== 커스텀 CSS ==========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 배경 그라데이션 */
.stApp {
    background: linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 30%, #0d1b3e 60%, #0a0a2e 100%);
}

/* 사이드바 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f3d 0%, #1a1a5e 50%, #0d0d35 100%);
    border-right: 1px solid rgba(100, 130, 255, 0.2);
}
section[data-testid="stSidebar"] * {
    color: #c8d6f0 !important;
}

/* 헤더 배너 */
.hero-banner {
    background: linear-gradient(135deg, #1e3a6d 0%, #2a1f5e 40%, #3d1a5e 70%, #1e3a6d 100%);
    border: 1px solid rgba(120, 140, 255, 0.25);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 0 60px rgba(80, 100, 255, 0.15), 0 0 120px rgba(120, 60, 200, 0.08);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(ellipse at 30% 20%, rgba(100, 140, 255, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 80%, rgba(180, 100, 255, 0.06) 0%, transparent 50%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #78a8ff 0%, #c084fc 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
    position: relative;
}
.hero-sub {
    font-size: 1.1rem;
    color: #8899bb;
    letter-spacing: 4px;
    text-transform: uppercase;
    position: relative;
}

/* 섹션 제목 */
.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #a8b8e8;
    padding: 1rem 0 0.5rem 0;
    border-bottom: 2px solid rgba(100, 130, 255, 0.2);
    margin: 2rem 0 1rem 0;
    letter-spacing: 1px;
}

/* 메트릭 카드 */
.metric-card {
    background: linear-gradient(145deg, rgba(30, 40, 80, 0.8), rgba(20, 25, 60, 0.9));
    border: 1px solid rgba(100, 140, 255, 0.2);
    border-radius: 16px;
    padding: 1.8rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
    transition: transform 0.3s, box-shadow 0.3s;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(80, 100, 255, 0.2);
}
.metric-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.metric-value {
    font-size: 2.2rem;
    font-weight: 900;
    margin: 0.3rem 0;
}
.metric-value.warm { color: #f97316; }
.metric-value.hot { color: #ef4444; }
.metric-value.cold { color: #38bdf8; }
.metric-label { font-size: 0.85rem; color: #7788aa; letter-spacing: 2px; text-transform: uppercase; }
.metric-date { font-size: 0.8rem; color: #556688; margin-top: 0.3rem; }

/* 표 스타일 */
.rank-header {
    font-size: 1.1rem;
    font-weight: 700;
    text-align: center;
    padding: 0.8rem;
    border-radius: 12px 12px 0 0;
    margin-bottom: 0;
}
.rank-hot { background: linear-gradient(90deg, rgba(239,68,68,0.2), rgba(249,115,22,0.2)); color: #fca5a5; }
.rank-cold { background: linear-gradient(90deg, rgba(56,189,248,0.2), rgba(99,102,241,0.2)); color: #93c5fd; }

/* Plotly 차트 컨테이너 */
div[data-testid="stPlotlyChart"] {
    background: rgba(15, 18, 40, 0.5);
    border: 1px solid rgba(100, 130, 255, 0.12);
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

/* expander */
div[data-testid="stExpander"] {
    background: rgba(15, 18, 40, 0.5);
    border: 1px solid rgba(100, 130, 255, 0.15);
    border-radius: 12px;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a2e; }
::-webkit-scrollbar-thumb { background: #3a3a7e; border-radius: 3px; }

/* 일반 텍스트 색상 */
.stMarkdown, .stCaption, p, span, label { color: #c0c8e0 !important; }
h1, h2, h3 { color: #a8b8e8 !important; }
</style>
""", unsafe_allow_html=True)

CSV_PATH = "seoul_temperature.csv"

# ========== 공통 Plotly 테마 ==========
_GRID = "rgba(80,100,160,0.15)"
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,12,30,0.6)",
    font=dict(family="Noto Sans KR", color="#a0b0d0"),
    hoverlabel=dict(bgcolor="#1a1a4e", font_color="#e0e8ff", bordercolor="#4a5aaa"),
    margin=dict(l=40, r=40, t=40, b=40),
)

def apply_layout(fig, **extra):
    """PLOTLY_LAYOUT + 축 그리드 + 추가 옵션을 안전하게 적용"""
    fig.update_layout(**PLOTLY_LAYOUT, **extra)
    fig.update_xaxes(gridcolor=_GRID, zerolinecolor=_GRID)
    fig.update_yaxes(gridcolor=_GRID, zerolinecolor=_GRID)


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = None
    for enc in ("utf-8-sig", "cp949"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("CSV 인코딩을 읽을 수 없습니다.")

    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["날짜"]).copy()

    for col in ["평균기온(℃)", "최고기온(℃)", "최저기온(℃)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["평균기온(℃)", "최고기온(℃)", "최저기온(℃)"]).copy()

    df["연도"] = df["날짜"].dt.year
    df["월"] = df["날짜"].dt.month
    df["일교차(℃)"] = df["최고기온(℃)"] - df["최저기온(℃)"]
    return df


@st.cache_data
def make_yearly(df: pd.DataFrame) -> pd.DataFrame:
    yearly = df.groupby("연도", as_index=False).agg(
        연평균기온=("평균기온(℃)", "mean"),
        평균일교차=("일교차(℃)", "mean"),
    )
    full_years = pd.DataFrame({"연도": range(yearly["연도"].min(), yearly["연도"].max() + 1)})
    yearly = full_years.merge(yearly, on="연도", how="left")
    yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5).mean()
    return yearly


# ========== 히어로 배너 ==========
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">서울 기온 변화 대시보드</div>
    <div class="hero-sub">Seoul Temperature Analysis</div>
</div>
""", unsafe_allow_html=True)

try:
    data = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(f"'{CSV_PATH}' 파일을 app.py와 같은 폴더에 넣어주세요.")
    st.stop()

yearly = make_yearly(data)

# ========== 사이드바 ==========
st.sidebar.markdown("## ⚙️ 분석 설정")
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
start, end = st.sidebar.slider("연도 범위", min_value=min_year, max_value=max_year, value=(min_year, max_year))

y_sel = yearly[(yearly["연도"] >= start) & (yearly["연도"] <= end)]
d_sel = data[(data["연도"] >= start) & (data["연도"] <= end)]

st.sidebar.markdown("---")
st.sidebar.download_button(
    "📥 필터 데이터 다운로드",
    data=d_sel.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"seoul_temp_{start}_{end}.csv",
    mime="text/csv",
)
st.sidebar.markdown(f"<br><div style='text-align:center;color:#556;font-size:0.75rem;'>데이터 {min_year}–{max_year} · {len(data):,}건</div>", unsafe_allow_html=True)

# ========== 메트릭 카드 ==========
if not d_sel.empty:
    mean_val = d_sel["평균기온(℃)"].mean()
    max_row = d_sel.loc[d_sel["최고기온(℃)"].idxmax()]
    min_row = d_sel.loc[d_sel["최저기온(℃)"].idxmin()]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🌡️</div>
            <div class="metric-label">구간 평균 기온</div>
            <div class="metric-value warm">{mean_val:.2f}℃</div>
            <div class="metric-date">{start}년 ~ {end}년</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔥</div>
            <div class="metric-label">역대 최고 기온</div>
            <div class="metric-value hot">{max_row['최고기온(℃)']:.1f}℃</div>
            <div class="metric-date">{max_row['날짜']:%Y-%m-%d}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">❄️</div>
            <div class="metric-label">역대 최저 기온</div>
            <div class="metric-value cold">{min_row['최저기온(℃)']:.1f}℃</div>
            <div class="metric-date">{min_row['날짜']:%Y-%m-%d}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("")

# ========== 1. 연평균기온 + 이동평균 + 추세선 ==========
st.markdown('<div class="section-title">📈 연평균기온 추이</div>', unsafe_allow_html=True)

fig1 = go.Figure()
# 범위 채우기 (연평균 ↔ 이동평균 사이, NaN 제거)
_fill = y_sel.dropna(subset=["연평균기온", "5년 이동평균"])
if not _fill.empty:
    fig1.add_trace(go.Scatter(
        x=pd.concat([_fill["연도"], _fill["연도"][::-1]]),
        y=pd.concat([_fill["연평균기온"], _fill["5년 이동평균"][::-1]]),
        fill="toself", fillcolor="rgba(99,130,255,0.06)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
fig1.add_trace(go.Scatter(
    x=y_sel["연도"], y=y_sel["연평균기온"],
    mode="lines+markers", name="연평균기온",
    line=dict(color="#60a5fa", width=2),
    marker=dict(size=4, color="#60a5fa"),
))
fig1.add_trace(go.Scatter(
    x=y_sel["연도"], y=y_sel["5년 이동평균"],
    mode="lines", name="5년 이동평균",
    line=dict(color="#f472b6", width=3),
))

if len(y_sel.dropna(subset=["연평균기온"])) >= 2:
    valid = y_sel.dropna(subset=["연평균기온"])
    z = np.polyfit(valid["연도"], valid["연평균기온"], 1)
    rate = z[0] * 10
    trend_y = np.polyval(z, valid["연도"])
    fig1.add_trace(go.Scatter(
        x=valid["연도"], y=trend_y,
        mode="lines", name=f"추세선 ({rate:+.2f}℃/10년)",
        line=dict(color="#a78bfa", dash="dash", width=2),
    ))

fig1.update_layout(**PLOTLY_LAYOUT, hovermode="x unified",
                    legend=dict(orientation="h", y=1.12, font=dict(color="#a0b0d0")),
                    xaxis_title="연도", yaxis_title="기온 (℃)")
st.plotly_chart(fig1, use_container_width=True)

# ========== 2. 월별 히트맵 ==========
st.markdown('<div class="section-title">🗓️ 월별 평균기온 히트맵</div>', unsafe_allow_html=True)

heatmap_data = (
    d_sel.groupby(["연도", "월"], as_index=False)["평균기온(℃)"]
    .mean()
    .pivot(index="연도", columns="월", values="평균기온(℃)")
)

fig2 = px.imshow(
    heatmap_data,
    labels=dict(x="월", y="연도", color="평균기온(℃)"),
    x=[f"{m}월" for m in range(1, 13)],
    y=heatmap_data.index,
    color_continuous_scale=["#1e3a5f", "#2563eb", "#7dd3fc", "#fde68a", "#f97316", "#dc2626"],
    aspect="auto",
)
fig2.update_layout(**PLOTLY_LAYOUT, yaxis=dict(autorange="reversed", gridcolor="rgba(80,100,160,0.15)"))
fig2.update_coloraxes(colorbar=dict(tickfont=dict(color="#8899bb")))
st.plotly_chart(fig2, use_container_width=True)

# ========== 3. 연도별 평균 일교차 ==========
st.markdown('<div class="section-title">🌤️ 연도별 평균 일교차</div>', unsafe_allow_html=True)

fig3 = go.Figure()
colors = ["#f97316" if v >= y_sel["평균일교차"].quantile(0.75) else
          "#38bdf8" if v <= y_sel["평균일교차"].quantile(0.25) else
          "#a78bfa" for v in y_sel["평균일교차"].fillna(0)]
fig3.add_trace(go.Bar(
    x=y_sel["연도"], y=y_sel["평균일교차"],
    marker_color=colors, name="평균 일교차",
))
fig3.update_layout(**PLOTLY_LAYOUT, xaxis_title="연도", yaxis_title="일교차 (℃)", hovermode="x unified")
st.plotly_chart(fig3, use_container_width=True)

# ========== 4. 최고 TOP 10 / 최저 BOTTOM 10 ==========
st.markdown('<div class="section-title">🏆 극한 기온 기록</div>', unsafe_allow_html=True)

top10 = d_sel.nlargest(10, "최고기온(℃)")[["날짜", "최고기온(℃)", "최저기온(℃)", "일교차(℃)"]].reset_index(drop=True)
top10.index = top10.index + 1
top10["날짜"] = top10["날짜"].dt.strftime("%Y-%m-%d")

bot10 = d_sel.nsmallest(10, "최저기온(℃)")[["날짜", "최고기온(℃)", "최저기온(℃)", "일교차(℃)"]].reset_index(drop=True)
bot10.index = bot10.index + 1
bot10["날짜"] = bot10["날짜"].dt.strftime("%Y-%m-%d")

col_l, col_r = st.columns(2)
with col_l:
    st.markdown('<div class="rank-header rank-hot">🔥 최고기온 TOP 10</div>', unsafe_allow_html=True)
    st.dataframe(top10, use_container_width=True)
with col_r:
    st.markdown('<div class="rank-header rank-cold">❄️ 최저기온 BOTTOM 10</div>', unsafe_allow_html=True)
    st.dataframe(bot10, use_container_width=True)

# ========== 5. 계절별 기온 추이 ==========
st.markdown('<div class="section-title">🍂 계절별 평균기온 추이</div>', unsafe_allow_html=True)

season_map = {12: "겨울", 1: "겨울", 2: "겨울", 3: "봄", 4: "봄", 5: "봄",
              6: "여름", 7: "여름", 8: "여름", 9: "가을", 10: "가을", 11: "가을"}
d_sel = d_sel.copy()
d_sel["계절"] = d_sel["월"].map(season_map)

season_yearly = d_sel.groupby(["연도", "계절"], as_index=False)["평균기온(℃)"].mean()

fig4 = go.Figure()
season_colors = {"봄": "#4ade80", "여름": "#f87171", "가을": "#fb923c", "겨울": "#60a5fa"}
for season in ["봄", "여름", "가을", "겨울"]:
    s = season_yearly[season_yearly["계절"] == season]
    fig4.add_trace(go.Scatter(
        x=s["연도"], y=s["평균기온(℃)"],
        mode="lines", name=season,
        line=dict(color=season_colors[season], width=2.5),
    ))

fig4.update_layout(**PLOTLY_LAYOUT, hovermode="x unified",
                    legend=dict(orientation="h", y=1.12, font=dict(color="#a0b0d0")),
                    xaxis_title="연도", yaxis_title="기온 (℃)")
st.plotly_chart(fig4, use_container_width=True)

# ========== 연도별 데이터 ==========
with st.expander("📋 연도별 데이터 보기"):
    st.dataframe(y_sel.round(2), use_container_width=True, hide_index=True)

# ========== 푸터 ==========
st.markdown("""
<div style="text-align:center; padding:3rem 0 1rem 0; color:#445;">
    <div style="font-size:0.75rem; letter-spacing:3px; text-transform:uppercase; color:#556688;">
        Seoul Temperature Dashboard · Data Visualization
    </div>
</div>
""", unsafe_allow_html=True)
