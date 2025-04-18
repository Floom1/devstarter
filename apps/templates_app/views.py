import base64
from django.db import transaction
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from .models import Template, Category
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
import os
from django.conf import settings
from .forms import RepoCreateForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.services.upload_zip import extract_zip, upload_file_to_repo


class TemplateListView(ListView):
    model = Template
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



    def post(self, request, template_id):
        form = RepoCreateForm(request.POST)
        if form.is_valid():
            repo_name = form.cleaned_data['repo_name']
            template = get_object_or_404(Template, id=template_id)
            token = request.user.profile.github_token
            owner = request.user.social_auth.get(provider='github').extra_data['login']

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
                "description": f"Шаблон: {template.description}", # Изменить
                "private": False,
            }
            response = requests.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json=data
            )

            if response.status_code != 201:
                return JsonResponse({"error": response.json().get("message", "Неизвестная ошибка")}, status=400)

            repo_url = response.json()["html_url"]
            zip_path = template.file.path

            temp_dir = extract_zip(zip_path)
            print(f"Распакованные файлы в {temp_dir}:")
            for root, dirs, files in os.walk(temp_dir):
                print(f"Папка: {root}")
                for file in files:
                    print(f"Файл: {file}")

            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, temp_dir)
                    print(f"Загрузка {file_path} как {relative_path}")
                    upload_response = upload_file_to_repo(owner, repo_name, file_path, relative_path, token)
                    print(f"Ответ API: {upload_response.status_code}, {upload_response.json()}")
                    if upload_response.status_code != 201:
                        import shutil
                        shutil.rmtree(temp_dir)
                        return JsonResponse({"error": f"Ошибка загрузки файла {file}: {upload_response.json().get('message')}"}, status=400)
            import shutil
            shutil.rmtree(temp_dir)
            return render(request, 'templates_app/repo_created.html', {'repo_url': repo_url})

            # with open(file_path, 'rb') as f:
            #     content = base64.b64encode(f.read()).decode('utf-8')

            # upload_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/template.zip"
            # upload_data = {
            #     "message": "Добавлен ZIP-архив с шаблоном",
            #     "content": content
            # }
            # upload_response = requests.put(upload_url, headers=headers, json=upload_data)

            # if upload_response.status_code == 201:
            #     return render(request, 'templates_app/repo_created.html', {'repo_url': repo_url})
            # else:
            #     return JsonResponse({"error": upload_response.json().get("message", "Ошибка загрузки файла")}, status=400)

        return render(request, self.template_name, {
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
