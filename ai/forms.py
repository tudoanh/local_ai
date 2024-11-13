from django import forms
from django.forms import ModelForm, Form
from rag.models import UploadFile
from rag.utils import process_file


class FileUploadForm(forms.ModelForm):
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}), required=True)

    class Meta:
        model = UploadFile
        fields = ['files']

    def clean_files(self):
        files = self.files.getlist('files')
        print(files)
        for file in files:
            if not file.name.endswith(('.pdf', '.txt')):
                raise forms.ValidationError('Only PDF and TXT files are allowed.')
        return files


class SubmitPromptForm(Form):
    prompt = forms.CharField(widget=forms.Textarea)
    uploaded_files = forms.ModelMultipleChoiceField(
        queryset=UploadFile.objects.all(), required=False
    )
