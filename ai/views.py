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

class SubmitPromptView(View):
    def post(self, request, *args, **kwargs):
        form = SubmitPromptForm(request.POST)
        thread_id = request.POST.get('thread_id')
        thread = get_object_or_404(Thread, id=thread_id)

        if form.is_valid():
            prompt = form.cleaned_data['prompt']

            with transaction.atomic():
                # Create user message
                user_message = Message.objects.create(
                    thread=thread,
                    role=Message.Role.USER,
                    text=prompt,
                    previous_message=None  # You can set this based on your logic
                )

                # Call gpt function to get AI response
                ai_response = gpt(prompt)

                # Create AI message
                ai_message = Message.objects.create(
                    thread=thread,
                    role=Message.Role.AI,
                    text=ai_response,
                    previous_message=user_message
                )

            # Fetch updated messages
            messages_qs = thread.message_set.order_by('created')
            context = {'messages': messages_qs}

            if request.headers.get('HX-Request'):
                return render(request, 'ai/chat_messages.html', context)
            else:
                return redirect(reverse('ai:home') + f"?thread_id={thread.id}")
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'ai/submit_prompt.html', {'form': form, 'thread_id': thread_id})
            else:
                return render(request, 'ai/submit_prompt.html', {'form': form})


class ThreadDetailView(TemplateView):
    template_name = "ai/chat_messages.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread_id = self.kwargs.get('thread_id')
        thread = get_object_or_404(Thread, id=thread_id)
        context['messages'] = thread.message_set.order_by('created')
        return context


class CreateThreadView(View):
    def post(self, request, *args, **kwargs):
        new_thread = Thread.objects.create(title="New Thread")
        threads = Thread.objects.order_by('-id').all()
        context = {
            'threads': threads,
            'current_thread': new_thread,
            'messages': new_thread.message_set.order_by('created'),
        }
        if request.headers.get('HX-Request'):
            # Update the thread list and load the new thread's messages
            threads_list = render(request, 'ai/threads_list.html', {'threads': threads, 'current_thread': new_thread})
            chat_messages = render(request, 'ai/chat_messages.html', {'messages': new_thread.message_set.order_by('created')})
            return JsonResponse({
                'threads_list': threads_list.content.decode('utf-8'),
                'chat_messages': chat_messages.content.decode('utf-8'),
                'thread_id': new_thread.id,
            })
        else:
            return redirect(reverse('ai:home') + f"?thread_id={new_thread.id}")

