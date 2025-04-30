import base64
import shutil
from django.db import transaction
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from .models import Template, Category
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse, HttpResponseRedirect, StreamingHttpResponse
import os
from django.conf import settings
from .forms import RepoCreateForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.services.utils import generate_ci_yaml
from apps.services.upload_zip import extract_zip, upload_file_to_repo
from apps.services.zip_utils import create_zip_from_dir
from apps.services.template_processing import process_template


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
        context['is_home'] = True
        return context


def download_template(request, id):
    try:
        # Получаем шаблон из базы данных
        template = Template.objects.get(id=id)
        template_dir = os.path.join(settings.MEDIA_ROOT, template.template_dir)

        # Проверяем, существует ли директория шаблона
        if not os.path.exists(template_dir):
            return HttpResponse(f"Папка шаблона не найдена: {template_dir}", status=404)

        # Формируем имя ZIP-файла
        zip_name = f"{template.name.replace(' ', '_').lower()}.zip"
        zip_path = os.path.join(settings.MEDIA_ROOT, 'temp', zip_name)

        # Создаём ZIP-архив
        zip_path = create_zip_from_dir(template_dir, zip_path)

        # Проверяем, создан ли ZIP-файл
        if not os.path.exists(zip_path):
            return HttpResponse("Не удалось создать ZIP-архив.", status=500)

        # Используем FileResponse для отправки файла
        response = FileResponse(
            open(zip_path, 'rb'),
            as_attachment=True,
            filename=zip_name,
            content_type='application/zip'
        )
        return response

    except Template.DoesNotExist:
        return HttpResponse("Шаблон не найден", status=404)
    # finally:
    #     # Удаляем временный файл, если он существует
    #     if 'zip_path' in locals() and os.path.exists(zip_path):
    #         try:
    #             os.remove(zip_path)
    #         except PermissionError:
    #             print(f"Не удалось удалить файл {zip_path}: файл занят другим процессом.")



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
            project_name = form.cleaned_data['project_name']
            python_version = form.cleaned_data['python_version']
            test_command = form.cleaned_data['test_command']
            template = get_object_or_404(Template, id=template_id)
            token = request.user.profile.github_token
            owner = request.user.social_auth.get(provider='github').extra_data['login']

            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }

            # Проверка доступности имени репозитория
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

            if response.status_code != 201:
                return JsonResponse({"error": response.json().get("message", "Неизвестная ошибка")}, status=400)

            repo_url = response.json()["html_url"]

            # Получаем имя ветки по умолчанию
            repo_info_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            repo_info = requests.get(repo_info_url, headers=headers).json()
            default_branch = repo_info['default_branch']
            print(f"Ветка по умолчанию: {default_branch}")

            # Путь к исходной папке шаблона
            template_dir = os.path.join(settings.MEDIA_ROOT, template.template_dir)

            if not os.path.exists(template_dir):
                return JsonResponse({"error": "Папка шаблона не найдена."}, status=400)

            # Создаём временную папку для обработанных файлов
            temp_output_dir = os.path.join(settings.MEDIA_ROOT, 'temp', f"processed_{template.name}_{template_id}")
            os.makedirs(temp_output_dir, exist_ok=True)

            # Заменяем переменные в файлах
            variables = {
                'project_name': project_name,
            }
            try:
                process_template(template_dir, temp_output_dir, variables)
            except Exception as e:
                shutil.rmtree(temp_output_dir, ignore_errors=True)
                return JsonResponse({"error": f"Ошибка обработки шаблона: {str(e)}"}, status=400)

            # Генерация и сохранение ci.yml, если заполнены поля CI
            if python_version and test_command:
                try:
                    ci_params = {
                        'python_version': python_version,
                        'test_command': test_command,
                        'node_version': python_version  # Для Node.js
                    }
                    ci_yaml = generate_ci_yaml(template, ci_params)

                    # Создаём директорию .github/workflows/ в temp_output_dir
                    ci_dir = os.path.join(temp_output_dir, '.github', 'workflows')
                    os.makedirs(ci_dir, exist_ok=True)

                    # Сохраняем ci.yml в temp_output_dir
                    ci_path = os.path.join(ci_dir, 'ci.yml')
                    with open(ci_path, 'w', encoding='utf-8') as f:
                        f.write(ci_yaml)
                except Exception as e:
                    print(f"Ошибка генерации ci.yml: {str(e)}")
                    return JsonResponse({"error": f"Ошибка генерации ci.yml: {str(e)}"}, status=400)

            # Логируем содержимое temp_output_dir
            print(f"Содержимое {temp_output_dir}:")
            for root, _, files in os.walk(temp_output_dir):
                for file in files:
                    print(f" - {os.path.join(root, file)}")

            # Загружаем обработанные файлы на GitHub
            for root, _, files in os.walk(temp_output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, temp_output_dir).replace('\\', '/')
                    print(f"Загрузка {file_path} как {relative_path} на ветку {default_branch}")
                    upload_response = upload_file_to_repo(owner, repo_name, file_path, relative_path, token, branch=default_branch)
                    if upload_response.status_code not in (201, 200):
                        print(f"Ошибка загрузки файла {file}: {upload_response.json()}")
                        return JsonResponse({"error": f"Ошибка загрузки файла {file}: {upload_response.json().get('message')}"}, status=400)

            # Удаляем временную папку
            shutil.rmtree(temp_output_dir, ignore_errors=True)

            return render(request, 'templates_app/repo_created.html', {'repo_url': repo_url})

        return render(request, self.template_name, {
            'form': form,
            'template_id': template_id
        })

            # zip_path = template.file.path

            # temp_dir = extract_zip(zip_path)
            # print(f"Распакованные файлы в {temp_dir}:")
            # for root, dirs, files in os.walk(temp_dir):
            #     print(f"Папка: {root}")
            #     for file in files:
            #         print(f"Файл: {file}")

            # for root, _, files in os.walk(temp_dir):
            #     for file in files:
            #         file_path = os.path.join(root, file)
            #         relative_path = os.path.relpath(file_path, temp_dir)
            #         print(f"Загрузка {file_path} как {relative_path}")
            #         upload_response = upload_file_to_repo(owner, repo_name, file_path, relative_path, token)
            #         print(f"Ответ API: {upload_response.status_code}, {upload_response.json()}")
            #         if upload_response.status_code != 201:
            #             import shutil
            #             shutil.rmtree(temp_dir)
            #             return JsonResponse({"error": f"Ошибка загрузки файла {file}: {upload_response.json().get('message')}"}, status=400)
            # import shutil
            # shutil.rmtree(temp_dir)
            # return render(request, 'templates_app/repo_created.html', {'repo_url': repo_url})

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

        # return render(request, self.template_name, {
        #     'form': form,
        #     'template_id': template_id
        # })


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
