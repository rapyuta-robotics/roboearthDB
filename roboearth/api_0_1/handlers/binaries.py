# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle the upload of binary files through the REST
                           API

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
import roboearth.db.roboearth
import roboearth.db.transactions.hdfs_op
import roboearth.db.transactions.environments
import roboearth.db.transactions.objects
from piston.utils import rc
from django.views.decorators.csrf import csrf_exempt
from roboearth.db.models import api_keys
from django.contrib.auth.models import User

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

environments = roboearth.db.transactions.environments
objects = roboearth.db.transactions.objects
hdfs_op = roboearth.db.transactions.hdfs_op
roboearth = roboearth.db.roboearth

@csrf_exempt
def upload(request, identifier):
    """ this function receives a POST request
        'http://roboearth.informatik.uni-stuttgart.de/api/0.1/binary/<identifier>',

        identifier: the complete UID of the corresponding data set
        
        Content-Type: application/json which contains:

        type : identfier of the file (content)

        api_key: authenticates the user

        file: the binary file
    """
    if request.method == 'POST':
        try:
            api_key = request.POST['api_key']
            api_key = api_keys.objects.get(key__exact=api_key)
            if not User.objects.get(username__exact=api_key.username).is_active:
                raise
        except Exception, e:
            return rc.BAD_REQUEST
        transport = roboearth.openDBTransport()
        client = transport['client']
        scanner = client.scannerOpenWithPrefix("Elements", identifier.lower(), [ ])
        res = client.scannerGet(scanner)
        client.scannerClose(scanner)
        if res:
            result = objects.upload(request, identifier.lower(), author=api_key.username)
        else:
            roboearth.closeDBTransport(transport)
            return rc.BAD_REQUEST

        roboearth.closeDBTransport(transport)
        if result:
            return rc.ALL_OK
        else:
            return rc.BAD_REQUEST
        
    return rc.NOT_HERE
