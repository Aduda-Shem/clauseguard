from django.db import models

from reviews.models.contract import Contract


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "USER", "User"
        ASSISTANT = "ASSISTANT", "Assistant"

    contract = models.ForeignKey(Contract, related_name="chat_messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
