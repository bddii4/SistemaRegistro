# Formularios: registro de usuario, envío de reporte, edición de usuario por admin
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Reporte


class RegistroForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, label='Nombre', required=True)
    last_name = forms.CharField(max_length=50, label='Apellido', required=True)
    email = forms.EmailField(label='Correo electrónico', required=True)

    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['autocomplete'] = 'off'


class ReporteForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ('actividad', 'avances', 'observaciones')
        widgets = {
            'actividad': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '¿Qué estás haciendo en este momento?',
            }),
            'avances': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe los avances del día...',
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones o bloqueos...',
            }),
        }
        labels = {
            'actividad': 'Actividad actual',
            'avances': 'Avances',
            'observaciones': 'Observaciones',
        }


class UsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ('username', 'first_name', 'last_name', 'email', 'rol', 'is_active')
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'})
                   for f in ('username', 'first_name', 'last_name', 'email')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].widget.attrs['class'] = 'form-select'
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'