#!/usr/bin/env python
import sys
 
from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
 
from hbase import Hbase
from hbase.ttypes import *

host = sys.argv[1]
port = int(sys.argv[2])

# Make socket
transport = TSocket.TSocket(host, port)
 
# Buffering is critical. Raw sockets are very slow
transport = TTransport.TBufferedTransport(transport)
 
# Wrap in a protocol
protocol = TBinaryProtocol.TBinaryProtocol(transport)

client = Hbase.Client(protocol)
 
transport.open()

try:
    client.createTable('Elements', 
                       [ColumnDescriptor(name='info:', maxVersions=1),
                        ColumnDescriptor(name='owl:', maxVersions=3),
                        ColumnDescriptor(name='file:', maxVersions=1),
                        ColumnDescriptor(name='subscriber:', maxVersions=1)])
except AlreadyExists, err:
    print "Thrift exception: %s" % (err.message)
    
try:
    client.createTable('Users', 
                       [ColumnDescriptor(name='info:', maxVersions=1),
                        ColumnDescriptor(name='element:', maxVersions=1),
                        ColumnDescriptor(name='news:', maxVersions=1)])
except AlreadyExists, err:
    print "Thrift exception: %s" % (err.message)

try:
    client.createTable('Subscriptions', 
                       [ColumnDescriptor(name='info:', maxVersions=1)])
except AlreadyExists, err:
    print "Thrift exception: %s" % (err.message)

print "Created tables: ", client.getTableNames()

transport.close()
