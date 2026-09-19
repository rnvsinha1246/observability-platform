import time
import random
from fastapi import FastAPI, Request
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse

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
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
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
    return {
        "slo_target": SLO_TARGET,
        "error_budget": calculate_error_budget()
    }