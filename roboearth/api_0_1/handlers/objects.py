# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle the upload and download of object data
                           through the REST API

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
import roboearth.db.transactions.objects
import roboearth.db.transactions.hbase_op
import roboearth.db.transactions.hdfs_op
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc, throttle
from roboearth.db.models import api_keys
from django.contrib.auth.models import User

transaction = roboearth.db.transactions.objects
hbase_op = roboearth.db.transactions.hbase_op
hdfs_op = roboearth.db.transactions.hdfs_op
roboearth = roboearth.db.roboearth

class ObjectHandler(AnonymousBaseHandler):
   """ This class provides the methodes to handle 'GET', 'PUT', 'DELETE' and
   'POST' requests
   """
   allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')

   def read(self, request, object_id="", semantic=False):
      """ handle GET request to
         'http://roboearth.informatik.uni-stuttgart.de/api/0.1/object/<object_id>',

         object_od: the complete UID of the corresponding data set
      """

      try:
         result = transaction.get(query=object_id, format="json", semanticQuery=semantic)
         if result:
            return result
         else:
            return rc.NOT_HERE
      except roboearth.DBReadErrorException, err:
         return rc.BAD_REQUEST;


   def update(self, request, object_id, api_key=None, data=None):
      """ handle PUT request to update the data set or to rate the
          corresponding object description
          'http://roboearth.informatik.uni-stuttgart.de/api/0.1/object/<object_id>/<api_key>/<rating>',

          update data set:

          object_id: the complete UID of the corresponding data set

          Content-Type: application/json which contains:

          description: human readable description of the object

          object_description: object description (OWL)

          api_key: authenticates the user

          submit rating:

          api_key: authenticates the user

          data: rating [0..10]
      """

      #chek if ranking or data set was submitted
      if api_key and object_id and data:
         # update rating
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            return rc.BAD_REQUEST

         obj = transaction.get(query=object_id, format="json", exact=True)
         if not obj: 
            return rc.NOT_HERE

         try:
            hbase_op.update_rating("Objects", object_id, roboearth.calc_rating(float(obj[0]['rating']), float(data)))
         except Exception, e:
            return rc.BAD_REQUEST

         return rc.ALL_OK


      #check if object exists
      if not transaction.get(query=object_id, format="json", exact=True):
         return rc.NOT_HERE

      try:
         data = request.data
         api_key = data['api_key']
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise
         transaction.update(id_=object_id,
                            author=api_key.username,
                            data=data)
         return rc.ALL_OK
      except Exception, e:
         return "2"
         return rc.BAD_REQUEST

   def create(self, request):
      """ handle POST request to
         'http://roboearth.informatik.uni-stuttgart.de/api/0.1/object' either
         to upload new data or to send a semantic query to the database.

         Upload new data:

         Content-Type: application/json which contains:

         id : unified identifier

         class : class of the object

         description: human readable description of the object

         object_description: object description (OWL)

         api_key: authenticates the user

         Send a semantic query:

         Content-Type: application/json which contains:

         query : semantic query
      """

      if request.content_type:
         data = request.data
      else:
         return rc.BAD_REQUEST

      if data.has_key("query"):
         return self.read(request, data['query'], True)

      try:
         class_ = data['class']
         id_ = data['id']
         description = data['description']
         object_description = data['object_description']
         api_key = data['api_key']
         #raw_files = data['files']
         #files = {}
         #for k,v in raw_files.items():
         #    files[raw_files[k]] = v
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise         

         result = transaction.set(id_=id_,
                                  class_=class_,
                                  author=api_key.username,
                                  description=description,
                                  object_description=object_description)
         if result:
            return result
         else:
            return rc.DUPLICATE_ENTRY

      except Exception, e:
         return rc.BAD_REQUEST

   def delete(self, request, object_id, api_key, data = None):
      """ handle DELETE request to
          'http://roboearth.informatik.uni-stuttgart.de/api/0.1/object/<api_key>/<env_id>',
          Content-Type: application/json which contains:

          api_key: identifies the user

          object_id: the complete UID of the environment (deletes the complete data set)

          data: file identifier to delete only the corresponding file
      """

      try:
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise         
      except Exception, e:
         return rc.BAD_REQUEST


      object_ = transaction.get(query=object_id, format="json", exact=True)
      if not object_:
         return rc.NOT_HERE
      if User.objects.get(username__exact=api_key.username).username != object_[0]['author']:
         return rc.BAD_REQUEST

      try:
         if data:
            file_type = data
            hdfs_op.rm_file(object_[0]["files"][file_type]["url"].replace(roboearth.BINARY_ROOT, roboearth.UPLOAD_DIR))
            hbase_op.delete_column("Elements", object_id, 'file:'+file_type)
         else:
            hbase_op.delete_row("Elements", object_id)
      except Exception, e:
         return rc.NOT_HERE

      return rc.DELETED
