from django.contrib import admin
from .models import Category, Location, Post


# Register your models here.
admin.site.register([Category, Location, Post])
