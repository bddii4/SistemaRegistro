import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class MonitorConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f'empleado_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        if self.user.rol == 'admin':
            await self.channel_layer.group_add('admins', self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if self.user.is_authenticated and self.user.rol == 'admin':
            await self.channel_layer.group_discard('admins', self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('tipo') == 'reporte_ws':
            # El empleado manda su reporte por WebSocket (alternativa al form)
            reporte = await self.guardar_reporte(data)
            await self.channel_layer.group_send('admins', {
                'type': 'nuevo_reporte',
                'payload': {
                    'empleado': self.user.get_full_name() or self.user.username,
                    'actividad': data.get('actividad', '')[:100],
                    'timestamp': reporte.creado_en.strftime('%H:%M'),
                }
            })
            await self.send(json.dumps({'tipo': 'confirmacion', 'mensaje': 'Reporte guardado'}))

    async def solicitud_reporte(self, event):
        """Llega del admin o Celery → activa el modal en el empleado."""
        await self.send(json.dumps({
            'tipo': 'solicitud',
            'solicitud_id': event['solicitud_id'],
        }))

    async def nuevo_reporte(self, event):
        """Admin recibe notificación de nuevo reporte en tiempo real."""
        await self.send(json.dumps({
            'tipo': 'nuevo_reporte',
            'payload': event['payload'],
        }))

    @database_sync_to_async
    def guardar_reporte(self, data):
        from tareas.models import Reporte, SolicitudReporte
        sol = SolicitudReporte.objects.filter(
            id=data.get('solicitud_id'), estado='pendiente'
        ).first()
        if sol:
            sol.estado = 'respondida'
            sol.save()
        return Reporte.objects.create(
            usuario=self.user,
            actividad=data.get('actividad', ''),
            avances=data.get('avances', ''),
            observaciones=data.get('observaciones', ''),
        )