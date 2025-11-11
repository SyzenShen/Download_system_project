from django import forms
from .models import File
from django.conf import settings


# Regular form
class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    upload_method = forms.CharField(label="Upload Method", max_length=20,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_file(self):
        file = self.cleaned_data['file']
        # Enforce optional size limit
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', None)
        if max_size is not None and file.size > max_size:
            raise forms.ValidationError(f"File too large; maximum allowed size is {int(max_size / (1024 * 1024 * 1024))} GB")
        
        # No strict file-type filtering; all formats are allowed
        
        # return cleaned data is very important.
        return file


# Model form
class FileUploadModelForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('file', 'upload_method',)

        widgets = {
            'upload_method': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data['file']
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', None)
        if max_size is not None and file.size > max_size:
            raise forms.ValidationError(f"File too large; maximum allowed size is {int(max_size / (1024 * 1024 * 1024))} GB")
        
        # Only validate by size; all formats are accepted
        
        # return cleaned data is very important.
        return file

    def save(self, commit=True):
        instance = super().save(commit=False)
        try:
            # Preserve the original filename from the uploaded file
            instance.original_filename = self.cleaned_data.get('file').name
        except Exception:
            pass
        if commit:
            instance.save()
        return instance
