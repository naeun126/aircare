import re
import streamlit as st

from datetime import date, timedelta
# utils/api.py: 에어코리아 대기질 예보(getMinuDustFrcstDspth)를 가져오는 함수
from utils.api import get_air_quality_forecast
# utils/grade.py: 등급별 색상 (좋음/보통/나쁨/매우 나쁨)
from utils.grade import GRADE_COLORS


# ========================================
# 1. 페이지 기본 설정
# ========================================

st.title("🔮 대기질 예보")

st.write(
    "에어코리아의 공식 대기질 예보를 조회합니다."
)

# 1페이지에서 실제 조회한 지역 가져오기.
# air_data_sido가 있으면 그것을, 없으면 선택만 한 지역을, 그것도 없으면 서울을 쓴다.
selected_sido = st.session_state.get(
    "air_data_sido",
    st.session_state.get("selected_sido", "서울")
)

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")


# ========================================
# 2. 예보 대기오염물질 설정
# ========================================

# 화면에 보여 줄 이름 -> API에 보낼 예보 코드.
# 공식 예보 API는 PM10과 PM2.5(코드 PM25)만 제공한다.
pollutant_options = {
    "PM10": "PM10",
    "PM2.5": "PM25",
}


# ========================================
# 3. 날짜 설정
# ========================================

today = date.today()
tomorrow = today + timedelta(days=1)

# API는 "오늘 날짜"를 기준으로 발표된 예보를 돌려주고,
# 그 안에서 "내일" 날짜의 예보만 골라 사용한다.
search_date = today.isoformat()      # 예: "2026-11-09"
target_date = tomorrow.isoformat()   # 예: "2026-11-10"


# ========================================
# 4. 데이터 정리 함수
# ========================================

def clean_text(value, default="정보 없음"):
    """값이 None이거나 빈 문자열이면 기본 문구로 바꾸고, 아니면 앞뒤 공백을 제거한다."""

    if value is None or str(value).strip() in ("", "None"):
        return default

    return str(value).strip()


def date_key(value):
    """예보 날짜를 YYYY-MM-DD 형식으로 변환한다."""

    value = str(value).strip()

    # "2026년 11월 10일" 형태
    match = re.search(
        r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
        value,
    )

    if match:
        year, month, day = match.groups()

        # :02d는 한 자리 숫자를 두 자리로 맞춘다. (예: 9 -> 09)
        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    # "2026-11-10" 형태
    match = re.search(
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        value,
    )

    if match:
        year, month, day = match.groups()

        return (
            f"{year}-{int(month):02d}-{int(day):02d}"
        )

    # 어느 형태도 아니면 변환할 수 없으므로 빈 문자열을 돌려준다.
    return ""


def normalize_region(region):
    """예보 지역명과 선택한 시도명을 비교하기 쉽게 정리한다."""

    region = str(region).strip()

    # 정식 명칭 -> 1페이지 목록에서 쓰는 짧은 이름
    aliases = {
        "충청북도": "충북",
        "충청남도": "충남",
        "전라북도": "전북",
        "전라남도": "전남",
        "경상북도": "경북",
        "경상남도": "경남",
        "강원특별자치도": "강원",
        "제주특별자치도": "제주",
        "경기도": "경기",
        "서울특별시": "서울",
        "부산광역시": "부산",
        "대구광역시": "대구",
        "인천광역시": "인천",
        "광주광역시": "광주",
        "대전광역시": "대전",
        "울산광역시": "울산",
        "세종특별자치시": "세종",
    }

    # 표에 없는 이름은 그대로 돌려준다.
    return aliases.get(region, region)


def parse_grades(grade_list):
    """지역별 예보 문자열을 지역과 등급으로 분리하고 중복을 제거한다."""

    results = []
    seen = set()   # 이미 담은 (지역, 등급) 조합

    for text in grade_list:
        if not text:
            continue

        text = str(text)

        # API 문자열에 섞여 있는 줄바꿈 태그를 쉼표로 바꿔 구분하기 쉽게 한다.
        text = (
            text.replace("<br>", ",")
            .replace("<br/>", ",")
            .replace("<br />", ",")
        )

        # "서울 : 나쁨, 인천 : 나쁨" 같은 문자열을 쉼표·세미콜론·줄바꿈 기준으로 나눈다.
        for part in re.split(r"[,;\n]", text):

            # 콜론이 없으면 "지역 : 등급" 형태가 아니므로 건너뛴다.
            if ":" not in part:
                continue

            # 첫 번째 콜론 기준으로 지역과 등급을 나눈다.
            region, grade = part.split(":", 1)

            region = region.strip()
            grade = grade.strip()

            if not region or not grade:
                continue

            # 지역명을 통일한 뒤 같은 (지역, 등급)이 이미 있으면 건너뛴다.
            key = (normalize_region(region), grade)

            if key not in seen:
                seen.add(key)
                results.append((region, grade))

    return results


