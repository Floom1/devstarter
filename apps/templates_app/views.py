from django.shortcuts import render
from django.views.generic import ListView
from .models import Template, Category
from django.shortcuts import get_object_or_404


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
