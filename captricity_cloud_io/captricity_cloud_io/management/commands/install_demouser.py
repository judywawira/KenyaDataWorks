
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site

from captricity_cloud_io.models import UserProfile

class Command(BaseCommand):
    help = """Creates a default super user"""
    args = ""

    def handle(self, *args, **options):
        u, created = User.objects.get_or_create(username='alice', is_superuser=True)
        u.set_password('1234')
        u.save()
        uprofile = UserProfile.objects.get_or_create(user=u)
