import vobject
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .forms import ContactUploadForm
from .models import Contact
from google_auth_oauthlib.flow import Flow
from django.conf import settings
# views.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pickle
from django.conf import settings
from .models import Contact
from google_auth_oauthlib.flow import Flow
import os
import pickle
from django.shortcuts import render, redirect
from googleapiclient.discovery import build
from django.conf import settings
from .models import Contact


import os
import requests
from google_auth_oauthlib.flow import Flow
from django.shortcuts import redirect
from django.conf import settings
import tempfile


def google_oauth(request):
    # URL du fichier credentials.json
    credentials_url = 'https://example.com/path/to/credentials.json'  # Remplacez par l'URL de votre fichier JSON
    
    # Télécharger le fichier JSON depuis l'URL
    response = requests.get(credentials_url)
    
    if response.status_code == 200:
        # Sauvegarder le fichier téléchargé dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(response.text)
            temp_file_path = temp_file.name
        
        # Set up the OAuth flow using the credentials and scopes
        flow = Flow.from_client_secrets_file(
            temp_file_path,  # Utiliser le fichier temporaire
            scopes=settings.GOOGLE_API_SCOPES,
            redirect_uri=settings.REDIRECT_URI
        )

        # Rediriger l'utilisateur vers la page de consentement OAuth de Google
        authorization_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
        return redirect(authorization_url)
    else:
        # Si le téléchargement échoue, retourner une erreur
        return HttpResponse("Erreur lors du téléchargement du fichier credentials.json", status=500)


def oauth2callback(request):
    # URL du fichier credentials.json
    credentials_url = 'https://example.com/path/to/credentials.json'  # Remplacez par l'URL de votre fichier JSON

    # Télécharger le fichier JSON depuis l'URL
    response = requests.get(credentials_url)
    
    if response.status_code == 200:
        # Sauvegarder le fichier téléchargé dans un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(response.text)
            temp_file_path = temp_file.name

        # Initialiser le flux OAuth2 avec le fichier téléchargé
        flow = Flow.from_client_secrets_file(
            temp_file_path,  # Utiliser le fichier temporaire
            scopes=settings.GOOGLE_API_SCOPES,
            redirect_uri=settings.REDIRECT_URI
        )

        # Récupérer la réponse d'autorisation et récupérer le jeton
        flow.fetch_token(authorization_response=request.build_absolute_uri())

        # Sauvegarder les informations d'identification
        credentials = flow.credentials
        if not os.path.exists('token.pickle'):
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        # Rediriger vers l'importation des contacts
        return redirect('import_google_contacts')
    else:
        # Si le téléchargement échoue, retourner une erreur
        return HttpResponse("Erreur lors du téléchargement du fichier credentials.json", status=500)


def import_google_contacts(request):
    # Charger les informations d'identification à partir du fichier pickle
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # Construire le service API People
    service = build('people', 'v1', credentials=credentials)

    # Récupérer les 10 premiers contacts (exemple)
    results = service.people().connections().list(
        resourceName='people/me',
        personFields='names,emailAddresses,phoneNumbers').execute()

    connections = results.get('connections', [])

    # Itérer à travers les contacts et les sauvegarder dans la base de données
    for person in connections:
        first_name = person.get('names', [{}])[0].get('givenName', '')
        last_name = person.get('names', [{}])[0].get('familyName', '')
        email = person.get('emailAddresses', [{}])[0].get('value', '')
        phone_number = person.get('phoneNumbers', [{}])[0].get('value', '')

        # Formater le numéro de téléphone si nécessaire
        formatted_number = format_number(phone_number)

        # Sauvegarder le contact dans la base de données (éviter les doublons)
        if not Contact.objects.filter(phone_number=phone_number).exists():
            Contact.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                formatted_number=formatted_number
            )

    return redirect('list_contacts')
# Helper function to format phone numbers (add custom logic if needed)
def format_number(phone_number):
    # Example formatting: remove non-numeric characters
    formatted_number = ''.join(filter(str.isdigit, phone_number))
    return formatted_number

def format_number(phone_number):
    """
    Formate un numéro de téléphone en suivant les règles spécifiques :
    - Si le numéro commence par "+229", ajoute le préfixe "01" si nécessaire.
    - Si le numéro fait exactement 8 chiffres, formate en "+229 01 xx xx xx xx".
    - Sinon, retourne le numéro tel quel.
    """
    phone_number = phone_number.strip()  # Supprime les espaces inutiles

    if phone_number.startswith("+229"):
        # Numéro international déjà avec l'indicatif
        if len(phone_number) == 12:  # Exemple : +22997000000
            return f"+229 01 {phone_number[5:7]} {phone_number[7:9]} {phone_number[9:11]}"
        return phone_number  # Retourne le numéro tel quel si bien formaté

    elif len(phone_number) == 8 and phone_number.isdigit():
        # Numéro local de 8 chiffres (exemple : 97000000)
        return f"+229 01 {phone_number[:2]} {phone_number[2:4]} {phone_number[4:6]} {phone_number[6:]}"
    
    else:
        # Retourne le numéro tel quel si non reconnu
        return phone_number


