Roboearth Hadoop Database
===========

This is a fork of the Roboearth Hadoop Database.

Installation
===========
1. Clone this repository
2. Install [Hadoop http://hadoop.apache.org/docs/stable/single_node_setup.html] 
3. Install [Hbase http://hbase.apache.org/book/quickstart.html]
4. Install [hdfs-fuse http://www.spaggiari.org/index.php/hbase/hadoop-hdfs-fuse-installation#.UcG6E1QW3oF] on hadoop
5. Install Apache [Tomcat http://tomcat.apache.org/tomcat-7.0-doc/setup.html]
6. Install [Sesame http://www.openrdf.org/doc/sesame2/users/] on Tomcat 
7. Correct variables in roboearth.py, roboearth.sh and stop-roboearth.sh
8. Run createTables.py to create necessary tables in Hbase
8. Now, you can start the server by running roboearth.sh and stop it by stop-roboearth.sh 