# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: read/write environment related data to the database

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
import roboearth.db.transactions.sesame
import roboearth.db.transactions.hbase_op
import roboearth.db.transactions.hdfs_op
from roboearth.db.transactions.external import GeoData
import xml.dom.minidom
import time

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

sesame = roboearth.db.transactions.sesame
hbase_op = roboearth.db.transactions.hbase_op
hdfs = roboearth.db.transactions.hdfs_op
roboearth = roboearth.db.roboearth

def set(id_, class_, description, environment, author, lat=None, lng=None, files=None):
    """
    write environment description to the database

    class_ : environment class

    id_ : unified identifier of environment

    environment : owl description

    author: author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']

    mutation_list =list()

    #create paths
    path = class_.replace(' ', '').lower().strip('.') +  '.' +id_.replace(' ', '').lower().strip('.')
    wwwPath = roboearth.DOMAIN + os.path.join("data/", 'environments/', path.replace('.', '/'))
    path = os.path.join(roboearth.UPLOAD_DIR, 'environments/', path.replace('.', '/'))

    if class_.lower() == "osm":
        try: # try geocoding
            lat, lng = GeoData.geocoding(query=id_, service="osm")
            mutation_list.append(Mutation(column="info:lat", value=lat))
            mutation_list.append(Mutation(column="info:lng", value=lng))
            envName = class_.replace(' ', '').lower().strip('.') + '.' + lat.replace(".", ",") + '.'+lng.replace(".", ",")

        except Exception, err:
            raise roboearth.FormInvalidException("For class \"osm\" the identifier has to consist of two float (<lat>;<lng>) or of an description of a location (e.g. address): " + err.__str__())

    
    if lat and lng:
        try:
            float(lat)
            float(lng)
            mutation_list.append(Mutation(column="info:lat", value=lat))
            mutation_list.append(Mutation(column="info:lng", value=lng))
        except Exception, err:
                raise roboearth.FormInvalidException("Latitude/Longitude need to be float" + err.__str__())

    envName = class_.replace(' ', '').lower().strip('.') + '.' + id_.replace(' ', '').lower().strip('.')
            
    # environment already exist
    if get(query=envName, exact=True):
        return None
    
    # upload files and build file mutation list for hbase operation
    file_mutation_list = [ ]
    if files:
        for file_ID, file_ in files.items():
            hdfs.upload_file(file_, path)
            file_mutation_list.append(Mutation(column="file:"+file_ID, value=wwwPath+"/"+file_.name))
              
    try:
        client.mutateRow("Elements", envName,
                         [Mutation(column="info:description", value=description),
                          Mutation(column="info:author", value=author),
                          Mutation(column="info:rating", value="1"),
                          Mutation(column="info:type", value="environment"),
                          Mutation(column="owl:description", value=environment)] +
                         mutation_list + file_mutation_list)

        #write data to sesame
        sesame_ret = sesame.set(environment, envName, "elements")
        if  sesame_ret != "0":
            hbase_op.delete_row("Elements", envName)
            raise IllegalArgument(sesame_ret+'bug'+envName+' ' +environment)

        client.mutateRow("Users", author,
                         [Mutation(column="element:"+envName, value="")])

        roboearth.closeDBTransport(transport)            

        return {'id' : envName, 'description' : description, 'environment' : environment}

    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Environment table: " + err.__str__())

def update(id_, data, author):
    """
    update an existing recipe at the database

    id_ : complete identifier (primary key) of the recipe

    data: dictionary with the updated data

    author: author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        mutation_list = [ ]
        if data.has_key('description'):
            mutation_list.append(Mutation(column="info:description", value=data['description']))            
        if data.has_key('environment'):
            mutation_list.append(Mutation(column="environment", value=data['environment']))            
        
        client.mutateRow("Environments", id_,
                         [Mutation(column="info:modified_by", value=author)] +
                         mutation_list)

        if data.has_key('environment'):
            sesame.rm(id_, "Environments")
            sesame.set(data['environment'], id_, "Environments")

        # push update to subscribers
        scanner = client.scannerOpenWithPrefix("Environments", id_, [ ])
        res = client.scannerGet(scanner)
        for r in res[0].columns:
            if r.startswith("subscriber:"):
                client.mutateRow("Users", res[0].columns[r].value,
                                 [Mutation(column="news:", value="Environments#"+id_)])
        client.scannerClose(scanner)

        roboearth.closeDBTransport(transport)

        if not roboearth.local_installation:
            roboearth.send_twitter_message("update", "Environment", id_, author)
        
        return True
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Action Recipe table: " + err.__str__())


