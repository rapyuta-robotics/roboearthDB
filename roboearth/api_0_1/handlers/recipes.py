# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle the upload and download of action recipes
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
import roboearth.db.transactions.recipes
import roboearth.db.transactions.hbase_op
from piston.handler import AnonymousBaseHandler, BaseHandler
from piston.utils import rc, throttle
from roboearth.db.models import api_keys
from django.contrib.auth.models import User

transaction = roboearth.db.transactions.recipes
hbase_op = roboearth.db.transactions.hbase_op
roboearth = roboearth.db.roboearth

class RecipeHandler(AnonymousBaseHandler):
   """
   This class provides the methodes to handle 'GET', 'PUT', 'DELETE' and
   'POST' requests
   """

   allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')

   def read(self, request, recipe_id, semantic=False):
      """ handle GET request to
         'http://roboearth.informatik.uni-stuttgart.de/api/0.1/recipe/<recipe_id>',

         'recipe_id' : the complete UID of the corresponding data set
      """

      try:
         result = transaction.get(query=recipe_id, format="json", semanticQuery=semantic)
         if result:
            return result
         else:
            return rc.NOT_HERE
      except roboearth.DBReadErrorException, err:
         return rc.BAD_REQUEST;


   def update(self, request, recipe_id, api_key=None, rating=None):
      """ handle PUT request to update the data set or to rate the
          corresponding action recipe.
         
          'http://roboearth.informatik.uni-stuttgart.de/api/0.1/recipe/<recipe_id>/<identifier>/<rating>',

          update data set:

          'recipe_id' : the complete UID of the corresponding data set
          
          Content-Type: application/json which contains:

          'description' : human readable description of the environment

          'recipe' : action recipe (OWL)
          
          'api_key' : authenticates the user

          submit rating:

          'api_key' : identify user

          'rating' : rating [0..10]
      """

      #chek if ranking or data set was submitted
      if api_key and recipe_id and rating:
         # update rating
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            return rc.BAD_REQUEST

         ar = transaction.get(query=recipe_id, format="json", exact=True)
         if not ar: 
            return rc.NOT_HERE

         try:
            hbase_op.update_rating("Recipes", recipe_id, roboearth.calc_rating(float(ar[0]['rating']), float(rating)))
         except Exception, e:
            return rc.BAD_REQUEST

         return rc.ALL_OK

      #check if recipe exists
      if not transaction.get(query=recipe_id, format="json", exact=True):
         return rc.NOT_HERE
      
      try:
         data = request.data
         api_key = data['api_key']
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise

         transaction.update(id_=recipe_id,
                            author=api_key.username,
                            data=data)
         return rc.ALL_OK
      except Exception, e:
         return rc.BAD_REQUEST

   def create(self, request):
      """
      handle POST request to
      'http://roboearth.informatik.uni-stuttgart.de/api/0.1/recipe' either
      to upload new data or to send a sematic query to the database.

      Upload new data:

      Content-Type: application/json which contains:

      'id' : unified identifier

      'class' : class of action recipe

      'description' : human readable description of the action recipe

      'recipe' : action recipe (OWL)

      'api_key' : authenticates the user

      Send a semantic query:

      Content-Type: application/json which contains:

      'query' : semantic query
      """

      if request.content_type:
         data = request.data
      else:
         return rc.BAD_REQUEST
      
      # add data set
      if data.has_key("query"):
         return self.read(request, data['query'], True)

      try:
         class_ = data['class']
         id_ = data['id']
         description = data['description']
         recipe = data['recipe']
         api_key = data['api_key']
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise

         result = transaction.set(id_=id_,
                                  class_=class_,
                                  author=api_key.username,
                                  description=description,
                                  recipe=recipe)
         if result:
            return result
         else:
            return rc.DUPLICATE_ENTRY         

      except Exception, e:
         return rc.BAD_REQUEST
      
   def delete(self, request, recipe_id, api_key):
      """ handle DELETE request to
          'http://roboearth.informatik.uni-stuttgart.de/api/0.1/recipe/<recipe_id>/<api_key>',
          Content-Type: application/json which contains:

          'api_key' : identifies the user

          'recipe_id' : the complete UID of the environment
      """

      try:
         api_key = api_keys.objects.get(key__exact=api_key)
         if not User.objects.get(username__exact=api_key.username).is_active:
            raise
      except Exception, e:
         return rc.BAD_REQUEST

      data = transaction.get(query=recipe_id, exact=True)
      if not data:
         return rc.NOT_HERE 
      if User.objects.get(username__exact=api_key.username).username != data[0]['author']:
         return rc.BAD_REQUEST

      try:
         hbase_op.delete_row("Recipes", recipe_id)

      except Exception, e:
         return rc.NOT_HERE

      return rc.DELETED


