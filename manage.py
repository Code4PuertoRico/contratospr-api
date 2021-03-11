#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    configuration = os.getenv("ENVIRONMENT", "development").title()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contratospr.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", configuration)

    if sys.version_info.major == 3 and sys.version_info.mior >= 7:
        Exception("Python version >= 3.7 is required")

    try:
        from configurations.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
