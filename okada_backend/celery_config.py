from celery.schedules import crontab

# Celery Beat schedule
CELERY_BEAT_SCHEDULE = {
    'expire-rides-every-minute': {
        'task': 'rides.tasks.expire_old_ride_requests',
        'schedule': crontab(minute='*/10'),
    },
}

# Celery settings
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC' 