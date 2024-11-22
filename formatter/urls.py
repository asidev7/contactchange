
from django.urls import path
from .views import import_contacts, list_contacts,download_vcard,download_csv,google_oauth,oauth2callback,import_google_contacts

urlpatterns = [
    path('import/', import_contacts, name='import_contacts'),
    path('list/', list_contacts, name='list_contacts'),
    path('download_vcard/', download_vcard, name='download_vcard'),
    path('download_csv/', download_csv, name='download_csv'),
    path('google_oauth/', google_oauth, name='google_oauth'),
    path('oauth2callback/', oauth2callback, name='oauth2callback'),
    path('import_google_contacts/', import_google_contacts, name='import_google_contacts'),

]
