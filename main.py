"""AirCare 메인(시작) 페이지.

프로그램 소개와 주요 기능을 보여 주는 첫 화면이다.
실제 기능은 pages 폴더의 1~4페이지가 맡고, Streamlit이
pages 폴더의 파일들을 왼쪽 메뉴에 자동으로 나열해 준다.
"""

import streamlit as st


# --------------------------------------------------
# 페이지 기본 설정
# --------------------------------------------------

# 브라우저 탭 제목, 탭 아이콘, 화면 폭을 설정한다.
# set_page_config는 다른 Streamlit 명령보다 먼저 실행해야 한다.
st.set_page_config(
    page_title="AirCare",
    page_icon="🌱",
    layout="wide"       # 화면 전체 폭을 사용한다.
)


# --------------------------------------------------
# 세션 데이터 초기화
# --------------------------------------------------

# 1페이지를 거치지 않고 다른 페이지로 먼저 들어가도 오류가 나지 않도록
# 앱 전체에서 공유하는 저장 공간을 미리 만들어 둔다.

# 조회한 측정소별 최신 데이터
if "air_data" not in st.session_state:
    st.session_state.air_data = []

# 측정소별 과거 측정값 기록
if "history" not in st.session_state:
    st.session_state.history = {}


# --------------------------------------------------
# 화면 디자인
# --------------------------------------------------

# 아래 화면에서 쓸 글자 크기, 색, 상자 모양을 CSS로 정의한다.
# unsafe_allow_html=True를 써야 HTML/CSS가 화면에 적용된다.
#   .main-title  : 큰 제목
#   .sub-title   : 제목 아래 설명 문구
#   .info-box    : 프로그램 소개 상자 (연한 파란색)
#   .feature-box : 기능 설명 상자 (연한 회색)
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

# 위에서 정의한 main-title 스타일로 프로그램 이름을 크게 표시한다.
st.markdown(
    '<div class="main-title">🌱 AirCare</div>',
    unsafe_allow_html=True
)

# 한 줄 소개 문구
st.markdown(
    '<div class="sub-title">'
    '전국 대기질 데이터 분석 및 예보 프로그램'
    '</div>',
    unsafe_allow_html=True
)

# 가로 구분선
st.divider()


# 프로그램 소개 상자
st.markdown(
    """
    <div class="info-box">
    <h3>🎯 AirCare는 무엇을 하는 프로그램인가요?</h3>
    <p>
  AirCare는 공공데이터를 활용하여 전국의 대기질을 조회하고,
  주요 대기오염물질의 상태를 분석하며 공식 대기질 예보를 확인하는 프로그램입니다.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# 주요 기능
# --------------------------------------------------

st.subheader("📌 주요 기능")

# 4개 기능을 가로로 나란히 보여 주기 위해 열을 4개 만든다.
# 각 열은 pages 폴더의 1~4페이지에 하나씩 대응한다.
col1, col2, col3, col4 = st.columns(4)

# 1페이지: 전국 대기질 조회
with col1:
    st.markdown("### 📡 대기질 조회")
    st.write("전국 시도의 최신 대기질 데이터를 조회합니다.")

# 2페이지: 대기질 분석
with col2:
    st.markdown("### 📊 대기질 분석")
    st.write("PM10, PM2.5 등의 평균과 최대·최소값을 분석합니다.")

# 3페이지: 대기질 예보
with col3:
    st.markdown("### 🔮 대기질 예보")
    st.write("에어코리아 공식 예보를 조회합니다.")

# 4페이지: 대기질 대응 방법
with col4:
    st.markdown("### 💡대기질 대응 방법")
    st.write("대기질 데이터를 바탕으로 대응방법을 안내합니다.")

st.divider()

# 사용 순서 안내.
# 다른 페이지들이 1페이지에서 불러온 데이터를 사용하므로 1페이지를 먼저 쓰도록 권한다.
st.info(
    "왼쪽 메뉴에서 원하는 기능을 선택하세요. "
    "먼저 '전국 대기질 조회'에서 데이터를 불러오는 것을 권장합니다."
)

# --------------------------------------------------
# 사이드바 (왼쪽 메뉴 영역)
# --------------------------------------------------

# 왼쪽 메뉴 맨 위에 프로그램 이름을 표시한다.
st.sidebar.title("🌏 AirCare")

# 데이터 출처와 다루는 오염물질 6종 안내
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
