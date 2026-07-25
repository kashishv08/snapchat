from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    profile_image = models.ImageField(upload_to="profile", blank=True, null=True)

class FriendRequest(models.Model):
    class StatusChoice(models.TextChoices):
        PENDING = ("pending", "Pending")
        ACCEPTED = ("accepted", "Accepted")

    to_user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="recieved_requests")
    from_user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="sent_requests")
    status = models.CharField(max_length=10, choices=StatusChoice.choices, default=StatusChoice.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("from_user", "to_user")

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.status}"

class Messages(models.Model):
    sender = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="receiver")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to="snaps", blank=True, null=True)

    def __str__(self):
        return f"{self.sender}->{self.receiver} "
