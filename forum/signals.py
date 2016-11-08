from . import models


def create_profile(sender, instance, **kwargs):
    models.UserProfile.objects.get_or_create(user=instance)
