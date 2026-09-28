import streamlit as st


# --------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="AirCare",
    page_icon="🌱",
    layout="wide"
)


# --------------------------------------------------
# 세션 데이터 초기화
# --------------------------------------------------

if "air_data" not in st.session_state:
    st.session_state.air_data = []

if "history" not in st.session_state:
    st.session_state.history = {}


# --------------------------------------------------
# 화면 디자인
# --------------------------------------------------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 48px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 20px;
        color: #666666;
        margin-bottom: 30px;
    }

    .info-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #F0F7FF;
        border: 1px solid #D5E8FF;
        margin-bottom: 20px;
    }

    .feature-box {
        padding: 20px;
        border-radius: 15px;
        background-color: #F8F8F8;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 메인 화면
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🌱 AirCare</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    '전국 대기질 데이터 분석 및 예측 프로그램'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


st.markdown(
    """
    <div class="info-box">
    <h3>🎯 AirCare는 무엇을 하는 프로그램인가요?</h3>
    <p>
  AirCare는 공공데이터를 활용하여 전국의 대기질을 조회하고,
  주요 대기오염물질의 상태를 분석하며 미래의 변화를 간단하게 예측하는 프로그램입니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 주요 기능
# --------------------------------------------------

st.subheader("📌 주요 기능")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📡 대기질 조회")
    st.write("전국 시도의 최신 대기질 데이터를 조회합니다.")

with col2:
    st.markdown("### 📊 대기질 분석")
    st.write("PM10, PM2.5 등의 평균과 최대·최소값을 분석합니다.")

with col3:
    st.markdown("### 🔮 대기질 예측")
    st.write("저장된 측정값을 이용하여 다음 값을 간단하게 예측합니다.")

st.divider()

st.info(
    "왼쪽 메뉴에서 원하는 기능을 선택하세요. "
    "먼저 '전국 대기질 조회'에서 데이터를 불러오는 것을 권장합니다."
)

st.sidebar.title("🌏 AirCare")

st.sidebar.info(
    """
    한국환경공단 에어코리아
    대기오염정보 OpenAPI를 활용합니다.

    주요 데이터:
    • PM10
    • PM2.5
    • O₃
    • NO₂
    • CO
    • SO₂
    """
)


st.info(
    "👈 왼쪽 사이드바에서 원하는 기능을 선택하세요."
)
