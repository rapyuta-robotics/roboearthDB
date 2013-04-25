# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle generic SeRQL queries

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
import roboearth.db.transactions.sesame
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc, throttle

sesame = roboearth.db.transactions.sesame
roboearth = roboearth.db.roboearth

class SerqlHandler(AnonymousBaseHandler):
   """
   This class provides the methodes to handle 'POST' requests to the sesame server
   """

   allowed_methods = ('POST')

   def create(self, request):
      """
      handle POST request to
      'http://roboearth.informatik.uni-stuttgart.de/api/0.1/serql' for generic
      semantic queries

      Upload new data:

      Content-Type: application/json which contains:

      'query' : semantic query

      'repository' : Data Repository (Objects, Recipes or Environments)
      """

      try:
         return sesame.generic_get(query=request.data['query'], repository=request.data['repository'], format="xml")
      except Exception, e:
         return rc.BAD_REQUEST
      
