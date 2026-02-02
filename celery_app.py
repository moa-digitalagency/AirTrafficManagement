"""
Celery Configuration for ATM-RDC
Handles asynchronous task processing for flight tracking and data ingestion
"""
import os
from celery import Celery

# Redis URL from environment or default
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Initialize Celery app
celery = Celery(
    'atm_rdc',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['tasks.flight_tasks', 'tasks.invoice_tasks']
)

# Celery configuration
celery.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Africa/Kinshasa',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
)

# Beat schedule for periodic tasks
celery.conf.beat_schedule = {
    'fetch-flight-positions': {
        'task': 'tasks.flight_tasks.fetch_flight_positions',
        'schedule': 5.0,  # Every 5 seconds
    },
    'check-overflights': {
        'task': 'tasks.flight_tasks.check_airspace_entries',
        'schedule': 10.0,  # Every 10 seconds
    },
    'check-airport-movements': {
        'task': 'tasks.flight_tasks.check_airport_movements',
        'schedule': 10.0,  # Every 10 seconds
    },
    'generate-pending-invoices': {
        'task': 'tasks.invoice_tasks.generate_pending_invoices',
        'schedule': 3600.0,  # Every hour
    },
}

if __name__ == '__main__':
    celery.start()