def grade_color(grade):
    """예보 등급에 따른 색상을 반환한다."""

    grade = str(grade).strip()

    # "매우 나쁨"에는 "나쁨"이 들어 있으므로 반드시 먼저 검사해야 한다.
    # 띄어쓰기 없는 "매우나쁨"도 함께 처리한다.
    if "매우나쁨" in grade or "매우 나쁨" in grade:
        return GRADE_COLORS["매우 나쁨"]

    elif "나쁨" in grade:
        return GRADE_COLORS["나쁨"]

    elif "보통" in grade:
        return GRADE_COLORS["보통"]

    elif "좋음" in grade:
        return GRADE_COLORS["좋음"]

    # 알 수 없는 등급은 회색
    return "#64748B"


# API 응답 항목 이름 -> 정리한 결과(row)에 저장할 이름
FORECAST_FIELDS = [
    ("informGrade", "grades"),     # 지역별 예보 등급
    ("informOverall", "overall"),  # 예보 개황
    ("informCause", "cause"),      # 발생 원인
    ("actionKnack", "action"),     # 행동 요령
]


def build_forecast_row(forecast_date, records):
    """같은 예보 날짜의 발표 자료 중 가장 최근 발표를 기준으로 정리한다."""

    # 같은 날짜의 예보가 하루에 여러 번 발표될 수 있다.
    # 발표 시각이 가장 늦은 자료가 앞에 오도록 정렬한다.
    records = sorted(
        records,
        key=lambda record: clean_text(record.get("dataTime"), ""),
        reverse=True,
    )

    row = {
        "date": forecast_date,
        "time": records[0].get("dataTime"),   # 가장 최근 발표 시각
        "grades": [],
        "overall": [],
        "cause": [],
        "action": [],
    }

    for field, target in FORECAST_FIELDS:

        # 가장 최근 발표부터 확인해 값이 있는 첫 자료만 사용한다.
        # (최신 발표에 항목이 비어 있으면 그 이전 발표의 값으로 채운다.)
        for record in records:

            value = record.get(field)

            if value and str(value).strip() not in ("", "None"):
                row[target].append(str(value).strip())
                break

    return row


def collect_unique_texts(rows, field):
    """여러 물질의 예보 문구를 모아 같은 내용은 한 번만 남긴다."""

    texts = []
    seen = set()

    for row in rows:

        for text in row[field]:

            # 공백 차이만 있는 같은 문장을 중복으로 처리하기 위해 공백을 하나로 맞춘다.
            key = " ".join(text.split())

            if key not in seen:
                seen.add(key)
                texts.append(text)

    return texts


# ========================================
# 5. 공식 예보 API 조회
# ========================================

