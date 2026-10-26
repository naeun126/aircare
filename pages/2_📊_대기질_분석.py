
import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    calculate_trend,
)
from utils.stations import get_station_coordinates


# ========================================
# 세션 상태 초기화
# ========================================

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"


st.title("📊 대기질 분석")

# 1페이지에서 선택한 지역
selected_sido = st.session_state.selected_sido

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")

# 조회 데이터 중 선택한 시도의 데이터만 사용
all_data = st.session_state.air_data

data = [
    record
    for record in all_data
    if str(record.get("sidoName") or "").strip() == selected_sido
]

# API 응답에 sidoName이 없을 때는 기존 데이터 전체를 사용하지 않고 안내
if all_data and not any(record.get("sidoName") for record in all_data):
    st.warning(
        "현재 측정 데이터에 시도 정보가 없어 지역별 필터링을 할 수 없습니다. "
        "1페이지에서 선택한 지역을 다시 조회해 주세요."
    )
    st.stop()

if not data:
    st.warning(
        f"{selected_sido} 지역의 데이터가 없습니다. "
        "1페이지에서 해당 지역을 선택한 뒤 데이터를 다시 불러오세요."
    )
    st.stop()


# ========================================
# 대기오염물질 분석
# ========================================

column_map = {
    "PM10": "pm10Value",
    "PM2.5": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value",
}

selected_name = st.selectbox(
    "분석할 대기오염물질을 선택하세요.",
    list(column_map.keys()),
)

column = column_map[selected_name]

average = calculate_average(data, column)
maximum = calculate_max(data, column)
minimum = calculate_min(data, column)
trend = calculate_trend(data, column)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("평균", f"{average:.2f}" if average is not None else "-")

with col2:
    st.metric("최대값", f"{maximum:.2f}" if maximum is not None else "-")

with col3:
    st.metric("최소값", f"{minimum:.2f}" if minimum is not None else "-")

with col4:
    st.metric("변화", trend)


# ========================================
# 측정소별 농도 비교 그래프
# ========================================

st.divider()
st.subheader(f"📈 {selected_sido} 측정소별 {selected_name} 비교")

comparison_points = []

for record in data:
    station = str(record.get("stationName") or "").strip()
    raw_value = record.get(column)

    try:
        value = float(raw_value)
    except (ValueError, TypeError):
        continue

    if not station or not pd.notna(value) or value < 0:
        continue

    comparison_points.append({
        "측정소": station,
        "농도": value,
    })

if comparison_points:
    comparison_df = pd.DataFrame(comparison_points)

    comparison_df = (
        comparison_df
        .groupby("측정소", as_index=False)["농도"]
        .mean()
        .sort_values("농도", ascending=False)
    )

    st.bar_chart(
        comparison_df,
        x="측정소",
        y="농도",
        height=400,
        use_container_width=True,
    )
else:
    st.info("비교할 수 있는 측정소별 농도 데이터가 없습니다.")


# ========================================
# 측정소별 미세먼지 지도
# ========================================

st.divider()
st.subheader(f"🗺️ {selected_sido} 측정소별 미세먼지 지도")

map_pollutant = st.radio(
    "지도에 표시할 미세먼지",
    ["PM10", "PM2.5"],
    horizontal=True,
    key="map_pollutant",
)

map_column = (
    "pm10Value"
    if map_pollutant == "PM10"
    else "pm25Value"
)

try:
    station_coordinates = get_station_coordinates()
except (RuntimeError, OSError, ValueError) as e:
    st.error(f"측정소 좌표 조회 실패: {e}")
    st.stop()

st.caption(f"전국 측정소 좌표 {len(station_coordinates)}개를 불러왔습니다.")

map_points = []

if map_pollutant == "PM10":
    limits = (30, 80, 150)
else:
    limits = (15, 35, 75)

for record in data:
    station = str(record.get("stationName") or "").strip()
    raw_value = record.get(map_column)

    if station not in station_coordinates:
        continue

    try:
        value = float(raw_value)
    except (ValueError, TypeError):
        continue

    if not pd.notna(value) or value < 0:
        continue

    lat, lon = station_coordinates[station]

    if value <= limits[0]:
        color = [46, 157, 80]
        grade = "좋음"
    elif value <= limits[1]:
        color = [229, 185, 0]
        grade = "보통"
    elif value <= limits[2]:
        color = [232, 117, 36]
        grade = "나쁨"
    else:
        color = [217, 54, 54]
        grade = "매우 나쁨"

    map_points.append({
        "측정소": station,
        "농도": value,
        "표시값": f"{value:g}",
        "등급": grade,
        "위도": lat,
        "경도": lon,
        "색상": color,
    })


# ========================================
# 지도 출력
# ========================================

if map_points:
    map_df = pd.DataFrame(map_points)

    circle_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_fill_color="색상",
        get_radius=1000,
        radius_min_pixels=13,
        radius_max_pixels=24,
        pickable=True,
        opacity=0.9,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_text="표시값",
        get_size=13,
        get_color=[20, 20, 20, 255],
        get_text_anchor="'middle'",
        get_alignment_baseline="'center'",
        get_pixel_offset=[0, 0],
        billboard=True,
        pickable=True,
    )

    view = pdk.ViewState(
        latitude=float(map_df["위도"].mean()),
        longitude=float(map_df["경도"].mean()),
        zoom=8,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[circle_layer, text_layer],
        initial_view_state=view,
        tooltip={
            "html": (
                "<b>측정소:</b> {측정소}<br/>"
                f"<b>{map_pollutant}:</b> {{농도}}<br/>"
                "<b>참고 등급:</b> {등급}"
            ),
            "style": {
                "backgroundColor": "white",
                "color": "black",
            },
        },
        map_style=None,
    )

    st.pydeck_chart(deck, use_container_width=True)

    st.caption(
        f"원 안의 숫자는 {map_pollutant} 농도입니다. "
        "원에 마우스를 올리면 측정소와 참고 등급을 확인할 수 있습니다."
    )

    with st.expander("지도에 표시된 측정소 확인"):
        display_df = map_df[
            ["측정소", "농도", "등급"]
        ].rename(
            columns={
                "측정소": "측정소 이름",
                "농도": f"{map_pollutant} 농도",
                "등급": "참고 등급",
            }
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
else:
    st.warning(
        f"{selected_sido} 지역에서 지도에 표시할 측정소가 없습니다. "
        "측정소 이름과 좌표를 확인해 주세요."
    )

st.caption(
    "색상 구간은 참고용이며 공식 대기질 등급과 다를 수 있습니다."
)
