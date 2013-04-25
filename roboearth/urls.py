# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: defining the URLs of the web interface

  Copyright 2011 Björn Schießle <schiessle@ipvs.uni-stuttgart.de>
                 Universität Stuttgart, IPVS, Abteilung Bildverstehen
  
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from django.conf.urls.defaults import *
#from django.contrib.auth.views import login, logout
from django.conf import settings

#(r'^static/(?P<path>.*)$', 'django.views.static.serve',
#        {'document_root': settings.STATIC_DOC_ROOT}),


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'roboearth.db.views.views.index'),
    (r'^documentation/$', 'roboearth.db.views.views.documentation'),
    (r'^about/$', 'roboearth.db.views.views.about'),
    # Action Recipes:                   
    (r'^recipes/$', 'roboearth.db.views.recipes.submitForm'),
    (r'^recipes/request/$', 'roboearth.db.views.recipes.requestForm'),
    (r'^recipes/submit', 'roboearth.db.views.recipes.submit'),
    (r'^recipes/update', 'roboearth.db.views.recipes.update'),
    (r'^recipes/result', 'roboearth.db.views.recipes.request'),
    # Objects:                   
    (r'^objects/$', 'roboearth.db.views.objects.submitForm'),
    (r'^objects/request$', 'roboearth.db.views.objects.requestForm'),
    (r'^objects/update', 'roboearth.db.views.objects.update'),
    (r'^objects/submit', 'roboearth.db.views.objects.submit'),
    (r'^objects/result', 'roboearth.db.views.objects.request'),
    # Environments:                   
    (r'^environments/$', 'roboearth.db.views.environments.submitForm'),
    (r'^environments/request/$', 'roboearth.db.views.environments.requestForm'),
    (r'^environments/submit', 'roboearth.db.views.environments.submit'),
    (r'^environments/update', 'roboearth.db.views.environments.update'),
    (r'^environments/result', 'roboearth.db.views.environments.request'),
    # Robots:                   
    (r'^robots/$', 'roboearth.db.views.robots.submitForm'),
    (r'^robots/request/$', 'roboearth.db.views.robots.requestForm'),
    (r'^robots/submit', 'roboearth.db.views.robots.submit'),
    (r'^robots/result', 'roboearth.db.views.robots.request'),
    # Objects Location:
    (r'^locations/objects/$', 'roboearth.db.views.locations.objects.submitForm'),
    (r'^locations/objects/request/$', 'roboearth.db.views.locations.objects.requestForm'),
    (r'^locations/objects/submit', 'roboearth.db.views.locations.objects.submit'),
    (r'^locations/objects/result', 'roboearth.db.views.locations.objects.request'),
    # SeRQL:
    (r'^serql/$', 'roboearth.db.views.serql.serql'),
    (r'^serql/result', 'roboearth.db.views.serql.request'),
    # user handling
    (r'^login$',  'roboearth.db.views.users.loginForm'),
    (r'^profile$',  'roboearth.db.views.users.profile'),
    (r'^myrobots$', 'roboearth.db.views.robots.myRobots'),
    (r'^subscriptions$', 'roboearth.db.views.users.subscriptions'),
    (r'^subscribe$', 'roboearth.db.views.users.subscribe'),
    (r'^unsubscribe$', 'roboearth.db.views.users.unsubscribe'),
    (r'^newsfeed$', 'roboearth.db.views.users.newsfeed'),
    (r'^deleteUser$',  'roboearth.db.views.users.delete_user'),
    (r'^accounts/login/$',  'roboearth.db.views.users.login'),
    (r'^logout$', 'roboearth.db.views.users.logout'),
    (r'^register$', 'roboearth.db.views.users.registerForm'),
    (r'^accounts/create/$', 'roboearth.db.views.users.create'),
    (r'^accounts/created/$', 'roboearth.db.views.users.created'),
    (r'^accounts/manage/$', 'roboearth.db.views.users.manage'),
    (r'^accounts/delete$', 'roboearth.db.views.users.delete'),
    (r'^accounts/activate$', 'roboearth.db.views.users.activate'),
    (r'^accounts/deactivate$', 'roboearth.db.views.users.deactivate'),
    (r'^accounts/update$', 'roboearth.db.views.users.update'),
    # misc:
    (r'^db$', 'roboearth.db.views.views.dbContent'),
    (r'^deleteEntity', 'roboearth.db.views.views.deleteEntity'),
    (r'^finalDelete', 'roboearth.db.views.views.finalDelete'),
    (r'^deleteBinary', 'roboearth.db.views.views.deleteBinary'),
    (r'^api/0.1/', include('roboearth.api_0_1.urls')),
    (r'^stylesheets/(?P<path>.*)$', 'django.views.static.serve', #ONLY FOR DEV!!!
     {'document_root': settings.STATIC_DOC_ROOT+'stylesheets'}),
    (r'^img/(?P<path>.*)$', 'django.views.static.serve', #ONLY FOR DEV!!!
     {'document_root': settings.STATIC_DOC_ROOT+'img'}), 
    (r'^data/(?P<path>.*)$', 'django.views.static.serve', #ONLY FOR DEV!!!
     {'document_root': settings.STATIC_DOC_ROOT+'../../data'}), 
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
