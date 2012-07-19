import sys

sys.path.insert(0, '/usr/NCPP')
#os.environ['DJANGO_SETTINGS_MODULE'] = 'ncpp_settings'
import ncpp_settings as settings

import django.core.management
django.core.management.setup_environ(settings)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')

command.validate()

import django.conf
import django.utils

django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
