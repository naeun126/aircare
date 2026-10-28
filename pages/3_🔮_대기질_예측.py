
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from utils.api import get_air_quality_forecast

st.set_page_config(page_title="대기질 예측", page_icon="🔮", layout="wide")

INFORM_CODES = {
    "미세먼지(PM10)": "PM10",
    "초미세먼지(PM2.5)": "PM25",
    "오존(O₃)": "O3",
}

REGION_ALIASES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원도": "강원",
    "강원특별자치도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전라북도": "전북",
    "전북특별자치도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}

GRADE_COLORS = {
    "좋음": "#2E8B57",
    "보통": "#D6A000",
    "나쁨": "#E87522",
    "매우 나쁨": "#C62828",
}


def normalize_region(region):
    """예보 지역명과 선택한 시도를 비교하기 쉽게 정리한다."""
    region = str(region or "").strip()
    return REGION_ALIASES.get(region, region)


def clean_text(value):
    """HTML 태그와 불필요한 공백을 제거한다."""
    text = str(value or "")
    text = re.sub(r"<[^>]*>", " ", text)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value):
    """예보 날짜 문자열에서 날짜를 추출한다."""
    text = clean_text(value)

    # 예: 2026년 10월 28일
    match = re.search(
        r"(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일",
        text,
    )
    if match:
        try:
            return date(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
        except ValueError:
            return None

    # 예: 2026-10-28 또는 2026.10.28
    match = re.search(
        r"(\d{4})[-./]\s*(\d{1,2})[-./]\s*(\d{1,2})",
        text,
    )
    if match:
        try:
            return date(
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
        except ValueError:
            return None

    return None


def parse_grades(value):
    """
    예보의 지역별 등급 문자열을 지역명과 등급으로 나눈다.
    예: 서울 : 좋음, 경기 : 보통
    """
    text = clean_text(value)
    result = {}

    for part in re.split(r"[,;]\s*", text):
        if ":" not in part:
            continue

        region, grade = part.split(":", 1)
        region = normalize_region(region)
        grade = grade.strip()

        if region and grade:
            result[region] = grade

    return result


def grade_color(grade):
    return GRADE_COLORS.get(grade, "#607D8B")


def get_korea_today():
    """서버 시간대와 관계없이 한국 날짜를 사용한다."""
    try:
        return datetime.now(ZoneInfo("Asia/Seoul")).date()
    except Exception:
        return date.today()


def merge_forecast_items(items):
    """같은 예보 날짜에 해당하는 여러 항목을 하나로 정리한다."""
    merged = {}

    for item in items:
        if not isinstance(item, dict):
            continue

        forecast_date_text = clean_text(item.get("informData", ""))
        forecast_date = parse_date(forecast_date_text)

        key = forecast_date.isoformat() if forecast_date else forecast_date_text

        if key not in merged:
            merged[key] = {
                "date": forecast_date,
                "date_text": forecast_date_text,
                "grades": {},
                "overall": [],
                "cause": [],
                "action": [],
                "time": [],
            }

        target = merged[key]

        grades = parse_grades(item.get("informGrade", ""))
        target["grades"].update(grades)

        for field, source_field in [
            ("overall", "informOverall"),
            ("cause", "informCause"),
            ("action", "actionKnack"),
            ("time", "dataTime"),
        ]:
            value = clean_text(item.get(source_field, ""))
            if value and value not in target[field]:
                target[field].append(value)

    return list(merged.values())


def display_text_list(values):
    if not values:
        st.write("제공된 정보가 없습니다.")
        return

    for value in values:
        st.write(value)


st.title("🔮 공식 대기질 예보")
st.write(
    "에어코리아 공공데이터 API의 예보 자료를 조회하고, "
    "선택한 지역의 예보 등급을 확인합니다."
)

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"

selected_sido = normalize_region(st.session_state.selected_sido)

col1, col2 = st.columns(2)

with col1:
    pollutant_label = st.selectbox(
        "예보 항목",
        list(INFORM_CODES.keys()),
    )

with col2:
    search_date = st.date_input(
        "예보 발표일",
        value=get_korea_today(),
        help="API에 전달할 발표 자료의 조회 날짜입니다.",
    )

target_date = search_date + timedelta(days=1)

st.caption(
    f"발표 자료 조회일: {search_date.isoformat()} · "
    f"확인할 예보 대상일: {target_date.isoformat()}"
)

if st.button("🔍 공식 예보 조회", type="primary"):
    try:
        service_key = st.secrets["service_key"]
    except (KeyError, FileNotFoundError):
        st.error(
            "Streamlit Secrets에 service_key가 설정되지 않았습니다. "
            "API 인증키 설정을 확인하세요."
        )
        st.stop()

    try:
        with st.spinner("공식 예보 자료를 조회하는 중입니다..."):
            raw_items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=INFORM_CODES[pollutant_label],
                search_date=search_date.isoformat(),
            )

        merged_items = merge_forecast_items(raw_items)

        # 예보 대상일이 정확히 일치하는 자료를 우선 선택한다.
        matching_items = [
            item
            for item in merged_items
            if item["date"] == target_date
        ]

        st.session_state.official_forecast_items = matching_items
        st.session_state.official_forecast_raw = raw_items
        st.session_state.official_forecast_date = target_date.isoformat()
        st.session_state.official_forecast_search_date = search_date.isoformat()
        st.session_state.official_forecast_code = INFORM_CODES[pollutant_label]
        st.session_state.official_forecast_label = pollutant_label
        st.session_state.official_forecast_region = selected_sido

        if matching_items:
            st.success(f"{target_date.isoformat()} 예보 자료를 찾았습니다.")
        else:
            st.warning(
                f"{target_date.isoformat()}에 해당하는 예보를 찾지 못했습니다. "
                "발표일을 바꾸거나 다른 예보 항목을 선택해 보세요."
            )

    except Exception as error:
        st.error(f"공식 예보를 불러오지 못했습니다: {error}")


# 조회 결과가 현재 화면의 조건과 맞을 때만 표시한다.
forecast_items = st.session_state.get("official_forecast_items", [])
stored_date = st.session_state.get("official_forecast_date")
stored_code = st.session_state.get("official_forecast_code")
stored_region = st.session_state.get("official_forecast_region")

if forecast_items:
    if (
        stored_date != target_date.isoformat()
        or stored_code != INFORM_CODES[pollutant_label]
        or stored_region != selected_sido
    ):
        st.info("선택 조건이 바뀌었습니다. 최신 조건으로 예보를 다시 조회하세요.")
        st.stop()

    st.divider()
    st.subheader(f"📅 {target_date.isoformat()} 예보")
    st.write(f"항목: {pollutant_label}")
    st.write(f"지역: {selected_sido}")

    # 날짜별 예보 항목 중 선택 지역의 등급이 있는 항목을 우선 표시한다.
    matching_region = [
        item
        for item in forecast_items
        if selected_sido in item["grades"]
    ]

    if matching_region:
        for item in matching_region:
            grade = item["grades"].get(selected_sido, "정보 없음")
            st.markdown(
                f"""
                <div style="
                    padding: 18px;
                    border-radius: 10px;
                    background-color: {grade_color(grade)};
                    color: white;
                    margin-bottom: 12px;
                ">
                    <div style="font-size: 16px;">{selected_sido} · {pollutant_label}</div>
                    <div style="font-size: 28px; font-weight: bold;">{grade}</div>
                    <div style="font-size: 13px;">예보 대상일: {target_date.isoformat()}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("#### 전체 예보")
            display_text_list(item["overall"])

            st.markdown("#### 예보 원인")
            display_text_list(item["cause"])

            st.markdown("#### 대응 요령")
            display_text_list(item["action"])

            if item["time"]:
                st.caption("자료 시각: " + " / ".join(item["time"]))

    else:
        st.warning(
            f"공식 예보 자료는 조회했지만 '{selected_sido}' 지역의 등급을 "
            "문자열에서 확인하지 못했습니다. 아래 전체 예보 내용을 확인하세요."
        )

        for item in forecast_items:
            st.markdown("#### 전체 예보")
            display_text_list(item["overall"])

            st.markdown("#### 예보 원인")
            display_text_list(item["cause"])

            st.markdown("#### 대응 요령")
            display_text_list(item["action"])

    # 다른 지역의 등급도 비교할 수 있도록 표시한다.
    all_grades = {}
    for item in forecast_items:
        all_grades.update(item["grades"])

    if all_grades:
        st.subheader("🗺️ 지역별 예보 등급")
        grade_rows = [
            {"지역": region, "예보 등급": grade}
            for region, grade in sorted(all_grades.items())
        ]
        st.dataframe(
            grade_rows,
            use_container_width=True,
            hide_index=True,
        )

elif st.session_state.get("official_forecast_search_date") is not None:
    st.info(
        "저장된 조회 결과에 표시할 대상 날짜의 예보가 없습니다. "
        "발표일이나 예보 항목을 바꾸어 다시 조회해 보세요."
    )
else:
    st.info("위에서 발표일과 예보 항목을 선택한 뒤 공식 예보를 조회하세요.")
