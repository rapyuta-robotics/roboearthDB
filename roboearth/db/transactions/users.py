# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: read/write user related data to the database

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

import roboearth.db.transactions.hbase_op
import roboearth.db.roboearth
import time

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

hbase_op = roboearth.db.transactions.hbase_op
roboearth = roboearth.db.roboearth

def create(user_name):
    """
    create hbase table for a new user

    user_name : user name of the new user
    """

    transport = roboearth.openDBTransport()
    client = transport['client']

    try:
        client.mutateRow("Users", user_name, [])

        roboearth.closeDBTransport(transport)

    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't write data to users table: " + err.__str__())

    return True

def delete(user_name):
    """
    delete user

    user_name : user name of the new user
    """

    hbase_op.delete_row("Users", user_name)
    return True

def getNewsfeed(username):
    """ returns the last 20 updates of the subscriptions from a specific user
    """
    transport = roboearth.openDBTransport()
    client = transport['client']

    results = list()
    items = client.getVer("Users", username, "news:", 20)
    for i in items:
        table, uid = i.value.split('#', 1)
        scanner2 = client.scannerOpenWithPrefix(table, uid, [ ])
        d = client.scannerGet(scanner2)
        results.append({'description' : d[0].columns['info:description'].value,
                        'timestamp' : time.ctime(int(i.timestamp)/1000),
                        'url' : roboearth.DOMAIN+table.lower()+"/"+"result?query="+uid+"&exact=True",
                        'table' : table[:len(table)-1],
                        'id' : uid})
        client.scannerClose(scanner2)

    return results

def getSubscriptions(username):
    """ returns all subscriptions of a given user
    """
    transport = roboearth.openDBTransport()
    client = transport['client']

    scanner = client.scannerOpenWithPrefix("Subscriptions", username, [ ])
    user = client.scannerGet(scanner)

    result = { }
    result['Robots'] = list()
    result['Recipes'] = list()
    result['Objects'] = list()
    result['Environments'] = list()
    result['Users'] = list()
    while user:
        uname, table, uid = user[0].row.split('#',2)
        result[table].append({'id' : uid,
                              'url' : roboearth.DOMAIN+table.lower()+"/"+"result?query="+uid+"&exact=True"})        
        user = client.scannerGet(scanner)

    client.scannerClose(scanner)
    roboearth.closeDBTransport(transport)

    return result


def subscribe(username, table, uid):
    transport = roboearth.openDBTransport()
    client = transport['client']
    client.mutateRow('Elements', uid, [Mutation(column="subscriber:"+username, value=username)])
    client.mutateRow("Subscriptions", username+"#"+table+"#"+uid,
                     [Mutation(column="info:"+table, value=uid)])
    roboearth.closeDBTransport(transport)

def unsubscribe(username, table, uid):
    hbase_op.delete_row(table="Subscriptions", rowKey=username+"#"+table+"#"+uid)
    hbase_op.delete_column(table='Elements', rowKey=uid, column="subscriber:"+username)
