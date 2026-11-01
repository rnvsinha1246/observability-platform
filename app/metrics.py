from prometheus_client import Counter, Histogram


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)


REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(
        0.05,
        0.1,
        0.2,
        0.3,
        0.5,
        1.0,
        2.0,
        5.0
    )
)