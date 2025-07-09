from django.db import models
from django.conf import settings

# Create your models here.

class TokenBlacklist(models.Model):
    token = models.TextField()
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'token_blacklist'
        indexes = [
            models.Index(fields=['token']),
        ]

    def __str__(self):
        return f"Blacklisted token (expires: {self.expires_at})"
