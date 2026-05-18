from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count
from django.views.decorators.http import require_POST

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timedelta
import json, csv

from .models import Usuario, Reporte, SolicitudReporte
from .forms import RegistroForm, ReporteForm, UsuarioAdminForm
from .tasks import re_notificar_solicitud


def solo_admin(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.rol != 'admin':
            return redirect('dashboard_empleado')
        return func(request, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@never_cache
def registro(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = 'empleado'
            user.save()
            messages.success(request, 'Cuenta creada correctamente. Inicia sesión.')
            return redirect('login')
    else:
        form = RegistroForm()
    return render(request, 'tareas/registro.html', {'form': form})


@login_required
def home(request):
    if request.user.rol == 'admin':
        return redirect('dashboard_admin')
    return redirect('dashboard_empleado')


@login_required
@never_cache
def dashboard_empleado(request):
    if request.user.rol == 'admin':
        return redirect('dashboard_admin')

    mis_reportes = Reporte.objects.filter(usuario=request.user)[:10]
    total = Reporte.objects.filter(usuario=request.user).count()
    hoy = Reporte.objects.filter(
        usuario=request.user,
        creado_en__date=timezone.now().date()
    ).count()

    ctx = {
        'mis_reportes': mis_reportes,
        'total_reportes': total,
        'reportes_hoy': hoy,
        'form': ReporteForm(),
    }
    return render(request, 'tareas/dashboard_empleado.html', ctx)


@login_required
@require_POST
def enviar_reporte(request):
    form = ReporteForm(request.POST)
    if form.is_valid():
        reporte = form.save(commit=False)
        reporte.usuario = request.user
        reporte.ip_origen = request.META.get('REMOTE_ADDR')
        reporte.save()

        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)('admins', {
                'type': 'nuevo_reporte',
                'payload': {
                    'empleado': request.user.get_full_name() or request.user.username,
                    'actividad': reporte.actividad[:100],
                    'timestamp': timezone.localtime(reporte.creado_en).strftime('%H:%M'),
                }
            })
        except Exception:
            pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'mensaje': 'Reporte guardado correctamente'})
        messages.success(request, 'Reporte enviado correctamente ✓')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'errores': form.errors}, status=400)
        messages.error(request, 'Por favor completa todos los campos requeridos.')

    return redirect('dashboard_empleado')


@login_required
@solo_admin
@never_cache
def dashboard_admin(request):
    total_usuarios = Usuario.objects.filter(rol='empleado').count()
    total_reportes = Reporte.objects.count()
    reportes_hoy = Reporte.objects.filter(creado_en__date=timezone.now().date()).count()
    ultimos_reportes = Reporte.objects.select_related('usuario').all()[:8]
    usuarios_activos = Usuario.objects.filter(rol='empleado', is_active=True).count()

    ctx = {
        'total_usuarios': total_usuarios,
        'total_reportes': total_reportes,
        'reportes_hoy': reportes_hoy,
        'ultimos_reportes': ultimos_reportes,
        'usuarios_activos': usuarios_activos,
    }
    return render(request, 'tareas/dashboard_admin.html', ctx)


@login_required
@solo_admin
def lista_reportes(request):
    reportes = Reporte.objects.select_related('usuario').all()

    usuario_id = request.GET.get('usuario')
    fecha = request.GET.get('fecha')
    if usuario_id:
        reportes = reportes.filter(usuario__id=usuario_id)
    if fecha:
        reportes = reportes.filter(creado_en__date=fecha)

    empleados = Usuario.objects.filter(rol='empleado')
    ctx = {
        'reportes': reportes,
        'empleados': empleados,
        'filtro_usuario': usuario_id,
        'filtro_fecha': fecha,
    }
    return render(request, 'tareas/lista_reportes.html', ctx)


