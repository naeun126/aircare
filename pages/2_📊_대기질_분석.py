import streamlit as st

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

chart_data = {}

for record in data:

    station_name = record.get(
        "stationName",
        "알 수 없는 측정소"
    )

    value = record.get(column)

    try:
        value = float(value)
    except (ValueError, TypeError):
        continue

    chart_data[station_name] = value


if chart_data:

    st.bar_chart(chart_data)

else:

    st.info(
        "그래프로 표시할 유효한 데이터가 없습니다."
    )
