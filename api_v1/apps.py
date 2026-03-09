from django.apps import AppConfig


class ApiV1Config(AppConfig):
    name = 'api_v1'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import api_v1.signals  # noqa: F401
