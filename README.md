Roboearth Hadoop Database
===========

This is a fork of the Roboearth Hadoop Database.

Installation
===========
1. Clone this repository
2. Install [Hadoop] (http://hadoop.apache.org/docs/stable/single_node_setup.html) 
3. Install [Hbase] (http://hbase.apache.org/book/quickstart.html)
4. Install [HDFS-Fuse] (https://github.com/IDSCETHZurich/roboearthDB/wiki/Install-hdfs-fuse) on hadoop
5. Install Apache [Tomcat]( http://tomcat.apache.org/tomcat-7.0-doc/setup.html)
6. Install [Sesame] (http://www.openrdf.org/doc/sesame2/users/) on Tomcat 
7. Make sure to create a user for login for tomcat server apps
8. Now login to tomcat and browse to sesame-workbench
9. Add a table called 'elements'
10. Correct variables in roboearth.py, roboearth.sh and stop-roboearth.sh, settings.py
11. Also correct url for static documents in urls.py (The fuse mountpoint)
12. Run createTables.py to create necessary tables in Hbase (You need hbase, hadoop and thrift server running)
13. Now, you can start the server by running roboearth.sh and stop it by stop-roboearth.sh 
14. The user database contains a dummy user called 'test' to login with password '123456'
