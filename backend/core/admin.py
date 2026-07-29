from .models import FriendRequest, Messages, User, Chat
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class MyUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("profile_image",)}),)

admin.site.register(FriendRequest)
admin.site.register(Messages)
admin.site.register(User, MyUserAdmin)
admin.site.register(Chat)
