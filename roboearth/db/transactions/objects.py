# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: read/write object related data to the database

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

import sys, os
import roboearth.db.roboearth
import roboearth.db.transactions.hdfs_op
import roboearth.db.transactions.hbase_op
import roboearth.db.transactions.sesame
import xml.dom.minidom
import time
import magic
import logging

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

sesame = roboearth.db.transactions.sesame
hdfs = roboearth.db.transactions.hdfs_op
hbase_op = roboearth.db.transactions.hbase_op
roboearth = roboearth.db.roboearth

#
# Object description
#

def set(id_, class_, description, object_description, author, files=None):
    """
    write a object description to the database

    id_ : object identifier

    class_: object class

    description: human readable description

    object_description: owl description

    author: author of the description

    files: dictionary of binary files (file identifier : file)
    """
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    transport = roboearth.openDBTransport()
    client = transport['client']

    identifier = class_.replace(' ', '').lower().strip('.') + '.' + id_.replace(' ', '').lower().strip('.')

    #create paths
    path = class_.replace(' ', '').lower().strip('.') +  '.' +id_.replace(' ', '').lower().strip('.')
    wwwPath = roboearth.DOMAIN + os.path.join("data/", 'elements/', path.replace('.', '/'))
    path = os.path.join(roboearth.UPLOAD_DIR, 'elements/', path.replace('.', '/'))

    try:
        # object already exists
        if get(query=identifier, exact=True):
            return None
        
        # upload files and build file mutation list for hbase operation
        file_mutation_list = [ ]
        if files:
            for file_ID, file_ in files.items():
                hdfs.upload_file(file_, path)
                file_mutation_list.append(Mutation(column="file:"+file_ID, value=wwwPath+"/"+file_.name))

        # now write to hbase
        client.mutateRow("Elements", identifier,
                         [Mutation(column="info:description", value=description),
                          Mutation(column="info:author", value=author),
                          Mutation(column="info:rating", value="1"),
                          Mutation(column="info:type", value="object"),
                          Mutation(column="owl:description", value=object_description)]+
                         file_mutation_list)
        
        #write data to sesame
        sesame_ret = sesame.set(object_description, identifier, "elements")
        if sesame_ret != "0":
            hbase_op.delete_row("Elements", identifier)
            print 'raising shit'
            raise IllegalArgument(sesame_ret)

        client.mutateRow("Users", author,
                         [Mutation(column="element:"+identifier, value="")])

        roboearth.closeDBTransport(transport)

        #if not roboearth.local_installation:
        #    roboearth.send_twitter_message("upload", "Object", identifier, author)

        return {'id' : identifier, 'description' : description, 'object_description' : object_description}

    except (IOError, IllegalArgument), err:
        try: # try clean up
            hdfs.rm_dir(path)
            hbase_op.delete_row("Elements", identifier)
            sesame.rm(identifier, "Elements")
        except:
            sys.exc_clear()
        import traceback
        logging.info(traceback.format_exc())
        raise roboearth.DBWriteErrorException("Can't write data to Object table: HEREEEEE " + err.__str__())

