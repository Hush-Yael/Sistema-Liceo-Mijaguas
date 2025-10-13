from django.contrib import admin
from django.contrib.auth.models import Group
from usuarios.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin

from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.admin import ModelAdmin


admin.site.unregister(Group)

BaseUserAdmin.list_display = ["username", "email", "is_staff", "is_active"]
BaseUserAdmin.search_fields = ["username", "email"]

BaseUserAdmin.fieldsets = (
    (None, {"fields": ("username", "password")}),
    (("Información personal"), {"fields": ("email",)}),
    (
        ("Permisos"),
        {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            ),
        },
    ),
    (("Fechas importantes"), {"fields": ("last_login", "date_joined")}),
)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
