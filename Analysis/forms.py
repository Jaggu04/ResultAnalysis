from django import forms
from .models import ExcelFile

class ExcelFileUploadForm(forms.ModelForm):
    year_of_admission = forms.IntegerField(label="Year of Admission")
    
    class Meta:
        model = ExcelFile
        fields = ['year_of_admission', 'studying_year', 'division', 'uploaded_file']

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if not file.name.endswith(('.xls', '.xlsx')):
            raise forms.ValidationError("Only Excel files are allowed!")
        return file
