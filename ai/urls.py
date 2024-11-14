from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('submit_prompt/', views.SubmitPromptView.as_view(), name='submit_prompt'),
    path('thread/<int:thread_id>/', views.ThreadDetailView.as_view(), name='thread_detail'),
    path('create_thread/', views.CreateThreadView.as_view(), name='create_thread'),
]
