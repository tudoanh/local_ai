from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('delete-file/<int:file_id>/', views.DeleteFileView.as_view(), name='delete_file'),
]
