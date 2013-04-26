import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'roboearth.settings'

sys.path.append('/home/marcus/workspace/roboearth')
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
