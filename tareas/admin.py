from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Reporte, SolicitudReporte


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'email', 'rol', 'is_active', 'date_joined')
    list_filter = ('rol', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (('Rol', {'fields': ('rol',)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Rol', {'fields': ('rol',)}),)


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'actividad_corta', 'estado', 'creado_en')
    list_filter = ('estado', 'creado_en')
    search_fields = ('usuario__username', 'actividad')
    readonly_fields = ('id', 'creado_en', 'ip_origen')

    def actividad_corta(self, obj):
        return obj.actividad[:60] + '...' if len(obj.actividad) > 60 else obj.actividad
    actividad_corta.short_description = 'Actividad'


@admin.register(SolicitudReporte)
class SolicitudReporteAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'estado', 'creado_en', 'expira_en')
    list_filter = ('tipo', 'estado')
    readonly_fields = ('id', 'creado_en')