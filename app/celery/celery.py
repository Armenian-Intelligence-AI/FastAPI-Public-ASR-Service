from celery import Celery
from app.core.config import settings
import ssl
import os

# Redis URL should use rediss:// scheme
redis_endpoint = settings.REDIS_URL

# Create Celery app
celery_app = Celery(
    "worker",
    broker=redis_endpoint,
    backend=redis_endpoint,
    include=["app.celery.tasks"]
)

# Determine if SSL should be required based on the environment
if settings.ENV == "DEV":
    broker_ssl_config = {}  # No SSL certificate requirement in development
    backend_ssl_config = {}
else:
    broker_ssl_config = {'ssl_cert_reqs': ssl.CERT_REQUIRED}
    backend_ssl_config = {'ssl_cert_reqs': ssl.CERT_REQUIRED}

# SSL Configuration for Redis with conditional certificate validation
celery_app.conf.update(
    broker_use_ssl=broker_ssl_config,
    redis_backend_use_ssl=backend_ssl_config
)

if __name__ == '__main__':
    celery_app.start()