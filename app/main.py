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
    SLO_TARGET,
    calculate_availability,
    calculate_error_budget,
    calculate_budget_consumed
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
    queries = {
        "availability": '''
            sum(rate(http_requests_total{endpoint="/api",status=~"2.."}[5m]))
            /
            sum(rate(http_requests_total{endpoint="/api"}[5m]))
        ''',

        "latency": '''
            sum(rate(http_request_duration_seconds_bucket{endpoint="/api",le="0.3"}[5m]))
            /
            sum(rate(http_request_duration_seconds_count{endpoint="/api"}[5m]))
        ''',

        "error_rate": '''
            sum(rate(http_requests_total{endpoint="/api",status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total{endpoint="/api"}[5m]))
        '''
    }

    try:
        measurements = {
            name: query_prometheus(query)
            for name, query in queries.items()
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

    if any(value is None for value in measurements.values()):
        raise HTTPException(
            status_code=503,
            detail="Insufficient Prometheus data to evaluate SLIs"
        )

    availability = evaluate_success_ratio(
        measurements["availability"],
        SLO_CONFIG["availability"]["target"]
    )

    latency = evaluate_success_ratio(
        measurements["latency"],
        SLO_CONFIG["latency"]["target"]
    )

    error_rate = evaluate_error_rate(
        measurements["error_rate"],
        SLO_CONFIG["error_rate"]["maximum"]
    )

    return {
        "service": "observability-api",
        "evaluation_window": "5m",
        "slis": {
            "availability": availability,
            "latency": latency,
            "error_rate": error_rate
        }
    }
