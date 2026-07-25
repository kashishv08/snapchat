from .models import FriendRequest, Messages, User
from django.contrib import admin

# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(Messages)
admin.site.register(User)
