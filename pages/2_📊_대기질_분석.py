import pandas as pd
import pydeck as pdk
import streamlit as st

# 세션 상태 초기화
if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}


from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    calculate_trend
)


st.title("📊 대기질 분석")

data = st.session_state.air_data

if not data:
    st.warning(
        "먼저 '전국 대기질 조회' 페이지에서 데이터를 불러오세요."
    )
    st.stop()


column_map = {
    "PM10": "pm10Value",
    "PM2.5": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value"
}

selected_name = st.selectbox(
    "분석할 대기오염물질을 선택하세요.",
    list(column_map.keys())
)

column = column_map[selected_name]


average = calculate_average(
    data,
    column
)

maximum = calculate_max(
    data,
    column
)

minimum = calculate_min(
    data,
    column
)

trend = calculate_trend(
    data,
    column
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    if average is not None:
        st.metric(
            "평균",
            f"{average:.2f}"
        )
    else:
        st.metric("평균", "-")

with col2:
    if maximum is not None:
        st.metric(
            "최대값",
            f"{maximum:.2f}"
        )
    else:
        st.metric("최대값", "-")

with col3:
    if minimum is not None:
        st.metric(
            "최소값",
            f"{minimum:.2f}"
        )
    else:
        st.metric("최소값", "-")

with col4:
    st.metric(
        "변화",
        trend
    )


st.divider()

st.subheader(
    f"📈 측정소별 {selected_name} 비교"
)


# ========================================
# 측정소별 미세먼지 지도
# ========================================

st.divider()
st.subheader("🗺️ 측정소별 미세먼지 농도 지도")

map_pollutant = st.radio(
    "지도에 표시할 미세먼지",
    ["PM10", "PM2.5"],
    horizontal=True,
    key="map_pollutant"
)

map_column = (
    "pm10Value"
    if map_pollutant == "PM10"
    else "pm25Value"
)

# 측정소 이름별 위도, 경도
# 아래는 좌표 등록 방법을 보여 주는 예시야.
# 실제 측정소의 정확한 좌표로 교체해야 해.
station_coordinates = {
    "중구": (37.564, 126.997),
    "종로구": (37.572, 126.979),
    "강남구": (37.517, 127.047),
    "마포구": (37.566, 126.901),
}

map_points = []

for record in data:
    station = record.get("stationName", "")
    raw_value = record.get(map_column)

    # 좌표가 등록된 측정소만 지도에 표시
    if station not in station_coordinates:
        continue

    try:
        value = float(raw_value)
    except (ValueError, TypeError):
        continue

    if value < 0:
        continue

    lat, lon = station_coordinates[station]

    # PM10과 PM2.5의 등급 기준을 각각 적용
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
        "색상": color
    })

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
        latitude=map_df["위도"].mean(),
        longitude=map_df["경도"].mean(),
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

    st.pydeck_chart(deck, use_container_width=True)

    st.caption(
        "점에 마우스를 올리면 측정소와 농도를 확인할 수 있어."
    )
else:
    st.info(
        "지도에 표시할 측정소가 없어. "
        "station_coordinates에 실제 측정소 좌표를 등록해 줘."
    )

st.caption(
    "색상은 참고용 등급 기준이야. "
    "정확한 좌표가 등록된 측정소만 표시돼."
)



# ========================================
# 시간에 따른 미세먼지 농도 변화
# ========================================

st.divider()
st.subheader("📈 시간에 따른 미세먼지 농도 변화")

history = st.session_state.get("history", {})

if history:
    available_stations = sorted(history.keys())

    trend_station = st.selectbox(
        "분석할 측정소",
        available_stations,
        key="analysis_trend_station"
    )

    trend_pollutant = st.radio(
        "분석할 물질",
        ["PM10", "PM2.5"],
        horizontal=True,
        key="analysis_trend_pollutant"
    )

    trend_column = (
        "pm10Value"
        if trend_pollutant == "PM10"
        else "pm25Value"
    )

    trend_records = []

    for record in history.get(trend_station, []):
        time_value = record.get("dataTime")
        raw_value = record.get(trend_column)

        try:
            value = float(raw_value)
        except (ValueError, TypeError):
            continue

        if not time_value or value < 0:
            continue

        trend_records.append({
            "측정 시각": time_value,
            "농도": value
        })

    # 시간순 정렬 후 동일 시각의 중복 기록 제거
    unique_records = {
        item["측정 시각"]: item
        for item in trend_records
    }

    trend_records = sorted(
        unique_records.values(),
        key=lambda item: item["측정 시각"]
    )

    if len(trend_records) >= 2:
        trend_df = pd.DataFrame(trend_records)

        st.line_chart(
            trend_df,
            x="측정 시각",
            y="농도",
            x_label="측정 시각",
            y_label=f"{trend_pollutant} 농도",
            use_container_width=True
        )

        st.caption(
            f"총 {len(trend_records)}개의 시간별 기록을 표시하고 있어."
        )
    elif len(trend_records) == 1:
        st.info(
            "저장된 기록이 1개야. "
            "첫 번째 페이지에서 시간을 두고 다시 조회하면 "
            "변화를 비교할 수 있어."
        )
    else:
        st.info("그래프로 표시할 유효한 측정값이 없어.")
else:
    st.info(
        "저장된 측정 기록이 없어. "
        "첫 번째 페이지에서 먼저 대기질 데이터를 조회해 줘."
    )
