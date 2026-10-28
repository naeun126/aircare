import streamlit as st

from utils.api import get_air_quality_data


# 세션 상태 초기화
if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state["selected_sido"] = "서울"


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
    "제주",
]


# 이전에 선택한 지역 유지
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

        # 조회한 지역 정보를 각 기록에 저장
        for record in data:
            record["_selectedSido"] = sido_name

        st.session_state.air_data = data

        # 센서별 기록 저장
        for record in data:
            station_name = record.get(
                "stationName",
                "알 수 없는 측정소",
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
