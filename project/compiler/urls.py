from django.urls import path

from . import views


app_name = 'compiler'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('editor/<str:mode>', views.index, name='index'),
    # path('editor/<str:mode>/<int:file_pk>/', views.index, name='index'),
    path('editor/showfile/<int:file_pk>/', views.show_file, name='showfile'),
    path('showfile/<int:file_pk>/', views.show_file, name='showfile'),
    path('compile/<int:file_pk>/', views.compile_file, name='compile'),
    path('generate_file_tree_html/', views.generate_file_tree_html, name='generate_file_tree_html'),
    path('addFileForm/', views.generate_file_form_html, name="addFileForm"),
    path('addDirectoryForm/', views.generate_directory_form_html, name="addDirectoryForm"),
    path('delete_file/<int:file_pk>', views.delete_file, name='delete_file'),
    path('delete_directory/<int:dir_pk>', views.delete_directory, name='delete_directory'),
    path('', views.login_view, name='index'),
    path('logout/', views.logout_view, name='logout'),
]