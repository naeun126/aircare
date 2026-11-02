
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
