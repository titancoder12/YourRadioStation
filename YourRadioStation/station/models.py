from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Extended user profile to store additional user information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    connected_to_spotify = models.BooleanField(default=False)
    spotify_access_token = models.CharField(max_length=500, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=500, blank=True, null=True)
    spotify_token_expires_at = models.DateTimeField(blank=True, null=True)
    spotify_display_name = models.CharField(max_length=100, blank=True, null=True)
    spotify_email = models.EmailField(blank=True, null=True)
    spotify_subscription = models.CharField(max_length=50, blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.user.username}'s Profile: {self.spotify_display_name or 'No Spotify Account'}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    instance.userprofile.save()
