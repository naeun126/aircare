import pandas as pd
import pydeck as pdk
import streamlit as st

from utils.analysis import (
    calculate_average,
    calculate_max,
    calculate_min,
    calculate_trend,
)
from utils.stations import get_station_coordinates


# ========================================
# 세션 상태 초기화
# ========================================

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}

if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = "서울"


st.title("📊 대기질 분석")

# 1페이지에서 선택한 지역
selected_sido = str(st.session_state.get("selected_sido", "서울")).strip()
st.caption(f"📍 현재 선택 지역: **{selected_sido}**")


# ========================================
# 선택 지역 데이터 가져오기
# ========================================

all_data = st.session_state.get("air_data", [])

if not all_data:
    st.warning(
        "측정 데이터가 없습니다. "
        "1페이지에서 지역을 선택한 뒤 데이터를 먼저 조회해 주세요."
    )
    st.stop()

# 우선 1페이지에서 저장한 _selectedSido를 사용하고,
# 없으면 API 응답의 sidoName을 사용한다.
def get_record_sido(record):
    value = record.get("_selectedSido")
    if value is None or not str(value).strip():
        value = record.get("sidoName")
    return str(value or "").strip()


records_with_region = [
    record for record in all_data if get_record_sido(record)
]

if records_with_region:
    # 지역 정보가 있는 데이터는 선택 지역과 정확히 일치하는 것만 사용
    data = [
        record
        for record in all_data
        if get_record_sido(record) == selected_sido
    ]

    if not data:
        available_regions = sorted(
            {get_record_sido(record) for record in records_with_region}
        )
        st.warning(
            f"{selected_sido} 지역의 데이터가 없습니다. "
            "1페이지에서 해당 지역을 선택하고 데이터를 다시 조회해 주세요."
        )
        st.caption(
            "현재 데이터에 기록된 지역: " + ", ".join(available_regions)
        )
        st.stop()
else:
    # 일부 API 응답에는 sidoName이 없을 수 있다.
    # 이 경우 1페이지에서 선택 지역을 조회해 받아온 데이터이므로
    # 전체 데이터를 사용하되, 사용자가 상황을 알 수 있도록 안내한다.
    data = all_data
    st.info(
        "API 응답에 시도 정보가 없어 지역별 추가 필터링은 할 수 없습니다. "
        "1페이지에서 선택한 지역으로 조회한 데이터를 표시합니다."
    )


# ========================================
# 대기오염물질 분석
# ========================================

column_map = {
