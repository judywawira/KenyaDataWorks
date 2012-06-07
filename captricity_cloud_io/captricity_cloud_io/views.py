import urllib2
import Image
import cStringIO as StringIO
import simplejson as json
from xml.dom import minidom

from django.template import RequestContext 
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseServerError, HttpResponseRedirect, HttpResponsePermanentRedirect
from dynamicresponse.json_response import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site

from oauth2client.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow
from captricity_cloud_io.models import CredentialsModel, FlowModel, SyncedDocument
import gdata.spreadsheets.client

from captricity_cloud_io.tasks import upload_to_captricity_by_url, upload_to_google, upload_to_captricity_by_cmis
from captricity_cloud_io.captricity_client import Client

# Captricity API
@login_required
def cap_jobs(request):
    # Get the jobs from captricity to feed into Backbone
    return JsonResponse(request.user.get_profile().get_captricity_client().read_jobs(params=request.GET))

@login_required
def cap_sheet_image(request, sheet_id):
    response = HttpResponse(mimetype="image/png")
    image_data = request.user.get_profile().get_captricity_client().read_sheet_image(sheet_id, accept="image/png")
    image_fake_file = StringIO.StringIO(image_data)
    image = Image.open(image_fake_file)
    image.save(response, "PNG")
    return response

# boxcap
@login_required
def boxcap_list(request):
    # Just return the box app
    return render_to_response('captricity_cloud_io/boxcap_list.html', {'box_api_key' : settings.BOX_API_KEY}, context_instance=RequestContext(request))

@login_required
def upload(request):
    # Initiate celery task to pull items from box and upload to job with job_id to captricity
    upload_to_captricity_by_url(json.loads(request.POST['files']), request.POST['job_id'], request.user.get_profile().id)
    return JsonResponse({"status" : "success"})


# GCap
@login_required
def gdata_list(request):
    """Return the list of spreadsheets owned by the user"""
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        return HttpResponseRedirect(reverse('captricity_cloud_io.views.gdata_login'))
    else:
        gclient = gdata.spreadsheets.client.SpreadsheetsClient()
        gclient = credential.authorize_gclient(gclient)
        raw_resources = gclient.GetSpreadsheets()
        resources = []
        for entry in raw_resources.entry:
            resources.append({'id':entry.GetSpreadsheetKey(), 'title':entry.title.text})
        return JsonResponse(resources)

@login_required
def test_gdata_token(request):
    """Tests to make sure credentials are still valid"""
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        return JsonResponse({'status' : 'failed'})
    return JsonResponse({'status' : 'success'})

@login_required
def dataset_export(request):
    """Default view for GCap"""
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        return HttpResponseRedirect(reverse('captricity_cloud_io.views.gdata_login'))
    else:
        return render_to_response('captricity_cloud_io/dataset_export.html', {}, context_instance=RequestContext(request))

@login_required
def oauth2_callback(request):
    """ Callback page user lands on after authenticating to google"""
    try:
        f = FlowModel.objects.get(id=request.user)
        credential = f.flow.step2_exchange(request.REQUEST)
        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        storage.put(credential)
        f.delete()
        return HttpResponseRedirect(reverse('captricity_cloud_io.views.dataset_export'))
    except FlowModel.DoesNotExist:
        pass

@login_required
def queue_for_gdata_upload(request):
    upload_to_google(request.POST['job_id'][0], request.user.id, False)
    return JsonResponse({"status" : "success"})

@login_required
def register_gdata_sync(request):
    SyncedDocument.objects.get_or_create(user=request.user, document=request.POST['document_name'], spreadsheet=request.POST['spreadsheet_id'][0])
    return JsonResponse({"status" : "success"})

@login_required
def register_create_sync(request):
    upload_to_google(request.POST['job_id'][0], request.user.id, True)
    return JsonResponse({"status" : "success"})

@login_required
def gdata_login(request):
    """Login page: start the oauth2.0 flow to allow captricity cloud io to access user's google resources"""
    storage = Storage(CredentialsModel, 'id', request.user, 'credential')
    credential = storage.get()
    flow = OAuth2WebServerFlow(
               client_id=settings.GOOG_CLIENTID,
               client_secret=settings.GOOG_SECRET_KEY,
               scope=['https://spreadsheets.google.com/feeds',
                   'https://docs.google.com/feeds/',
                   'https://docs.googleusercontent.com/'],
               user_agent='captricity',
               approval_prompt='force',
           )
    callback_url = "http://" + Site.objects.get_current().domain + reverse('captricity_cloud_io.views.oauth2_callback')
    authorize_url = flow.step1_get_authorize_url(callback_url)
    f = FlowModel(id=request.user, flow=flow)
    f.save()
    return HttpResponseRedirect(authorize_url)

# General
@login_required
def update_tokens(request):
    if request.method == 'POST':
        profile = request.user.get_profile()
        profile.captricity_api_token = request.POST.get('captricity-api-token', '')
        profile.cmis_user = request.POST.get('cmis_user', '')
        profile.cmis_pass = request.POST.get('cmis_pass', '')
        profile.save()
    return render_to_response('captricity_cloud_io/profile.html', {'user': request.user.get_profile()}, context_instance=RequestContext(request))
