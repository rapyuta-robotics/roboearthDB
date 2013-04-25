# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle generic hbase operations

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
import roboearth.db.transactions.sesame
import xml.dom.minidom

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

sesame = roboearth.db.transactions.sesame
hdfs = roboearth.db.transactions.hdfs_op
roboearth = roboearth.db.roboearth

def list_all(table):
    """
    returns a list of all entries of a table
    """
    transport = roboearth.openDBTransport()
    client = transport['client']
    scanner = client.scannerOpenWithPrefix(table, "", [ ])
    result = list()

    res = client.scannerGet(scanner)
    while res:
        result.append(res[0].row) 
        res = client.scannerGet(scanner)

    client.scannerClose(scanner)
    roboearth.closeDBTransport(transport)

    return result

def delete_row(table, rowKey):
    """
    deletes a complete row (rowKey) from a given table
    """

    hasBinaryFiles = ["Objects", "Robots"]
    hasGraphData = ["Objects", "Recipes", "Environments"]

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        client.deleteAllRow(table, rowKey)
        roboearth.closeDBTransport(transport)
        if table in hasBinaryFiles:
            hdfs.rm_dir(os.path.join(roboearth.UPLOAD_DIR, table.lower(), rowKey.replace('.', '/')))
        if table in hasGraphData:
            sesame.rm(rowKey, table)
            
    except IOError, err:
        roboearth.closeDBTransport(transport)
        raise roboearth.DBWriteErrorException("Can't delete data: " + err.__str__())

def delete_column(table, rowKey, column):
    """
    deletes a column from a given row (rowKey) in a specific table
    """
    transport = roboearth.openDBTransport()
    client = transport['client']
    
    scanner = client.scannerOpenWithPrefix(table, rowKey, [ ])
    res = client.scannerGet(scanner)

    for i in res[0].columns:
        if i == column:
            break

    client.scannerClose(scanner)

    try:
        client.deleteAll(table, rowKey, column)
        roboearth.closeDBTransport(transport)
            
    except IOError, err:
        roboearth.closeDBTransport(transport)
        raise roboearth.DBWriteErrorException("Can't delete column: " + err.__str__())


def update_rating(table, id_, rating):
    """
    update the rating of an existing recipe at the database

    table: database table

    id_ : complete identifier (primary key) of the recipe

    rating : new rating
    """

    transport = roboearth.openDBTransport()
    client = transport['client']
    try:
        client.mutateRow(table, id_,
                         [Mutation(column="rating", value=str(rating))])

        roboearth.closeDBTransport(transport)

        return True
    except (IOError, IllegalArgument), err:
        raise roboearth.DBWriteErrorException("Can't update Action Reecipe rating: " + err.__str__())
