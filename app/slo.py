SLO_TARGET = 0.999


def calculate_availability(successful_requests: float, total_requests: float) -> float:
    if total_requests == 0:
        return 1.0

    return successful_requests / total_requests


def calculate_error_budget() -> float:
    return 1.0 - SLO_TARGET


def calculate_budget_consumed(availability: float) -> float:
    error_rate = 1.0 - availability
    error_budget = calculate_error_budget()

    if error_budget == 0:
        return 0.0

    return error_rate / error_budget