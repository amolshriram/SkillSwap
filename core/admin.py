from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Conversation, Message, Skill, SwapRequest, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("full_name", "email", "first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("full_name", "email", "username", "password1", "password2"),
            },
        ),
    )
    list_display = ("id", "full_name", "email", "username", "is_staff")
    search_fields = ("full_name", "email", "username")
    ordering = ("id",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "category", "skill_name", "skill_level")
    list_filter = ("category", "skill_level")
    search_fields = ("skill_name", "user__full_name", "user__email")


@admin.register(SwapRequest)
class SwapRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "receiver", "skill_offered", "skill_requested", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("sender__full_name", "receiver__full_name", "skill_offered", "skill_requested")


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "created_at")
    search_fields = ("user1__full_name", "user2__full_name", "user1__email", "user2__email")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    search_fields = ("body", "sender__full_name", "sender__email")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

