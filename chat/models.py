from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    room = models.CharField(max_length=255)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    delivered = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text[:20]