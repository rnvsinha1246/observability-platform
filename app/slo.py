SLO_CONFIG = {
    "availability": {
        "target": 0.999,
        "window_days": 30
    },
    "latency": {
        "target": 0.95,
        "threshold_seconds": 0.3,
        "window_days": 30
    },
    "error_rate": {
        "maximum": 0.001,
        "window_days": 30
    }
}

# Backward compatibility with the existing main.py
SLO_TARGET = SLO_CONFIG["availability"]["target"]


def calculate_availability(
    successful_requests: float,
    total_requests: float
) -> float:
    if total_requests == 0:
        return 1.0

    return successful_requests / total_requests


def calculate_error_budget(target: float = SLO_TARGET) -> float:
    return 1.0 - target


def calculate_budget_consumed(
    availability: float,
    target: float = SLO_TARGET
) -> float:
    error_budget = calculate_error_budget(target)

    if error_budget <= 0:
        return 0.0

    return (1.0 - availability) / error_budget


def evaluate_success_ratio(
    observed: float,
    target: float
) -> dict:
    error_budget = 1.0 - target

    if error_budget <= 0:
        raise ValueError("Target must be less than 1.0")

    budget_consumed = (1.0 - observed) / error_budget

    return {
        "target": target,
        "observed": observed,
        "compliant": observed >= target,
        "error_budget_percent": error_budget * 100,
        "budget_consumed_percent": budget_consumed * 100,
        "budget_remaining_percent": max(
            0.0,
            (1.0 - budget_consumed) * 100
        )
    }


def evaluate_error_rate(
    observed: float,
    maximum: float
) -> dict:
    if maximum <= 0:
        raise ValueError("Maximum error rate must be positive")

    budget_consumed = observed / maximum

    return {
        "target": maximum,
        "observed": observed,
        "compliant": observed <= maximum,
        "error_budget_percent": maximum * 100,
        "budget_consumed_percent": budget_consumed * 100,
        "budget_remaining_percent": max(
            0.0,
            (1.0 - budget_consumed) * 100
        )
    }
