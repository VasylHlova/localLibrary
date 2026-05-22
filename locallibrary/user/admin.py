from django.contrib import admin

from user.models import CustomUser, UserProfile

admin.site.register(CustomUser)
admin.site.register(UserProfile)
