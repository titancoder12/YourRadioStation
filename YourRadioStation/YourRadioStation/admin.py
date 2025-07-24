# myapp/admin.py
from django.contrib import admin
from .models import UserProfile

admin.site.register(UserProfile)
admin.site.site_header = "Your Radio Station Admin"
admin.site.site_title = "Your Radio Station Admin Portal"
admin.site.index_title = "Welcome to the Your Radio Station Admin Portal"
