import streamlit as st


st.title("💡 대기질 대응 방법")

st.write(
    "현재 대기질 상태를 바탕으로 오염물질별 대응 방법을 확인할 수 있습니다."
)

st.info(
    "아래 내용은 AirCare 프로젝트에서 대기질 상태에 따라 "
    "일상적인 대응 방법을 안내하기 위한 참고 정보입니다."
)

st.divider()


# -------------------------
# 상황별 대응 방법 (먼저 표시)
# -------------------------

st.subheader("📌 현재 대기질에 따른 대응 방법")

# 1페이지에서 실제 조회한 지역 가져오기
selected_sido = st.session_state.get(
    "air_data_sido",
    st.session_state.get("selected_sido", "서울")
)

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")

data = st.session_state.get("air_data", [])

if not data:

    st.warning(
        "먼저 '전국 대기질 조회' 페이지에서 데이터를 불러오세요."
    )

else:

    station_names = []

    for record in data:

        station_name = record.get(
            "stationName",
            "알 수 없는 측정소"
        )

        if station_name not in station_names:
            station_names.append(station_name)

    # 측정소 이름을 가나다순으로 정렬
    station_names.sort()


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

        pm10 = selected_record.get("pm10Value")
        pm25 = selected_record.get("pm25Value")
        o3 = selected_record.get("o3Value")


        st.write("### 현재 측정값")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("PM10", pm10 if pm10 else "-")

        with col2:
            st.metric("PM2.5", pm25 if pm25 else "-")

        with col3:
            st.metric("오존(O₃)", o3 if o3 else "-")


        st.write("### 💡 대응 방법")


        try:

            if float(pm10) > 80:

                st.warning(
                    """
                    🌫️ PM10 농도가 높은 상태입니다.

                    • 외부 대기질을 확인하세요.
                    • 장시간 야외활동을 줄이는 것을 고려하세요.
                    • 환기 시간을 조절하세요.
                    """
                )

            elif float(pm25) > 35:

                st.warning(
                    """
                    🌫️ PM2.5 농도가 높은 상태입니다.

                    • 실외 대기질을 확인하세요.
                    • 장시간 야외활동을 줄이는 것을 고려하세요.
                    • 외부 공기 상태를 확인하여 환기 시간을 조절하세요.
                    """
                )

            elif float(o3) > 0.09:

                st.warning(
                    """
                    ☀️ 오존 농도가 높은 상태입니다.

                    • 오존 농도가 높은 시간대를 확인하세요.
                    • 장시간 야외활동을 줄이는 것을 고려하세요.
                    """
                )

            else:

                st.success(
                    """
                    🌱 현재 주요 대기오염물질의 농도가
                    비교적 낮은 상태입니다.

                    • 현재 대기질 상태를 지속적으로 확인하세요.
                    • 적절한 시간에 환기하세요.
                    """
                )

        except (ValueError, TypeError):

            st.info(
                "일부 측정값이 없어 현재 상태를 정확하게 판단하기 어렵습니다."
            )


st.divider()


# -------------------------
# 대기오염물질별 대응 방법
# -------------------------

st.subheader("🧭 대기오염물질별 대응 방법")

st.caption("오염물질별 특징과 행동 요령을 한눈에 확인하세요.")

pollutant_guides = [
    {
        "icon": "🌫️",
        "name": "PM10",
        "color": "#E87524",
        "summary": (
            "PM10 농도가 높을 때는 외부에서 유입되는 미세먼지를 줄이고 "
            "실내 공기질을 관리하는 것이 중요합니다."
        ),
        "tips": [
            "외출 시 미세먼지 농도를 확인합니다.",
            "외부 공기가 좋지 않은 시간에는 불필요한 외출을 줄입니다.",
            "실내에서는 공기청정기나 환기장치를 적절히 활용합니다.",
            "청소할 때 먼지가 다시 날리지 않도록 주의합니다.",
        ],
    },
    {
        "icon": "🌫️",
        "name": "PM2.5",
        "color": "#D93636",
        "summary": "PM2.5는 입자가 매우 작은 미세먼지입니다.",
        "tips": [
            "실외 대기질을 확인한 후 환기 시간을 조절합니다.",
            "미세먼지가 높은 날에는 장시간 야외활동을 줄이는 것을 고려합니다.",
            "실내에서 발생하는 연기와 먼지를 줄입니다.",
        ],
    },
    {
        "icon": "☀️",
        "name": "오존(O₃)",
        "color": "#E5B900",
        "summary": (
            "오존 농도가 높은 경우에는 특히 햇빛이 강한 시간대의 "
            "야외활동에 주의할 필요가 있습니다."
        ),
        "tips": [
            "오존 농도가 높은 시간대에는 장시간 야외활동을 줄입니다.",
            "실시간 오존 정보를 확인합니다.",
            "환기할 때 외부 대기질을 함께 확인합니다.",
        ],
    },
    {
        "icon": "🏭",
        "name": "이산화질소(NO₂)",
        "color": "#7C5CBF",
        "summary": (
            "NO₂는 자동차 배기가스나 연소 과정 등과 관련이 있는 "
            "대기오염물질입니다."
        ),
        "tips": [
            "교통량이 많은 도로 주변의 대기질을 확인합니다.",
            "대기오염이 높은 시간대에는 불필요한 야외활동을 줄입니다.",
            "실내에서는 적절한 환기를 실시합니다.",
        ],
    },
    {
        "icon": "💨",
        "name": "일산화탄소(CO)",
        "color": "#2F80C8",
        "summary": (
            "CO는 연료의 불완전 연소 과정에서 발생할 수 있는 "
            "대기오염물질입니다."
        ),
        "tips": [
            "실내 연소기기의 적절한 사용과 환기에 주의합니다.",
            "연소기기를 사용하는 공간의 환기 상태를 확인합니다.",
            "이상이 있는 연소기기는 사용하지 않고 점검합니다.",
        ],
    },
    {
        "icon": "🏭",
        "name": "아황산가스(SO₂)",
        "color": "#2E9D50",
        "summary": (
            "SO₂는 주로 연료의 연소 과정에서 발생할 수 있는 "
            "대기오염물질입니다."
        ),
        "tips": [
            "대기질 정보를 확인합니다.",
            "농도가 높은 경우 장시간 야외활동을 줄이는 것을 고려합니다.",
            "실내 공기질도 함께 관리합니다.",
        ],
    },
]


# 두 개씩 나누어 카드 형태로 표시
for i in range(0, len(pollutant_guides), 2):

    guide_cols = st.columns(2)

    for col, guide in zip(guide_cols, pollutant_guides[i:i + 2]):

        with col:

            with st.container(border=True):

                # 오염물질 이름 (색상 띠 포함)
                st.markdown(
                    f'<div style="'
                    f'border-left:6px solid {guide["color"]}; '
                    f'padding-left:12px; '
                    f'font-size:22px; '
                    f'font-weight:700; '
                    f'margin-bottom:8px;">'
                    f'{guide["icon"]} {guide["name"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # 한 줄 설명
                st.markdown(guide["summary"])

                # 행동 요령 (한 줄씩 목록으로 표시)
                st.markdown("**✅ 이렇게 대응하세요**")

                st.markdown(
                    "\n".join(f"- {tip}" for tip in guide["tips"])
                )


st.divider()

st.caption(
    "※ AirCare의 대응 방법은 대기질 데이터를 바탕으로 한 일반적인 참고 정보입니다."
)
