from django.db import models

class Contact(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True)  # Clé de session
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    formatted_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



from django.db import models

# Model for Social Links
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('youtube', 'YouTube'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()

    def __str__(self):
        return f"{self.platform} - {self.url}"

# Model for vCard Information
class vCard(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    # Link to social media platforms
    social_links = models.ManyToManyField(SocialLink, blank=True)

    # Information about the company
    company_info = models.TextField(blank=True, null=True)

    # Method to return full name
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name()

    def generate_vcard(self):
        """ Generates vCard format text with all information """
        vcard_data = f"""
BEGIN:VCARD
VERSION:3.0
FN:{self.full_name()}
PHOTO;ENCODING=BASE64;TYPE=JPEG:{self.photo.url if self.photo else ''}
TEL:{self.phone_number}
TEL;TYPE=cell:{self.whatsapp_number if self.whatsapp_number else self.phone_number}
EMAIL:{self.email if self.email else ''}
URL:{self.website if self.website else ''}
ORG:{self.company if self.company else ''}
ADR:{self.address if self.address else ''}
NOTE:{self.bio if self.bio else ''}
"""

        # Add social links
        for social_link in self.social_links.all():
            vcard_data += f"SOCIAL;TYPE={social_link.platform.capitalize()}:{social_link.url}\n"

        vcard_data += f"NOTE:{self.company_info if self.company_info else ''}\n"
        vcard_data += "END:VCARD"
        
        return vcard_data

    def save(self, *args, **kwargs):
        """Override save to auto-generate/update vCard when saved"""
        # You can add logic here to handle more advanced updating if needed
        super().save(*args, **kwargs)
        # Optionally, trigger an update for a related QR code or other logic
