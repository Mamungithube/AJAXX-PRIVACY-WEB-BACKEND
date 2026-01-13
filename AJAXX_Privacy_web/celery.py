# AJAXX_Privacy_web/celery.py

import os
from celery import Celery
from celery.signals import task_postrun, task_prerun

# Django settings module set করুন
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AJAXX_Privacy_web.settings')

app = Celery('AJAXX_Privacy_web')

# Django settings থেকে configuration load করুন
app.config_from_object('django.conf:settings', namespace='CELERY')

# ✅ এই configuration গুলো add করুন
app.conf.update(
    # Result backend configuration
    result_backend='django-db',  # Django DB তে save হবে
    result_extended=True,  # Extended result info save করবে
    result_expires=3600 * 24 * 7,  # 7 days
    
    # Task tracking
    task_track_started=True,  # Task start হলে track করবে
    task_send_sent_event=True,  # Task sent event পাঠাবে
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # Serialization
    accept_content=['json'],
    task_serializer='json',
    result_serializer='json',
    
    # Timezone
    timezone='America/New_York',
    enable_utc=True,
    
    # Broker
    broker_connection_retry_on_startup=True,
)

# Automatically discover tasks from all installed apps
app.autodiscover_tasks()


# ✅ Task lifecycle signals (optional - for debugging)
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Task শুরু হওয়ার আগে"""
    print(f"🚀 Task starting: {task.name} [{task_id}]")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    """Task শেষ হওয়ার পরে"""
    print(f"✅ Task completed: {task.name} [{task_id}] - State: {state}")


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')