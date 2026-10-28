
import pandas as pd
import pydeck as pdk
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="대기질 분석", page_icon="📊", layout="wide")

POLLUTANTS = {
    "미세먼지(PM10)": "pm10Value",
    "초미세먼지(PM2.5)": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value",
}


def to_number(value):
    try:
        if value is None or str(value).strip() in ("", "-", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_record_sido(record):
    value = record.get("_selectedSido")
    if value is None or not str(value).strip():
        value = record.get("sidoName")
    return str(value or "").strip()


def find_column(df, candidates):
    """CSV에서 후보 열 이름 중 실제로 존재하는 열을 찾는다."""
    normalized = {
        str(column).strip().lower().replace(" ", ""): column
        for column in df.columns
    }
    for candidate in candidates:
        key = candidate.strip().lower().replace(" ", "")
        if key in normalized:
            return normalized[key]
    return None


def load_station_coordinates():
    """측정소 좌표 CSV를 읽고 위도·경도 열을 표준화한다."""
    possible_paths = [
        Path("data/station_coordinates.csv"),
        Path(__file__).resolve().parents[1] / "data" / "station_coordinates.csv",
    ]

    csv_path = next((path for path in possible_paths if path.exists()), None)
    if csv_path is None:
        return pd.DataFrame()

    try:
        coordinates = pd.read_csv(csv_path)
    except Exception as error:
        st.warning(f"측정소 좌표 파일을 읽지 못했습니다: {error}")
        return pd.DataFrame()

    station_col = find_column(
        coordinates,
        ["stationName", "station_name", "측정소", "측정소명", "name"],
    )
    lat_col = find_column(
        coordinates,
        ["lat", "latitude", "위도", "y"],
    )
    lon_col = find_column(
        coordinates,
        ["lon", "lng", "longitude", "경도", "x"],
    )

    if not station_col or not lat_col or not lon_col:
        st.warning(
            "좌표 CSV에서 측정소명·위도·경도 열을 찾지 못했습니다. "
            "data/station_coordinates.csv의 열 이름을 확인하세요."
        )
        return pd.DataFrame()

    result = coordinates[[station_col, lat_col, lon_col]].copy()
    result.columns = ["stationName", "lat", "lon"]
    result["stationName"] = result["stationName"].astype(str).str.strip()
    result["lat"] = pd.to_numeric(result["lat"], errors="coerce")
    result["lon"] = pd.to_numeric(result["lon"], errors="coerce")
    result = result.dropna(subset=["lat", "lon"])
    return result


st.title("📊 대기질 분석")
st.write("측정소별 오염물질 농도를 비교하고 측정소 위치를 지도에서 확인합니다.")

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"

data = st.session_state.air_data
selected_sido = st.session_state.selected_sido

if not data:
    st.info("먼저 '전국 대기질 조회' 페이지에서 데이터를 불러오세요.")
    st.stop()

# 선택한 시도와 일치하는 자료만 분석한다.
records_with_region = [
    record for record in data if get_record_sido(record)
]

if records_with_region:
    filtered_data = [
        record
        for record in data
        if get_record_sido(record) == selected_sido
    ]
    if not filtered_data:
        st.warning(
            f"현재 저장된 자료는 '{selected_sido}' 지역 자료가 아닙니다. "
            "전국 대기질 조회 페이지에서 해당 지역을 선택한 뒤 데이터를 다시 불러오세요."
        )
        st.stop()
else:
    filtered_data = data
    st.info(
        "자료에 지역 정보가 없어 저장된 자료 전체를 분석합니다. "
        "정확한 지역별 분석을 위해 조회 페이지에서 데이터를 새로 불러오세요."
    )

st.subheader(f"📍 분석 지역: {selected_sido}")

pollutant_label = st.selectbox(
    "분석할 오염물질을 선택하세요.",
    list(POLLUTANTS.keys()),
)
pollutant_column = POLLUTANTS[pollutant_label]

rows = []
for record in filtered_data:
    value = to_number(record.get(pollutant_column))
    if value is None:
        continue

    rows.append({
        "측정소": record.get("stationName", "알 수 없는 측정소"),
        "농도": value,
        "측정 시각": record.get("dataTime", "-"),
    })

if not rows:
    st.warning(f"{pollutant_label}의 유효한 측정값이 없습니다.")
    st.stop()

df = pd.DataFrame(rows)

average_value = df["농도"].mean()
max_value = df["농도"].max()
min_value = df["농도"].min()
max_station = df.loc[df["농도"].idxmax(), "측정소"]
min_station = df.loc[df["농도"].idxmin(), "측정소"]

col1, col2, col3 = st.columns(3)
col1.metric("평균 농도", f"{average_value:.2f}")
col2.metric("최고 농도", f"{max_value:.2f}", help=f"측정소: {max_station}")
col3.metric("최저 농도", f"{min_value:.2f}", help=f"측정소: {min_station}")

st.caption(
    f"분석 대상: {len(df)}개 측정소 · "
    f"단위는 선택한 오염물질의 원자료 단위를 따릅니다."
)

st.subheader("📊 측정소별 농도 비교")

station_df = (
    df.groupby("측정소", as_index=False)["농도"]
    .mean()
    .sort_values("농도", ascending=False)
)

st.bar_chart(
    station_df.set_index("측정소"),
    y="농도",
)

with st.expander("측정소별 수치 표 보기"):
    st.dataframe(
        station_df,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("🗺️ 측정소 위치와 농도")

coordinates = load_station_coordinates()

if coordinates.empty:
    st.info(
        "지도에 표시할 좌표를 찾지 못했습니다. "
        "data/station_coordinates.csv에 측정소명, 위도, 경도 정보가 있는지 확인하세요."
    )
else:
    map_df = station_df.merge(coordinates, on="측정소", how="left")
    map_df = map_df.dropna(subset=["lat", "lon"]).copy()

    if map_df.empty:
        st.info(
            "측정소 이름과 좌표 파일의 측정소명이 일치하지 않아 "
            "지도에 표시할 위치를 찾지 못했습니다."
        )
    else:
        # 농도에 따라 원의 크기를 조정한다.
        map_df["radius"] = map_df["농도"].apply(
            lambda value: max(80, min(value * 20, 1500))
        )

        max_value = max(float(map_df["농도"].max()), 1.0)
        map_df["color"] = map_df["농도"].apply(
            lambda value: [
                220,
                max(40, int(180 * (1 - value / max_value))),
                40,
                180,
            ]
        )

        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[lon, lat]",
            get_radius="radius",
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            latitude=float(map_df["lat"].mean()),
            longitude=float(map_df["lon"].mean()),
            zoom=7,
            pitch=0,
        )

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "html": (
                    "<b>측정소:</b> {측정소}<br/>"
                    f"<b>{pollutant_label}:</b> " + "{농도}"
                ),
                "style": {"backgroundColor": "steelblue", "color": "white"},
            },
        )

        st.pydeck_chart(deck, use_container_width=True)

        st.caption(
            "원의 크기와 색은 선택한 오염물질의 측정 농도를 시각적으로 비교하기 위한 표현입니다."
        )

        st.dataframe(
            map_df[["측정소", "농도", "lat", "lon"]],
            use_container_width=True,
            hide_index=True,
        )

st.subheader("📈 측정값 분포")

col1, col2 = st.columns(2)

with col1:
    st.write("**농도 구간별 측정소 수**")
    histogram = (
        df.assign(구간=pd.cut(df["농도"], bins=5, duplicates="drop"))
        .groupby("구간", observed=False)
        .size()
        .rename("측정소 수")
    )
    st.bar_chart(histogram)

with col2:
    st.write("**측정 자료 요약**")
    st.dataframe(
        df["농도"].describe()
        .rename_axis("통계")
        .reset_index(name="값"),
        use_container_width=True,
        hide_index=True,
    )
