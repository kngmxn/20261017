import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 분석", page_icon="🌡️", layout="wide")

CSV_PATH = "seoul_temperature.csv"


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    # BOM이 있는 utf-8 → 안 되면 cp949로 재시도
    df = None
    for enc in ("utf-8-sig", "cp949"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        raise ValueError("CSV 인코딩을 읽을 수 없습니다.")

    # 컬럼명 공백/BOM 제거
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    # 날짜 앞의 탭 문자 제거 후 날짜형으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["날짜"]).copy()
    df["연도"] = df["날짜"].dt.year
    return df


@st.cache_data
def make_yearly(df: pd.DataFrame) -> pd.DataFrame:
    yearly = df.groupby("연도", as_index=False)["평균기온(℃)"].mean()
    yearly = yearly.rename(columns={"평균기온(℃)": "연평균기온"})
    # 전체 기간으로 먼저 계산해야 구간 시작 부분도 정확함
    yearly["5년 이동평균"] = yearly["연평균기온"].rolling(window=5).mean()
    return yearly


st.title("🌡️ 서울 연도별 기온 변화")

try:
    data = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(f"'{CSV_PATH}' 파일을 app.py와 같은 폴더에 넣어주세요.")
    st.stop()

yearly = make_yearly(data)

# ---------- 사이드바 ----------
st.sidebar.header("설정")
min_year, max_year = int(yearly["연도"].min()), int(yearly["연도"].max())
start, end = st.sidebar.slider(
    "연도 범위",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

# ---------- 선택 구간 필터 ----------
y_sel = yearly[(yearly["연도"] >= start) & (yearly["연도"] <= end)]
d_sel = data[(data["연도"] >= start) & (data["연도"] <= end)]

# ---------- 그래프 ----------
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=y_sel["연도"],
        y=y_sel["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#1f77b4"),
    )
)
fig.add_trace(
    go.Scatter(
        x=y_sel["연도"],
        y=y_sel["5년 이동평균"],
        mode="lines",
        name="5년 이동평균",
        line=dict(color="#d62728", width=3),
    )
)
fig.update_layout(
    xaxis_title="연도",
    yaxis_title="기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", y=1.1),
)
st.plotly_chart(fig, use_container_width=True)

# ---------- 통계 ----------
st.subheader(f"{start}년 ~ {end}년 기온 요약")

if d_sel.empty:
    st.warning("선택한 구간에 데이터가 없습니다.")
else:
    mean_val = d_sel["평균기온(℃)"].mean()
    max_row = d_sel.loc[d_sel["최고기온(℃)"].idxmax()]
    min_row = d_sel.loc[d_sel["최저기온(℃)"].idxmin()]

    c1, c2, c3 = st.columns(3)
    c1.metric("평균 기온", f"{mean_val:.2f} ℃")
    c2.metric(
        "최고 기온",
        f"{max_row['최고기온(℃)']:.1f} ℃",
        help=f"{max_row['날짜']:%Y-%m-%d}",
    )
    c3.metric(
        "최저 기온",
        f"{min_row['최저기온(℃)']:.1f} ℃",
        help=f"{min_row['날짜']:%Y-%m-%d}",
    )
    st.caption(
        f"최고: {max_row['날짜']:%Y-%m-%d} / 최저: {min_row['날짜']:%Y-%m-%d}"
    )

with st.expander("연도별 데이터 보기"):
    st.dataframe(y_sel.round(2), use_container_width=True, hide_index=True)
