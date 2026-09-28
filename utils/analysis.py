def get_valid_values(data, column):
    values = []

    for record in data:
        value = record.get(column)

        if value is None:
            continue

        try:
            number = float(value)

            if number >= 0:
                values.append(number)

        except (ValueError, TypeError):
            continue

    return values


def calculate_average(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return sum(values) / len(values)


def calculate_max(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return max(values)


def calculate_min(data, column):
    values = get_valid_values(data, column)

    if not values:
        return None

    return min(values)


def calculate_change(data, column):
    values = get_valid_values(data, column)

    if len(values) < 2:
        return None

    return values[-1] - values[0]


def calculate_trend(data, column):
    change = calculate_change(data, column)

    if change is None:
        return "데이터 부족"

    if change > 0:
        return "증가"

    if change < 0:
        return "감소"

    return "변화 없음"


def predict_next_value(data, column, window_size=3):
    values = get_valid_values(data, column)

    if len(values) < window_size:
        return None

    recent_values = values[-window_size:]

    return sum(recent_values) / len(recent_values)


def evaluate_air_quality(column, value):
    """
    프로젝트에서 비교를 쉽게 하기 위한 단순 참고 기준.
    공식 환경기준이나 건강 판단 기준으로 사용하지 않는다.
    """

    if value is None:
        return "데이터 없음"

    if column == "pm10":
        if value <= 30:
            return "낮음"
        elif value <= 80:
            return "보통"
        else:
            return "높음"

    if column == "pm25":
        if value <= 15:
            return "낮음"
        elif value <= 35:
            return "보통"
        else:
            return "높음"

    if column == "o3":
        if value <= 0.03:
            return "낮음"
        elif value <= 0.09:
            return "보통"
        else:
            return "높음"

    if column == "no2":
        if value <= 0.03:
            return "낮음"
        elif value <= 0.06:
            return "보통"
        else:
            return "높음"

    return "확인 필요"
