from django.urls import path
from . import views

urlpatterns = [
    path('', views.enviar_actividad, name='dashboard'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('avisos/', views.avisos, name='avisos'),
]