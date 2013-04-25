# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: web forms

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

from django import forms
#from django.db import models

TABLE_CHOICES = (
    ("ARs", "ActionRecipes"),
    ("OBJs", "Objects"))

class DeleteEntity(forms.Form):
    table = forms.CharField()
    rowKey = forms.CharField()

class ActionRecipe(forms.Form):
    id_ = forms.CharField()
    class_ = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    recipe  = forms.CharField(widget=forms.Textarea)

class Object(forms.Form):
    id_ = forms.CharField()
    class_ = forms.CharField()
    description = forms.CharField(widget=forms.Textarea)
    object_description = forms.CharField(widget=forms.Textarea)
    model = forms.FileField()
    image = forms.ImageField()

class EnvironmentLocation(forms.Form):
    zip = forms.CharField()
    country = forms.CharField()
    city = forms.CharField()
    street = forms.CharField()
    number = forms.CharField()
    map = forms.FileField()

class RobotLocation(forms.Form):
    id_ = forms.CharField()
    environment = forms.CharField(required=False)
    room_number = forms.CharField(required=False) 
    latitude = forms.CharField(required=False)
    longitude = forms.CharField(required=False)
    web = forms.CharField(required=False) 

class ObjectLocation(forms.Form):
    environment= forms.CharField()
    posX = forms.CharField()
    posY = forms.CharField()
    posZ = forms.CharField()
    posR = forms.CharField()
    object_ = forms.CharField()
