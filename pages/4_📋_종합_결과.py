import streamlit as st

from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    predict_next_value
)


st.title("📋 종합 결과")

data = st.session_state.air_data
history = st.session_state.history


if not data:
    st.warning(
        "먼저 전국 대기질 데이터를 불러오세요."
    )
    st.stop()


station_names = []

for record in data:

    station_name = record.get(
        "stationName",
        "알 수 없는 측정소"
    )

    if station_name not in station_names:
        station_names.append(station_name)


selected_station = st.selectbox(
    "종합 결과를 확인할 측정소를 선택하세요.",
    station_names
)


selected_record = None

for record in data:

    if record.get("stationName") == selected_station:
        selected_record = record
        break


if selected_record:

    st.subheader(
        f"📍 {selected_station}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "PM10",
            selected_record.get("pm10Value", "-")
        )

    with col2:
        st.metric(
            "PM2.5",
            selected_record.get("pm25Value", "-")
        )

    with col3:
        st.metric(
            "오존(O₃)",
            selected_record.get("o3Value", "-")
        )


st.divider()

st.subheader("📊 전체 측정소 분석")

for name, column in [
    ("PM10", "pm10Value"),
    ("PM2.5", "pm25Value"),
    ("오존(O₃)", "o3Value")
]:

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

    st.write(f"### {name}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(
            f"평균: {average:.2f}"
            if average is not None
            else "평균: -"
        )

    with col2:
        st.write(
            f"최대: {maximum:.2f}"
            if maximum is not None
            else "최대: -"
        )

    with col3:
        st.write(
            f"최소: {minimum:.2f}"
            if minimum is not None
            else "최소: -"
        )


st.divider()

st.subheader("🔮 간단한 미래값 예측")

station_history = history.get(
    selected_station,
    []
)

for name, column in [
    ("PM10", "pm10Value"),
    ("PM2.5", "pm25Value")
]:

    prediction = predict_next_value(
        station_history,
        column,
        3
    )

    if prediction is not None:

        st.write(
            f"**{name} 예상값:** {prediction:.2f}"
        )

    else:

        st.write(
            f"**{name} 예상값:** 데이터 부족"
        )


st.divider()

st.info(
    """
    AirCare는 공공데이터를 활용하여 전국의 대기질을 조회하고,
    측정소별 데이터를 분석한 뒤 최근 측정값을 이용해
    간단한 미래값을 예측하는 프로그램입니다.
    """
)
