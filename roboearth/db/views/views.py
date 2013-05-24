# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle some generic HTTP request like showing the
                           start page, error pages, etc.
  
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
import roboearth.db.transactions.recipes
import roboearth.db.transactions.objects
import roboearth.db.transactions.hbase_op
import roboearth.db.transactions.hdfs_op
from django.http import HttpResponse
from django.template import Context, loader
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.shortcuts import render_to_response
import os,sys

hbase = roboearth.db.transactions.hbase_op
hdfs = roboearth.db.transactions.hdfs_op

forms = roboearth.db.forms
recipes = roboearth.db.transactions.recipes
objects = roboearth.db.transactions.objects
roboearth = roboearth.db.roboearth


#
# main page
#

def startPage(request):
    """ show start page """
    template = loader.get_template('index.html')
    webpage_values = Context(roboearth.webpage_values(request))
    
    return template.render(webpage_values)

def index(request):
    return HttpResponse(startPage(request))


def documentation(request):
    """ show documentation page for the REST-API """
    template = loader.get_template('documentation.html')
    webpage_values = Context(roboearth.webpage_values(request))
    
    return HttpResponse(template.render(webpage_values))


def about(request):
    """ show general information about RoboEarth """
    template = loader.get_template('about.html')
    webpage_values = Context(roboearth.webpage_values(request))
    
    return HttpResponse(template.render(webpage_values))


def error(request, nextPage='/', errorType=0, errorMessage=""):
    """ show error page:

    nextPage : what page should be shown after the error notice

    errorType : "0" -> "unknown error", "1" -> "data not valid", "2" -> "hadoop error"

    errorMessage : the message of the error notice
    """
    template = loader.get_template('errorMessage.html')
    webpage_values = Context(roboearth.webpage_values(request,
                                                      {'nextPage' : nextPage,
                                                       'errorType' : roboearth.ERROR_TYPES[errorType],
                                                       'errorMessage' : errorMessage}))
    return template.render(webpage_values)


def success(request, nextPage='/'):
    """ page for successful operations:

    nextPage : which page should be shown after the success notice
    """
    template = loader.get_template('successMessage.html')
    webpage_values = Context(roboearth.webpage_values(request,
                                                      {'nextPage' : nextPage}))
    return template.render(webpage_values)

def dbContent(request):
    """ DEPRECIATED: show the complete content of the database
    """
    
    try:
        template = loader.get_template('showDBcontent.html')
        webpage_values = Context(roboearth.webpage_values(request,
                                                          {'Recipes' : recipes.get(numOfVersions=3),
                                                           'Objects' : objects.get(numOfVersions=3)}))
        return HttpResponse(template.render(webpage_values))
    except roboearth.DBException, err:
        return HttpResponse(error(request, errorType=2, errorMessage=err.__str__()))


def removeEmptyFolders(path):
    if not os.path.isdir(path):
        return
    
    # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                removeEmptyFolders(fullpath)
    
    # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0:
        os.rmdir(path)



def finalDelete(request):
    """ execute delete operation after the user approved the operation
    """
    try:
        if request.POST['binary'] == "0":
            transport = roboearth.openDBTransport()
            client = transport['client']
            scanner = client.scannerOpenWithPrefix("Elements", request.POST['rowKey'], [ ])
            res = client.scannerGet(scanner)
            
            subscribers = []
            for r in res[0].columns:
                if r.startswith("file:") or r.startswith("info:picture"):
                    hdfs.rm_file(res[0].columns[r].value.replace(roboearth.BINARY_ROOT, roboearth.UPLOAD_DIR))
                if r.startswith("subscriber:"):
                    subscribers.append(res[0].columns[r].value)
            
            client.scannerClose(scanner)
            
            for subscriber in subscribers:
                scannersub = client.scannerOpenWithPrefix("Subscriptions", subscriber, [ ])
                user = client.scannerGet(scannersub)
                if user:
                    uname, table, uid = user[0].row.split('#',2)
                    if uid == request.POST['rowKey']:
                        hbase.delete_row(table="Subscriptions", rowKey=uname+"#"+table+"#"+uid)        
            client.scannerClose(scannersub)
            
            roboearth.closeDBTransport(transport)
            
            removeEmptyFolders(roboearth.UPLOAD_DIR+'/elements')
            
            hbase.delete_row(request.POST['table'], request.POST['rowKey'])
            hbase.delete_column('Users', request.user.username, request.POST['table'].lower()[0:len(request.POST['table'])-1]+':'+request.POST['rowKey'])
            
            return  HttpResponse(success(request))
        else:
            hdfs.rm_file(request.POST['file'].replace(roboearth.BINARY_ROOT, roboearth.UPLOAD_DIR))
            hbase.delete_column(request.POST['table'], request.POST['rowKey'], 'file:'+request.POST['colID'])
            return  HttpResponse(success(request))

            
    except roboearth.DBWriteErrorException, err:
        return HttpResponse(error(request, errorType=2, errorMessage=err.__str__()))



def deleteEntity(request):
    """ get called for delete operations, expected data: table and rowKey
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.user.username != request.POST['author']:
        return HttpResponse(error(request, errorType=0, errorMessage="User not allowed to delete " + request.POST['rowKey']))

    webpage_values = roboearth.webpage_values(request,
                                              {'table' : request.POST['table'],
                                               'binary' : '0',
                                               'row_key' : request.POST['rowKey']})
    
    return render_to_response('confirmDeleteRequest.html', webpage_values)

def deleteBinary(request):
    """ get called to delete binary files, expected data: file, table and rowKey
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.user.username != request.POST['author']:
        return HttpResponse(error(request, errorType=0, errorMessage="User not allowed to delete " + request.POST['rowKey']))

    webpage_values = roboearth.webpage_values(request,
                                              {'table' : request.POST['table'],
                                               'file' : request.POST['file'],
                                               'colID' : request.POST['colID'],
                                               'binary' : '1',
                                               'row_key' : request.POST['rowKey']})
    
    return render_to_response('confirmDeleteRequest.html', webpage_values)
            
