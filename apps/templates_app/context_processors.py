from .models import Category

def add_categories(request):
    return {'categories': Category.objects.all()}

def sidebar_context(request):
    return {'show_sidebar': True}