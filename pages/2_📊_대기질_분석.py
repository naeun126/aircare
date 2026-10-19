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

# -------------------------
# 1. 측정소별 농도 비교
# -------------------------

st.divider()
st.subheader(f"📊 측정소별 {selected_name} 농도 비교")

chart_data = []

for record in data:
    station_name = record.get(
        "stationName",
        "알 수 없는 측정소"
    )

    value = record.get(column)

    try:
        number = float(value)

        if number >= 0:
            chart_data.append({
                "측정소": station_name,
                "농도": number
            })

    except (ValueError, TypeError):
        continue

# 농도가 높은 측정소부터 정렬
chart_data.sort(
    key=lambda item: item["농도"],
    reverse=True
)

if chart_data:
    st.caption("농도가 높은 측정소부터 표시합니다.")

    st.bar_chart(
        chart_data,
        x="농도",
        y="측정소",
        horizontal=True
    )
else:
    st.info("그래프로 표시할 유효한 데이터가 없습니다.")


# -------------------------
# 2. 시간에 따른 미세먼지 변화
# -------------------------

st.divider()
st.subheader("⏱️ 시간에 따른 미세먼지 변화")

history = st.session_state.get("history", {})

if history:
    trend_station = st.selectbox(
        "변화를 확인할 측정소",
        list(history.keys()),
        key="trend_station"
    )

    trend_pollutant = st.radio(
        "미세먼지 종류",
        ["PM10", "PM2.5"],
        horizontal=True,
        key="trend_pollutant"
    )

    trend_column = (
        "pm10Value"
        if trend_pollutant == "PM10"
        else "pm25Value"
    )

    # 저장된 기록에서 시간과 농도를 추출
    trend_points = []

    for record in history[trend_station]:
        time_value = record.get("dataTime")
        raw_value = record.get(trend_column)

        try:
            number = float(raw_value)

            if time_value and number >= 0:
                trend_points.append({
                    "시간": time_value,
                    trend_pollutant: number
                })

        except (ValueError, TypeError):
            continue

    # 시간순 정렬 및 중복 시간 제거
    unique_points = {}

    for point in trend_points:
        unique_points[point["시간"]] = point

    trend_points = [
        unique_points[time]
        for time in sorted(unique_points)
    ]

    if len(trend_points) < 2:
        st.info(
            "선그래프를 표시하려면 서로 다른 시간의 "
            "유효한 측정 기록이 최소 2개 필요합니다. "
            "첫 번째 페이지에서 시간을 두고 데이터를 "
            "다시 조회해 주세요."
        )

    else:
        st.caption(
            "저장된 측정 기록을 시간순으로 표시합니다."
        )

        # 자동 애니메이션을 켜거나 끄는 기능
        animate = st.toggle(
            "선그래프 자동 움직임",
            value=True,
            key="animate_trend"
        )

        if animate:
            @st.fragment(run_every="1s")
            def animated_trend_chart():
                animation_key = (
                    f"trend_index_{trend_station}_{trend_column}"
                )

                if animation_key not in st.session_state:
                    st.session_state[animation_key] = 0

                st.session_state[animation_key] += 1

                index = st.session_state[animation_key]

                # 저장된 기록을 앞에서부터 순차적으로 표시
                visible_count = (
                    2 + ((index - 1) % (len(trend_points) - 1))
                )

                visible_points = trend_points[:visible_count]

                chart_data = {
                    "시간": [
                        point["시간"]
                        for point in visible_points
                    ],
                    trend_pollutant: [
                        point[trend_pollutant]
                        for point in visible_points
                    ]
                }

                st.line_chart(
                    chart_data,
                    x="시간",
                    y=trend_pollutant
                )

                st.caption(
                    f"표시 중: {visible_count}개 측정 기록"
                )

            animated_trend_chart()

        else:
            chart_data = {
                "시간": [
                    point["시간"]
                    for point in trend_points
                ],
                trend_pollutant: [
                    point[trend_pollutant]
                    for point in trend_points
                ]
            }

            st.line_chart(
                chart_data,
                x="시간",
                y=trend_pollutant
            )

        st.caption(
            "※ 애니메이션은 이미 저장된 측정 기록을 "
            "순차적으로 보여 줍니다. 새로운 대기질 데이터를 "
            "자동으로 수집하는 기능은 아닙니다."
        )

else:
    st.info(
        "아직 저장된 측정 기록이 없습니다. "
        "첫 번째 페이지에서 대기질 데이터를 조회해 주세요."
    )
