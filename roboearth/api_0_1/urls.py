# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: defining the URLs of the web interface

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

from django.conf.urls.defaults import *
from piston.resource import Resource
from roboearth.api_0_1.handlers.recipes import RecipeHandler
from roboearth.api_0_1.handlers.serql import SerqlHandler
from roboearth.api_0_1.handlers.objects import ObjectHandler
from roboearth.api_0_1.handlers.environments import EnvironmentHandler
from roboearth.api_0_1.handlers.robots import RobotHandler
import roboearth.api_0_1.handlers.binaries

class CsrfExemptResource(Resource):
    """A Custom Resource that is csrf exempt"""
    def __init__(self, handler, authentication=None):
        super(CsrfExemptResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)
        
recipe_handler = CsrfExemptResource(RecipeHandler)
serql_handler = CsrfExemptResource(SerqlHandler)
object_handler = CsrfExemptResource(ObjectHandler)
environment_handler = CsrfExemptResource(EnvironmentHandler)
robot_handler = CsrfExemptResource(RobotHandler)

urlpatterns = patterns('',
    url(r'^binary/objects/(?P<identifier>[^/]+)$', 'roboearth.api_0_1.handlers.binaries.upload'),
    url(r'^recipe/(?P<recipe_id>[^/]+)$', recipe_handler),
    url(r'^recipe/(?P<recipe_id>[^/]+)/(?P<api_key>[^/]+)$', recipe_handler),
    url(r'^recipe/(?P<recipe_id>[^/]+)/(?P<api_key>[^/]+)/(?P<rating>[^/]+)$', recipe_handler),
    url(r'^recipe$', recipe_handler),
    url(r'^serql$', serql_handler),
    url(r'^object/(?P<object_id>[^/]+)$', object_handler),
    url(r'^object/(?P<object_id>[^/]+)/(?P<api_key>[^/]+)$', object_handler),
    url(r'^object/(?P<object_id>[^/]+)/(?P<api_key>[^/]+)/(?P<data>[^/]+)$', object_handler),
    url(r'^object$', object_handler),
    url(r'^environment/(?P<env_id>[^/]+)$', environment_handler),
    url(r'^environment/(?P<env_id>[^/]+)/(?P<api_key>[^/]+)$', environment_handler),
    url(r'^environment/(?P<env_id>[^/]+)/(?P<api_key>[^/]+)/(?P<rating>[^/]+)$', environment_handler),
    url(r'^environment$', environment_handler),
    #url(r'^robot/(?P<robot_id>[^/]+)$', robot_handler),
    #url(r'^robot/(?P<robot_id>[^/]+)/(?P<api_key>[^/]+)$', robot_handler),
    #url(r'^robot$', robot_handler),
)
