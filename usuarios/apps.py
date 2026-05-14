# Registro de la app 'usuarios' (mantenida para compatibilidad con migraciones viejas).
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuarios'