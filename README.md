# Production-Grade Observability Platform

A production-style observability platform built to monitor application health, request traffic, latency, and reliability using modern SRE practices.

## Current Progress

The project currently includes:

- FastAPI-based application
- Health check endpoint
- Prometheus-compatible `/metrics` endpoint
- HTTP request counting
- HTTP request latency tracking using histograms
- Python runtime metrics
- Isolated Python 3.13 virtual environment

## Tech Stack

- Python 3.13
- FastAPI
- Uvicorn
- Prometheus Client
- Requests
- Schedule

## Project Structure

```text
observability-platform/
│
├── app/
│   ├── main.py
│   ├── metrics.py
│   └── requirements.txt
│
├── .gitignore
└── README.md