def update(id_, data, author):
    """
    update an existing object description at the database

    id_ : complete identifier (primary key) of the object

    data: dictionary with the updated data ('description' (human readable) and
    'object_description' (OWL))

    author: author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        mutation_list = [ ]
        if data.has_key('description'):
            mutation_list.append(Mutation(column="info:description", value=data['description']))            
        if data.has_key('object_description'):
            mutation_list.append(Mutation(column="owl:description", value=data['object_description']))            
        
        client.mutateRow("Elements", id_,
                         [Mutation(column="info:modified_by", value=author)] +
                         mutation_list)

        if data.has_key('object_description'):
            sesame.rm(id_, "Elements")
            sesame.set(data['object_description'], id_, "Elements")

        # push update to subscribers
        scanner = client.scannerOpenWithPrefix("Elements", id_, [ ])
        res = client.scannerGet(scanner)
        for r in res[0].columns:
            if r.startswith("subscriber:"):
                client.mutateRow("Users", res[0].columns[r].value,
                                 [Mutation(column="news:", value="Objects#"+id_)])

        client.scannerClose(scanner)
        roboearth.closeDBTransport(transport)

        return True
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Elements table: " + err.__str__())

def get(query="", format="html", numOfVersions = 1, user="", semanticQuery=False, exact=False):
    """
    read a object description from the database

    query : search query

    format : output format (html/json)

    numOfVersions : allows to get older version of the object description

    semantic_query : is the query a semantic query?

    exact : search for the exact object or for a class of objects
    """

    def addObject(row):
        """
        add results to the output dictionary
        """
        rating = row.columns['info:rating'].value
        output = {"id" : row.row,
                  "description" : row.columns['info:description'].value,
                  "author" : row.columns['info:author'].value,
                  "rating" : rating,
                  "object_description" : list(),
                  "files" : {}}

        #check subscription
        if user != "" and format=="html":
            scannerSub = client.scannerOpenWithPrefix("Subscriptions", user+"#Objects#"+row.row, [ ])
            subRes = client.scannerGet(scannerSub)
            if subRes and subRes[0].row == user+"#Objects#"+row.row:
                output['subscribed'] = True
            else:
                output['subscribed'] = False

        if row.columns.has_key('info:modified_by'):
            output['modified_by'] = row.columns['info:modified_by'].value

        for r in row.columns:
            if r.startswith("file:"):
                url_ = res[0].columns[r].value
                file_ = roboearth.UPLOAD_DIR+url_[len(roboearth.BINARY_ROOT):]
                output["files"][r[5:]] = {'url' : url_,
                                          'mime-type' : m.from_file(file_)} 

        versions = client.getVer("Elements", row.row, "owl:description", numOfVersions)
        if format=="html":
            for v in versions:
                try:
                    output['object_description'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                                          'description' : xml.dom.minidom.parseString(v.value).toprettyxml(indent="    ") })
                except:
                    output['object_description'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                                          'description' : v.value })
                output['fullStars'] = range(int(round(float(rating))))
                output['emptyStars'] = range(10 - int(round(float(rating))))
        else:
            for v in versions:            
                output['object_description'].append({ 'timestamp' : v.timestamp,
                                                      'description' : v.value.replace("\n", "") })

       # if not roboearth.local_installation:
       #     roboearth.send_twitter_message("download", "Object", row.row)

        return output

    # semantic query get send to the reasoning server
    if semanticQuery:
        query = sesame.get(query.replace("SELECT source FROM CONTEXT source", ""), "elements")
        if query['status'] == 0:
            query = [q.rsplit("/", 1)[1] for q in query['stdout']]
        else:
            raise roboearth.DBReadErrorException(query['stderr'])
    else:
        query = [query]

    transport = roboearth.openDBTransport()
    client = transport['client']

    m = magic.Magic(mime=True)

    result = list()
    for q in query:
        scanner = client.scannerOpenWithPrefix("Elements", q.lower(), [ ])
        res = client.scannerGet(scanner)
        while res:
            if ((semanticQuery == False and exact == False) or res[0].row == q) and res[0].columns['info:type'].value == 'object':
                result.append(addObject(res[0])) 
            res = client.scannerGet(scanner)

        client.scannerClose(scanner)

    roboearth.closeDBTransport(transport)

    return result

def upload(request, identifier, author):
    """
    add binary file to object description

    identifier : object identifier

    author: author of the description
    """

    try:
        file_ = request.FILES['file']
        type_ = request.POST['type']

        upload_path = os.path.join(roboearth.UPLOAD_DIR, "elements/", identifier.replace('.', '/'))
        transport = roboearth.openDBTransport()
        client = transport['client']

        hdfs.upload_file(file_, upload_path)

        # add reference to table
        client.mutateRow("Elements", identifier,
                         [Mutation(column="info:modified_by", value=author),
                          Mutation(column="file:"+type_, value=roboearth.DOMAIN + os.path.join("data/", "elements/", identifier.replace('.', '/'), file_.name))])
        roboearth.closeDBTransport(transport)
        return True
    except Exception, e:
        return False
    

#
# Object location
#

def setLocation(environment, room_number, object_, posX, posY, posZ, delta, author):
    """
    write a object location to the database

    environment : reference to an environment, stored at the database

    room_number: the room where the object is located

    object : reference to the object description

    posX, posY, posZ : coordiantes which describes the exact location

    delta : impreciseness of position data

    author : author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
 
    try:
        scanner = client.scannerOpenWithPrefix("Objects", object_.lower(), [ ]) 
        if not client.scannerGet(scanner):
            raise roboearth.NoDBEntryFoundException("Couldn't connect location with the named object. Object doesn't exits in database")
        scanner = client.scannerOpenWithPrefix("Environments", environment.lower(), [ ])
        if not client.scannerGet(scanner):
            raise roboearth.NoDBEntryFoundException("Couldn't connect location with the named environment. Environment doesn't exits in database")

        id_ = environment + '.' + room_number + '.' + posX + '.' + posY + '.' + posZ + '.' + delta

        if getLocation(query=id_, exact = True):
            return None

        client.mutateRow("ObjectLocations", id_,
                         [Mutation(column="object:id", value=object_),
                          Mutation(column="info:author", value=author),
                          Mutation(column="environment:id", value=environment),
                          Mutation(column="environment:room", value=room_number),
                          Mutation(column="position:x", value=posX),
                          Mutation(column="position:y", value=posY),
                          Mutation(column="position:z", value=posZ),
                          Mutation(column="position:delta", value=delta)])
        roboearth.closeDBTransport(transport)
        return {'id' : id_, 'posX' : posX, 'posY' : posY, 'posZ' : posZ, 'delta' : delta, 'object' : object_, 'environment' : environment, 'room_number' : room_number}
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write dataop to Object table: " + err.__str__())

