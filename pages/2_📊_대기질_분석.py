
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


st.title("📊 대기질 분석")

data = st.session_state.air_data

if not data:
    st.warning(
        "먼저 '전국 대기질 조회' 페이지에서 데이터를 불러오세요."
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
    st.metric(
        "평균",
        f"{average:.2f}" if average is not None else "-",
    )

with col2:
    st.metric(
        "최대값",
        f"{maximum:.2f}" if maximum is not None else "-",
    )

with col3:
    st.metric(
        "최소값",
        f"{minimum:.2f}" if minimum is not None else "-",
    )

with col4:
    st.metric("변화", trend)

st.divider()

st.subheader(f"📈 측정소별 {selected_name} 비교")


# ========================================
# 측정소별 미세먼지 지도
# ========================================

st.divider()
st.subheader("🗺️ 측정소별 미세먼지 농도 지도")

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


# ========================================
# 에어코리아 측정소 좌표 조회
# ========================================

try:
    service_key = st.secrets["service_key"]

    station_coordinates = get_station_coordinates(
        service_key
    )

except KeyError:
    st.error(
        "서비스 키를 찾을 수 없어. "
        ".streamlit/secrets.toml에 service_key가 있는지 확인해 줘."
    )
    st.stop()

except RuntimeError as e:
    st.error(f"측정소 좌표 조회 실패: {e}")
    st.stop()


st.caption(
    f"측정소 좌표 {len(station_coordinates)}개를 조회했어."
)


# ========================================
# 농도별 지도 데이터 생성
# ========================================

map_points = []

for record in data:
    station = str(
        record.get("stationName") or ""
    ).strip()

    raw_value = record.get(map_column)

    # 좌표가 없는 측정소는 제외
    if station not in station_coordinates:
        continue

    try:
        value = float(raw_value)
    except (ValueError, TypeError):
        continue

    # 측정값이 없거나 유효하지 않은 경우 제외
    if not pd.notna(value) or value < 0:
        continue

    lat, lon = station_coordinates[station]

    # 참고용 농도 구간
    if map_pollutant == "PM10":
        limits = (30, 80, 150)
    else:
        limits = (15, 35, 75)

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
        "등급": grade,
        "위도": lat,
        "경도": lon,
        "색상": color,
    })


# ========================================
# PyDeck 지도 출력
# ========================================

if map_points:
    map_df = pd.DataFrame(map_points)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[경도, 위도]",
        get_fill_color="색상",
        get_radius=700,
        radius_min_pixels=7,
        radius_max_pixels=20,
        pickable=True,
        opacity=0.85,
    )

    view = pdk.ViewState(
        latitude=float(map_df["위도"].mean()),
        longitude=float(map_df["경도"].mean()),
        zoom=8,
        pitch=0,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={
            "html": (
                "<b>측정소:</b> {측정소}<br/>"
                "<b>농도:</b> {농도}<br/>"
                "<b>상태:</b> {등급}"
            ),
            "style": {
                "backgroundColor": "white",
                "color": "black",
            },
        },
        map_style=None,
    )

    st.pydeck_chart(
        deck,
        use_container_width=True,
    )

    st.caption(
        "점에 마우스를 올리면 측정소 이름과 농도를 확인할 수 있어."
    )

    # 지도에 실제로 표시된 측정소 목록
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
        "지도에 표시할 측정소가 없어. "
        "측정소 이름과 좌표 조회 결과가 일치하는지 확인해 줘."
    )

st.caption(
    "색상 구간은 참고용이며, 공식 대기질 등급과 다를 수 있어. "
    "조회된 좌표와 농도 데이터가 있는 측정소만 표시돼."
)
