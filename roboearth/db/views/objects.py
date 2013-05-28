# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: Handle HTTP request regarding object descriptions
  
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
import os
import roboearth.db.transactions.objects
import roboearth.db.transactions.sesame
import xml.dom.minidom
import urllib2
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

sesame = roboearth.db.transactions.sesame
transaction = roboearth.db.transactions.objects
forms = roboearth.db.forms
views = roboearth.db.views.views
roboearth = roboearth.db.roboearth

#
# Forms
#

def submitForm(request):
    """ show form to submit new object description """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")
    
    return render_to_response('submitObject.html', roboearth.webpage_values(request))

def requestForm(request):
    """ show form to request object description """
    return render_to_response('requestObject.html', roboearth.webpage_values(request))

#
# Actions
#


def submit(request):
    """ submit new object description, expected data: id, class,
    description (human readable), object_description and an arbitrary
    number of binary files."""
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            #  Hbase row and upload files
            files = {}
            for k,v in request.FILES.items():
                files[request.POST[k]] = v
                
            if transaction.set(id_=request.POST['id'],
                               author=request.user.username,
                               class_=request.POST['class'],
                               description=request.POST['description'],
                               object_description=request.POST['object_description'],
                               files=files):
                
                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/objects", errorType=2, errorMessage="Object already exist. Please choose another Identifier"))

        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/objects", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/objects', errorType=1))


def update(request):
    """ update existing object description, expected data: complete id
    (class.id), object description and/or human readable description """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            if transaction.update(id_=request.POST['id'],
                                  author=request.user.username,
                                  data=request.POST):

                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage="Object already exist. Please choose another Identifier"))

        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/', errorType=1))


def request(request):
    """ handle search request and return the result """
    def output(objects, query, semantic):
        template = loader.get_template('showObject.html')
        values = {'Objects' : objects,
                  'is_auth' : request.user.is_authenticated(),
                  'Query' : query,
                  'Semantic' : semantic}

        return render_to_response('showObject.html', roboearth.webpage_values(request,values))

    try:
        if request.method == 'GET':

            if request.user.is_authenticated():
                username = request.user.username
            else:
                username = ""

            result = list()
            semantic = False
            # syntactic query
            
            print request.GET
            if request.GET.has_key('query'):
                query = request.GET['query']
            else:
                semantic = True
                query = request.GET['semanticQuery']

            if request.GET.has_key('exact') and request.GET['exact'] == "True":
                exact = True
            else:
                exact = False
            objects_list = transaction.get(query=query, semanticQuery=semantic, user=username, exact=exact)
            paginator = Paginator(objects_list, 10)
            page = request.GET.get('page')
            try:
                objects = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                objects = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                objects = paginator.page(paginator.num_pages)
            print 'query:', query
            return output(objects, urllib2.quote(query.encode("utf8")), semantic)

        else:
            return requestForm(request)
    except roboearth.DBReadErrorException, err:
        return HttpResponse(views.error(request, nextPage="/objects/request/", errorType=3, errorMessage=err.__str__()))
