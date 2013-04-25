# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handles the web forms for arbitrary SeRQL queries
  
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
import roboearth.db.transactions.sesame
import xml.dom.minidom
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response

sesame = roboearth.db.transactions.sesame
roboearth = roboearth.db.roboearth

#
# Forms
#

def serql(request):
    """ show the web page to execute serql queries """   
    return render_to_response('serql.html', roboearth.webpage_values(request))


def request(request):
    """ handles the request regarding serql queries and return the results """
    def output(result, query):
        template = loader.get_template('serql.html')
        values = {'query' : query,
                  'result' : result}
    
        return render_to_response('serql.html', roboearth.webpage_values(request,values))

    if request.method == 'GET':
        query = request.GET['semanticQuery']
        repository = request.GET['repository']

        return output(sesame.generic_get(query, repository), query)
    else:
        return serql(request)
