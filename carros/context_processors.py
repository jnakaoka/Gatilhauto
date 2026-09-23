from django.conf import settings


def contact_details(request):
    return {
        "CONTACT_PHONE_DISPLAY": settings.CONTACT_PHONE_DISPLAY,
        "CONTACT_PHONE_E164": settings.CONTACT_PHONE_E164,
        "CONTACT_PHONE_TEL": settings.CONTACT_PHONE_TEL,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
    }
