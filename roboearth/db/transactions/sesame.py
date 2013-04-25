# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: access the sesame database (reasoning server)

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
from subprocess import Popen, PIPE
import roboearth.db.roboearth

roboearth = roboearth.db.roboearth

def rm(rowKey, repository):
    """
    removes owl description from the database

    rowKey : complete identifier of the data (primary key)

    repository: the repository which hosts the owl description
    """

    if repository.lower() == "recipes":
        location="recipe"
    if repository.lower() == "objects":
        location = "object"
    if repository.lower() == "environments":
        location="environment"
    uid = roboearth.DOMAIN + "api/" + location + "/" + rowKey
    cmd = ["java", "-cp", roboearth.SESAME_CONNECTOR_LIBS, roboearth.SESAME_CONNECTOR, "rm", roboearth.SESAME_SERVER, repository.lower(), uid]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return p.returncode

def set(data, data_id, repository):
    """
    write owl description to the database

    data : the owl data

    data_id : the identifier, row key at the hdfs

    repository: the repository which should store the data
    """
    
    data = (" ".join("%s" % line for line in data.splitlines())).strip()
    if repository.lower() == "recipes":
        location="recipe"
    if repository.lower() == "objects":
        location = "object"
    if repository.lower() == "environments":
        location = "environment"
    uid = roboearth.DOMAIN + "api/" + location + "/"+data_id
    cmd = ["java", "-cp", roboearth.SESAME_CONNECTOR_LIBS, roboearth.SESAME_CONNECTOR, "set", roboearth.SESAME_SERVER, repository.lower(), uid, data_id]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        return "0"
    else:
        return stdout

def get(query, repository):
    """

    execute reasoning and return the results

    query : the semantic search query (SeRQL)

    repository: the repository which hosts the owl data
    """

    query = " ".join("%s" % opt for opt in query.splitlines())
    cmd = ["java", "-cp", roboearth.SESAME_CONNECTOR_LIBS, roboearth.SESAME_CONNECTOR, "get", roboearth.SESAME_SERVER, repository.lower(), query]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return {'stdout' : stdout.splitlines(),
            'stderr' : stderr,
            'status' : p.returncode}

def generic_get(query, repository, format="xml"):
    """
    execute generic reasoning requests

    query : the semantic search query (SeRQL)

    repository: the repository which hosts the owl data

    format: output format (json or xml)
    """
    
    query = " ".join("%s" % opt for opt in query.splitlines())
    cmd = ["java", "-cp", roboearth.SESAME_CONNECTOR_LIBS,
    roboearth.SESAME_CONNECTOR, "generic_get", roboearth.SESAME_SERVER, repository.lower(), query, format]
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return stdout
