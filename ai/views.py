from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView
from rag.models import Knowledge, UploadFile
from rag.utils import process_file
from ai.models import Thread, Message
from ai.forms import FileUploadForm, SubmitPromptForm


class HomeView(TemplateView):
    template_name = "ai/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['uploaded_files'] = UploadFile.objects.order_by('-id').all()
        context['threads'] = Thread.objects.order_by('-id').all()
        return context


class FileListView(TemplateView):
    template_name = "ai/file_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files"] = UploadFile.objects.all()
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
        return super().form_valid(form)


class SubmitPromptView(TemplateView):
    template_name = "ai/submit_prompt.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SubmitPromptForm()
        return context
