from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin
from .models import Category, Template


@admin.register(Category)
class CategoryAdmin(DjangoMpttAdmin):
    pass

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')