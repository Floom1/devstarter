from django.urls import path
from .views import *


urlpatterns = [
    path('', CategoryListView.as_view(), name='home'),
    path('category/<slug:slug>/', TemplateListView.as_view(), name='category_templates'),
    path('download/<int:id>', download_template, name='download_template'),
]