from django.urls import path
from .views import *


urlpatterns = [
    path('category/<slug:slug>/', TemplateListView.as_view(), name='category_templates'),
]