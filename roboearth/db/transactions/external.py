# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: defines external interfaces

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

import urlparse, urllib, httplib
import json

class GeoData:
    """
    This class contains all methods concerning the access of external services
    regarding goeraphical data
    """
    
    @staticmethod
    def getRawData(lat, lng, delta, service="osm"):
        """
        returns raw geo data from an external service

        lat : latitude
        
        lng : longitude

        delta : sice of the map section (lat-delta, lng-delta, lat+delta, lng+delta)

        service : external service (default: OpenStreetMap (osm))
        """
            

        def osm():
            """
            get raw geo data from Open Street Map
            """

            api_url = "http://www.openstreetmap.org/api/0.6/"
            
            urlparts = urlparse.urlparse(api_url)
            conn = httplib.HTTPConnection(urlparts[1])
            url = urlparts[2]

            conn.request("GET", url+'/'+"map?bbox="+
                         str(lng-delta)+","+str(lat-delta)+","+str(lng+delta)+","+str(lat+delta))
            response = conn.getresponse()

            if response.status == 200:
                return response.read()

            else:
                return str(response.status)

        if service == "osm":
            return osm()


    @staticmethod
    def getEmbeddedMap(lat, lng, delta, service="osm"):
        """
        returns the HTML code to display a map provided by an external service

        lat : latitude
        
        lng : longitude

        delta : sice of the map section (lat-delta, lng-delta, lat+delta, lng+delta)

        service : external service (default: OpenStreetMap (osm))
        """

        def osm():
            return """
            <iframe width="425" height="350" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="http://www.openstreetmap.org/export/embed.html?bbox=%(left)f,%(top)f,%(right)f,%(bottom)f&amp;layer=mapnik&amp;marker=%(lat)f,%(lng)f" style="border: 1px solid black"></iframe><br /><small><a href="http://www.openstreetmap.org/?lat=%(lat)f&amp;lon=%(lng)f&amp;zoom=18&amp;layers=M&amp;mlat=%(lat)f&amp;mlon=%(lng)f">View Larger Map</a></small>
            """ % {'left' : lng-delta,
                   'top' : lat-delta,
                   'right' : lng+delta,
                   'bottom' : lat+delta,
                   'lat' : lat,
                   'lng' : lng}

        if service == "osm":
            return osm()

    @staticmethod
    def geocoding(query, service="osm"):
        """
        finding associated geographic coordinates and returns the tuple (lat,lng)
        
        query : data (e.g. an address) which should be transferred into geographical coordinates
        
        service : external service (default: OpenStreetMap (osm))
        """

        def osm(query):
            api_url = "http://open.mapquestapi.com/nominatim/v1/"
            
            urlparts = urlparse.urlparse(api_url)
            conn = httplib.HTTPConnection(urlparts[1])
            url = urlparts[2]

            conn.request("GET", url+'/'+"search.php?q="+urllib.quote(query)+"&format=json")
            response = conn.getresponse()

            if response.status == 200:
                result = json.loads(response.read())
                return result[0]['lat'], result[0]['lon']
            else:
                return str(response.status)
    
        if service == "osm":
            return osm(query)

    @staticmethod
    def reverseGeocoding(lat, lng, delta, service="osm"):
        """
        find the address according the geographical coordinates

        lat : latitude
        
        lng : longitude

        delta : sice of the map section (lat-delta, lng-delta, lat+delta, lng+delta)

        service : external service (default: OpenStreetMap (osm))
        """

        def osm():
            """
            get the address of a given location
            """

            api_url = "http://nominatim.openstreetmap.org"
            
            urlparts = urlparse.urlparse(api_url)
            conn = httplib.HTTPConnection(urlparts[1])
            url = urlparts[2]

            conn.request("GET", url+'/'+"reverse?format=json&lat="+str(lat)+"&lon="+str(lng)+"&zoom=18&addressdetails=1")
            response = conn.getresponse()

            if response.status == 200:
                return json.loads(response.read())
            else:
                return str(response.status)
            

        if service == "osm":
            return osm()
