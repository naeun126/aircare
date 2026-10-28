import streamlit as st

from utils.api import get_air_quality_data


# 세션 상태 초기화
if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}


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


# 이전에 선택한 지역 유지
if "selected_sido" not in st.session_state:
    st.session_state["selected_sido"] = "서울"

sido_name = st.selectbox(
    "조회할 지역을 선택하세요.",
    sido_list,
    key="selected_sido",
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
        data = get_air_quality_data(service_key, sido_name)

        # 조회한 데이터에 선택 지역을 기록
        for record in data:
            record["_selectedSido"] = sido_name

        st.session_state.air_data = data
        st.session_state.air_data_sido = sido_name
        
        # 센서별 기록 저장
        for record in data:
            station_name = record.get(
                "stationName",
                "알 수 없는 측정소"
            )

            if station_name not in st.session_state.history:
                st.session_state.history[station_name] = []

            # 중복 측정값 방지
            data_time = record.get("dataTime", "")

            duplicate = False

            for old_record in st.session_state.history[station_name]:
                if old_record.get("dataTime") == data_time:
                    duplicate = True
                    break

            if not duplicate:
                st.session_state.history[station_name].append(record)

            # 최근 20개만 유지
            st.session_state.history[station_name] = (
                st.session_state.history[station_name][-20:]
            )

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

# 미세먼지 농도에 따른 색상 표시
def show_pollutant_status(name, value, limits):

    try:
        value = float(value)
    except (ValueError, TypeError):
        st.info(f"{name}: 측정값 없음")
        return

    if value < 0:
        st.info(f"{name}: 유효하지 않은 측정값")
        return

    if value <= limits[0]:
        color = "#2E9D50"
        status = "좋음"

    elif value <= limits[1]:
        color = "#E5B900"
        status = "보통"

    elif value <= limits[2]:
        color = "#E87524"
        status = "나쁨"

    else:
        color = "#D93636"
        status = "매우 나쁨"

    st.markdown(
        f"""
        <div style="
            background-color: {color};
            color: white;
            padding: 12px;
            border-radius: 10px;
            margin: 5px 0 12px 0;
        ">
            <b>{name}</b><br>
            농도: {value:g}<br>
            상태: {status}
        </div>
        """,
        unsafe_allow_html=True
    )
    
data = st.session_state.air_data

if data:

    st.subheader(
        f"📍 {sido_name} 측정소 목록"
    )

    st.write("선택한 지역:", repr(sido_name))

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

        # 현재 대기질 요약
        st.subheader("🌏 현재 대기질 요약")

        pm10 = selected_record.get("pm10Value")
        pm25 = selected_record.get("pm25Value")

        def get_pm_status(value, limits):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return None

            if value < 0:
                return None
            elif value <= limits[0]:
                return (0, "좋음", "#2E9D50")
            elif value <= limits[1]:
                return (1, "보통", "#E5B900")
            elif value <= limits[2]:
                return (2, "나쁨", "#E87524")
            else:
                return (3, "매우 나쁨", "#D93636")

        pm10_status = get_pm_status(pm10, (30, 80, 150))
        pm25_status = get_pm_status(pm25, (15, 35, 75))

        statuses = [
            status for status in [pm10_status, pm25_status]
            if status is not None
        ]

        if statuses:
            overall = max(statuses, key=lambda item: item[0])
            grade = overall[1]
            color = overall[2]

            if grade == "좋음":
                message = "현재 미세먼지 농도가 낮은 상태입니다."
            elif grade == "보통":
                message = "현재 미세먼지 농도를 계속 확인하세요."
            elif grade == "나쁨":
                message = "실외 대기질을 확인하고 야외활동에 유의하세요."
            else:
                message = (
                    "실외 대기질을 확인하고 장시간 야외활동을 "
                    "줄이는 것을 고려하세요."
                )

            st.markdown(
                f"""
                <div style="
                    background-color: {color};
                    color: white;
                    padding: 22px;
                    border-radius: 15px;
                    margin-bottom: 15px;
                ">
                    <div style="font-size: 14px;">
                        AIRCARE · 미세먼지 참고 등급
                    </div>
                    <div style="
                        font-size: 32px;
                        font-weight: bold;
                        margin: 8px 0;
                    ">
                        {grade}
                    </div>
                    <div>{message}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.info("미세먼지 측정값이 없어 상태를 표시할 수 없습니다.")

        status_col1, status_col2 = st.columns(2)

        with status_col1:
            show_pollutant_status(
                "PM10", pm10, (30, 80, 150)
            )

        with status_col2:
            show_pollutant_status(
                "PM2.5", pm25, (15, 35, 75)
            )

        # 기존 측정값 표시 코드는 아래에 그대로 유지
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

       
