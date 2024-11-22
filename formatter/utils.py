
def format_number(phone_number):
    if phone_number.startswith('+229'):
        # Ajouter "01" après l'indicatif si absent
        if not phone_number[4:6] == "01":
            return phone_number[:4] + "01" + phone_number[4:]
    return phone_number
