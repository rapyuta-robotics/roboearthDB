# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: read/write robot related data to the database

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
import xml.dom.minidom

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

hdfs = roboearth.db.transactions.hdfs_op
roboearth = roboearth.db.roboearth

def set(id_, environment, description, picture, author, latitude="", longitude=""):
    """
    write a robot location to the database

    id_ : robot identifier

    environmanet : reference to the related environment

    description : description of the reobot

    picture: picture of the robot

    author : author who submitted the data
    """

    transport = roboearth.openDBTransport()
    client = transport['client']

    if get(query=id_, exact=True):
        return None
    
    try:
        #create paths
        path = id_.replace(' ', '').lower().strip('.') +  '.' +id_.replace(' ', '').lower().strip('.')
        wwwPath = roboearth.DOMAIN + os.path.join("data/", 'robots/', id_.replace(' ', '').lower().strip('.'), picture.name)
        hdfs.upload_file(picture, os.path.join(roboearth.UPLOAD_DIR, 'robots/', id_.replace(' ', '').lower().strip('.')))
        
        if environment == "":
            client.mutateRow("Robots", id_.lower(),
                             [Mutation(column="geographical:latitude", value=latitude),
                              Mutation(column="info:author", value=author),
                              Mutation(column="info:description", value=description),
                              Mutation(column="info:picture", value=wwwPath),
                              Mutation(column="geographical:longitude", value=longitude)])
        else:
            scanner = client.scannerOpenWithPrefix("Environments", environment.lower(), [ ])
            if not client.scannerGet(scanner):
                raise roboearth.NoDBEntryFoundException("Couldn't connect robot with the named environment. Environment doesn't exits in database")
            
            client.mutateRow("Robots", id_,
                             [Mutation(column="environment:id", value=environment.lower()),
                              Mutation(column="info:author", value=author),
                              Mutation(column="info:description", value=description),
                              Mutation(column="info:picture", value=wwwPath)])
            
        client.mutateRow("Users", author,
                         [Mutation(column="robot:"+id_, value="")])

        roboearth.closeDBTransport(transport)
        return {'id' : id_, 'environment' : environment, 'description' : description}
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Robot table: " + err.__str__())

def update(id_, environment, room_number, author):
    """
    update location information at the database

    id_ : robot identifier

    environmanet : reference to the related environment

    room_number : the room where the robot is located

    author : author who submitted the data
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        client.mutateRow("Robots", id_,
                         [Mutation(column="environment:id", value=environment),
                          Mutation(column="info:author", value=author),
                          Mutation(column="environment:room", value=room_number)])

        # push update to subscribers
        scanner = client.scannerOpenWithPrefix("Robots", id_, [ ])
        res = client.scannerGet(scanner)
        for r in res[0].columns:
            if r.startswith("subscriber:"):
                client.mutateRow("Users", res[0].columns[r].value,
                                 [Mutation(column="news:", value="Robots#"+id_)])
        client.scannerClose(scanner)

        roboearth.closeDBTransport(transport)
        
        return {'id' : id_, 'environment' : environment, 'room_number' : room_number}
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Robots table: " + err.__str__())


def get(query="", numOfVersions = 1, user="", format="html", exact=False):
    """
    read a robot location from the database

    query : search query

    numOfVersions : allows to get older version of the location

    exact : search for the exact object or for a class of objects
    """

    def addObject(row):
        output = {"id" : row.row,
                  "description" : row.columns['info:description'].value,
                  "picture" : row.columns['info:picture'].value,
                  "author" : row.columns['info:author'].value}

        #check subscription
        if user != "" and format=="html":
            scannerSub = client.scannerOpenWithPrefix("Subscriptions", user+"#Robots#"+row.row, [ ])
            subRes = client.scannerGet(scannerSub)
            if subRes and subRes[0].row == user+"#Robots#"+row.row:
                output['subscribed'] = True
            else:
                output['subscribed'] = False

 
        if row.columns.has_key('environment:id'):
            output['environment'] =  row.columns['environment:id'].value
        if row.columns.has_key('geographical:latitude'):
            output["latitude"] = row.columns['geographical:latitude'].value
            output["longitude"] = row.columns['geographical:longitude'].value
        return output

    
    transport = roboearth.openDBTransport()
    client = transport['client']
    scanner = client.scannerOpenWithPrefix("Robots", query.lower(), [ ])
    result = list()

    res = client.scannerGet(scanner)
    while res:
        if exact==False or res[0].row == query:
            result.append(addObject(res[0])) 
        res = client.scannerGet(scanner)

    client.scannerClose(scanner)
    roboearth.closeDBTransport(transport)

    return result


def myRobots(user, numOfVersions = 1, exact=False):
    """
    get all robots from a specific user
    """

    def addObject(row):
        output = {"id" : row.row,
                  "description" : row.columns['info:description'].value,
                  "picture" : row.columns['info:picture'].value,
                  "author" : row.columns['info:author'].value}

        #check subscription
        if user != "" and format=="html":
            scannerSub = client.scannerOpenWithPrefix("Subscriptions", user+"#Robots#"+row.row, [ ])
            subRes = client.scannerGet(scannerSub)
            if subRes and subRes[0].row == user+"#Robots#"+row.row:
                output['subscribed'] = True
            else:
                output['subscribed'] = False


        if row.columns.has_key('environment:id'):
            output['environment'] =  row.columns['environment:id'].value
        if row.columns.has_key('geographical:latitude'):
            output["latitude"] = row.columns['geographical:latitude'].value
            output["longitude"] = row.columns['geographical:longitude'].value
        return output

    
    transport = roboearth.openDBTransport()
    client = transport['client']

    scanner = client.scannerOpenWithPrefix("Users", user, [ ])
    
    res = client.scannerGet(scanner)

    output = list()
    for r in res[0].columns:
        if r.startswith("robot:"):
            output.append(get(query=r[6:], exact=True)[0])

    return output
