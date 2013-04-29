# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: Handle HTTP requests regarding robot locations
                           (STILL IN DEVELOPMENT!)
  
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
import roboearth.db.transactions.robots
import roboearth.db.transactions.hbase_op
import xml.dom.minidom
from django.http import HttpResponse
from django.template import Context, loader
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response

transaction = roboearth.db.transactions.robots
hbase_op = roboearth.db.transactions.hbase_op
forms = roboearth.db.forms
views = roboearth.db.views.views
roboearth = roboearth.db.roboearth


#
# Forms
#

def submitForm(request):
    """ show form to submit new robot locations """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    values = {}#'Environments' : hbase_op.list_all("Environments")}
    
    return render_to_response('submitRobot.html', roboearth.webpage_values(request, values))

def requestForm(request):
    """ show form to request robot location """    
    return render_to_response('requestRobot.html', roboearth.webpage_values(request))

#
# Actions
#

def submit(request):
    """ submit new robot location, expected data: id, complete id of an already
        stored environment, description and a picture of the robot"""
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            transaction.set(id_=request.POST['id'],
                            author=request.user.username,
                            description=request.POST['description'],
                            srdl=request.POST['srdl'],
                            picture=request.FILES['picture'])
            return HttpResponse(views.success(request))
        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/robots", errorType=2, errorMessage=err.__str__()))
        except (roboearth.FormInvalidException, roboearth.NoDBEntryFoundException), err:
            return HttpResponse(views.error(request, nextPage="/robots", errorType=1, errorMessage=err.__str__()))
    else:
        return HttpResponse(views.error(request, nextPage='/robots', errorType=1))


def request(request):
    """ handle search request and return the result """
    def output(robots, query):
        template = loader.get_template('showRobot.html')
        values = {'Robots' : robots,
                  'Query' : query,
                  'is_auth' : request.user.is_authenticated()}
    
        return render_to_response('showRobot.html', roboearth.webpage_values(request, values))

    if request.method == 'GET':
        if request.user.is_authenticated():
            username = request.user.username
        else:
            username = ""

        if request.GET.has_key('exact') and request.GET['exact'] == "True":
            exact = True
        else:
            exact = False

        query = request.GET['query']
        return output(transaction.get(query=query, user=username, exact=exact), query)
    else:
        requestForm(request)


def myRobots(request):
    """ get all robots from a user """
    def output(robots):
        template = loader.get_template('showRobot.html')
        values = {'Robots' : robots,
                  'is_auth' : request.user.is_authenticated(),
                  'my_robots' : True}
    
        return render_to_response('showRobot.html', roboearth.webpage_values(request,values))

    if request.method == 'GET':
        return output(transaction.myRobots(request.user.username))
    else:
        requestForm(request)
