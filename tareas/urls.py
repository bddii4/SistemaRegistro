from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registro/', views.registro, name='registro'),
    path('dashboard/', views.dashboard_empleado, name='dashboard_empleado'),
    path('enviar/', views.enviar_reporte, name='enviar_reporte'),
    path('panel/', views.dashboard_admin, name='dashboard_admin'),
    path('panel/reportes/', views.lista_reportes, name='lista_reportes'),
    path('panel/reportes/<int:pk>/', views.detalle_reporte, name='detalle_reporte'),
    path('panel/reportes/exportar/', views.exportar_reportes_csv, name='exportar_reportes'),
    path('panel/usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('panel/usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('panel/usuarios/<int:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('panel/usuarios/<int:pk>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('panel/usuarios/<int:pk>/toggle/', views.toggle_usuario, name='toggle_usuario'),
    path('api/trigger/', views.api_trigger_reporte, name='api_trigger'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
