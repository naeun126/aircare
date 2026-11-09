import streamlit as st

# utils/api.py: 에어코리아 API에서 시도별 실시간 측정값을 가져오는 함수
from utils.api import get_air_quality_data
# utils/grade.py: 등급 색상, 등급 순서, 물질별 기준값, 등급 판정 함수
from utils.grade import GRADE_COLORS, GRADE_LEVELS, GRADE_LIMITS, get_grade


# ---------------------------------------------------------
# 1. 세션 상태 초기화
#    session_state는 페이지를 옮겨 다녀도 값이 유지되는 저장 공간이다.
#    2~4페이지가 이 값을 가져다 쓰므로 먼저 빈 값을 만들어 둔다.
# ---------------------------------------------------------

# 조회한 측정소별 최신 데이터(리스트)를 저장한다.
if "air_data" not in st.session_state:
    st.session_state.air_data = []

# 측정소별 과거 측정값 기록(딕셔너리)을 저장한다. 변화 추이 분석에 사용한다.
if "history" not in st.session_state:
    st.session_state.history = {}


st.title("📡 전국 대기질 조회")

st.write(
    "한국환경공단 에어코리아의 실시간 대기질 데이터를 조회합니다."
)

# ---------------------------------------------------------
# 2. 지역 선택
# ---------------------------------------------------------

# 에어코리아 API가 사용하는 전국 17개 시도 이름 목록
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


# 처음 접속했을 때만 기본 지역을 서울로 정한다.
# 이미 값이 있으면 덮어쓰지 않으므로, 다른 페이지에 다녀와도 선택이 유지된다.
if "selected_sido" not in st.session_state:
    st.session_state["selected_sido"] = "서울"

# key를 "selected_sido"로 지정하면 선택값이 session_state에 자동 저장된다.
# 그래서 2~4페이지에서도 st.session_state["selected_sido"]로 같은 값을 읽을 수 있다.
sido_name = st.selectbox(
    "조회할 지역을 선택하세요.",
    sido_list,
    key="selected_sido",
)


# ---------------------------------------------------------
# 3. 데이터 불러오기 (버튼을 눌렀을 때만 실행)
# ---------------------------------------------------------

if st.button("🔄 최신 대기질 데이터 불러오기"):

    # [예외 처리 1] API 인증키 확인
    # 키는 코드에 직접 적지 않고 Streamlit Secrets에 따로 보관한다.
    try:
        service_key = st.secrets["service_key"]

    except KeyError:
        # 키가 없으면 안내 메시지를 보여 주고 st.stop()으로 이후 코드 실행을 멈춘다.
        st.error(
            "Streamlit Secrets에 service_key가 설정되지 않았습니다."
        )
        st.stop()

    # [예외 처리 2] API 호출과 데이터 저장
    try:
        # 선택한 시도의 측정소별 실시간 측정값을 받아 온다.
        data = get_air_quality_data(service_key, sido_name)

        # 각 측정소 데이터에 "어느 지역을 조회한 결과인지"를 함께 기록한다.
        for record in data:
            record["_selectedSido"] = sido_name

        # 최신 데이터와 조회 지역을 저장한다.
        # 2~4페이지는 air_data_sido를 읽어 현재 조회한 지역을 표시한다.
        st.session_state.air_data = data
        st.session_state.air_data_sido = sido_name

        # 측정소별 기록 저장 (변화 추이용)
        for record in data:
            station_name = record.get(
                "stationName",
                "알 수 없는 측정소"
            )

            # 처음 보는 측정소이면 빈 기록 리스트를 만든다.
            if station_name not in st.session_state.history:
                st.session_state.history[station_name] = []

            # 같은 측정 시각의 값이 이미 있으면 다시 저장하지 않는다.
            # 버튼을 여러 번 눌러도 같은 데이터가 중복되지 않게 하기 위해서다.
            data_time = record.get("dataTime", "")

            duplicate = False

            for old_record in st.session_state.history[station_name]:
                if old_record.get("dataTime") == data_time:
                    duplicate = True
                    break

            if not duplicate:
                st.session_state.history[station_name].append(record)

            # 기록이 너무 길어지지 않도록 최근 20개만 남긴다.
            st.session_state.history[station_name] = (
                st.session_state.history[station_name][-20:]
            )

        st.success(
            f"{sido_name} 지역의 대기질 데이터를 불러왔습니다."
        )

    # 지역 이름 오류, 빈 응답 등 잘못된 값 처리
    except ValueError as error:
        st.error(str(error))

    # 네트워크 연결 실패, API 서버 오류 처리
    except ConnectionError as error:
        st.error(str(error))

    # 위에서 예상하지 못한 나머지 오류 처리 (앱이 멈추지 않도록 한다)
    except Exception as error:
        st.error(
            f"예상하지 못한 오류가 발생했습니다: {error}"
        )


# ---------------------------------------------------------
# 4. 물질별 상태를 색상 박스로 보여 주는 함수
# ---------------------------------------------------------

