from django.db import transaction
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from .models import Template, Category
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings
from .forms import RepoCreateForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin



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


class CategoryListView(ListView):
    model = Category
    template_name = 'templates_app/category.html'
    context_object_name = 'categories'
    # paginate_by = 1

    def get_queryset(self):
        return Category.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Категории'
        context['show_sidebar'] = False
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


class RepoCreateView(LoginRequiredMixin, View):
    template_name = 'templates_app/create_repo.html'

    def get(self, request, template_id):
            form = RepoCreateForm()
            return render(request, self.template_name, {
                'title': 'Добавление названия репозитория',
                'form': form,
                'template_id': template_id
            })

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['title'] = f'Добавление названия репозитория'
    #     if self.request.POST:
    #         context['repo-create_form'] = RepoCreateForm(self.request.POST,
    #                                               instance=self.request.user)
    #     else:
    #         context['repo-create_form'] = RepoCreateForm(instance=self.request.user)
    #     return context

    # def form_valid(self, form):
    #     context = self.get_context_data()
    #     repo_create_form = context['repo-create_form']
    #     with transaction.atomic():
    #         if all([form.is_valid(), repo_create_form.is_valid()]):
    #             repo_create_form.save()
    #             form.save()
    #         else:
    #             context.update({"repo-create_form": repo_create_form})
    #             return self.render_to_response(context)
    #     return super().form_valid(form)


    def post(self, request, template_id):
        form = RepoCreateForm(request.POST)
        if form.is_valid():
            repo_name = form.cleaned_data['repo_name']
            template = get_object_or_404(Template, id=template_id)
            token = request.user.profile.github_token
            owner = request.user.social_auth.get(provider='github').uid

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Проверка доступности имени
            check_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            check_response = requests.get(check_url, headers=headers)

            if check_response.status_code == 200:
                return render(request, self.template_name, {
                    'form': form,
                    'error': 'Имя репозитория уже занято!'
                })
            elif check_response.status_code != 404:
                return render(request, self.template_name, {
                    'form': form,
                    'error': 'Ошибка при проверке имени!'
                })

            # Создание репозитория
            data = {
                "name": repo_name,
                "description": f"Шаблон: {template.description}",
                "private": False,
            }
            response = requests.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json=data
            )

            if response.status_code == 201:
                return JsonResponse({"success": True, "repo_url": response.json()["html_url"]})
            else:
                return JsonResponse({"error": response.json()["message"]}, status=400)
        return render(request, self.template_name, {'form': form})