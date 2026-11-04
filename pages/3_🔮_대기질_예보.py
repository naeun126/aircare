import re
import streamlit as st

from datetime import date, timedelta
from utils.api import get_air_quality_forecast


# ========================================
# 1. 페이지 기본 설정
# ========================================

st.title("🔮 대기질 예보")

st.write(
    "에어코리아의 공식 대기질 예보를 조회합니다."
)

# 1페이지에서 실제 조회한 지역 가져오기
selected_sido = st.session_state.get(
    "air_data_sido",
    st.session_state.get("selected_sido", "서울")
)

st.caption(f"📍 현재 선택 지역: **{selected_sido}**")


# ========================================
# 2. 예보 대기오염물질 설정
# ========================================

pollutant_options = {
    "PM10": "PM10",
    "PM2.5": "PM25",
}


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


def normalize_region(region):
    """예보 지역명과 선택한 시도명을 비교하기 쉽게 정리한다."""

    region = str(region).strip()

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

    return aliases.get(region, region)


def parse_grades(grade_list):
    """지역별 예보 문자열을 지역과 등급으로 분리하고 중복을 제거한다."""

    results = []
    seen = set()

    for text in grade_list:
        if not text:
            continue

        text = str(text)

        text = (
            text.replace("<br>", ",")
            .replace("<br/>", ",")
            .replace("<br />", ",")
        )

        for part in re.split(r"[,;\n]", text):

            if ":" not in part:
                continue

            region, grade = part.split(":", 1)

            region = region.strip()
            grade = grade.strip()

            if not region or not grade:
                continue

            key = (normalize_region(region), grade)

            if key not in seen:
                seen.add(key)
                results.append((region, grade))

    return results


def grade_color(grade):
    """예보 등급에 따른 색상을 반환한다."""

    grade = str(grade).strip()

    if "매우나쁨" in grade or "매우 나쁨" in grade:
        return "#D93636"

    elif "나쁨" in grade:
        return "#E87524"

    elif "보통" in grade:
        return "#E5B900"

    elif "좋음" in grade:
        return "#2E9D50"

    return "#64748B"


FORECAST_FIELDS = [
    ("informGrade", "grades"),
    ("informOverall", "overall"),
    ("informCause", "cause"),
    ("actionKnack", "action"),
]


def build_forecast_row(forecast_date, records):
    """같은 예보 날짜의 발표 자료 중 가장 최근 발표를 기준으로 정리한다."""

    # 발표 시각이 가장 늦은 자료가 앞에 오도록 정렬
    records = sorted(
        records,
        key=lambda record: clean_text(record.get("dataTime"), ""),
        reverse=True,
    )

    row = {
        "date": forecast_date,
        "time": records[0].get("dataTime"),
        "grades": [],
        "overall": [],
        "cause": [],
        "action": [],
    }

    for field, target in FORECAST_FIELDS:

        # 가장 최근 발표부터 확인해 값이 있는 첫 자료만 사용
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

            key = " ".join(text.split())

            if key not in seen:
                seen.add(key)
                texts.append(text)

    return texts


# ========================================
# 5. 공식 예보 API 조회
# ========================================

for selected_name, inform_code in pollutant_options.items():

    query_key = f"{search_date}_{inform_code}"
    session_prefix = f"official_forecast_{inform_code}"

    if st.session_state.get(
        f"{session_prefix}_query_key"
    ) != query_key:

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

        try:
            service_key = st.secrets["service_key"]

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

                forecast_date = clean_text(
                    item.get("informData"),
                    "날짜 정보 없음",
                )

                merge_key = date_key(forecast_date) or forecast_date

                if merge_key not in grouped:

                    grouped[merge_key] = {
                        "date": forecast_date,
                        "records": [],
                    }

                grouped[merge_key]["records"].append(item)

            # 내일 날짜에 해당하는 예보만 선택
            result_items = [
                build_forecast_row(group["date"], group["records"])
                for group in grouped.values()
                if date_key(group["date"]) == target_date
            ]

            st.session_state[f"{session_prefix}_items"] = result_items
            st.session_state[f"{session_prefix}_date"] = search_date
            st.session_state[f"{session_prefix}_code"] = inform_code
            st.session_state[f"{session_prefix}_query_key"] = query_key

        except KeyError:

            st.error(
                "Streamlit Secrets에 service_key가 설정되어 있는지 확인하세요."
            )

        except (ValueError, ConnectionError) as error:

            st.error(
                f"{selected_name} 예보 조회에 실패했습니다: {error}"
            )

        except Exception as error:

            st.error(
                f"{selected_name} 예보 조회 중 오류가 발생했습니다: {error}"
            )


# ========================================
# 6. 예보 결과 가져오기
# ========================================

valid_forecasts = {}

for selected_name, inform_code in pollutant_options.items():

    session_prefix = f"official_forecast_{inform_code}"

    forecast_items = st.session_state.get(
        f"{session_prefix}_items",
        []
    )

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

st.subheader(
    f"📋 {tomorrow:%Y년 %m월 %d일} 대기질 예보"
)

if not valid_forecasts:

    st.warning(
        f"{tomorrow:%Y년 %m월 %d일}의 예보를 찾지 못했습니다. "
        "예보 발표 여부를 확인해 주세요."
    )

    st.stop()

# 발표 시각은 한 번만 표시
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

normalized_selected = normalize_region(selected_sido)


# ========================================
# 7-1. 선택 지역 예보 (PM10 / PM2.5)
# ========================================

st.markdown("### 📍 선택 지역 예보")

cols = st.columns(2)

for col, selected_name in zip(
    cols,
    pollutant_options.keys()
):

    with col:

        row = valid_forecasts.get(selected_name)

        if row is None:

            st.warning(
                f"{selected_name} 예보를 찾지 못했습니다."
            )

            continue

        selected_grades = [
            (region, grade)
            for region, grade in parse_grades(row["grades"])
            if normalize_region(region) == normalized_selected
        ]

        if selected_grades:

            region, grade = selected_grades[0]

            color = grade_color(grade)

            forecast_card = (
                f'<div style="'
                f'background:{color}15; '
                f'border-left:7px solid {color}; '
                f'border-radius:12px; '
                f'padding:22px; '
                f'margin:8px 0 20px 0;">'

                f'<div style="'
                f'font-size:15px; '
                f'color:#64748b;">'
                f'{region} · {selected_name}'
                f'</div>'

                f'<div style="'
                f'font-size:32px; '
                f'font-weight:700; '
                f'color:{color}; '
                f'margin:8px 0;">'
                f'{grade}'
                f'</div>'

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

            st.warning(
                f"선택한 지역인 '{selected_sido}'의 "
                f"{selected_name} 등급을 찾지 못했습니다."
            )


# ========================================
# 7-2. 다른 지역 예보 (PM10만 표시)
# ========================================

st.divider()

st.markdown("### 🗺️ 다른 지역 예보 (PM10)")

other_regions = {}

pm10_row = valid_forecasts.get("PM10")

if pm10_row:

    for region, grade in parse_grades(pm10_row["grades"]):

        normalized_region = normalize_region(region)

        # 선택 지역 제외, 지역별로 한 번만 저장
        if normalized_region == normalized_selected:
            continue

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

all_rows = list(valid_forecasts.values())

overall_texts = collect_unique_texts(all_rows, "overall")
cause_texts = collect_unique_texts(all_rows, "cause")
action_texts = collect_unique_texts(all_rows, "action")

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

if not (overall_texts or cause_texts or action_texts):

    st.info("표시할 예보 종합 정보가 없습니다.")
