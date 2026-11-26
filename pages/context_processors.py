import os


def site_config(request):
    return {
        "EMAILJS_SERVICE_ID": os.environ.get("EMAILJS_SERVICE_ID", ""),
        "EMAILJS_TEMPLATE_ID": os.environ.get("EMAILJS_TEMPLATE_ID", ""),
        "EMAILJS_PUBLIC_KEY": os.environ.get("EMAILJS_PUBLIC_KEY", ""),
        "CONTACT_EMAIL": os.environ.get("CONTACT_EMAIL", ""),
    }
