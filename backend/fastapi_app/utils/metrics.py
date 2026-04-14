"""
Prometheus metrics configuration for FastAPI.
"""
import os

from fastapi import Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# Metrics
http_requests_total = Counter(
    'fastapi_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'fastapi_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'fastapi_active_connections',
    'Number of active connections'
)

vector_db_queries_total = Counter(
    'fastapi_vector_db_queries_total',
    'Total vector database queries',
    ['operation']
)

embedding_requests_total = Counter(
    'fastapi_embedding_requests_total',
    'Total embedding generation requests',
    ['model']
)


async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    if not os.getenv('ENABLE_METRICS', 'False').lower() == 'true':
        return PlainTextResponse('Metrics disabled', status_code=403)

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

