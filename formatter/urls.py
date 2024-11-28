
from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', import_contacts, name='import_contacts'),
    path('list/', list_contacts, name='list_contacts'),
    path('download_vcard/', download_vcard, name='download_vcard'),
    path('vcard',vcard,name="vcard"),
    path('download_csv/', download_csv, name='download_csv'),
    path('google_oauth/', google_oauth, name='google_oauth'),
    path('oauth2callback/', oauth2callback, name='oauth2callback'),

    # Affichage des détails d'une vCard avec le QR Code
    path('vcard/<int:vcard_id>/', vcard_detail, name='vcard_detail'),
    path('vcard/<int:vcard_id>/pdf/', vcard_pdf, name='vcard_pdf'),
    path('vcard/<int:vcard_id>/', vcard_detail, name='vcard_detail'),
    path('vcard/<int:vcard_id>/download/', download_vcard2, name='vcard_download'),


]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)