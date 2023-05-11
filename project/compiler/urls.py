from django.urls import path

from . import views


app_name = 'compiler'
urlpatterns = [
    path('file_delete/', views.file_delete, name='file_delete'),
    path('delete_directory/', views.delete_directory, name='delete_directory'),
    path('create_directory/', views.create_directory, name='create_directory'),
    path('file_upload/', views.file_upload, name='file_upload'),
    path('', views.index, name='index'),
    
]