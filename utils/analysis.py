"""측정값 목록에서 평균·최대·최소·변화 추세를 계산하는 함수 모음.

2페이지(대기질 분석)에서 선택한 물질의 통계를 계산할 때 사용한다.
data는 측정소별 측정 기록(딕셔너리)의 리스트이고,
column은 "pm10Value"처럼 API 응답에서 값을 꺼낼 항목 이름이다.
"""


def get_valid_values(data, column):
    """측정 기록(data)에서 column 값 중 사용할 수 있는 숫자만 골라 반환한다.

    값이 없거나(None), 숫자가 아니거나, 음수인 측정값은 제외한다.
    다른 계산 함수들이 모두 이 함수의 결과를 사용한다.
    """

    # 사용할 수 있는 값만 담을 리스트
    values = []

    for record in data:
        # 이 측정소 기록에서 해당 항목의 값을 꺼낸다. 항목이 없으면 None이 된다.
        value = record.get(column)

        # 측정값이 비어 있으면 건너뛴다.
        if value is None:
            continue

        try:
            # API 값은 문자열이므로 숫자로 바꾼다.
            # 측정값이 없을 때 API가 주는 "-" 같은 문자열은 여기서 ValueError가 난다.
            number = float(value)

            # 음수는 측정 오류 값이므로 제외한다. (0은 정상 값이므로 포함)
            if number >= 0:
                values.append(number)

        except (ValueError, TypeError):
            # 숫자로 바꿀 수 없는 값은 무시하고 다음 측정소로 넘어간다.
            # 이 처리 덕분에 값이 빠진 측정소가 있어도 프로그램이 멈추지 않는다.
            continue

    return values


def calculate_average(data, column):
    """유효한 측정값의 평균을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    # 계산할 값이 없으면 0으로 나누는 오류를 막기 위해 None을 반환한다.
    if not values:
        return None

    # 평균 = 모든 값의 합 / 값의 개수
    return sum(values) / len(values)


def calculate_max(data, column):
    """유효한 측정값 중 가장 큰 값을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    # 빈 리스트에 max()를 쓰면 오류가 나므로 먼저 확인한다.
    if not values:
        return None

    return max(values)


def calculate_min(data, column):
    """유효한 측정값 중 가장 작은 값을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    # 빈 리스트에 min()을 쓰면 오류가 나므로 먼저 확인한다.
    if not values:
        return None

    return min(values)


def calculate_change(data, column):
    """처음 값에서 마지막 값까지의 변화량을 구한다.

    비교하려면 값이 2개 이상 필요하므로, 부족하면 None을 반환한다.
    """

    values = get_valid_values(data, column)

    # 값이 0개 또는 1개이면 비교할 대상이 없다.
    if len(values) < 2:
        return None

    # 마지막 값 - 처음 값 (양수면 늘어난 것, 음수면 줄어든 것)
    # values[-1]은 리스트의 마지막 항목, values[0]은 첫 번째 항목이다.
    return values[-1] - values[0]


def calculate_trend(data, column):
    """변화량을 바탕으로 '증가', '감소', '변화 없음', '데이터 부족' 중 하나를 반환한다."""

    change = calculate_change(data, column)

    # 변화량을 구할 수 없는 경우
    if change is None:
        return "데이터 부족"

    # 마지막 값이 처음 값보다 크면 증가
    if change > 0:
        return "증가"

    # 마지막 값이 처음 값보다 작으면 감소
    if change < 0:
        return "감소"

    # 두 값이 같은 경우
    return "변화 없음"
