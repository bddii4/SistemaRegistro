from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


DELAY_RE_NOTIFICACION = 300  # 5 minutos


def _enviar_solicitud_ws(channel_layer, empleado_id, solicitud_id):
    async_to_sync(channel_layer.group_send)(
        f'empleado_{empleado_id}',
        {'type': 'solicitud_reporte', 'solicitud_id': str(solicitud_id)}
    )


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
        _enviar_solicitud_ws(channel_layer, emp.id, sol.id)
        re_notificar_solicitud.apply_async(
            args=[str(sol.id)],
            countdown=DELAY_RE_NOTIFICACION,
        )

    return f'{empleados.count()} empleados notificados'


@shared_task(bind=True, max_retries=0)
def re_notificar_solicitud(self, solicitud_id):
    from tareas.models import SolicitudReporte

    try:
        sol = SolicitudReporte.objects.get(
            id=solicitud_id,
            estado='pendiente',
        )
    except SolicitudReporte.DoesNotExist:
        return f'Solicitud {solicitud_id} ya fue respondida o no existe'

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'empleado_{sol.empleado_id}',
        {
            'type': 're_solicitud_reporte',
            'solicitud_id': str(sol.id),
            'mensaje': 'Aún tienes un reporte pendiente por enviar',
        }
    )
    return f'Re-notificación enviada para solicitud {solicitud_id}'


@shared_task
def expirar_solicitudes_viejas():
    from tareas.models import SolicitudReporte

    n = SolicitudReporte.objects.filter(
        estado='pendiente',
        expira_en__lt=timezone.now()
    ).update(estado='expirada')

    return f'{n} solicitudes expiradas'