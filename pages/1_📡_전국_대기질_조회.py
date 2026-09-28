import streamlit as st

from utils.api import get_air_quality_data


st.title("📡 전국 대기질 조회")

st.write(
    "한국환경공단 에어코리아의 실시간 대기질 데이터를 조회합니다."
)

# 전국 시도 목록
sido_list = [
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "세종",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주"
]

sido_name = st.selectbox(
    "조회할 지역을 선택하세요.",
    sido_list
)

if st.button("🔄 최신 대기질 데이터 불러오기"):

    try:
        service_key = st.secrets["service_key"]

    except KeyError:
        st.error(
            "Streamlit Secrets에 service_key가 설정되지 않았습니다."
        )
        st.stop()

    try:
        data = get_air_quality_data(
            service_key,
            sido_name
        )

        st.session_state.air_data = data

        # 센서별 기록 저장
        for record in data:

            station_name = record.get(
                "stationName",
                "알 수 없는 측정소"
            )

            if station_name not in st.session_state.history:
                st.session_state.history[station_name] = []

            # 중복 측정값 방지
            data_time = record.get(
                "dataTime",
                ""
            )

            duplicate = False

            for old_record in st.session_state.history[
                station_name
            ]:
                if old_record.get("dataTime") == data_time:
                    duplicate = True
                    break

            if not duplicate:
                st.session_state.history[
                    station_name
                ].append(record)

            # 최근 20개만 유지
            st.session_state.history[
                station_name
            ] = st.session_state.history[
                station_name
            ][-20:]

        st.success(
            f"{sido_name} 지역의 대기질 데이터를 불러왔습니다."
        )

    except ValueError as error:
        st.error(str(error))

    except ConnectionError as error:
        st.error(str(error))

    except Exception as error:
        st.error(
            f"예상하지 못한 오류가 발생했습니다: {error}"
        )


data = st.session_state.air_data

if data:

    st.subheader(
        f"📍 {sido_name} 측정소 목록"
    )

    station_names = []

    for record in data:
        station_name = record.get(
            "stationName",
            "알 수 없는 측정소"
        )

        if station_name not in station_names:
            station_names.append(station_name)

    selected_station = st.selectbox(
        "측정소를 선택하세요.",
        station_names
    )

    selected_record = None

    for record in data:
        if record.get("stationName") == selected_station:
            selected_record = record
            break

    if selected_record:

        st.subheader(
            f"📊 {selected_station} 최신 측정값"
        )

        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

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

        with col4:
            st.metric(
                "이산화질소(NO₂)",
                selected_record.get("no2Value", "-")
            )

        with col5:
            st.metric(
                "일산화탄소(CO)",
                selected_record.get("coValue", "-")
            )

        with col6:
            st.metric(
                "아황산가스(SO₂)",
                selected_record.get("so2Value", "-")
            )

        st.write(
            "측정 시간:",
            selected_record.get("dataTime", "-")
        )

        st.write(
            "측정망:",
            selected_record.get("stationName", "-")
        )

        with st.expander("전체 데이터 보기"):
            st.json(selected_record)

else:

    st.info(
        "먼저 지역을 선택하고 데이터를 불러오세요."
    )