def import_contacts(request):
    """
    Fonction pour importer des contacts depuis un fichier CSV ou VCF, 
    et supprimer les anciens contacts liés à la session avant chaque importation.
    """
    if request.method == "POST":
        form = ContactUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Supprimer les contacts liés à la session avant l'importation
            session_key = request.session.session_key
            Contact.objects.filter(session_key=session_key).delete()

            file = request.FILES['csv_file']
            try:
                # Vérifie si c'est un fichier CSV ou VCF
                if file.name.endswith('.csv'):
                    decoded_file = file.read().decode('utf-8-sig')
                    reader = csv.DictReader(decoded_file.splitlines())
                    for row in reader:
                        first_name = row.get('first_name', '').strip()
                        last_name = row.get('last_name', '').strip()
                        email = row.get('email', '').strip()
                        phone_number = row.get('phone_number', '').strip()
                        formatted_number = format_number(phone_number)

                        # Enregistrement dans la base de données
                        Contact.objects.create(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone_number=phone_number,
                            formatted_number=formatted_number,
                            session_key=session_key  # Ajout du session_key
                        )
                    messages.success(request, "Contacts importés avec succès depuis le fichier CSV.")
                elif file.name.endswith('.vcf'):
                    vcf_content = file.read().decode('utf-8')
                    for vcard in vobject.readComponents(vcf_content):
                        first_name = vcard.n.value.given if hasattr(vcard.n.value, 'given') else ''
                        last_name = vcard.n.value.family if hasattr(vcard.n.value, 'family') else ''
                        email = vcard.email.value if hasattr(vcard, 'email') else ''
                        phone_number = vcard.tel.value if hasattr(vcard, 'tel') else ''
                        formatted_number = format_number(phone_number)

                        # Enregistrement dans la base de données
                        Contact.objects.create(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone_number=phone_number,
                            formatted_number=formatted_number,
                            session_key=session_key  # Ajout du session_key
                        )
                    messages.success(request, "Contacts importés avec succès depuis le fichier VCF.")
                else:
                    messages.error(request, "Format de fichier non supporté. Veuillez importer un fichier CSV ou VCF.")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'importation : {str(e)}")
        else:
            messages.error(request, "Formulaire invalide. Veuillez réessayer.")
        return redirect('list_contacts')
    else:
        form = ContactUploadForm()
    return render(request, "main/import_contacts.html", {"form": form})


def auto_delete_after_import(request):
    """
    Supprime les contacts associés à la session après l'importation.
    """
    if 'imported' in request.session:
        session_key = request.session.session_key
        Contact.objects.filter(session_key=session_key).delete()
        del request.session['imported']  # Réinitialise la session après suppression
        messages.success(request, "Les contacts ont été supprimés après l'importation.")

from django.contrib.sessions.models import Session

def download_csv(request):
    """
    Fonction pour exporter les contacts dans un fichier CSV et les supprimer après le téléchargement.
    """
    # Export des contacts au format CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'

    writer = csv.writer(response)
    writer.writerow(['Prénom', 'Nom', 'Email', 'Numéro formaté'])

    contacts = Contact.objects.all()
    for contact in contacts:
        writer.writerow([contact.first_name, contact.last_name, contact.email, contact.formatted_number])

    # Supprimer les contacts après le téléchargement
    Contact.objects.all().delete()

    return response

def download_vcard(request):
    """
    Fonction pour exporter les contacts dans un fichier VCF (vCard) et les supprimer après le téléchargement.
    """
    # Export des contacts au format vCard
    response = HttpResponse(content_type='text/vcard')
    response['Content-Disposition'] = 'attachment; filename="contacts.vcf"'

    contacts = Contact.objects.all()
    vcard_content = ""

    for contact in contacts:
        vcard_content += f"""
BEGIN:VCARD
VERSION:3.0
N:{contact.last_name};{contact.first_name}
FN:{contact.first_name} {contact.last_name}
EMAIL:{contact.email}
TEL;TYPE=WORK,VOICE:{contact.formatted_number}
END:VCARD
"""

    response.write(vcard_content)

    # Supprimer les contacts après le téléchargement
    Contact.objects.all().delete()

    return response



def list_contacts(request):
    """
    Fonction pour afficher la liste des contacts enregistrés dans la base de données.
    """
    contacts = Contact.objects.all().order_by('first_name')
    return render(request, "main/list_contacts.html", {"contacts": contacts})