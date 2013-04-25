# -*- coding: utf-8 -*- 
"""
  RoboEarth Web Interface: User management
  
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

import roboearth.db.roboearth
import roboearth.db.forms
import roboearth.db.views.views
import roboearth.db.transactions.users
import datetime
import hashlib
import smtplib
from email.mime.text import MIMEText
from roboearth.db.models import api_keys
from django.http import HttpResponse
from django.template import Context, loader
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.shortcuts import render_to_response

forms = roboearth.db.forms
views = roboearth.db.views.views
transaction = roboearth.db.transactions.users
roboearth = roboearth.db.roboearth


#
# Forms
#

def registerForm(request, error=False):
    """ show form to register new user """
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")

    values = {'error' : error}
    return render_to_response('register.html', roboearth.webpage_values(request,values))

def loginForm(request, error=False):
    """ show login form """
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")

    values = {'error' : error}
    
    return render_to_response('login.html', roboearth.webpage_values(request,values))

def profile(request):
    """ show the profil of the authenticated user """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/")

    template = loader.get_template('profile.html')
    values = {'username' : request.user.username,
              'email' : request.user.email,
              'api_key' : api_keys.objects.get(pk=request.user.username).key}

    return render_to_response('profile.html', roboearth.webpage_values(request,values))

def manage(request):
    """ admin view to manage registered users """
    if not request.user.is_authenticated() or request.user.is_superuser==False:
        return HttpResponseRedirect("/")

    users = User.objects.all()
    users_list = list()
    for u in users:
        users_list.append({'username' : u.username,
                           'first_name' : u.first_name,
                           'last_name' : u.last_name,
                           'email' : u.email,
                           'is_active' : u.is_active,
                           'is_superuser' : u.is_superuser})
        
    values = {'Users' : users_list}

    return render_to_response('manage.html', roboearth.webpage_values(request,values))


def delete(request):
    """ delete user """
    if not request.user.is_authenticated() or request.user.is_superuser==False:
        return HttpResponseRedirect("/")
    user = User.objects.get(username__exact=request.POST['username'])
    api_keys.objects.get(pk=user.username).delete()
    user.delete()

    transaction.delete(request.POST['username'])

    return HttpResponseRedirect("/accounts/manage")

def activate(request):
    """ activate user account """
    if not request.user.is_authenticated() or request.user.is_superuser==False:
        return HttpResponseRedirect("/")

    user = User.objects.get(username__exact=request.POST['username'])
    user.is_active=True
    user.save()

    # send mail to user
    message = """
    Your account for the RoboEarth platform has been activated.
    Visit %(roboearth_url)slogin
    """ % {'roboearth_url' : roboearth.DOMAIN}

    msg = MIMEText(message)
    msg['Subject'] = "your account has been activated"
    msg['From'] = roboearth.ADMIN
    msg['To'] = request.POST['email']

    try:
        smtpObj = smtplib.SMTP('hermes')
        smtpObj.sendmail(roboearth.ADMIN, request.POST['email'], msg.as_string())
        smtpObj.quit()
    except Exception, e:
        pass

    
    return HttpResponseRedirect("/accounts/manage")

def deactivate(request):
    """ deactivate user account """
    if not request.user.is_authenticated() or request.user.is_superuser==False:
        return HttpResponseRedirect("/")

    user = User.objects.get(username__exact=request.POST['username'])
    user.is_active=False
    user.save()
    
    return HttpResponseRedirect("/accounts/manage")



def create(request):
    """ create new user account. The user have to provide first name, last
    name, username, password and a valid email address """
    firstname = request.POST['firstname']
    lastname = request.POST['lastname']
    username = request.POST['username']
    password = request.POST['password']
    email = request.POST['email']

    try:
        User.objects.get(username__exact=username)
        return HttpResponse(registerForm(request, error=True))
    except:
        pass
    
    user = User.objects.create_user(username, email, password)
    #user.is_active=False
    user.is_active=True # for ICRA
    user.first_name = firstname
    user.last_name = lastname
    user.save()

    #generate API key
    salt = str(datetime.datetime.now())
    hashvalue = hashlib.sha1(username+password+email+salt).hexdigest()
    for c in username:
        hashvalue = hex(ord(c)).lstrip("0x")+hashvalue
            
    api_key = api_keys(username=username, key=hashvalue)
    api_key.save()

    transaction.create(username)

    # send mail to admin
    message = """
    A new user asks for access to the RoboEarth platform:

    Username: %(username)s
    First Name: %(firstname)s
    Last Name: %(lastname)s
    E-Mail: %(email)s
    """ % {'username' : roboearth.replace_unicode(username),
           'firstname' : roboearth.replace_unicode(firstname),
           'lastname' : roboearth.replace_unicode(lastname),
           'email' : roboearth.replace_unicode(email)}


    msg = MIMEText(message)
    msg['Subject'] = "new user registered"
    msg['From'] = roboearth.ADMIN
    msg['To'] = roboearth.ADMIN

    try:
        smtpObj = smtplib.SMTP('hermes')
        smtpObj.sendmail(roboearth.ADMIN, roboearth.ADMIN, msg.as_string())
        smtpObj.quit()
    except Exception, e:
        return HttpResponse(views.error(request, errorType=2, errorMessage=e.__str__()))


    return HttpResponseRedirect("/accounts/created")

def created(request):
    """ user account successful created """
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")

    return render_to_response('registration_finished.html', roboearth.webpage_values(request))


def login(request):
    """ authenticate a user. The user has to provide his user name and password """
    username = request.POST['username']
    password = request.POST['password']
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        # Correct password, and the user is marked "active"
        auth.login(request, user)
        # Redirect to a success page.
        return HttpResponseRedirect("/")
    else:
        # Show an error page
        return HttpResponse(loginForm(request, error=True))

def logout(request):
    """ user logout """
    auth.logout(request)
    return HttpResponseRedirect("/")

def update(request):
    """ update user data """
    
    def change_password(request):
        """ change password of the authenticated user """
        if request.user.check_password(request.POST['password_old']) and request.POST['password_new0'] == request.POST['password_new1']:
            request.user.set_password(request.POST['password_new0'])
            request.user.save()
            return HttpResponse(views.success(request))
        else:
            return HttpResponse(views.error(request, nextPage="/profile", errorType=0, errorMessage="Couldn't change your password, please try again!"+request.user.password))

    def change_email(request):
        """ change e-mail address of the authenticated user """
        if request.POST['email_new'] != request.POST['email_old']:
            request.user.email = request.POST['email_new']
            request.user.save()
            return HttpResponse(views.success(request))
        else:
            return HttpResponseRedirect("/profile")

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.POST['type'] == "password":
        return change_password(request)
    elif request.POST['type'] == "email":
        return change_email(request)

def newsfeed(request):
    """ show the newsfeed from a specific user
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    values = {'Domain' : roboearth.DOMAIN,
                      'news' : transaction.getNewsfeed(request.user.username),
                      }

    return render_to_response('newsfeed.html', roboearth.webpage_values(request,values))

def subscriptions(request):
    """ show all subscriptions of a user
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    try:
        values = {'Domain' : roboearth.DOMAIN,
                  'Subscriptions' : transaction.getSubscriptions(username=request.user.username),
                  }

        return render_to_response('subscriptions.html', roboearth.webpage_values(request,values))
    except Exception, err:
        return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))

    
def subscribe(request):
    """ subscribe to a datum
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    try:
        transaction.subscribe(username = request.user.username,
                              table = request.POST['table'],
                              uid = request.POST['rowKey'])
        return HttpResponse(views.success(request))
    except Exception, err:
        return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))

def unsubscribe(request):
    """ subscribe to a datum
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    try:
        transaction.unsubscribe(username = request.user.username,
                                table = request.POST['table'],
                                uid = request.POST['rowKey'])
        return HttpResponse(views.success(request))
    except Exception, err:
        return HttpResponse(views.error(request, nextPage="/", errorType=2, errorMessage=err.__str__()))

