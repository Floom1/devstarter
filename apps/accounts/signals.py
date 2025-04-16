from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Profile
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from social_django.models import UserSocialAuth


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(user_logged_in)
def save_github_token(sender, request, user, **kwargs):
    try:
        github_login = UserSocialAuth.objects.get(user=user, provider='github')
        access_token = github_login.access_token
        if access_token:
            user.profile.github_token = access_token
            user.profile.save()
    except UserSocialAuth.DoesNotExist:
        pass