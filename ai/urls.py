from django.urls import path
from .views import HomeView, FileUploadView, FileListView, SubmitPromptView

app_name = 'ai'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('upload/', FileUploadView.as_view(), name='file_upload'),
    path('files/', FileListView.as_view(), name='file_list'),
    path('submit-prompt/', SubmitPromptView.as_view(), name='submit_prompt'),
]
