#!/usr/bin/python

import json
import sys
import os
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = """Changes the domain used to generate HIT urls"""
    args = ""
    
    option_list = BaseCommand.option_list + (
        make_option('--domain', '-d',
            dest='domain',
            default='localhost:8000',
            help='Address of domain'),
        )

    
    def handle(self, *args, **options):
        if not options['domain']:
            raise CommandError("Please specify what you would like to change the domain to using the -d flag.  See help for details")
        s = Site.objects.get_current()
        print "Domain was:", s.domain
        s.domain = options['domain']
        s.save()
        new_s = Site.objects.get_current()
        print "Domain is now:", new_s.domain
