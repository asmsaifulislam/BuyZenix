from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Catalog"

    def ready(self):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass
