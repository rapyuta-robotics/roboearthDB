# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: Handle HTTP request regarding environments
  
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

import roboearth.db.roboearth
import roboearth.db.forms
import roboearth.db.views.views
import roboearth.db.transactions.environments
import xml.dom.minidom
import os
from django.http import HttpResponse
from django.template import Context, loader
import roboearth.db.transactions.hdfs_op
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.core.context_processors import csrf
from django.shortcuts import render_to_response


hdfs_op = roboearth.db.transactions.hdfs_op
transaction = roboearth.db.transactions.environments
forms = roboearth.db.forms
views = roboearth.db.views.views
roboearth = roboearth.db.roboearth

#
# Forms
#

def submitForm(request):
    """ show form to submit new environment """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    return render_to_response('submitEnvironment.html', roboearth.webpage_values(request))

def requestForm(request):
    """ show form to request environment """
    return render_to_response('requestEnvironment.html', roboearth.webpage_values(request))

#
# Actions
#

def submit(request):
    """ submit new environment, expected data: id, class, (human readable) description,
    environment, lat (optional), lng (optional)

    For the class "osm" the database will perfom osm based geocoding based on the "id" string"""
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            lat = None
            lng = None
            if request.POST.has_key('addGeodata'):
                lat = request.POST['lat']
                lng = request.POST['lng']
                
            if transaction.set(id_=request.POST['id'],
                               class_=request.POST['class'],
                               description=request.POST['description'],
                               environment=request.POST['environment'],
                               lat = lat,
                               lng = lng,
                               author=request.user.username):

                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/recipes", errorType=2, errorMessage="Environment already exist. Please choose another Identifier"))
            
        except (roboearth.DBWriteErrorException, roboearth.DBException, roboearth.FormInvalidException), err:
            return HttpResponse(views.error(request, nextPage="/environments", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/environments', errorType=1))

def update(request):
    """ update an existing environment, expected data: complete id (class.id),
    environment and/or human readable description """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            # now create the Hbase row
            if transaction.update(id_=request.POST['id'],
                                  data=request.POST,
                                  author=request.user.username):

                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage="Environment already exist. Please choose another Identifier"))
            
        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/', errorType=1))


def request(request):
    """ handle search request and return the result """
    def output(environments, query, semantic):
        template = loader.get_template('showEnvironment.html')
        values = {'Environments' : environments,
                  'is_auth' : request.user.is_authenticated(),
                  'Query' : query,
                  'Semantic' : semantic}

        return render_to_response('showEnvironment.html', roboearth.webpage_values(request, values))

    try:
        if request.method == 'GET':

            if request.user.is_authenticated():
                username = request.user.username
            else:
                username = ""

            result = list()
            semantic = False
            # syntactic query
            if request.GET.has_key('query'):
                query = request.GET['query']
            #semantic query
            else:
                semantic = True
                query = request.GET['semanticQuery']

            if request.GET.has_key('exact') and request.GET['exact'] == "True":
                exact = True
            else:
                exact = False

            return output(transaction.get(query=query, semanticQuery=semantic, user=username, exact=exact), query, semantic)
        else:
            return requestForm(request)
    except roboearth.DBReadErrorException, err:
        return HttpResponse(views.error(request, nextPage="/environments/request/", errorType=3, errorMessage=err.__str__()))
