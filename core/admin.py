from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra", {"fields": ("gender", "age")}),
    )
    list_display = ("username", "email", "gender", "age", "is_staff")


admin.site.register(User, UserAdmin)
