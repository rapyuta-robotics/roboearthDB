# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: Handle HTTP request regarding action recipes
  
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
import roboearth.db.transactions.recipes
import roboearth.db.transactions.sesame
import xml.dom.minidom
import urllib2
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


sesame = roboearth.db.transactions.sesame
transaction = roboearth.db.transactions.recipes
forms = roboearth.db.forms
views = roboearth.db.views.views
roboearth = roboearth.db.roboearth

#
# Forms
#

def submitForm(request):
    """ show form to submit new action recipes """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")
     
    return render_to_response('submitRecipe.html', roboearth.webpage_values(request))

def requestForm(request):
    """ show form to request action recipes """
    return render_to_response('requestRecipe.html', roboearth.webpage_values(request))

#
# Actions
#

def submit(request):
    """ submit new action recipe, expected data: id, class, (human
    readable) description, recipe """

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")
    if request.method == 'POST':
        try:
            if transaction.set(id_=request.POST['id'],
                               class_=request.POST['class'],
                               description=request.POST['description'],
                               recipe=request.POST['recipe'],
                               author=request.user.username):
                
                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/recipes", errorType=2, errorMessage="Recipe already exist. Please choose another Identifier"))
        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/recipes", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/recipes', errorType=1))


def update(request):
    """ update existing action recipe, expected data: complete id (class.id),
    new recipe and/or human readable description """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")
    if request.method == 'POST':
        try:
            if transaction.update(id_=request.POST['id'],
                                  data=request.POST,
                                  author=request.user.username):
                
                return HttpResponse(views.success(request))
            else:
                return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage="Recipe already exist. Please choose another Identifier"))
        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/', errorType=1))

def request(request):    
    """ handle search request and return the result """
    def output(recipes, query, semantic):
        values = {'Recipes' : recipes,
                  'is_auth' : request.user.is_authenticated(),
                  'Query' : query,
                  'Semantic' : semantic}

        return render_to_response('showRecipe.html', roboearth.webpage_values(request, values))

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

            recipes_list = transaction.get(query=query, semanticQuery=semantic, user=username, exact=exact)
            paginator = Paginator(recipes_list, 10)
            page = request.GET.get('page')
            try:
                recipes = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                recipes = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                recipes = paginator.page(paginator.num_pages)
            return output(recipes, urllib2.quote(query.encode("utf8")), semantic)

        else:
            return requestForm(request)
    except roboearth.DBReadErrorException, err:
        return HttpResponse(views.error(request, nextPage="/recipes/request/", errorType=3, errorMessage=err.__str__()))