# PM10과 PM2.5를 차례로 조회한다.
for selected_name, inform_code in pollutant_options.items():

    # 오늘 날짜 + 물질 코드를 합친 조회 기준.
    # 같은 날 같은 물질은 한 번만 조회해 API 호출을 줄인다.
    query_key = f"{search_date}_{inform_code}"
    session_prefix = f"official_forecast_{inform_code}"

    # 저장된 조회 기준이 지금과 다를 때(처음이거나 날짜가 바뀌었을 때)만 새로 조회한다.
    if st.session_state.get(
        f"{session_prefix}_query_key"
    ) != query_key:

        # 이전에 저장한 예보 결과를 모두 지운다. (없어도 오류가 나지 않게 pop(..., None) 사용)
        for suffix in (
            "items",
            "date",
            "code",
            "query_key",
        ):
            st.session_state.pop(
                f"{session_prefix}_{suffix}",
                None
            )

        # [예외 처리] 키 확인, API 호출, 결과 정리를 한꺼번에 감싼다.
        try:
            # Streamlit Secrets에 키가 없으면 KeyError가 발생한다.
            service_key = st.secrets["service_key"]

            # 조회하는 동안 로딩 문구를 보여 준다.
            with st.spinner(
                f"{selected_name} 공식 예보를 조회하고 있습니다..."
            ):

                items = get_air_quality_forecast(
                    service_key=service_key,
                    inform_code=inform_code,
                    search_date=search_date,
                )

            # 예보 대상 날짜별로 발표 자료 묶기
            grouped = {}

            for item in items:

                # informData는 "예보 대상 날짜"이다.
                forecast_date = clean_text(
                    item.get("informData"),
                    "날짜 정보 없음",
                )

                # 날짜 표기가 달라도 같은 날로 묶이도록 YYYY-MM-DD로 통일한다.
                merge_key = date_key(forecast_date) or forecast_date

                if merge_key not in grouped:

                    grouped[merge_key] = {
                        "date": forecast_date,
                        "records": [],
                    }

                grouped[merge_key]["records"].append(item)

            # 내일 날짜에 해당하는 예보만 선택해 정리한다.
            result_items = [
                build_forecast_row(group["date"], group["records"])
                for group in grouped.values()
                if date_key(group["date"]) == target_date
            ]

            # 결과와 조회 기준을 session_state에 저장한다.
            # 다음에 페이지가 다시 그려져도 위 if 조건이 거짓이 되어 API를 다시 부르지 않는다.
            st.session_state[f"{session_prefix}_items"] = result_items
            st.session_state[f"{session_prefix}_date"] = search_date
            st.session_state[f"{session_prefix}_code"] = inform_code
            st.session_state[f"{session_prefix}_query_key"] = query_key

        # 인증키가 없는 경우
        except KeyError:

            st.error(
                "Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요."
            )

        # API 응답 오류, 네트워크 연결 실패
        except (ValueError, ConnectionError) as error:

            st.error(
                f"{selected_name} 예보 조회에 실패했습니다: {error}"
            )

        # 그 밖의 예상하지 못한 오류
        except Exception as error:

            st.error(
                f"{selected_name} 예보 조회 중 오류가 발생했습니다: {error}"
            )


# ========================================
# 6. 예보 결과 가져오기
# ========================================

# 화면에 보여 줄 수 있는 유효한 예보만 모은다. (물질 이름 -> 예보 정리 결과)
valid_forecasts = {}

for selected_name, inform_code in pollutant_options.items():

    session_prefix = f"official_forecast_{inform_code}"

    forecast_items = st.session_state.get(
        f"{session_prefix}_items",
        []
    )

    # 결과가 있고, 오늘 조회한 것이며, 코드도 일치할 때만 유효한 예보로 인정한다.
    if (
        forecast_items
        and st.session_state.get(f"{session_prefix}_date") == search_date
        and st.session_state.get(f"{session_prefix}_code") == inform_code
    ):

        # 내일 예보는 날짜별로 하나만 남아 있으므로 첫 번째 사용
        valid_forecasts[selected_name] = forecast_items[0]


# ========================================
# 7. 예보 결과 화면 출력
# ========================================

st.divider()

# :%Y년 %m월 %d일 은 날짜를 "2026년 11월 10일" 형태로 보여 준다.
st.subheader(
    f"📋 {tomorrow:%Y년 %m월 %d일} 대기질 예보"
)

# [예외 처리] 내일 예보가 하나도 없으면(아직 발표 전이거나 조회 실패) 안내 후 멈춘다.
if not valid_forecasts:

    st.warning(
        f"{tomorrow:%Y년 %m월 %d일}의 예보를 찾지 못했습니다. "
        "예보 발표 여부를 확인해 주세요."
    )

    st.stop()

# 발표 시각은 한 번만 표시한다.
# 값이 있는 첫 번째 예보의 발표 시각을 찾는다. 없으면 None.
release_time = next(
    (
        clean_text(row["time"])
        for row in valid_forecasts.values()
        if row.get("time")
    ),
    None,
)

if release_time:
    st.caption(f"발표 시각: {release_time}")

# 선택 지역 이름을 예보 지역명과 비교할 수 있게 통일한다.
normalized_selected = normalize_region(selected_sido)


# ========================================
# 7-1. 선택 지역 예보 (PM10 / PM2.5)
# ========================================

st.markdown("### 📍 선택 지역 예보")

# PM10은 왼쪽, PM2.5는 오른쪽에 나란히 표시한다.
cols = st.columns(2)

