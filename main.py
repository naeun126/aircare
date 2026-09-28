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
    '공공데이터를 활용한 실내 공기질 분석 및 예측 프로그램'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


st.markdown(
    """
    <div class="info-box">
    <h3>🎯 AirCare는 무엇을 하는 프로그램인가요?</h3>
    <p>
    공공데이터 API에서 실제 실내 공기질 측정 데이터를 가져와
    PM10, PM2.5, CO₂, 온도, 습도 등의 상태를 분석하고
    시간에 따른 변화와 미래 공기질을 예측하는 프로그램입니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 주요 기능
# --------------------------------------------------

st.subheader("📌 주요 기능")

col1, col2 = st.columns(2)

with col1:

    st.markdown(
        """
        <div class="feature-box">
        <h3>📡 공기질 조회</h3>
        <p>
        공공데이터 API에서 실제 실내공기질 측정 데이터를
        불러옵니다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="feature-box">
        <h3>🔮 공기질 예측</h3>
        <p>
        저장된 측정 데이터를 이용하여 다음 공기질을
        이동평균 방식으로 예측합니다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
        <div class="feature-box">
        <h3>📊 데이터 분석</h3>
        <p>
        평균, 최댓값, 최솟값과 변화 추세를 분석하고
        그래프로 나타냅니다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="feature-box">
        <h3>📋 종합 결과</h3>
        <p>
        현재 공기질과 분석 결과, 예측 결과를
        한 화면에서 확인합니다.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()


# --------------------------------------------------
# 사용 방법
# --------------------------------------------------

st.subheader("🚀 사용 방법")

st.markdown(
    """
    **STEP 1. 공기질 조회**  
    측정 데이터를 제공할 측정소의 데이터를 불러옵니다.

    **STEP 2. 공기질 분석**  
    PM10, PM2.5, CO₂ 등의 평균·최댓값·최솟값과 변화 추세를 확인합니다.

    **STEP 3. 공기질 예측**  
    여러 번 저장한 측정값을 이용하여 다음 값을 예측합니다.

    **STEP 4. 종합 결과**  
    현재 공기질과 분석 및 예측 결과를 한눈에 확인합니다.
    """
)


st.info(
    "👈 왼쪽 사이드바에서 원하는 기능을 선택하세요."
)
