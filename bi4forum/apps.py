from django.apps import AppConfig
from django.conf import settings
#from .signals import create_profile
from django.db.models.signals import post_save, post_migrate

class ForumConfig(AppConfig):
    name = 'forum'

    def ready(self):
        from . import signals
        from .models import Post, Thread
        post_save.connect(signals.create_profile, sender=settings.AUTH_USER_MODEL)



