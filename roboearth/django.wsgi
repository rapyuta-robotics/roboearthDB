import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'roboearth.settings'

sys.path.append('/home/marcus/Downloads/roboearth-20110701')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
