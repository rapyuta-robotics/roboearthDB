export HADOOP_FOLDER='/home/marcus/Downloads/hadoop-1.0.4'
export FUSE_MOUNTPOINT='/home/marcus/hadoop'
export ROBOEARTH='/home/marcus/workspace/roboearth/roboearth'
export TOMCAT='/home/marcus/Downloads/apache-tomcat-7.0.37'
export HBASE_FOLDER='/home/marcus/Downloads/hbase-0.94.4'
$HADOOP_FOLDER/bin/start-dfs.sh
cd $HADOOP_FOLDER/src/contrib/fuse-dfs/src/
sudo ./fuse_dfs_wrapper.sh dfs://localhost:9000 $FUSE_MOUNTPOINT
cd
$HBASE_FOLDER/bin/start-hbase.sh
$HBASE_FOLDER/bin/hbase-daemon.sh start thrift
$TOMCAT/bin/startup.sh
cd $ROBOEARTH
./start-all.sh
