from django.db import models
from django.conf import settings

class ReporteActividad(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Reportes de Actividad"

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha_creacion}"