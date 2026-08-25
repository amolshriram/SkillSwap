from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """
    Uses Django auth, but aligns registration fields to the project spec:
    - name (stored as full_name)
    - email (unique)
    - password (handled by Django)
    """

    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        # Keep username required by AbstractUser, but make it consistent.
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.full_name or self.email or super().__str__()


class Skill(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "Beginner", "Beginner"
        INTERMEDIATE = "Intermediate", "Intermediate"
        ADVANCED = "Advanced", "Advanced"

    class Category(models.TextChoices):
        OFFERED = "Offered", "Offered"
        WANTED = "Wanted", "Wanted"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills")
    skill_name = models.CharField(max_length=100)
    skill_level = models.CharField(max_length=20, choices=Level.choices)
    category = models.CharField(max_length=10, choices=Category.choices)

    class Meta:
        unique_together = ("user", "skill_name", "category")
        ordering = ["category", "skill_name"]

    def __str__(self) -> str:
        return f"{self.user} - {self.category}: {self.skill_name} ({self.skill_level})"


class SwapRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ACCEPTED = "Accepted", "Accepted"
        REJECTED = "Rejected", "Rejected"

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_swap_requests"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_swap_requests"
    )

    skill_offered = models.CharField(max_length=100)
    skill_requested = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.sender_id and self.receiver_id and self.sender_id == self.receiver_id:
            raise ValidationError("You cannot send a swap request to yourself.")

    def __str__(self) -> str:
        return f"{self.sender} -> {self.receiver} ({self.status})"


class Conversation(models.Model):
    """
    A private chat between exactly two users.
    We create it after a swap request is accepted.
    """

    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_user1")
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations_as_user2")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(user1=models.F("user2")),
                name="conversation_users_not_equal",
            )
        ]

    @staticmethod
    def get_or_create_between(user_a, user_b):
        if user_a.pk == user_b.pk:
            raise ValidationError("Conversation participants must be different users.")
        low, high = (user_a, user_b) if user_a.pk < user_b.pk else (user_b, user_a)
        convo, _ = Conversation.objects.get_or_create(user1=low, user2=high)
        return convo

    def has_user(self, user) -> bool:
        return user.pk in (self.user1_id, self.user2_id)

    def other_user(self, user):
        return self.user2 if user.pk == self.user1_id else self.user1

    def __str__(self) -> str:
        return f"Conversation: {self.user1} & {self.user2}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def clean(self):
        if self.conversation_id and self.sender_id:
            if not self.conversation.has_user(self.sender):
                raise ValidationError("Sender must be a participant of the conversation.")

    def __str__(self) -> str:
        return f"{self.sender} @ {self.created_at:%Y-%m-%d %H:%M}"

