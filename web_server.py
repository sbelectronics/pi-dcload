#!/usr/bin/env python
import os
import sys
import dcload_control

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dcload_django.settings")

    from django.core.management import execute_from_command_line

    dcload_control.startup()

    execute_from_command_line([sys.executable, "runserver", "0.0.0.0:80", "--noreload"])