@login_required
@solo_admin
def detalle_reporte(request, pk):
    reporte = get_object_or_404(Reporte, pk=pk)
    if request.method == 'POST' and 'marcar_revisado' in request.POST:
        reporte.estado = 'revisado'
        reporte.save()
        messages.success(request, 'Reporte marcado como revisado.')
        return redirect('lista_reportes')
    return render(request, 'tareas/detalle_reporte.html', {'reporte': reporte})


@login_required
@solo_admin
def exportar_reportes_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="reportes_regintra.csv"'
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Usuario', 'Nombre completo', 'Fecha', 'Hora', 'Actividad', 'Avances', 'Observaciones', 'Estado'])

    for r in Reporte.objects.select_related('usuario').all():
        writer.writerow([
            r.usuario.username,
            r.usuario.get_full_name(),
            r.creado_en.strftime('%d/%m/%Y'),
            r.creado_en.strftime('%H:%M'),
            r.actividad,
            r.avances,
            r.observaciones,
            r.get_estado_display(),
        ])
    return response


@login_required
@solo_admin
def lista_usuarios(request):
    usuarios = Usuario.objects.filter(rol='empleado').annotate(num_reportes=Count('reportes'))
    return render(request, 'tareas/lista_usuarios.html', {'usuarios': usuarios})


@login_required
@solo_admin
def crear_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            rol = request.POST.get('rol', 'empleado')
            user.rol = rol
            user.save()
            messages.success(request, f'Usuario {user.username} creado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = RegistroForm()
    return render(request, 'tareas/form_usuario.html', {'form': form, 'titulo': 'Crear usuario'})


@login_required
@solo_admin
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado correctamente.')
            return redirect('lista_usuarios')
    else:
        form = UsuarioAdminForm(instance=usuario)
    return render(request, 'tareas/form_usuario.html', {'form': form, 'titulo': 'Editar usuario', 'usuario': usuario})


@login_required
@solo_admin
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        nombre = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario {nombre} eliminado.')
        return redirect('lista_usuarios')
    return render(request, 'tareas/confirmar_eliminar.html', {'objeto': usuario, 'tipo': 'usuario'})


@login_required
@solo_admin
def toggle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = not usuario.is_active
    usuario.save()
    estado = 'activado' if usuario.is_active else 'desactivado'
    messages.success(request, f'Usuario {usuario.username} {estado}.')
    return redirect('lista_usuarios')


@login_required
@require_POST
def api_trigger_reporte(request):
    try:
        if request.user.rol != 'admin':
            return JsonResponse({'error': 'Sin permiso'}, status=403)

        data = json.loads(request.body or '{}')
        empleado_id = data.get('empleado_id')
        channel_layer = get_channel_layer()

        if empleado_id:
            empleados = Usuario.objects.filter(id=empleado_id, rol='empleado', is_active=True)
        else:
            empleados = Usuario.objects.filter(rol='empleado', is_active=True)

        notificados = 0
        for emp in empleados:
            sol = SolicitudReporte.objects.create(
                admin=request.user,
                empleado=emp,
                tipo='manual',
                estado='pendiente',
                expira_en=timezone.now() + timedelta(minutes=10),
            )
            try:
                async_to_sync(channel_layer.group_send)(
                    f'empleado_{emp.id}',
                    {'type': 'solicitud_reporte', 'solicitud_id': str(sol.id)}
                )
            except Exception:
                pass
            try:
                re_notificar_solicitud.apply_async(
                    args=[str(sol.id)],
                    countdown=300,
                )
            except Exception:
                pass
            notificados += 1

        return JsonResponse({'ok': True, 'notificados': notificados})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@solo_admin
def api_stats(request):
    hoy = timezone.now().date()
    return JsonResponse({
        'total_reportes': Reporte.objects.count(),
        'reportes_hoy': Reporte.objects.filter(creado_en__date=hoy).count(),
        'usuarios_activos': Usuario.objects.filter(rol='empleado', is_active=True).count(),
    })