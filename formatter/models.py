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
