"""
Database models for Marvel Mosaic.

Author: Sai Saketh Gooty Kase
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    subscribe_news = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class FavoriteCharacter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    character_id = models.IntegerField(db_index=True)
    rank = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "character_id")
        ordering = ("rank", "id")

    def __str__(self):
        return f"{self.user.username} → character {self.character_id}"


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    character_id = models.IntegerField(db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username}: {self.content[:60]}"


class Reply(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"{self.user.username} → post {self.post_id}: {self.content[:60]}"
