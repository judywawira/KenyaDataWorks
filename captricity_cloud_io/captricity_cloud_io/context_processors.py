from django.conf import settings
from django.contrib.sites.models import Site

def site(request):
    """Adds the site wide context to the default template context"""
    return {
        'site': Site.objects.get_current(),
        'CAPTRICITY_SCHEMA_URL': settings.CAPTRICITY_SCHEMA_URL,
        'CAPTRICITY_API_TARGET': settings.API_TARGET,
    }

