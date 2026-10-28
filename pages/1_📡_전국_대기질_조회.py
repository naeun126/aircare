
import pandas as pd
import streamlit as st

from utils.api import get_air_quality_data

st.set_page_config(page_title="전국 대기질 조회", page_icon="📡", layout="wide")

SIDO_LIST = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "세종",
]

POLLUTANTS = {
    "미세먼지(PM10)": "pm10Value",
    "초미세먼지(PM2.5)": "pm25Value",
    "오존(O₃)": "o3Value",
    "이산화질소(NO₂)": "no2Value",
    "일산화탄소(CO)": "coValue",
    "아황산가스(SO₂)": "so2Value",
}


def to_number(value):
    """숫자로 변환할 수 없는 값은 None으로 처리한다."""
    try:
        if value is None or str(value).strip() in ("", "-", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_pm10_status(value):
    """PM10 농도를 기준으로 간단한 상태를 반환한다."""
    number = to_number(value)
    if number is None:
        return "정보 없음"
    if number <= 30:
        return "좋음"
    if number <= 80:
        return "보통"
    if number <= 150:
        return "나쁨"
    return "매우 나쁨"


def get_pm25_status(value):
    """PM2.5 농도를 기준으로 간단한 상태를 반환한다."""
    number = to_number(value)
    if number is None:
        return "정보 없음"
    if number <= 15:
        return "좋음"
    if number <= 35:
        return "보통"
    if number <= 75:
        return "나쁨"
    return "매우 나쁨"


if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"


st.title("📡 전국 대기질 조회")
st.write("시도를 선택하고 공공데이터 API에서 최신 측정 자료를 불러오세요.")

selected_sido = st.selectbox(
    "조회할 지역을 선택하세요.",
    SIDO_LIST,
    key="selected_sido",
)

if st.button("🔄 최신 대기질 데이터 불러오기", type="primary"):
    try:
        service_key = st.secrets["service_key"]
    except (KeyError, FileNotFoundError):
        st.error(
            "Streamlit Secrets에 service_key가 설정되지 않았습니다. "
            "프로젝트의 Secrets 설정을 확인하세요."
        )
        st.stop()

    try:
        with st.spinner(f"{selected_sido} 대기질 데이터를 불러오는 중입니다..."):
            data = get_air_quality_data(service_key, selected_sido)

        # 데이터마다 조회한 시도를 기록해 다른 지역 자료와 섞이지 않게 한다.
        for record in data:
            record["_selectedSido"] = selected_sido

            station_name = record.get("stationName", "알 수 없는 측정소")
            history_key = f"{selected_sido}|{station_name}"

            if history_key not in st.session_state.history:
                st.session_state.history[history_key] = []

            old_records = st.session_state.history[history_key]
            data_time = record.get("dataTime", "")

            if not any(
                old_record.get("dataTime") == data_time
                for old_record in old_records
            ):
                old_records.append(record)

            # 측정소별 최근 20개 기록만 유지한다.
            st.session_state.history[history_key] = old_records[-20:]

        st.session_state.air_data = data
        st.success(f"{selected_sido} 지역의 측정 자료 {len(data)}건을 불러왔습니다.")

    except Exception as error:
        st.error(f"대기질 데이터를 불러오지 못했습니다: {error}")


data = st.session_state.air_data

if data:
    # 현재 선택한 지역의 자료만 표시한다.
    current_data = [
        record
        for record in data
        if record.get("_selectedSido") == selected_sido
    ]

    if not current_data:
        st.info(
            "현재 선택한 지역의 자료가 없습니다. "
            "위에서 최신 대기질 데이터를 다시 불러오세요."
        )
    else:
        st.subheader(f"📍 {selected_sido} 측정소 현황")

        latest_time = next(
            (
                record.get("dataTime")
                for record in current_data
                if record.get("dataTime")
            ),
            "정보 없음",
        )
        st.caption(f"자료 기준 시각: {latest_time}")

        average_pm10 = [
            to_number(record.get("pm10Value"))
            for record in current_data
        ]
        average_pm10 = [value for value in average_pm10 if value is not None]

        average_pm25 = [
            to_number(record.get("pm25Value"))
            for record in current_data
        ]
        average_pm25 = [value for value in average_pm25 if value is not None]

        col1, col2, col3 = st.columns(3)
        col1.metric("측정소 수", f"{len(current_data)}개")
        col2.metric(
            "PM10 평균",
            f"{sum(average_pm10) / len(average_pm10):.1f} µg/m³"
            if average_pm10 else "정보 없음",
        )
        col3.metric(
            "PM2.5 평균",
            f"{sum(average_pm25) / len(average_pm25):.1f} µg/m³"
            if average_pm25 else "정보 없음",
        )

        display_rows = []
        for record in current_data:
            pm10 = record.get("pm10Value")
            pm25 = record.get("pm25Value")

            display_rows.append({
                "측정소": record.get("stationName", "정보 없음"),
                "측정 시각": record.get("dataTime", "정보 없음"),
                "PM10 (µg/m³)": pm10,
                "PM10 상태": get_pm10_status(pm10),
                "PM2.5 (µg/m³)": pm25,
                "PM2.5 상태": get_pm25_status(pm25),
                "오존 (ppm)": record.get("o3Value", "-"),
                "이산화질소 (ppm)": record.get("no2Value", "-"),
                "일산화탄소 (ppm)": record.get("coValue", "-"),
                "아황산가스 (ppm)": record.get("so2Value", "-"),
            })

        st.dataframe(
            pd.DataFrame(display_rows),
            use_container_width=True,
            hide_index=True,
        )

        csv_data = pd.DataFrame(display_rows).to_csv(
            index=False,
            encoding="utf-8-sig",
        )
        st.download_button(
            "📥 측정 자료 CSV 다운로드",
            data=csv_data,
            file_name=f"{selected_sido}_대기질.csv",
            mime="text/csv",
        )

        st.subheader("📊 오염물질별 측정값")

        pollutant_label = st.selectbox(
            "그래프로 확인할 항목",
            list(POLLUTANTS.keys()),
        )
        pollutant_column = POLLUTANTS[pollutant_label]

        chart_rows = []
        for record in current_data:
            value = to_number(record.get(pollutant_column))
            if value is not None:
                chart_rows.append({
                    "측정소": record.get("stationName", "알 수 없음"),
                    pollutant_label: value,
                })

        if chart_rows:
            chart_df = pd.DataFrame(chart_rows).set_index("측정소")
            st.bar_chart(chart_df, y=pollutant_label)
        else:
            st.info(f"{pollutant_label} 측정값이 없습니다.")

        with st.expander("🕘 측정소별 최근 조회 기록"):
            station_options = sorted({
                record.get("stationName", "알 수 없는 측정소")
                for record in current_data
            })

            if station_options:
                selected_station = st.selectbox(
                    "측정소 선택",
                    station_options,
                    key="history_station",
                )
                history_key = f"{selected_sido}|{selected_station}"
                history_records = st.session_state.history.get(history_key, [])

                if history_records:
                    history_rows = [
                        {
                            "측정 시각": item.get("dataTime", "-"),
                            "PM10": item.get("pm10Value", "-"),
                            "PM2.5": item.get("pm25Value", "-"),
                            "오존": item.get("o3Value", "-"),
                        }
                        for item in history_records
                    ]
                    st.dataframe(
                        pd.DataFrame(history_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("저장된 조회 기록이 없습니다.")
else:
    st.info("아직 조회한 데이터가 없습니다. 위 버튼을 눌러 데이터를 불러오세요.")
