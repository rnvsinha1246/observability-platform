SLO_CONFIG = {
    "burn_rate_windows": ["5m", "30m", "1h", "6h"],
    "evaluation_window": "5m",

    "availability": {
        "target": 0.999
    },

    "latency": {
        "target": 0.95,
        "threshold_seconds": 0.3
    },

    "error_rate": {
        "maximum": 0.001
    }
}


def calculate_availability(
    successful_requests: float,
    total_requests: float
) -> float:
    if total_requests <= 0:
        return 1.0

    return successful_requests / total_requests


def calculate_error_budget(target: float = 0.999) -> float:
    return 1.0 - target


def evaluate_success_ratio(
    observed: float,
    target: float
) -> dict:

    if not 0 <= observed <= 1:
        raise ValueError("Observed ratio must be between 0 and 1")

    if not 0 <= target < 1:
        raise ValueError("Target must be between 0 and 1")

    allowed_error_rate = 1.0 - target
    actual_error_rate = 1.0 - observed

    burn_rate = actual_error_rate / allowed_error_rate

    return {
        "target": round(target, 4),
        "observed": round(observed, 4),
        "compliant": observed >= target,
        "error_budget_percent": round(allowed_error_rate * 100, 4),
        "budget_consumed_percent": round(burn_rate * 100, 2),
        "budget_remaining_percent": round(
            max(0.0, (1.0 - burn_rate) * 100), 2
        ),
        "burn_rate": round(burn_rate, 2)
    }


def evaluate_error_rate(
    observed: float,
    maximum: float
) -> dict:

    if not 0 <= observed <= 1:
        raise ValueError("Observed error rate must be between 0 and 1")

    if not 0 < maximum <= 1:
        raise ValueError("Maximum error rate must be between 0 and 1")

    burn_rate = observed / maximum

    return {
        "target": round(maximum, 4),
        "observed": round(observed, 4),
        "compliant": observed <= maximum,
        "error_budget_percent": round(maximum * 100, 4),
        "budget_consumed_percent": round(burn_rate * 100, 2),
        "budget_remaining_percent": round(
            max(0.0, (1.0 - burn_rate) * 100), 2
        ),
        "burn_rate": round(burn_rate, 2)
    }