def show_pollutant_status(name, value, limits):
    """물질 이름, 측정값, 등급 기준을 받아 등급별 색상 박스를 표시한다."""

    # 측정값과 기준값으로 등급(좋음~매우 나쁨)을 판정한다.
    grade = get_grade(value, limits)

    # 측정값이 없거나 "-" 같은 잘못된 값이면 등급이 None이므로 안내만 하고 끝낸다.
    if grade is None:
        st.info(f"{name}: 측정값 없음 또는 유효하지 않은 값")
        return

    # 등급에 맞는 배경색의 박스를 HTML로 그린다.
    # float(value):g 는 "35.0"을 "35"처럼 불필요한 소수점 없이 보여 준다.
    st.markdown(
        f"""
        <div style="
            background-color: {GRADE_COLORS[grade]};
            color: white;
            padding: 12px;
            border-radius: 10px;
            margin: 5px 0 12px 0;
        ">
            <b>{name}</b><br>
            농도: {float(value):g}<br>
            상태: {grade}
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# 5. 조회한 데이터 화면에 표시
# ---------------------------------------------------------

# 저장된 데이터를 꺼낸다. 아직 불러오지 않았으면 빈 리스트이므로 아래 블록은 건너뛴다.
data = st.session_state.air_data

if data:

    st.subheader(
        f"📍 {sido_name} 측정소 목록"
    )

    # 측정소 이름 목록 만들기 (중복 제거)
    station_names = []

    for record in data:
        station_name = record.get(
            "stationName",
            "알 수 없는 측정소"
        )

        if station_name not in station_names:
            station_names.append(station_name)

    # 선택하기 편하도록 가나다순으로 정렬한다.
    station_names = sorted(station_names)

    # 사용자가 볼 측정소를 고른다.
    selected_station = st.selectbox(
        "측정소를 선택하세요.",
        station_names
    )

    # 고른 측정소의 데이터를 data에서 찾는다.
    selected_record = None

    for record in data:
        if record.get("stationName") == selected_station:
            selected_record = record
            break

    if selected_record:

        # -------------------------------------------------
        # 5-1. 현재 대기질 요약 (PM10, PM2.5 기준)
        # -------------------------------------------------
        st.subheader("🌏 현재 대기질 요약")

        # API가 문자열로 주는 측정값을 꺼낸다. 값이 없으면 None이 된다.
        pm10 = selected_record.get("pm10Value")
        pm25 = selected_record.get("pm25Value")

        # 물질별 기준값(GRADE_LIMITS)으로 각각의 등급을 판정한다.
        pm10_grade = get_grade(pm10, GRADE_LIMITS["PM10"])
        pm25_grade = get_grade(pm25, GRADE_LIMITS["PM2.5"])

        # 등급을 판정할 수 있었던 것(None이 아닌 것)만 모은다.
        known_grades = [
            g for g in (pm10_grade, pm25_grade) if g is not None
        ]

        if known_grades:
            # 두 물질 중 더 나쁜 등급을 전체 등급으로 사용한다.
            # GRADE_LEVELS.index는 등급의 순서 번호(좋음=0 ... 매우 나쁨=3)이다.
            grade = max(known_grades, key=GRADE_LEVELS.index)
            color = GRADE_COLORS[grade]

            # 등급별 안내 문구
            if grade == "좋음":
                message = "현재 미세먼지 농도가 낮은 상태입니다."
            elif grade == "보통":
                message = "현재 미세먼지 농도를 계속 확인하세요."
            elif grade == "나쁨":
                message = "실외 대기질을 확인하고 야외활동에 유의하세요."
            else:
                # 매우 나쁨
                message = (
                    "실외 대기질을 확인하고 장시간 야외활동을 "
                    "줄이는 것을 고려하세요."
                )

            # 요약 카드: 등급 색상 배경에 등급과 안내 문구를 크게 보여 준다.
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
            # 두 물질 모두 값이 없으면 등급을 만들 수 없다.
            st.info("미세먼지 측정값이 없어 상태를 표시할 수 없습니다.")

        # PM10과 PM2.5의 등급 박스를 나란히 보여 준다.
        status_col1, status_col2 = st.columns(2)

        with status_col1:
            show_pollutant_status(
                "PM10", pm10, GRADE_LIMITS["PM10"]
            )

        with status_col2:
            show_pollutant_status(
                "PM2.5", pm25, GRADE_LIMITS["PM2.5"]
            )

        # -------------------------------------------------
        # 5-2. 최신 측정값 6종 (3개씩 두 줄)
        # -------------------------------------------------
        st.subheader(
            f"📊 {selected_station} 최신 측정값"
        )

        # 위 줄 3칸, 아래 줄 3칸
        col1, col2, col3 = st.columns(3)
        col4, col5, col6 = st.columns(3)

        # st.metric(이름, 값): 숫자를 크게 보여 주는 요소.
        # 값이 없는 항목은 "-"로 표시한다.
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
