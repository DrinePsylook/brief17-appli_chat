from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    CREATOR = 'CREATOR'
    SUBSCRIBER = 'SUBSCRIBER'

    ROLE_CHOICES = (
        (CREATOR, 'Creator'),
        (SUBSCRIBER, 'Subscriber'),
    )

    profile_photo = models.ImageField(
        verbose_name='Photo de profil',
        upload_to='profile_photos/',
        null=True,
        blank=True,
        default=''
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=SUBSCRIBER)

    #  Champ pour l'authentification faciale
    face_auth_enabled = models.BooleanField(default=False)
    face_image_registered = models.BooleanField(default=False)
    
    def get_profile_photo_url(self):
        """Retourne l'URL de la photo de profil ou l'avatar par défaut"""
        if self.profile_photo and hasattr(self.profile_photo, 'url') and self.profile_photo.name:
            return self.profile_photo.url
        return '/static/images/default_avatar.png'