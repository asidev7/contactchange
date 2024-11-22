from django import forms

class ContactUploadForm(forms.Form):
    csv_file = forms.FileField(label="Importer un fichier CSV")
