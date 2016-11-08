from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_save


class ForumConfig(AppConfig):
    name = 'forum'

    def ready(self):
        from . import signals
        post_save.connect(signals.create_profile, sender=settings.AUTH_USER_MODEL)
