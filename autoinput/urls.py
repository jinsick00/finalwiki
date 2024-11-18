from django.urls import path
from . import views

app_name = 'autoinput'

urlpatterns = [
    path('', views.input_index, name='input_index'),
    path("combine_files", views.combine_files, name="combine_files"),
]