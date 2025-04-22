from django import forms

from apps.accounts.models import Profile


class RepoCreateForm(forms.Form):
    class_css = {"class": "form-control mb-1"}

    repo_name = forms.CharField(max_length=128,
                          widget=forms.TextInput(attrs={"rows": 1, "class": "form-control mb-1"}))
    project_name = forms.CharField(max_length=100, label='Название проекта')
