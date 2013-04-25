""" DEPRECIATED, don't use this module! """
import roboearth.db.roboearth
import roboearth.db.forms
import roboearth.db.views.views
import roboearth.db.transactions.objects
import roboearth.db.transactions.hbase_op
import xml.dom.minidom
from django.http import HttpResponse
from django.template import Context, loader
from django.http import HttpResponseRedirect

transaction = roboearth.db.transactions.objects
hbase_op = roboearth.db.transactions.hbase_op
forms = roboearth.db.forms
views = roboearth.db.views.views
roboearth = roboearth.db.roboearth

#
# Forms
#

def submitForm(request):
    """ show form to submit new object locations """
    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")


    template = loader.get_template('locations/submitObject.html')
    webpage_values = Context({'MainMenu' : roboearth.MainMenu(request),
                              'Objects' : hbase_op.list_all("Objects"),
                              'Environments' : hbase_op.list_all("Environments")})
    
    return HttpResponse(template.render(webpage_values))

def requestForm(request):
    """ show form to request object locations """
    template = loader.get_template('locations/requestObject.html')
    webpage_values = Context({'MainMenu' : roboearth.MainMenu(request)})
    
    return HttpResponse(template.render(webpage_values))

#
# Actions
#

def submit(request):
    """ submit new object location, expected data """

    if not request.user.is_authenticated():
        return HttpResponseRedirect("/login")

    if request.method == 'POST':
        try:
            transaction.setLocation(environment=request.POST['environment'],
                                    author=request.user.username,
                                    room_number = request.POST['room_number'],
                                    posX=request.POST['posX'],
                                    posY=request.POST['posY'],
                                    posZ=request.POST['posZ'],
                                    delta=request.POST['delta'],
                                    object_=request.POST['object'])
            return HttpResponse(views.success(request))
        except (roboearth.DBWriteErrorException, roboearth.DBException), err:
            return HttpResponse(views.error(request, nextPage="/locations/objects", errorType=2, errorMessage=err.__str__()))

def request(request):
    
    def output(objects, query):
        template = loader.get_template('locations/showObject.html')
        webpage_values = Context({'MainMenu' : roboearth.MainMenu(request),
                                  'Objects' : objects,
                                  'Domain' : roboearth.DOMAIN,
                                  'is_auth' : request.user.is_authenticated(),
                                  'Query' : query})    
        return template.render(webpage_values)


    if request.method == 'GET':
        query = request.GET['query']
        if request.GET.has_key('obj'):
            obj = request.GET['obj']
        else:
            obj = ""
        return HttpResponse(output(transaction.getLocation(query, obj), query))
    else:
        template = loader.get_template('requestObjects.html')
        webpage_values = Context({'MainMenu' : roboearth.MainMenu(request)})
    
        return HttpResponse(template.render(webpage_values))
