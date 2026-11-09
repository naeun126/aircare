"""측정값 목록에서 평균·최대·최소·변화 추세를 계산하는 함수 모음."""


def get_valid_values(data, column):
    """측정 기록(data)에서 column 값 중 사용할 수 있는 숫자만 골라 반환한다.

    값이 없거나(None), 숫자가 아니거나, 음수인 측정값은 제외한다.
    """

    values = []

    for record in data:
        value = record.get(column)

        # 측정값이 비어 있으면 건너뛴다.
        if value is None:
            continue

        try:
            # API 값은 문자열이므로 숫자로 바꾼다. ("-" 등은 오류가 난다.)
            number = float(value)

            # 음수는 측정 오류 값이므로 제외한다.
            if number >= 0:
                values.append(number)

        except (ValueError, TypeError):
            # 숫자로 바꿀 수 없는 값은 무시한다.
            continue

    return values


def calculate_average(data, column):
    """유효한 측정값의 평균을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    # 계산할 값이 없으면 0으로 나누는 오류를 막기 위해 None을 반환한다.
    if not values:
        return None

    return sum(values) / len(values)


def calculate_max(data, column):
    """유효한 측정값 중 가장 큰 값을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    if not values:
        return None

    return max(values)


def calculate_min(data, column):
    """유효한 측정값 중 가장 작은 값을 구한다. 값이 없으면 None을 반환한다."""

    values = get_valid_values(data, column)

    if not values:
        return None

    return min(values)


def calculate_change(data, column):
    """처음 값에서 마지막 값까지의 변화량을 구한다.

    비교하려면 값이 2개 이상 필요하므로, 부족하면 None을 반환한다.
    """

    values = get_valid_values(data, column)

    if len(values) < 2:
        return None

    # 마지막 값 - 처음 값 (양수면 늘어난 것)
    return values[-1] - values[0]


def calculate_trend(data, column):
    """변화량을 바탕으로 '증가', '감소', '변화 없음', '데이터 부족' 중 하나를 반환한다."""

    change = calculate_change(data, column)

    if change is None:
        return "데이터 부족"

    if change > 0:
        return "증가"

    if change < 0:
        return "감소"

    return "변화 없음"
