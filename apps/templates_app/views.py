from django.shortcuts import render
from django.views.generic import ListView
from .models import Template, Category
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings

class TemplateListView(ListView):
    model = Template # {% url 'download_template' template.id %} !!!!!
    template_name = 'templates_app/templates.html'
    context_object_name = 'templates'
    paginate_by = 4
    extra_content = {'title': 'Шаблоны'}
    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.kwargs.get('slug')
        if not slug:
            return Template.objects.none()

        category = get_object_or_404(Category, slug=slug)

        descendants = category.get_descendants(include_self=True)
        return Template.objects.filter(category__in=descendants)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Шаблоны'

        context['categories'] = Category.objects.all()

        return context




def download_template(request, id):
    try:
        # Получаем объект модели по ID
        file_m = Template.objects.get(id=id)

        # Проверяем, существует ли файл на сервере
        file_path = file_m.file.path
        if os.path.exists(file_path):
            # Открываем файл для чтения
            file = open(file_path, 'rb')

            # Извлекаем оригинальное имя файла
            filename = os.path.basename(file_m.file.name)
            print(f"Полный путь: {file_m.file.name}")
            print(f"Имя файла: {filename}")

            # Создаём ответ с файлом
            response = FileResponse(file)
            # Используем filename* с явной кодировкой UTF-8
            response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{filename}'
            print(f"Заголовок Content-Disposition: {response['Content-Disposition']}")
            return response
        else:
            return HttpResponse(f"Файл не найден: {file_path}", status=404)
    except Template.DoesNotExist:
        return HttpResponse("Шаблон не найден", status=404)