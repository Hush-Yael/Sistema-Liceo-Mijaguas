from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from usuarios.models import User

UserAdmin.list_display = ["username", "email", "is_staff", "is_active"]
UserAdmin.search_fields = ["username", "email"]

UserAdmin.fieldsets = (
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

admin.site.register(User, UserAdmin)