def get(query="", format="html", numOfVersions = 1, user="", semanticQuery = False, exact=False):
    """
    read environment description from the database

    query : search query

    format : output format (html/json)

    numOfVersions : allows to get older version of the object description

    semantic_query : is the query a semantic query?

    exact : search the specific environment or for an area
    """


    def addEnv(row):
        """
        add results to the output dictionary
        """
        rating = row.columns['info:rating'].value
        output = {"id" : row.row,
                  "description" : row.columns['info:description'].value,
                  "author" : row.columns['info:author'].value,
                  "rating" : rating,
                  "environments" : list()}

        #check subscription
        if user != "" and format=="html":
            scannerSub = client.scannerOpenWithPrefix("Subscriptions", user+"#Environments#"+row.row, [ ])
            subRes = client.scannerGet(scannerSub)
            if subRes and subRes[0].row == user+"#Environments#"+row.row:
                output['subscribed'] = True
            else:
                output['subscribed'] = False

        if row.columns.has_key('info:modified_by'):
            output['modified_by'] = row.columns['info:modified_by'].value

        if row.columns.has_key("info:lat"):
            lat = row.columns['info:lat'].value
            lng = row.columns['info:lng'].value
            delta = 0.002607
            output["location"] = {"latitude" : lat,
                                  "longitude" : lng}

            if format=="html":
                output['location']["html"] = GeoData.getEmbeddedMap(float(lat), float(lng), delta)
            else:
                output['location']['osm'] = {'info' : GeoData.reverseGeocoding(float(lat), float(lng), delta),
                                             'raw_map_data' : GeoData.getRawData(float(lat), float(lng), delta)}

            
        versions = client.getVer("Elements", row.row, "owl:", numOfVersions)
        if format=="html":
            for v in versions:
                try:
                    output['environments'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                               'environment' : xml.dom.minidom.parseString(v.value).toprettyxml(indent="    ") })
                except:
                    output['environments'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                                    'environment' : v.value})
                output['fullStars'] = range(int(rating))
                output['emptyStars'] = range(10 - int(rating))
        else:
            for v in versions:
                    output['environments'].append({ 'timestamp' : v.timestamp,
                                                    'environment' : v.value.replace("\n","")})

        #if not roboearth.local_installation:
        #    roboearth.send_twitter_message("download", "Environment", row.row)

        return output

    # semantic query get send to the reasoning server
    if semanticQuery:
        query = sesame.get(query.replace("SELECT source FROM CONTEXT source", ""), "environments")
        if query['status'] == 0:
            query = [q.rsplit("/", 1)[1] for q in query['stdout']]
        else:
            raise roboearth.DBReadErrorException(query['stderr'])
    else:
        query = [query]

    
    transport = roboearth.openDBTransport()
    client = transport['client']

    result = list()
    for q in query:
        scanner = client.scannerOpenWithPrefix("Elements", q.lower(), [ ])
        res = client.scannerGet(scanner)
        while res:
            if ((semanticQuery == False and exact == False) or res[0].row == q) and res[0].columns['info:type'].value == 'environment':
                result.append(addEnv(res[0])) 
            res = client.scannerGet(scanner)

        client.scannerClose(scanner)

    roboearth.closeDBTransport(transport)

    return result
