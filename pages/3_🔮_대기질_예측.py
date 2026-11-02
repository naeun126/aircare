
import re
import streamlit as st

from datetime import date, timedelta
from utils.api import get_air_quality_forecast


# ========================================
# 1. 페이지 기본 설정
# ========================================

st.title("🔮 대기질 예측")

st.write(
    "에어코리아의 공식 대기질 예보를 조회합니다."
)

# 1페이지에서 선택한 지역 가져오기
selected_sido = st.session_state.get(
    "selected_sido",
    "서울"
)

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")


# ========================================
# 2. 예보 대기오염물질 선택
# ========================================

pollutant_options = {
    "PM10": "PM10",
    "PM2.5": "PM25",
}

selected_name = st.selectbox(
    "예보할 대기오염물질을 선택하세요.",
    list(pollutant_options.keys()),
)

inform_code = pollutant_options[selected_name]


# ========================================
# 3. 날짜 설정
# ========================================

today = date.today()
tomorrow = today + timedelta(days=1)

search_date = today.isoformat()
target_date = tomorrow.isoformat()


# ========================================
# 4. 데이터 정리 함수
# ========================================

def clean_text(value, default="정보 없음"):
    if value is None or str(value).strip() in ("", "None"):
        return default

    return str(value).strip()


def date_key(value):
    """예보 날짜를 YYYY-MM-DD 형식으로 변환한다."""

    value = str(value).strip()

    match = re.search(
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        value,
    )

    if match:
        year, month, day = match.groups()

        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    match = re.search(
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        value,
    )

    if match:
        year, month, day = match.groups()

        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    return ""


def parse_grades(grade_list):
    """지역별 예보 문자열을 지역과 등급으로 분리한다."""

    results = []

    for text in grade_list:
        if not text:
            continue

        text = str(text)

        text = (
            text.replace("<br>", ",")
            .replace("<br/>", ",")
            .replace("<br />", ",")
        )

        for part in re.split(r"[,;\n]", text):

            if ":" not in part:
                continue

            region, grade = part.split(":", 1)

            region = region.strip()
            grade = grade.strip()

            if region and grade:
                results.append((region, grade))

    return results


def grade_color(grade):
    """예보 등급에 따른 색상을 반환한다."""

    grade = str(grade).strip()

    if "매우나쁨" in grade or "매우 나쁨" in grade:
        return "#D93636"

    elif "나쁨" in grade:
        return "#E87524"

    elif "보통" in grade:
        return "#E5B900"

    elif "좋음" in grade:
        return "#2E9D50"

    return "#64748B"


def normalize_region(region):
    """예보 지역명과 선택한 시도명을 비교하기 쉽게 정리한다."""

    region = str(region).strip()

    aliases = {
        "충청북도": "충북",
        "충청남도": "충남",
        "전라북도": "전북",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
        "강원특별자치도": "강원",
        "제주특별자치도": "제주",
        "경기도": "경기",
        "서울특별시": "서울",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
    }

    return aliases.get(region, region)


# ========================================
# 5. 공식 예보 API 조회
# ========================================

query_key = f"{search_date}_{inform_code}"

if st.session_state.get("official_forecast_query_key") != query_key:

    for key in (
        "official_forecast_items",
        "official_forecast_date",
        "official_forecast_code",
        "official_forecast_query_key",
    ):
        st.session_state.pop(key, None)

    try:
        service_key = st.secrets["service_key"]

        with st.spinner("공식 예보를 조회하고 있습니다..."):

            items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=inform_code,
                search_date=search_date,
            )

        # 예보 대상 날짜별로 내용 통합
        merged = {}

        for item in items:

            forecast_date = clean_text(
                item.get("informData"),
                "날짜 정보 없음",
            )

            if forecast_date not in merged:

                merged[forecast_date] = {
                    "date": forecast_date,
                    "time": item.get("dataTime"),
                    "grades": [],
                    "overall": [],
                    "cause": [],
                    "action": [],
                }

            row = merged[forecast_date]

            for field, target in [
                ("informGrade", "grades"),
                ("informOverall", "overall"),
                ("informCause", "cause"),
                ("actionKnack", "action"),
            ]:

                value = item.get(field)

                if value and str(value).strip() not in ("", "None"):

                    text = str(value).strip()

                    if text not in row[target]:
                        row[target].append(text)

            if item.get("dataTime"):
                row["time"] = item["dataTime"]

        # 내일 날짜에 해당하는 예보만 선택
        result_items = [
            item
            for item in merged.values()
            if date_key(item["date"]) == target_date
        ]

        result_items.sort(
            key=lambda item: item["date"]
        )

        st.session_state["official_forecast_items"] = result_items
        st.session_state["official_forecast_date"] = search_date
        st.session_state["official_forecast_code"] = inform_code
        st.session_state["official_forecast_query_key"] = query_key

    except KeyError:

        st.error(
            "Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요."
        )

    except (ValueError, ConnectionError) as error:

        st.error(
            f"예보 조회에 실패했습니다: {error}"
        )

    except Exception as error:

        st.error(
            f"예상하지 못한 오류가 발생했습니다: {error}"
        )


