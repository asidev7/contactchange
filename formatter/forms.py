from django import forms

from django import forms
from .models import vCard, SocialLink

class ContactUploadForm(forms.Form):
    csv_file = forms.FileField(label="Importer un fichier CSV")



class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ['platform', 'url']

class vCardForm(forms.ModelForm):
    class Meta:
        model = vCard
        fields = ['first_name', 'last_name', 'phone_number', 'whatsapp_number', 'email',
                  'website', 'bio', 'company', 'address', 'photo', 'company_info', 'social_links']
