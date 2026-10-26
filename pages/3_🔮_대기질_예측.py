
import streamlit as st
from datetime import date, timedelta, datetime

from utils.api import get_air_quality_forecast


st.title("🔮 대기질 예측")

st.write(
    "에어코리아 공식 예보 자료를 바탕으로 "
    "날짜별 대기질 전망과 대응 방법을 확인합니다."
)

inform_code_map = {
    "미세먼지(PM10)": "PM10",
    "초미세먼지(PM2.5)": "PM25",
    "오존(O₃)": "O3",
}

selected_name = st.selectbox(
    "예보 물질을 선택하세요.",
    list(inform_code_map.keys()),
)

inform_code = inform_code_map[selected_name]

today = date.today()

search_date = st.date_input(
    "예보 발표일을 선택하세요.",
    value=today,
    min_value=today - timedelta(days=30),
    max_value=today,
)


def display_text(value, default="정보가 없습니다."):
    """None이나 빈 문자열을 사용자 친화적인 문구로 바꾼다."""
    if value is None or not str(value).strip() or str(value).strip() == "None":
        return default
    return str(value).strip()


def parse_announcement_time(value):
    """발표 시각을 정렬할 수 있는 값으로 변환한다."""
    value = display_text(value, "")

    for fmt in ("%Y-%-%d %H시 발표", "%Y-%m-%d %H시 발표"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    # 날짜 형식이 다르거나 알 수 없으면 가장 오래된 값으로 처리
    return datetime.min


if st.button("🔍 공식 예보 조회", type="primary"):
    st.session_state.pop("official_forecast_items", None)
    st.session_state.pop("official_forecast_date", None)
    st.session_state.pop("official_forecast_code", None)

    try:
        service_key = st.secrets["service_key"]

        with st.spinner("공식 예보 자료를 조회하고 있습니다..."):
            items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=inform_code,
                search_date=search_date.isoformat(),
            )

        # 예보 대상 날짜별로 최신 발표 자료만 남긴다.
        latest_by_date = {}

        for item in items:
            forecast_date = display_text(
                item.get("informData"),
                "날짜 정보 없음",
            )

            announced_at = display_text(
                item.get("dataTime"),
                "",
            )

            if forecast_date not in latest_by_date:
                latest_by_date[forecast_date] = item
            else:
                old_time = display_text(
                    latest_by_date[forecast_date].get("dataTime"),
                    "",
                )

                if parse_announcement_time(announced_at) > parse_announcement_time(old_time):
                    latest_by_date[forecast_date] = item

        # 날짜순 정렬
        result_items = sorted(
            latest_by_date.values(),
            key=lambda item: display_text(
                item.get("informData"), ""
            ),
        )

        st.session_state["official_forecast_items"] = result_items
        st.session_state["official_forecast_date"] = search_date.isoformat()
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
    st.subheader(f"📋 {selected_name} 공식 예보")

    for index, item in enumerate(items):
        forecast_date = display_text(
            item.get("informData"),
            "날짜 정보 없음",
        )
        overall = display_text(item.get("informOverall"))
        cause = display_text(item.get("informCause"))
        grade = display_text(item.get("informGrade"))
        action = display_text(item.get("actionKnack"))
        announced_at = display_text(
            item.get("dataTime"),
            "발표 시간 정보 없음",
        )

        with st.expander(
            f"예보 대상 날짜: {forecast_date}",
            expanded=(index == 0),
        ):
            st.caption(f"발표 시각: {announced_at}")

            st.markdown("**예보 등급**")
            st.write(grade)

            st.markdown("**예보 개황**")
            st.write(overall)

            st.markdown("**발생 원인**")
            st.write(cause)

            st.markdown("**행동 요령**")
            st.write(action)

    st.info(
        "이 자료는 권역별 공식 예보이며, "
        "개별 측정소의 미래 농도 측정값을 의미하지 않습니다."
    )

elif (
    saved_date == search_date.isoformat()
    and saved_code == inform_code
):
    st.warning(
        "선택한 발표일에 표시할 예보 자료가 없습니다. "
        "다른 발표일을 선택해 다시 조회해 보세요."
    )

else:
    st.info(
        "예보 발표일과 물질을 선택한 뒤 "
        "공식 예보 조회 버튼을 눌러 주세요."
    )
