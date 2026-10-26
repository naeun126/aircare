
import streamlit as st
from datetime import date, timedelta

from utils.api import get_air_quality_forecast


st.title("🔮 대기질 예측")

st.write(
    "에어코리아 공식 예보 자료를 바탕으로 "
    "날짜별 대기질 전망과 대응 방법을 확인합니다."
)

# 예보 물질 선택
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

# 예보 발표일 선택
today = date.today()

search_date = st.date_input(
    "예보 발표일을 선택하세요.",
    value=today,
    min_value=today - timedelta(days=30),
    max_value=today,
)

# 예보 조회
if st.button("🔍 공식 예보 조회", type="primary"):

    # 이전 조회 결과 초기화
    st.session_state.pop("official_forecast_items", None)
    st.session_state.pop("official_forecast_date", None)
    st.session_state.pop("official_forecast_code", None)

    try:
        # 첫 번째 페이지와 동일한 인증키 사용
        service_key = st.secrets["service_key"]

        with st.spinner("공식 예보 자료를 조회하고 있습니다..."):
            items = get_air_quality_forecast(
                service_key=service_key,
                inform_code=inform_code,
                search_date=search_date.isoformat(),
            )

        st.session_state["official_forecast_items"] = items
        st.session_state["official_forecast_date"] = (
            search_date.isoformat()
        )
        st.session_state["official_forecast_code"] = inform_code

    except KeyError:
        st.error(
            "Streamlit Secrets에 service_key가 설정되어 있는지 "
            "확인하세요."
        )

    except (ValueError, ConnectionError) as error:
        st.error(f"예보 조회에 실패했습니다: {error}")

    except Exception as error:
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")


# 조회 결과 표시
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

        forecast_date = item.get(
            "informData", "날짜 정보 없음"
        )
        overall = item.get(
            "informOverall", "예보 개황 정보 없음"
        )
        cause = item.get(
            "informCause", "발생 원인 정보 없음"
        )
        grade = item.get(
            "informGrade", "예보 등급 정보 없음"
        )
        action = item.get(
            "actionKnack", "행동 요령 정보 없음"
        )
        announced_at = item.get(
            "dataTime", "발표 시간 정보 없음"
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
