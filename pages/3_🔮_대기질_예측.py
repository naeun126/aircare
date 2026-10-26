
import streamlit as st
from datetime import date, timedelta

from utils.api import get_air_quality_forecast


st.title("🔮 대기질 예측")
st.caption("에어코리아 공식 예보 · 날짜별 전망 및 지역별 등급")

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

        # 예보 대상 날짜별로 자료 정리
        # 동일 날짜에 여러 권역 자료가 있으면 등급을 합쳐 표시
        merged = {}

        for item in items:
            forecast_date = str(
                item.get("informData") or "날짜 정보 없음"
            ).strip()

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
            key=lambda x: x["date"],
        )

        st.session_state["official_forecast_items"] = result_items
        st.session_state["official_forecast_date"] = search_date.isoformat()
        st.session_state["official_forecast_code"] = inform_code

    except KeyError:
        st.error("Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요.")
    except (ValueError, ConnectionError) as error:
        st.error(f"예보 조회에 실패했습니다: {error}")
    except Exception as error:
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")


items = st.session_state.get("official_forecast_items", [])
saved_date = st.session_state.get("official_forecast_date")
saved_code = st.session_state.get("official_forecast_code")


def clean_text(value, default="정보가 없습니다."):
    if value is None:
        return default
    text = str(value).strip()
    if not text or text == "None":
        return default
    return text


def parse_grades(grade_texts):
    """'서울 : 좋음,부산 : 보통' 형식의 지역별 등급을 분리한다."""
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

            # 전체 예보 요약
            st.caption(
                f"발표 시각: {clean_text(item['time'])}"
            )

            if grades:
                counts = {}
                for _, grade in grades:
                    counts[grade] = counts.get(grade, 0) + 1

                # 가장 많이 나타나는 등급을 대표 등급으로 표시
                main_grade = max(
                    counts,
                    key=counts.get,
                )

                color = grade_color(main_grade)

                st.markdown(
                    f"""
                    <div style="
                        background: {color}15;
                        border-left: 6px solid {color};
                        padding: 18px;
                        border-radius: 10px;
                        margin: 8px 0 18px 0;
                    ">
                        <div style="font-size:14px;color:#64748b;">
                            지역별 예보 요약
                        </div>
                        <div style="
                            font-size:28px;
                            font-weight:700;
                            color:{color};
                            margin:5px 0;
                        ">
                            {main_grade}
                        </div>
                        <div>
                            전체 {len(grades)}개 지역의 등급을 확인하세요.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("#### 🗺️ 지역별 예보 등급")

                # 지역별 등급을 3열 카드로 표시
                for start in range(0, len(grades), 3):
                    cols = st.columns(3)

                    for col, (region, grade) in zip(
                        cols,
                        grades[start:start + 3],
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
                st.info("지역별 예보 등급을 확인할 수 없습니다.")

            # 전망과 원인을 별도 영역으로 분리
            st.markdown("#### 📝 예보 상세")

            left, right = st.columns(2)

            with left:
                st.markdown("**🌤️ 예보 개황**")
                for text in item["overall"]:
                    st.info(text)

                if not item["overall"]:
                    st.write("예보 개황 정보가 없습니다.")

            with right:
                st.markdown("**🔎 발생 원인**")
                for text in item["cause"]:
                    st.info(text)

                if not item["cause"]:
                    st.write("발생 원인 정보가 없습니다.")

            with st.expander("💡 행동 요령 확인"):
                if item["action"]:
                    for text in item["action"]:
                        st.write(text)
                else:
                    st.write(
                        "별도 행동 요령이 제공되지 않았습니다. "
                        "예보 등급에 맞는 일반적인 대기질 대응 수칙을 확인하세요."
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
    st.info("예보 발표일과 물질을 선택한 뒤 공식 예보를 조회하세요.")
