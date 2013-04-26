# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: Main file defines global variables and methods

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

import os
import unicodedata
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from django.core.context_processors import csrf

from hbase import Hbase
from hbase.ttypes import *

#some project wide constants

# Running on a local machine
local_installation = True
# RoboEarth URL
DOMAIN = "http://localhost:8000/"
BINARY_ROOT = DOMAIN+"data"
# location of binary data
UPLOAD_DIR = "/home/marcus/hadoop"
# Hadoop name node
NAMENODE = "localhost"
NAMENODE_PORT = 9090
# reasoning server
SESAME_SERVER="http://localhost:8080/openrdf-sesame"
# java program to access the reasoning server
SESAME_CONNECTOR="SesameConnector"
SESAME_CONNECTOR_LIBS=".:/home/marcus/workspace/roboearth/SesameConnector:/home/marcus/workspace/roboearth/SesameConnector/lib/*"
# e-mail address which is used for system notifications
ADMIN="admin@admin/com"

# some pre-defined error types
ERROR_TYPES = {0 : "UNKNOWN ERROR",
               1 : "DATA NOT VALID ERROR",
               2 : "HADOOP ERROR",
               3 : "Sesame ERROR"}


FOOTER = """The RoboEarth web interface is licensed under
      the <a href="http://www.apache.org/licenses/LICENSE-2.0">Apache
      License</a> Version 2.0. &#151; <a href="http://roboearth.informatik.uni-stuttgart.de/releases">Get</a> the source code!"""

if not local_installation:
    import twitter

# strings which are already in use for the database columns
class OBJECTS():
    RESERVED_STRINGS = ("description")

# some pre-defined exceptions
class DBException(Exception):
    def __str__(self):
        return repr(self.args[0])

class DBWriteErrorException(Exception):
    def __str__(self):
        return repr(self.args[0])

class DBReadErrorException(Exception):
    def __str__(self):
        return repr(self.args[0])

class FormInvalidException(Exception):
    def __str__(self):
        return repr(self.args[0])

class NoDBEntryFoundException(Exception):
    def __str__(self):
        return repr(self.args[0])


def send_twitter_message(action, data, id_, author=""):
    try:
        api = twitter.Api()
        api = twitter.Api(consumer_key='foo',
                          consumer_secret='foo',
                          access_token_key='foo',
                          access_token_secret='foo')

        if action == "upload":
            api.PostUpdate("New "+data+": \""+id_+"\" uploaded by "+author)
        elif action == "update":
            api.PostUpdate(data+": \""+id_+"\" updated by "+author)
        elif action == "download":
            api.PostUpdate(data+": \""+id_+"\" downloaded")
    except:
        None


def openDBTransport():
    """
    Open trasport to access hbase by the Thrift interface
    """
    try:
        transport = TSocket.TSocket(NAMENODE, NAMENODE_PORT)
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        client = Hbase.Client(protocol)
        transport.open()
        return { 'client' : client, 'transport' : transport }
    except Exception, err:
        raise DBException("Hbase connection failed: " + err.__str__())

def closeDBTransport(transport):
    """
    Close hbase transport
    """

    transport['transport'].close()

def replace_unicode(string):

    string = string.replace(u'\xf6', 'oe').replace(u'\xd6', 'Oe').replace(u'\xe4', 'ae').replace(u'\xc4', 'Ae').replace(u'\xfc', 'ue').replace(u'\xdc', 'Ue').replace(u'\xdf','ss')

    return unicodedata.normalize('NFKD', string).encode('ascii','ignore')


def calc_rating(old_rating, new_rating):    
    if new_rating > 10:
        new_rating = 10
    if new_rating < 0:
        new_rating = 0

    return old_rating + (new_rating - old_rating) / 10


def webpage_values(request, values={}):
    values['MainMenu'] = MainMenu(request)
    values['Footer'] = FOOTER
    values['Domain'] = DOMAIN
    values.update(csrf(request))
    return values

def MainMenu(request):
    """ This is the main menu, shown at every webpage """
    documentation = '<li class="topmenu"><a href="/documentation">Documentation</a></li><!--<li class="topmenu"><a href="/about">About</a></li>-->'
    generic_profil = """
    <ul>
    <li class="submenu"><a href="/profile">My Profile</a></li>
    <li class="submenu"><a href="/subscriptions">My Subscriptions</a></li>
    <li class="submenu"><a href="/myrobots">My Robots</a></li>
    <li class="submenu"><a href="/newsfeed">Newsfeed</a></li>
    """
    super_user = '<li class="submenu"><a href="/accounts/manage">User Management</a></li>'
    logout = '<li class="submenu"><a href="/logout">Logout</a></li>'


    if request.user.is_authenticated():
        user = '<li class="topmenu"><a href="">'+request.user.username+'</a>'+generic_profil
        if request.user.is_superuser:
            user = user + super_user
        user = user + logout + '</ul></li>'
    else:
        user = """
        <li class="topmenu"><a href="/register">Register</a></li>
        <li class="topmenu"><a href="/login">Login</a></li>
        """

    public = """
        <li class="topmenu"><a href="">Search</a>
        <ul>
          <li class="submenu"><a href="/recipes/request">Action Recipes</a></li>
          <li class="submenu"><a href="/objects/request">Objects</a></li>
          <li class="submenu"><a href="/environments/request">Environments</a></li>        
          <li class="submenu"><a href="/robots/request">Robots</a></li>
          <li class="submenu"><a href="/serql">SeRQL Console</a></li>
            <!--<li><a href="/locations/objects/request">Objects</a></li>-->
        </ul></li>
      """
    private = """
        <li class="topmenu"><a href="">Submit</a>
        <ul>
          <li class="submenu"><a href="/recipes">Action Recipe</a></li>
          <li class="submenu"><a href="/objects">Object</a></li>
          <li class="submenu"><a href="/environments">Environments</a></li>
          <li class="submenu"><a href="/robots">Robots</a></li>
            <!--<li><a href="/locations/objects">Objects</a></li>-->
        </ul></li>
     """

    
    if request.user.is_authenticated():
        return '<ul>'+public + private + documentation + user+'</ul>'
    else:
        return '<ul>'+public + documentation + user+'</ul>'
