import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="서울 기온 분석", page_icon="🌡️", layout="wide")

CSV_PATH = "seoul_temperature.csv"


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

    # 결측치 처리
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
    yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5).mean()
    return yearly


st.title("🌡️ 서울 연도별 기온 변화")

try:
    data = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(f"'{CSV_PATH}' 파일을 app.py와 같은 폴더에 넣어주세요.")
    st.stop()

yearly = make_yearly(data)

# ========== 사이드바 ==========
st.sidebar.header("설정")
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
start, end = st.sidebar.slider(
    "연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

y_sel = yearly[(yearly["연도"] >= start) & (yearly["연도"] <= end)]
d_sel = data[(data["연도"] >= start) & (data["연도"] <= end)]

# CSV 다운로드 버튼
st.sidebar.download_button(
    "📥 필터 데이터 다운로드",
    data=d_sel.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"seoul_temp_{start}_{end}.csv",
    mime="text/csv",
)

# ========== 1. 연평균기온 + 5년 이동평균 ==========
st.subheader("📈 연평균기온 추이")

fig1 = go.Figure()
fig1.add_trace(
    go.Scatter(
        x=y_sel["연도"], y=y_sel["연평균기온"],
        mode="lines+markers", name="연평균기온",
        line=dict(color="#1f77b4"),
    )
)
fig1.add_trace(
    go.Scatter(
        x=y_sel["연도"], y=y_sel["5년 이동평균"],
        mode="lines", name="5년 이동평균",
        line=dict(color="#d62728", width=3),
    )
)

# 10년 단위 기온 변화율 추세선
if len(y_sel) >= 2:
    import numpy as np
    z = np.polyfit(y_sel["연도"], y_sel["연평균기온"], 1)
    rate_per_decade = z[0] * 10
    trend_y = np.polyval(z, y_sel["연도"])
    fig1.add_trace(
        go.Scatter(
            x=y_sel["연도"], y=trend_y,
            mode="lines", name=f"추세선 ({rate_per_decade:+.2f}℃/10년)",
            line=dict(color="#2ca02c", dash="dash", width=2),
        )
    )

fig1.update_layout(
    xaxis_title="연도", yaxis_title="기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig1, use_container_width=True)

# ========== 기온 요약 카드 ==========
st.subheader(f"📊 {start}년 ~ {end}년 기온 요약")

if d_sel.empty:
    st.warning("선택한 구간에 데이터가 없습니다.")
else:
    mean_val = d_sel["평균기온(℃)"].mean()
    max_row = d_sel.loc[d_sel["최고기온(℃)"].idxmax()]
    min_row = d_sel.loc[d_sel["최저기온(℃)"].idxmin()]

    c1, c2, c3 = st.columns(3)
    c1.metric("평균 기온", f"{mean_val:.2f} ℃")
    c2.metric("최고 기온", f"{max_row['최고기온(℃)']:.1f} ℃",
              help=f"{max_row['날짜']:%Y-%m-%d}")
    c3.metric("최저 기온", f"{min_row['최저기온(℃)']:.1f} ℃",
              help=f"{min_row['날짜']:%Y-%m-%d}")
    st.caption(f"최고: {max_row['날짜']:%Y-%m-%d} / 최저: {min_row['날짜']:%Y-%m-%d}")

# ========== 2. 월별 평균기온 히트맵 ==========
st.subheader("🗓️ 월별 평균기온 히트맵")

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
    color_continuous_scale="RdYlBu_r",
    aspect="auto",
)
fig2.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig2, use_container_width=True)

# ========== 3. 연도별 평균 일교차 ==========
st.subheader("🌤️ 연도별 평균 일교차")

fig3 = go.Figure()
fig3.add_trace(
    go.Bar(
        x=y_sel["연도"], y=y_sel["평균일교차"],
        marker_color="#ff7f0e", name="평균 일교차",
    )
)
fig3.update_layout(
    xaxis_title="연도", yaxis_title="일교차 (℃)",
    hovermode="x unified",
)
st.plotly_chart(fig3, use_container_width=True)

# ========== 4. 최고기온 TOP 10 / 최저기온 BOTTOM 10 ==========
st.subheader("🔥 최고기온 상위 10일 & ❄️ 최저기온 하위 10일")

col_left, col_right = st.columns(2)

top10 = (
    d_sel.nlargest(10, "최고기온(℃)")[["날짜", "최고기온(℃)", "최저기온(℃)", "일교차(℃)"]]
    .reset_index(drop=True)
)
top10.index = top10.index + 1
top10["날짜"] = top10["날짜"].dt.strftime("%Y-%m-%d")

bot10 = (
    d_sel.nsmallest(10, "최저기온(℃)")[["날짜", "최고기온(℃)", "최저기온(℃)", "일교차(℃)"]]
    .reset_index(drop=True)
)
bot10.index = bot10.index + 1
bot10["날짜"] = bot10["날짜"].dt.strftime("%Y-%m-%d")

with col_left:
    st.markdown("**🔥 최고기온 TOP 10**")
    st.dataframe(top10, use_container_width=True)

with col_right:
    st.markdown("**❄️ 최저기온 BOTTOM 10**")
    st.dataframe(bot10, use_container_width=True)

# ========== 5. 계절별 기온 추이 ==========
st.subheader("🍂 계절별 평균기온 추이")

season_map = {12: "겨울", 1: "겨울", 2: "겨울",
              3: "봄", 4: "봄", 5: "봄",
              6: "여름", 7: "여름", 8: "여름",
              9: "가을", 10: "가을", 11: "가을"}
d_sel = d_sel.copy()
d_sel["계절"] = d_sel["월"].map(season_map)

season_yearly = d_sel.groupby(["연도", "계절"], as_index=False)["평균기온(℃)"].mean()

fig4 = px.line(
    season_yearly, x="연도", y="평균기온(℃)", color="계절",
    category_orders={"계절": ["봄", "여름", "가을", "겨울"]},
    color_discrete_map={"봄": "#2ca02c", "여름": "#d62728", "가을": "#ff7f0e", "겨울": "#1f77b4"},
)
fig4.update_layout(hovermode="x unified")
st.plotly_chart(fig4, use_container_width=True)

# ========== 연도별 데이터 테이블 ==========
with st.expander("연도별 데이터 보기"):
    st.dataframe(y_sel.round(2), use_container_width=True, hide_index=True)
