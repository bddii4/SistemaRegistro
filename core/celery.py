# Configuración de Celery y programación de tareas automáticas (reportes cada 30min, expirar solicitudes).
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('regintra')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'reporte-automatico-30min': {
        'task': 'tareas.tasks.disparar_reporte_automatico',
        'schedule': crontab(minute='*/30'),
    },
    'expirar-solicitudes': {
        'task': 'tareas.tasks.expirar_solicitudes_viejas',
        'schedule': crontab(minute='*/5'),
    },
}