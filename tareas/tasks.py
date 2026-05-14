# Tareas automáticas de Celery: disparar reportes cada 30min y expirar solicitudes viejas.
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@shared_task
def disparar_reporte_automatico():
    from tareas.models import Usuario, SolicitudReporte

    channel_layer = get_channel_layer()
    empleados = Usuario.objects.filter(rol='empleado', is_active=True)

    for emp in empleados:
        sol = SolicitudReporte.objects.create(
            empleado=emp,
            tipo='automatica',
            estado='pendiente',
            expira_en=timezone.now() + timedelta(minutes=10),
        )
        async_to_sync(channel_layer.group_send)(
            f'empleado_{emp.id}',
            {'type': 'solicitud_reporte', 'solicitud_id': str(sol.id)}
        )

    return f'{empleados.count()} empleados notificados'


@shared_task
def expirar_solicitudes_viejas():
    from tareas.models import SolicitudReporte

    n = SolicitudReporte.objects.filter(
        estado='pendiente',
        expira_en__lt=timezone.now()
    ).update(estado='expirada')

    return f'{n} solicitudes expiradas'