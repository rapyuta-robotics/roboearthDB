export HADOOP_FOLDER='/home/marcus/Downloads/hadoop-1.0.4'
export FUSE_MOUNTPOINT='/home/marcus/hadoop'
export TOMCAT='/home/marcus/Downloads/apache-tomcat-7.0.37'
export HBASE_FOLDER='/home/marcus/Downloads/hbase-0.94.4'
$TOMCAT/bin/shutdown.sh
$HBASE_FOLDER/bin/hbase-daemon.sh stop thrift
$HBASE_FOLDER/bin/stop-hbase.sh
sudo umount $FUSE_MOUNTPOINT
$HADOOP_FOLDER/bin/stop-dfs.sh

