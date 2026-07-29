from celery import Celery
from .config import settings
celery_app = Celery("coach", broker=settings.redis_url, backend=settings.redis_url)
@celery_app.task
def schedule_reviews():
    """Reserved for spaced-repetition review scheduling."""
    return "review schedule checked"
