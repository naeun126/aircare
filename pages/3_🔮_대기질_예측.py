import streamlit as st

from utils.analysis import predict_next_value


st.title("🔮 대기질 예측")

history = st.session_state.history

if not history:
    st.warning(
        "먼저 대기질 데이터를 여러 번 조회하여 "
        "측정 기록을 축적하세요."
    )
    st.stop()


station_names = list(history.keys())

selected_station = st.selectbox(
    "예측할 측정소를 선택하세요.",
    station_names
)


column_map = {
    "PM10": "pm10Value",
    "PM2.5": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value"
}


selected_name = st.selectbox(
    "예측할 대기오염물질을 선택하세요.",
    list(column_map.keys())
)

column = column_map[selected_name]


window_size = st.slider(
    "이동평균에 사용할 최근 데이터 개수",
    min_value=3,
    max_value=10,
    value=3
)


station_history = history[selected_station]


valid_count = 0

for record in station_history:

    value = record.get(column)

    try:
        float(value)
        valid_count += 1

    except (ValueError, TypeError):
        continue


if valid_count < window_size:

    st.warning(
        f"예측하려면 최소 {window_size}개의 "
        f"유효한 측정값이 필요합니다. "
        f"현재 유효한 데이터는 {valid_count}개입니다."
    )

else:

    prediction = predict_next_value(
        station_history,
        column,
        window_size
    )

    if prediction is not None:

        st.subheader(
            f"🔮 {selected_station} 예측 결과"
        )

        st.metric(
            f"다음 {selected_name} 예상값",
            f"{prediction:.2f}"
        )

        st.info(
            f"최근 {window_size}개의 유효한 측정값을 "
            "평균하여 다음 값을 추정했습니다."
        )

        st.write(
            """
            ※ 이 결과는 단순 이동평균을 이용한 예측값이며,
            실제 미래 측정값과 다를 수 있습니다.
            """
        )
