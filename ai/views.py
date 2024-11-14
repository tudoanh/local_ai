from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, FormView, View
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages as django_messages
from rag.models import Knowledge, UploadFile
from rag.utils import process_file
from ai.models import Thread, Message
from ai.forms import FileUploadForm, SubmitPromptForm
import ell  # Assuming this is necessary
from django.db import transaction
from django_htmx.http import HttpResponseClientRefresh


# Import your GPT function
from .utils import gpt  # Adjust the import path accordingly

class HomeView(TemplateView):
    template_name = "ai/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uploaded_files'] = UploadFile.objects.order_by('-id').all()
        context['threads'] = Thread.objects.order_by('-id').all()
        # If no thread is selected, create or select the latest
        thread_id = self.request.GET.get('thread_id')
        if thread_id:
            thread = get_object_or_404(Thread, id=thread_id)
        else:
            thread, created = Thread.objects.get_or_create(id=1, defaults={'title': 'Default Thread'})
        context['current_thread'] = thread
        context['messages'] = thread.message_set.order_by('created')  # Assuming 'created' field
        context['submit_form'] = SubmitPromptForm()
        return context

class FileUploadView(FormView):
    template_name = "ai/file_upload.html"
    form_class = FileUploadForm
    success_url = reverse_lazy("ai:home")

    def form_valid(self, form):
        files = self.request.FILES.getlist('files')
        for f in files:
            u = UploadFile.objects.create(file=f)
            process_file(u)
        django_messages.success(self.request, "Files uploaded successfully.")
        return super().form_valid(form)

class DeleteFileView(View):
    def delete(self, request, file_id):
        file = get_object_or_404(UploadFile, id=file_id)
        # Delete the actual file
        if file.file:
            file.file.delete()
        # Delete the database record
        file.delete()

        return HttpResponseClientRefresh()