from .models import FriendRequest, Messages, User, Chat
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
class MyUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("profile_image",)}),)

class MessagesAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)

class FriendRequestAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at",)

class ChatAdmin(admin.ModelAdmin):
    readonly_fields = ("updated_at", "streak")

admin.site.register(FriendRequest, FriendRequestAdmin)
admin.site.register(Messages, MessagesAdmin)
admin.site.register(User, MyUserAdmin)
admin.site.register(Chat, ChatAdmin)
