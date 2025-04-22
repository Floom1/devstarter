from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin
from django import forms
import zipfile
import os
from django.conf import settings
from .models import Category, Template


@admin.register(Category)
class CategoryAdmin(DjangoMpttAdmin):
    pass


class TemplateAdminForm(forms.ModelForm):
    # Поле для загрузки ZIP-файла в админке
    zip_file = forms.FileField(label='Загрузить ZIP-архив', required=False)

    class Meta:
        model = Template
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        zip_file = self.cleaned_data.get('zip_file')

        if zip_file:
            # Генерируем уникальное имя для папки на основе имени шаблона
            template_name = instance.name.replace(' ', '_').lower()
            template_dir = os.path.join(settings.MEDIA_ROOT, 'templates', template_name)

            # Создаём папку, если её нет
            os.makedirs(template_dir, exist_ok=True)

            # Сохраняем ZIP-файл временно
            temp_zip_path = os.path.join(settings.MEDIA_ROOT, 'templates', zip_file.name)
            with open(temp_zip_path, 'wb') as temp_zip:
                for chunk in zip_file.chunks():
                    temp_zip.write(chunk)

            # Распаковываем ZIP
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(template_dir)

            # Удаляем временный ZIP-файл
            os.remove(temp_zip_path)

            # Сохраняем относительный путь к папке в template_dir
            instance.template_dir = os.path.join('templates', template_name)

            # Очищаем поле file, так как ZIP больше не нужен
            instance.file = None

        if commit:
            instance.save()
        return instance


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    form = TemplateAdminForm
    list_display = ('name', 'category', 'template_dir')  # Добавляем template_dir в список отображения