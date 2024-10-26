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

# SSL Configuration for Redis with certificate validation
celery_app.conf.update(
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,  # Require SSL certificate validation
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,  # Require SSL certificate validation
    }
)

if __name__ == '__main__':
    celery_app.start()