def updateLocation(id_, posX, posY, posZ, delta, author):
    """
    update existing object location at the database

    id_ : complete identifier (primary key) of the data

    posX, posY, posZ : coordiantes which describes the exact location

    delta : impreciseness of position data

    author: author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        oldLocation = getLocation(id_)
        object_ = oldLocation[0]['object']
        environment = oldLocation[0]['environment']
        room_number = oldLocation[0]['room_number']
        newID = environment + '.' + room_number + '.' + posX + '.' + posY + '.' + posZ + '.' + delta
        
        client.mutateRow("ObjectLocations", newID,
                         [Mutation(column="object:id", value=object_),
                          Mutation(column="info:author", value=author),
                          Mutation(column="environment:id", value=environment),
                          Mutation(column="environment:room", value=room_number),
                          Mutation(column="position:x", value=posX),
                          Mutation(column="position:y", value=posY),
                          Mutation(column="position:z", value=posZ),
                          Mutation(column="position:delta", value=delta)])

        roboearth.closeDBTransport(transport)

        hbase_op.delete_row("ObjectLocations", id_)
        
        return {'id' : id_, 'posX' : posX, 'posY' : posY, 'posZ' : posZ, 'delta' : delta, 'object' : object_, 'environment' : environment, 'room_number' : room_number}
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Robots table: " + err.__str__())


def getLocation(query="", obj="", numOfVersions = 1, exact = False):
    """
    read object location from the database

    query : search query (describes the location)

    object : search a special object at the location

    numOfVersions : allows to get older version of the object location

    exact : search for the exact object location or for an area
    """


    def addObject(row):
        """
        add results to the output dictionary
        """

        output = {"id" : row.row,
                  "author" : row.columns['info:author'].value,
                  "object" : row.columns['object:id'].value,
                  "environment" : row.columns['environment:id'].value,
                  "room_number" : row.columns['environment:room'].value,
                  "posX" : row.columns['position:x'].value,
                  "posY" : row.columns['position:y'].value,
                  "posZ" : row.columns['position:z'].value,                  
                  "delta" : row.columns['position:delta'].value}
                  
        return output

    
    transport = roboearth.openDBTransport()
    client = transport['client']
    scanner = client.scannerOpenWithPrefix("ObjectLocations", query.lower(), [ ])
    result = list()

    res = client.scannerGet(scanner)
    while res:
        if (exact==False or res[0].row == query) and (obj == "" or res[0].columns['object:id'].value.find(obj) > -1):
            result.append(addObject(res[0])) 
        res = client.scannerGet(scanner)

    client.scannerClose(scanner)
    roboearth.closeDBTransport(transport)

    return result
