#!/usr/bin/env python
# Punto de entrada principal. Ejecuta comandos de Django (runserver, migrate, etc).
import os, sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("No se pudo importar Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()