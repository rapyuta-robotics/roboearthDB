#!/usr/bin/env python
# first argument: Table
# second argument: row key
import sys
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

from hbase import Hbase
from hbase.ttypes import *

NAMENODE = "localhost"
NAMENODE_PORT = 9090

transport = TSocket.TSocket(NAMENODE, NAMENODE_PORT)
transport = TTransport.TBufferedTransport(transport)
protocol = TBinaryProtocol.TBinaryProtocol(transport)
client = Hbase.Client(protocol)
transport.open()

scanner = client.scannerOpenWithPrefix(sys.argv[1].capitalize(), sys.argv[2], [ ])

res = client.scannerGet(scanner)

if sys.argv[1].capitalize() == "Elements":
    print res[0].columns['owl:description'].value

client.scannerClose(scanner)
transport.close()
