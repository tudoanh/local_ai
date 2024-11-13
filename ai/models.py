from django.db import models
from django_extensions.db.models import TimeStampedModel


class Thread(TimeStampedModel):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"Thread {self.id} - {self.title}"


class Message(TimeStampedModel):
    class Role(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"
        AI = "ai", "AI"

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    text = models.TextField()
    previous_message = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    metadata = models.JSONField(default=dict)

    def __str__(self):
        return f"Message {self.id} - {self.text[:50]}"
