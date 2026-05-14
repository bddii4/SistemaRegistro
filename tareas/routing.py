# Rutas WebSocket: /ws/monitor/ para conexión en tiempo real.
from django.urls import re_path
from tareas import consumers

websocket_urlpatterns = [
    re_path(r'ws/monitor/$', consumers.MonitorConsumer.as_asgi()),
]