# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: handle generic hdfs operations

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

import os
import shutil
import roboearth.db.roboearth

roboearth = roboearth.db.roboearth

def upload_file(f, path):
    """
    write file to hdfs

    f : file

    path : hdfs location of the file
    """
    try:
        # write file to hdfs
        filename = os.path.join(path, f.name)
        if not os.path.exists(path):
            os.makedirs(path)
        if os.path.exists(filename):
            raise roboearth.DBWriteErrorException
            #os.remove(filename)
        destination = open(filename, 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()

    except:
        raise roboearth.DBWriteErrorException("Can't write" + os.path.join(path, f.name) + " to hdfs")

def rm_dir(path):
    """
    removes a directory (path) at the hdfs
    """
    if os.path.exists(path):
        return shutil.rmtree(path)

def rm_file(file_):
    """
    removes a file (file_) at the hdfs
    """
    return os.remove(file_)
