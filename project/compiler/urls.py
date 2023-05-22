from django.urls import path

from . import views


app_name = 'compiler'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('editor/<str:mode>', views.index, name='index'),
    path('editor/<str:mode>/<int:file_pk>/', views.index, name='index'),

    path('delete_file/<int:file_pk>', views.delete_file, name='delete_file'),
    path('delete_directory/<int:dir_pk>', views.delete_directory, name='delete_directory'),
    path('', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),
]