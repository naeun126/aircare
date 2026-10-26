
import streamlit as st
from datetime import date, timedelta

from utils.api import get_air_quality_forecast


st.title("🔮 대기질 예측")
st.caption("에어코리아 공식 예보 · 날짜별 전망 및 지역별 등급")

# 1페이지에서 선택한 시도
selected_sido = st.session_state.get("selected_sido", "서울")

st.info(f"📍 선택한 지역: **{selected_sido}**")

inform_code_map = {
    "미세먼지(PM10)": "PM10",
    "초미세먼지(PM2.5)": "PM25",
    "오존(O₃)": "O3",
}

selected_name = st.selectbox(
    "예보 물질",
    list(inform_code_map.keys()),
)
inform_code = inform_code_map[selected_name]

today = date.today()

search_date = st.date_input(
    "예보 발표일",
    value=today,
    min_value=today - timedelta(days=30),
    max_value=today,
)


def clean_text(value, default="정보가 없습니다."):
    if value is None:
        return default

    text = str(value).strip()

    if not text or text == "None":
        return default

    return text


def parse_grades(grade_texts):
    """예보 등급 문자열을 지역명과 등급으로 분리한다."""
    regions = []

    for text in grade_texts:
        for part in text.replace("\n", ",").split(","):
            if ":" not in part:
                continue

            region, grade = part.split(":", 1)
            region = region.strip()
            grade = grade.strip()

            if region and grade:
                pair = (region, grade)

                if pair not in regions:
                    regions.append(pair)

    return regions


def grade_color(grade):
    if "매우 나쁨" in grade:
        return "#D93636"
    if "나쁨" in grade:
        return "#E87524"
    if "보통" in grade:
        return "#B28B00"
    if "좋음" in grade:
        return "#2E9D50"

    return "#64748B"


def normalize_region(region):
    """예보 지역명과 선택한 시도를 비교하기 쉽게 정리한다."""
    region = str(region).strip()

    # 예보에 시·도 이름이 길게 표시되는 경우도 고려
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


if st.button("🔍 공식 예보 조회", type="primary"):
    for key in (
        "official_forecast_items",
        "official_forecast_date",
        "official_forecast_code",
    ):
        st.session_state.pop(key, None)

    try:
        service_key = st.secrets["service_key"]

        with st.spinner("공식 예보를 조회하고 있습니다..."):
            items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=inform_code,
                search_date=search_date.isoformat(),
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

        result_items = sorted(
            merged.values(),
            key=lambda item: item["date"],
        )

        st.session_state["official_forecast_items"] = result_items
        st.session_state["official_forecast_date"] = (
            search_date.isoformat()
        )
        st.session_state["official_forecast_code"] = inform_code

    except KeyError:
        st.error(
            "Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요."
        )
    except (ValueError, ConnectionError) as error:
        st.error(f"예보 조회에 실패했습니다: {error}")
    except Exception as error:
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")


items = st.session_state.get("official_forecast_items", [])
saved_date = st.session_state.get("official_forecast_date")
saved_code = st.session_state.get("official_forecast_code")


if (
    items
    and saved_date == search_date.isoformat()
    and saved_code == inform_code
):
    st.divider()
    st.subheader(f"📋 {selected_name} 예보 결과")

    tabs = st.tabs([item["date"] for item in items])

    for tab, item in zip(tabs, items):
        with tab:
            grades = parse_grades(item["grades"])

            # 선택한 시도에 해당하는 예보를 먼저 찾는다.
            normalized_selected = normalize_region(selected_sido)

            selected_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) == normalized_selected
            ]

            st.caption(
                f"발표 시각: {clean_text(item['time'])}"
            )

            # ========================================
            # 선택 지역 예보를 최상단에 강조 표시
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
                            <div style="font-size:15px;color:#64748b;">
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
            # 나머지 지역 예보
            # ========================================

            st.markdown("### 🗺️ 다른 지역 예보")

            other_grades = [
                (region, grade)
                for region, grade in grades
                if normalize_region(region) != normalized_selected
            ]

            if other_grades:
                for start in range(0, len(other_grades), 3):
                    cols = st.columns(3)

                    for col, (region, grade) in zip(
                        cols,
                        other_grades[start:start + 3],
                    ):
                        color = grade_color(grade)

                        with col:
                            st.markdown(
                                f"""
                                <div style="
                                    border:1px solid #e2e8f0;
                                    border-radius:10px;
                                    padding:12px;
                                    margin-bottom:10px;
                                ">
                                    <div style="
                                        font-size:14px;
                                        color:#64748b;
                                    ">
                                        {region}
                                    </div>
                                    <div style="
                                        color:{color};
                                        font-weight:700;
                                        font-size:18px;
                                        margin-top:5px;
                                    ">
                                        ● {grade}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
            else:
                st.info("표시할 다른 지역 예보가 없습니다.")

            # ========================================
            # 예보 개황 및 발생 원인
            # ========================================

            st.divider()
            st.markdown("### 📝 예보 상세")

            left, right = st.columns(2)

            with left:
                st.markdown("**🌤️ 예보 개황**")

                if item["overall"]:
                    for text in item["overall"]:
                        st.info(text)
                else:
                    st.write("예보 개황 정보가 없습니다.")

            with right:
                st.markdown("**🔎 발생 원인**")

                if item["cause"]:
                    for text in item["cause"]:
                        st.info(text)
                else:
                    st.write("발생 원인 정보가 없습니다.")

            with st.expander("💡 행동 요령 확인"):
                if item["action"]:
                    for text in item["action"]:
                        st.write(text)
                else:
                    st.write(
                        "별도 행동 요령이 제공되지 않았습니다."
                    )

    st.caption(
        "※ 권역별 공식 예보이며, 개별 측정소의 미래 농도 측정값은 아닙니다."
    )

elif (
    saved_date == search_date.isoformat()
    and saved_code == inform_code
):
    st.warning("선택한 발표일에 표시할 예보 자료가 없습니다.")

else:
    st.info(
        "예보 발표일과 물질을 선택한 뒤 공식 예보 조회를 눌러 주세요."
    )
