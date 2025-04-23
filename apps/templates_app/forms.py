from django import forms
from apps.accounts.models import Profile



class RepoCreateForm(forms.Form):
    class_css = {"class": "form-control mb-1"}

    repo_name = forms.CharField(
        max_length=128,
        label='Имя репозитория',
        widget=forms.TextInput(attrs={"rows": 1, "class": "form-control mb-1"})
    )
    project_name = forms.CharField(
        max_length=100,
        label='Название проекта',
        widget=forms.TextInput(attrs={"class": "form-control mb-1"})
    )

    # Флажок для включения CI
    enable_ci = forms.BooleanField(
        label='Включить CI',
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input", "id": "enable_ci"})
    )

    # Поля для CI (необязательные)
    python_version = forms.ChoiceField(
        choices=[('3.8', '3.8'), ('3.9', '3.9'), ('3.10', '3.10')],
        label='Версия Python',
        required=False,
        widget=forms.Select(attrs={"class": "form-control mb-1", "id": "python_version"})
    )
    test_command = forms.CharField(
        max_length=100,
        label='Команда для тестов',
        initial='pytest',
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control mb-1", "id": "test_command"})
    )