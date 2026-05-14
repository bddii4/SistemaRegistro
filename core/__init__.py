# Inicializa Celery para tareas programadas (reportes automáticos cada 30 min).
from .celery import app as celery_app
__all__ = ('celery_app',)