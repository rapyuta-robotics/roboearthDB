# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: read/write action recipes to the database

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
import sys, os
import xml.dom.minidom
import roboearth.db.transactions.sesame
import roboearth.db.transactions.hbase_op
import time
import twitter

from subprocess import Popen, PIPE
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

sesame = roboearth.db.transactions.sesame
hbase_op = roboearth.db.transactions.hbase_op
roboearth = roboearth.db.roboearth

def set(id_, class_, description, recipe, author):
    """
    write recipe to the database

    id_ : recipe identifier

    class_: recipe class

    description: human readable description

    recipe: owl description

    author: author of the description
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    recipeName = class_.replace(' ', '').lower().strip('.') + '.' + id_.replace(' ', '').lower().strip('.')
    try:
        # recipe already exist
        if get(query=recipeName, exact=True):
            return None

        #write data to hbase
        client.mutateRow("Elements", recipeName,
                         [Mutation(column="info:description", value=description),
                          Mutation(column="info:author", value=author),
                          Mutation(column="info:rating", value="1"),
                          Mutation(column="info:type", value="recipe"),
                          Mutation(column="owl:description", value=recipe)])

        #write data to sesame
        sesame_ret = sesame.set(recipe, recipeName, "elements")
        if sesame_ret != "0":
            hbase_op.delete_row("Elements", recipeName)
            raise IllegalArgument(sesame_ret)
            
        client.mutateRow("Users", author,
                         [Mutation(column="element:"+recipeName, value="")])

        roboearth.closeDBTransport(transport)      

        return {'id' : recipeName, 'description' : description, 'recipe' : recipe}
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Action Recipe table: " + err.__str__())

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
        if data.has_key('recipe'):
            mutation_list.append(Mutation(column="owl:description", value=data['recipe']))            
        
        client.mutateRow("Elements", id_,
                         [Mutation(column="info:modified_by", value=author)] +
                         mutation_list)

        if data.has_key('recipe'):
            sesame.rm(id_, "Elements")
            sesame.set(data['recipe'], id_, "Elements")
        
        # push update to subscribers
        scanner = client.scannerOpenWithPrefix("Elements", id_, [ ])
        res = client.scannerGet(scanner)
        for r in res[0].columns:
            if r.startswith("subscriber:"):
                client.mutateRow("Users", res[0].columns[r].value,
                                 [Mutation(column="news:", value="Recipes#"+id_)])
        client.scannerClose(scanner)

        roboearth.closeDBTransport(transport)

        return True
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to Elements table: " + err.__str__())


def update_rating(id_, rating):
    """
    update the rating of an existing recipe at the database

    id_ : complete identifier (primary key) of the recipe

    rating : new rating
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        client.mutateRow("Recipes", id_,
                         [Mutation(column="rating", value=str(rating))])

        roboearth.closeDBTransport(transport)

        return True
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't update Action Reecipe rating: " + err.__str__())

    
def get(query="", user="", format="html", numOfVersions = 1, semanticQuery = False, exact=False):
    """
    read recipe to the database

    query : search query

    format : output format (html/json)

    numOfVersions : allows to get older version of the object description

    semantic_query : is the query a semantic query?

    exact : search for the exact object or for a class of objects
    """

    def addRecipe(row):
        """
        add results to the output dictionary
        """
        rating = row.columns['info:rating'].value
        
        output = {"id" : row.row,
                  "description" : row.columns['info:description'].value,
                  "author" : row.columns['info:author'].value,
                  "rating" : rating,
                  "recipes" : list()}

        #check subscription
        if user != "" and format=="html":
            scannerSub = client.scannerOpenWithPrefix("Subscriptions", user+"#Recipes#"+row.row, [ ])
            subRes = client.scannerGet(scannerSub)
            if subRes and subRes[0].row == user+"#Recipes#"+row.row:
                output['subscribed'] = True
            else:
                output['subscribed'] = False


        if row.columns.has_key('info:modified_by'):
            output['modified_by'] = row.columns['info:modified_by'].value
            
        versions = client.getVer("Elements", row.row, "owl:description", numOfVersions)
        if format=="html":
            for v in versions:
                try:
                    output['recipes'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                               'recipe' : xml.dom.minidom.parseString(v.value).toprettyxml(indent="    ") })
                except:
                    output['recipes'].append({ 'timestamp' : time.ctime(int(v.timestamp)/1000),
                                               'recipe' : v.value})
                output['fullStars'] = range(int(round(float(rating))))
                output['emptyStars'] = range(10 - int(round(float(rating))))
                
        else:
            for v in versions:
                    output['recipes'].append({ 'timestamp' : v.timestamp,
                                               'recipe' : v.value.replace("\n","")})

        #if not roboearth.local_installation:
        #    roboearth.send_twitter_message("download", "Action Recipe", row.row)

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

    result = list()
    for q in query:
        scanner = client.scannerOpenWithPrefix("Elements", q.lower(), [ ])
        res = client.scannerGet(scanner)
        while res:
            if ((semanticQuery == False and exact == False) or res[0].row == q) and res[0].columns['info:type'].value == 'recipe':
                result.append(addRecipe(res[0])) 
            res = client.scannerGet(scanner)

        client.scannerClose(scanner)

    roboearth.closeDBTransport(transport)

    return result
