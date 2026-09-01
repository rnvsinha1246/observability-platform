# Production-Grade Observability Platform

A production-style observability platform built to monitor application health, request traffic, latency, and reliability using modern SRE practices.

## Features

- FastAPI-based REST service
- Health check endpoint
- Prometheus-compatible `/metrics` endpoint
- HTTP request and status code monitoring
- Request latency tracking using histograms
- Prometheus metrics collection
- Grafana dashboards
- Docker-based monitoring stack

## Architecture

The platform follows a pull-based observability architecture where the FastAPI application exposes telemetry, Prometheus collects and stores the metrics, and Grafana provides visualization and analysis.

```text
                         ┌──────────────────┐
                         │      Client      │
                         │  / API Traffic   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     FastAPI      │
                         │    :8000         │
                         │                  │
                         │  REST Endpoints  │
                         │  /health         │
                         │  /metrics        │
                         └────────┬─────────┘
                                  │
                           Metrics Scraping
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Prometheus    │
                         │      :9090       │
                         │                  │
                         │  Metrics Storage │
                         │     + PromQL     │
                         └────────┬─────────┘
                                  │
                               PromQL
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Grafana      │
                         │      :3000       │
                         │                  │
                         │    Dashboards    │
                         │   Visualization  │
                         └──────────────────┘



Tech Stack
- Python 3.13
- FastAPI
- Uvicorn
- Prometheus
- Grafana
- Docker
- Docker Compose



Project Structure

observability-platform/
│
├── app/
│   ├── main.py
│   ├── metrics.py
│   └── requirements.txt
│
├── prometheus/
│   └── prometheus.yml
│
├── docker-compose.yml
├── .gitignore
└── README.md



Running Locally

Create and activate the virtual environment:

    python3.13 -m venv .venv
    source .venv/bin/activate

Install dependencies:

    cd app
    python -m pip install -r requirements.txt

Start the application:

    uvicorn main:app --reload

Start Prometheus and Grafana from the project root:

docker compose up -d
Services
Service	URL
FastAPI	http://localhost:8000
API Docs	http://localhost:8000/docs
Metrics	http://localhost:8000/metrics
Prometheus	http://localhost:9090
Grafana	http://localhost:3000


Current Status

The initial observability pipeline is complete, with application metrics being collected by Prometheus and visualized through Grafana.

The next phase focuses on SLI/SLO monitoring, error budgets, alerting, and synthetic monitoring.