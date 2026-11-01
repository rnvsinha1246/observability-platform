
import requests


PROMETHEUS_URL = "http://localhost:9090"


def query_prometheus(query: str) -> float | None:
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=5
    )

    response.raise_for_status()

    result = response.json()

    if result["status"] != "success":
        raise RuntimeError("Prometheus query failed")

    data = result["data"]["result"]

    if not data:
        return None

    return float(data[0]["value"][1])
