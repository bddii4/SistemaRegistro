import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Usuario(AbstractUser):
    ROL_CHOICES = [('admin', 'Administrador'), ('empleado', 'Empleado')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='empleado')

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    @property
    def es_admin(self):
        return self.rol == 'admin'


class Reporte(models.Model):
    """Reporte que envía el empleado cada 30 minutos."""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente revisión'),
        ('revisado', 'Revisado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reportes')
    actividad = models.TextField(verbose_name='Actividad actual')
    avances = models.TextField(verbose_name='Avances', blank=True)
    observaciones = models.TextField(verbose_name='Observaciones', blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'

    def __str__(self):
        return f'{self.usuario.username} – {self.creado_en:%d/%m/%Y %H:%M}'


class SolicitudReporte(models.Model):
    """Solicitud manual del admin o automática del scheduler."""
    TIPO = [('manual', 'Manual'), ('automatica', 'Automática')]
    ESTADO = [('pendiente', 'Pendiente'), ('respondida', 'Respondida'), ('expirada', 'Expirada')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitudes_enviadas'
    )
    empleado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True,
        related_name='solicitudes_recibidas'
    )
    tipo = models.CharField(max_length=10, choices=TIPO, default='manual')
    estado = models.CharField(max_length=10, choices=ESTADO, default='pendiente')
    creado_en = models.DateTimeField(auto_now_add=True)
    expira_en = models.DateTimeField()

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Solicitud de Reporte'
        verbose_name_plural = 'Solicitudes de Reporte'

    def __str__(self):
        return f'{self.tipo} → {self.empleado} [{self.estado}]'

    @property
    def expirada(self):
        return timezone.now() > self.expira_en