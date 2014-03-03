Roboearth Hadoop Database
===========

This is a fork of the Roboearth Hadoop Database.

Installation
===========
1. Clone this repository
2. Install [Hadoop] (https://hadoop.apache.org/docs/r1.2.1/single_node_setup.html) 
3. Install [Hbase] (http://hbase.apache.org/book/quickstart.html)
4. Install [HDFS-Fuse] (https://github.com/IDSCETHZurich/roboearthDB/wiki/Install-hdfs-fuse) on hadoop
5. Install Apache [Tomcat]( http://tomcat.apache.org/tomcat-7.0-doc/setup.html)
6. Install [Sesame] (http://openrdf.callimachus.net/sesame/2.7/docs/users.docbook?view) on Tomcat 
7. Make sure to create a user for login for tomcat server apps
8. Now login to tomcat and browse to sesame-workbench
9. Add a table called 'elements'
10. Correct variables in roboearth.py, roboearth.sh and stop-roboearth.sh, settings.py
11. Also correct url for static documents in urls.py (The fuse mountpoint)
12. Run createTables.py to create necessary tables in Hbase (You need hbase, hadoop and thrift server running)
13. Now, you can start the server by running start-roboearth.sh and stop it by stop-roboearth.sh 
14. The user database contains a dummy user called 'test' to login with password '123456'

Using the AMI
===========
1. If you are using the AMI, you should start from point 13 of the previous list of instructions

FAQ
==========
1. If you get "could not connect to 'thrift server ip'" (which is mostly on port 9090), Wait sometime. If you still get the error, try restarting roboearth.
2. If it takes ages to stop hbase while running stop-roboearth.sh, try pressing Ctrl+C and try again. 
3. If you reboot an instance, roboearth may not work on the first attempt due to change in ip. Start roboearth and check (ip of instance):60010 to see if hbase is running.
If it's not, restart roboearth and wait for sometime for hbase to start. Keep checking logs at hbase/logs/(master log file). 

