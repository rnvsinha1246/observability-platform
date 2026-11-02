import time
import random
from fastapi import FastAPI, Request
import requests
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse
from fastapi import HTTPException
from prometheus_api import query_prometheus
from slo import (
    SLO_CONFIG,
    evaluate_success_ratio,
    evaluate_error_rate
)

from metrics import REQUEST_COUNT, REQUEST_LATENCY

from slo import (
    calculate_availability,
    calculate_error_budget
)


app = FastAPI(
    title="Production Observability Platform",
    description="A production-style SRE observability platform",
    version="1.0.0"
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    route = request.scope.get("route")
    endpoint = route.path if route else "unmatched"

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)

    return response


@app.get("/")
def root():
    return {
        "message": "Observability Platform is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/api")
def api():
    """
    Simulates a production API with variable latency
    and occasional failures.
    """

    # Simulate 50-300 ms latency
    delay = random.uniform(0.05, 0.3)
    time.sleep(delay)

    # Simulate approximately 10% failures
    if random.random() < 0.10:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Simulated internal server error"
            }
        )

    return {
        "status": "success",
        "message": "Request processed successfully"
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )




@app.get("/slo")
def slo():
    window = SLO_CONFIG["evaluation_window"]
    latency_threshold = SLO_CONFIG["latency"]["threshold_seconds"]

    queries = {
        "total_requests": f'''
            sum(increase(
                http_requests_total{{endpoint="/api"}}[{window}]
            ))
        ''',

        "successful_requests": f'''
            sum(increase(
                http_requests_total{{endpoint="/api",status=~"2.."}}[{window}]
            )) or vector(0)
        ''',

        "failed_requests": f'''
            sum(increase(
                http_requests_total{{endpoint="/api",status=~"5.."}}[{window}]
            )) or vector(0)
        ''',

        "fast_requests": f'''
            sum(increase(
                http_request_duration_seconds_bucket{{
                    endpoint="/api",
                    le="{latency_threshold}"
                }}[{window}]
            )) or vector(0)
        '''
    }

    burn_rate_queries = {}

    for window in SLO_CONFIG["burn_rate_windows"]:
        burn_rate_queries[window] = {
            "total": f'''
                sum(rate(
                    http_requests_total{{endpoint="/api"}}[{window}]
                ))
            ''',
            "failed": f'''
                sum(rate(
                    http_requests_total{{
                        endpoint="/api",
                        status!~"2.."
                    }}[{window}]
                ))
            '''
        }

    try:
        measurements = {
            name: query_prometheus(query)
            for name, query in queries.items()
        }
        burn_rate_measurements = {}

        for window, window_queries in burn_rate_queries.items():
            burn_rate_measurements[window] = {
                "total": query_prometheus(window_queries["total"]),
                "failed": query_prometheus(window_queries["failed"])
            }

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail="Prometheus is unavailable"
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc

    total = measurements["total_requests"]

    if total is None or total <= 0:
        raise HTTPException(
            status_code=503,
            detail="Insufficient request data for SLO evaluation"
        )

    successful = measurements["successful_requests"] or 0.0
    failed = measurements["failed_requests"] or 0.0
    fast = measurements["fast_requests"] or 0.0

    actual_failed = max(0.0, total - successful)

    availability_sli = successful / total
    latency_sli = fast / total
    error_rate_sli = failed / total

    availability = evaluate_success_ratio(
        availability_sli,
        SLO_CONFIG["availability"]["target"]
    )

    latency = evaluate_success_ratio(
        latency_sli,
        SLO_CONFIG["latency"]["target"]
    )

    error_rate = evaluate_error_rate(
        error_rate_sli,
        SLO_CONFIG["error_rate"]["maximum"]
    )

    allowed_error_rate = (
        1 - SLO_CONFIG["availability"]["target"]
    )

    burn_rates = {}

    for window, values in burn_rate_measurements.items():
        window_total = values["total"]
        window_failed = values["failed"] or 0.0

        if window_total is None or window_total <= 0:
            burn_rates[window] = None
            continue

        observed_error_rate = window_failed / window_total

        burn_rates[window] = round(
            observed_error_rate / allowed_error_rate, 2
        )

    allowed_failures = (
        total * (1 - SLO_CONFIG["availability"]["target"])
    )

    return {
        "service": "observability-api",
        "evaluation_window": window,

        "request_volume": {
            "total": round(total, 2),
            "successful": round(successful, 2),
            "failed_5xx": round(failed, 2),
            "failed_for_availability": round(actual_failed, 2),
            "within_latency_threshold": round(fast, 2)
        },

        "error_budget": {
            "allowed_failures": round(allowed_failures, 2),
            "actual_failures": round(actual_failed, 2),
            "burn_rate": availability["burn_rate"],
            "budget_consumed_percent": availability[
                "budget_consumed_percent"
            ],
            "budget_remaining_percent": availability[
                "budget_remaining_percent"
            ]
        },

        "slis": {
            "availability": availability,
            "latency": latency,
            "error_rate": error_rate
        },
        "burn_rates": burn_rates
    }