for col, selected_name in zip(
    cols,
    pollutant_options.keys()
):

    with col:

        row = valid_forecasts.get(selected_name)

        # 이 물질의 예보가 없으면 안내만 하고 다음 물질로 넘어간다.
        if row is None:

            st.warning(
                f"{selected_name} 예보를 찾지 못했습니다."
            )

            continue

        # 예보 문자열에서 지역·등급 쌍을 꺼낸 뒤, 선택 지역과 같은 것만 남긴다.
        selected_grades = [
            (region, grade)
            for region, grade in parse_grades(row["grades"])
            if normalize_region(region) == normalized_selected
        ]

        if selected_grades:

            region, grade = selected_grades[0]

            # 등급에 맞는 색상
            color = grade_color(grade)

            # 예보 카드 (HTML). {color}15는 색상에 투명도를 더해 연한 배경으로 만든다.
            forecast_card = (
                f'<div style="'
                f'background:{color}15; '
                f'border-left:7px solid {color}; '
                f'border-radius:12px; '
                f'padding:22px; '
                f'margin:8px 0 20px 0;">'

                # 지역 · 물질 이름
                f'<div style="'
                f'font-size:15px; '
                f'color:#64748b;">'
                f'{region} · {selected_name}'
                f'</div>'

                # 예보 등급 (크게)
                f'<div style="'
                f'font-size:32px; '
                f'font-weight:700; '
                f'color:{color}; '
                f'margin:8px 0;">'
                f'{grade}'
                f'</div>'

                # 출처 표시
                f'<div style="font-size:14px;">'
                f'에어코리아 공식 권역별 예보'
                f'</div>'

                f'</div>'
            )

            st.markdown(
                forecast_card,
                unsafe_allow_html=True
            )

        else:

            # 예보 문자열에서 선택 지역의 등급을 찾지 못한 경우
            st.warning(
                f"선택한 지역인 '{selected_sido}'의 "
                f"{selected_name} 등급을 찾지 못했습니다."
            )


# ========================================
# 7-2. 다른 지역 예보 (PM10만 표시)
# ========================================

st.divider()

st.markdown("### 🗺️ 다른 지역 예보 (PM10)")

# 정규화한 지역명 -> (원래 지역명, 등급)
other_regions = {}

pm10_row = valid_forecasts.get("PM10")

if pm10_row:

    for region, grade in parse_grades(pm10_row["grades"]):

        normalized_region = normalize_region(region)

        # 선택 지역은 위에서 이미 보여 주었으므로 제외한다.
        if normalized_region == normalized_selected:
            continue

        # 같은 지역이 여러 번 나와도 한 번만 저장한다.
        if normalized_region not in other_regions:
            other_regions[normalized_region] = (region, grade)

if other_regions:

    # 지역 이름 가나다순 정렬
    sorted_regions = sorted(
        other_regions.values(),
        key=lambda item: item[0]
    )

    # 두 개씩 나누어 화면에 표시
    for i in range(0, len(sorted_regions), 2):

        other_cols = st.columns(2)

        for col, (region, grade) in zip(
            other_cols,
            sorted_regions[i:i + 2]
        ):

            color = grade_color(grade)

            with col:

                st.markdown(f"**{region}**")

                # 칸에는 예보 상태만 표시
                st.markdown(
                    f'<div style="'
                    f'background:{color}15; '
                    f'border-left:5px solid {color}; '
                    f'border-radius:10px; '
                    f'padding:12px; '
                    f'margin:5px 0 18px 0; '
                    f'color:{color}; '
                    f'font-size:20px; '
                    f'font-weight:bold;">'
                    f'{grade}'
                    f'</div>',
                    unsafe_allow_html=True
                )

else:

    st.info(
        "표시할 다른 지역 예보가 없습니다."
    )


# ========================================
# 7-3. 예보 종합 정보 (한 번만 표시)
# ========================================

st.divider()

st.markdown("### 📢 예보 종합 정보")

# PM10과 PM2.5의 예보 결과를 하나의 리스트로 합친다.
all_rows = list(valid_forecasts.values())

# 두 물질의 설명이 같은 경우가 많아, 중복을 제거해 한 번씩만 모은다.
overall_texts = collect_unique_texts(all_rows, "overall")   # 예보 개황
cause_texts = collect_unique_texts(all_rows, "cause")       # 발생 원인
action_texts = collect_unique_texts(all_rows, "action")     # 행동 요령

if overall_texts:

    for text in overall_texts:
        st.write(text)

if cause_texts:

    st.markdown("**주요 발생 원인**")

    for text in cause_texts:
        st.write(text)

if action_texts:

    st.markdown("**대응 요령**")

    for text in action_texts:
        st.write(text)

# 세 항목이 모두 비어 있을 때의 안내
if not (overall_texts or cause_texts or action_texts):

    st.info("표시할 예보 종합 정보가 없습니다.")