# ========================================
# 6. 예보 결과 가져오기
# ========================================

forecast_items = st.session_state.get(
    "official_forecast_items",
    []
)

saved_date = st.session_state.get(
    "official_forecast_date"
)

saved_code = st.session_state.get(
    "official_forecast_code"
)


# ========================================
# 7. 예보 결과 화면 출력
# ========================================

if (
    forecast_items
    and saved_date == search_date
    and saved_code == inform_code
):

    st.divider()

    st.subheader(
        f"📋 {tomorrow:%Y년 %m월 %d일} {selected_name} 예보"
    )

    tabs = st.tabs(
        [item["date"] for item in forecast_items]
    )

    for tab, item in zip(tabs, forecast_items):

        with tab:

            grades = parse_grades(item["grades"])

            normalized_selected = normalize_region(
                selected_sido
            )

            selected_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) == normalized_selected
            ]

            st.caption(
                f"발표 시각: {clean_text(item['time'])}"
            )

            # ========================================
            # 선택 지역 예보
            # ========================================

            st.markdown("### 📍 선택 지역 예보")

            if selected_grades:

                for region, grade in selected_grades:

                    color = grade_color(grade)

                    st.markdown(
                        f"""
                        <div style="
                            background:{color}15;
                            border-left:7px solid {color};
                            border-radius:12px;
                            padding:22px;
                            margin:8px 0 20px 0;
                        ">
                            <div style="
                                font-size:15px;
                                color:#64748b;
                            ">
                                {region} · {selected_name}
                            </div>

                            <div style="
                                font-size:32px;
                                font-weight:700;
                                color:{color};
                                margin:8px 0;
                            ">
                                {grade}
                            </div>

                            <div style="font-size:14px;">
                                에어코리아 공식 권역별 예보
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.warning(
                    f"선택한 지역인 '{selected_sido}'의 등급을 "
                    "예보 자료에서 찾지 못했습니다. "
                    "아래 지역별 예보를 확인해 주세요."
                )

            # ========================================
            # 다른 지역 예보
            # ========================================

            st.markdown("### 🗺️ 다른 지역 예보")

            other_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) != normalized_selected
            ]

            if other_grades:

                # 지역 이름 가나다순 정렬
                other_grades.sort(
                    key=lambda item: item[0]
                )

                # 두 개씩 나누어 화면에 표시
                for i in range(0, len(other_grades), 2):

                    cols = st.columns(2)

                    for col, (region, grade) in zip(
                        cols,
                        other_grades[i:i + 2]
                    ):

                        color = grade_color(grade)

                        with col:

                            st.markdown(
                                f"""
                                <div style="
                                    background:{color}15;
                                    border-left:5px solid {color};
                                    border-radius:10px;
                                    padding:15px;
                                    margin:5px 0;
                                ">
                                    <b>{region}</b>

                                    <div style="
                                        color:{color};
                                        font-size:22px;
                                        font-weight:bold;
                                    ">
                                        {grade}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

            else:

                st.info(
                    "표시할 다른 지역 예보가 없습니다."
                )

            # ========================================
            # 예보 종합 정보
            # ========================================

            st.divider()

            st.markdown("### 📢 예보 종합 정보")

            if item["overall"]:

                for text in item["overall"]:
                    st.write(text)

            if item["cause"]:

                st.markdown("**주요 발생 원인**")

                for text in item["cause"]:
                    st.write(text)

            if item["action"]:

                st.markdown("**대응 요령**")

                for text in item["action"]:
                    st.write(text)


else:

    st.warning(
        f"{tomorrow:%Y년 %m월 %d일}의 {selected_name} 예보를 "
        "현재 조회한 자료에서 찾지 못했습니다. "
        "예보 발표 여부를 확인해 주세요."
    )
