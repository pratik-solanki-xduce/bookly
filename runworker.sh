celery -A src.celery_tasks.app worker --loglevel=INFO &

celery -A src.celery_tasks.app flower
