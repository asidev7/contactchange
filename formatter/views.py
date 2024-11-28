import os
import pickle
import base64
import qrcode
import tempfile
import requests
import csv
import vobject

from io import BytesIO
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import qrcode
from PIL import Image

from .forms import ContactUploadForm, vCardForm
from .models import Contact, vCard
from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from .models import vCard


def google_oauth(request):
    # URL du fichier credentials.json
    credentials_url = 'https://raw.githubusercontent.com/asidev7/contactchange/refs/heads/main/credentials.json'  # Remplacez par l'URL de votre fichier JSON
    
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
    credentials_url = 'https://raw.githubusercontent.com/asidev7/contactchange/refs/heads/main/credentials.json'  # Remplacez par l'URL de votre fichier JSON

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


     
def format_number(phone_number):
    """
    Formate un numéro de téléphone en suivant les règles spécifiques :
    - Ajoute le préfixe "01" si nécessaire pour les numéros béninois.
    - Reconnaît les formats locaux, nationaux, et internationaux.
    - Retourne le numéro formaté ou tel quel si déjà conforme.

    Arguments :
    phone_number (str) : Le numéro de téléphone à formater.

    Retourne :
    str : Le numéro de téléphone formaté.
    """
    # Supprime tous les espaces et caractères non numériques sauf '+'
    phone_number = ''.join(filter(lambda x: x.isdigit() or x == '+', phone_number))

    if phone_number.startswith("+229"):
        # Numéro international béninois avec indicatif
        if len(phone_number) == 12:  # Format sans espace : +22997000000
            # Ajoute le préfixe "01" si nécessaire
            return f"+229 01 {phone_number[5:7]} {phone_number[7:9]} {phone_number[9:11]}"
        elif len(phone_number) == 15 and phone_number[4:6] == "01":  # Déjà bien formaté
            return phone_number
        return phone_number  # Retourne tel quel si inconnu

    elif len(phone_number) == 8 and phone_number.isdigit():
        # Numéro local de 8 chiffres (exemple : 97000000 ou 64003675)
        return f"+229 01 {phone_number[:2]} {phone_number[2:4]} {phone_number[4:6]} {phone_number[6:]}"

    elif len(phone_number) == 10 and phone_number.startswith('229'):
        # Numéro national avec indicatif béninois (exemple : 22990776888)
        return f"+229 01 {phone_number[3:5]} {phone_number[5:7]} {phone_number[7:9]} {phone_number[9:]}"

    # Retourne le numéro tel quel si non reconnu ou déjà formaté
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



def vcard(request, vcard_id=None):
    if vcard_id:
        vcard = vCard.objects.get(id=vcard_id)
        form = vCardForm(request.POST or None, request.FILES or None, instance=vcard)
    else:
        vcard = None
        form = vCardForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        vcard = form.save()

        # Génération du QR code pour la vCard
        qr = qrcode.make(f"https://127.0.0.1:8000/vcard/{vcard.id}/")
        qr_image = BytesIO()
        qr.save(qr_image, format='PNG')
        qr_image.seek(0)

        # Convertir l'image QR en base64
        qr_image_base64 = base64.b64encode(qr_image.getvalue()).decode('utf-8')

        # Rediriger vers la page de succès ou la page de détails de la vCard
        return render(request, 'main/vcardsuccess.html', {'vcard': vcard, 'qr_image_base64': qr_image_base64})

    return render(request, 'main/vcardplus.html', {'form': form, 'vcard': vcard})


def vcard_pdf(request, vcard_id):
    # Récupération des données de la vCard depuis la base
    vcard = get_object_or_404(vCard, id=vcard_id)

    # Générer les données au format vCard
    vcard_data = f"""
    BEGIN:VCARD
    VERSION:3.0
    N:{vcard.last_name};{vcard.first_name}
    FN:{vcard.first_name} {vcard.last_name}
    EMAIL:{vcard.email}
    TEL:{vcard.phone_number}
    ORG:{vcard.company}
    ADR:{vcard.address}
    END:VCARD
    """

    # Générer un QR code contenant les données vCard
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(vcard_data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Convertir l'image du QR code en flux mémoire
    qr_buffer = BytesIO()
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    # Créer un PDF avec les informations et le QR code
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="vcard_{vcard_id}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, f"Nom: {vcard.first_name} {vcard.last_name}")
    p.drawString(100, 780, f"Email: {vcard.email}")
    p.drawString(100, 760, f"Téléphone: {vcard.phone_number}")
    p.drawString(100, 740, f"Entreprise: {vcard.company}")
    p.drawString(100, 720, f"Adresse: {vcard.address}")

    # Ajouter le QR code au PDF
    p.drawImage(qr_buffer, 100, 600, width=150, height=150)

    p.showPage()
    p.save()
    return response

# Vue pour afficher les détails de la vCard et son QR code
def vcard_detail(request, vcard_id):
    vcard = get_object_or_404(vCard, id=vcard_id)
    qr = qrcode.make(f"https://127.0.0.1:8000/vcard/{vcard.id}/")

    # Convertir le QR code en base64
    qr_io = BytesIO()
    qr.save(qr_io, format='PNG')
    qr_image_base64 = base64.b64encode(qr_io.getvalue()).decode()

    context = {
        'vcard': vcard,
        'qr_image_base64': qr_image_base64,
    }
    return render(request, 'main/vcard_detail.html', context)

# Génération d'un QR code stylé
def generate_styled_qr(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="teal", back_color="white").convert("RGBA")

    # Ajouter un logo au centre (facultatif)
    logo_path = 'static/images/logo.png'  # Modifier en fonction de votre projet
    try:
        logo = Image.open(logo_path)
        logo = logo.resize((50, 50))  # Ajuster la taille du logo
        pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
        img.paste(logo, pos, mask=logo)
    except FileNotFoundError:
        pass  # Si le logo n'existe pas, continuer sans lui

    return img

# Télécharger la vCard au format .vcf
def download_vcard2(request, vcard_id):
    vcard = get_object_or_404(vCard, id=vcard_id)

    # Contenu de la vCard
    vcard_content = f"""
    BEGIN:VCARD
    VERSION:3.0
    N:{vcard.last_name};{vcard.first_name}
    FN:{vcard.first_name} {vcard.last_name}
    EMAIL:{vcard.email}
    TEL:{vcard.phone_number}
    ORG:{vcard.company}
    ADR:{vcard.address}
    END:VCARD
    """
    response = HttpResponse(vcard_content, content_type='text/vcard')
    response['Content-Disposition'] = f'attachment; filename="{vcard.first_name}_{vcard.last_name}.vcf"'
    return response