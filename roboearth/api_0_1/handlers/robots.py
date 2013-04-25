# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle the upload and download of robot
                           locations through the REST API

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

import roboearth.db.transactions.robots
import roboearth.db.transactions.environments
import roboearth.db.transactions.hbase_op
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc, throttle
from roboearth.db.models import api_keys
from django.contrib.auth.models import User

transaction = roboearth.db.transactions.robots
environments = roboearth.db.transactions.environments
hbase_op = roboearth.db.transactions.hbase_op

class RobotHandler(AnonymousBaseHandler):
   """ This class provides the methodes to handle 'GET', 'PUT', 'DELETE' and
   'POST' requests
   """

   allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')

   def read(self, request, robot_id):
      result = transaction.get(query=robot_id)
      if result:
         return result
      else:
         return rc.NOT_HERE

   def update(self, request, robot_id):
      if request.content_type:
         data = request.data
      else:
         return rc.BAD_REQUEST

      #check if object exists
      if not transaction.get(robot_id, exact=True):
         return rc.NOT_HERE

      try:
         api_key = data['api_key']
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise
         
         if not environments.get(environment):
            return rc.BAD_REQUEST

         return transaction.update(id_=robot_id,
                                   author=api_key.username,
                                   data=data)
      except Exception, e:
         return rc.BAD_REQUEST

   def create(self, request):
      if request.content_type:
         data = request.data
      else:
         return rc.BAD_REQUEST

      try:
         id_ = data['id']
         environment = data['environment']
         room_number = data['room_number']
         api_key = data['api_key']
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise
      except Exception, e:
         return rc.BAD_REQUEST

      #check if robot already exists
      if transaction.get(id_):
         return rc.DUPLICATE_ENTRY

      try:
         result = transaction.set(id_=id_,
                                  author=api_key.username,
                                  environment=environment,
                                  room_number=room_number)
         if result:
            return result
         else:
            return rc.DUPLICATE_ENTRY
         
      except Exception, e:
         return rc.NOT_HERE
      
   def delete(self, request, robot_id, api_key):
      try:
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise
      except Exception, e:
         return rc.BAD_REQUEST

      data = transaction.get(robot_id, exact=True)
      if not data:
         return rc.NOT_HERE
      if User.objects.get(username__exact=api_key.username).username != data[0]['author']:
         return rc.BAD_REQUEST

      try:
         hbase_op.delete_row("Robots", robot_id)
      except Exception, e:
         return rc.NOT_HERE

      return rc.DELETED
