from django.apps import AppConfig


class DataviewerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dataviewer"
    verbose_name = "KOD Data Viewer"

    def ready(self):
        from . import sources  # noqa: F401  (runs the register() calls)
