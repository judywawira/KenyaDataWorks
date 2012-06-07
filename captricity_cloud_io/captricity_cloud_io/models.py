from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

import oauth2client.client
from oauth2client.django_orm import FlowField
from oauth2client.django_orm import CredentialsField

from captricity_cloud_io.captricity_client import Client

# Model for tracking document sync up
class SyncedDocument(models.Model):
    user = models.ForeignKey(User)
    document = models.CharField(max_length=128)
    spreadsheet = models.CharField(max_length=128)

class UserProfile(models.Model):
    captricity_api_token = models.CharField(max_length=128, blank=True)
    box_auth_token = models.CharField(max_length=128, blank=True)
    user = models.ForeignKey(User, unique=True)

    def get_captricity_client(self):
        return Client(endpoint=settings.API_TARGET, api_token=self.captricity_api_token)

# Model for tracking phase in oauth2.0 flow
class FlowModel(models.Model):
    id = models.ForeignKey(User, primary_key=True)
    flow = FlowField()

# Model for tracking oauth2.0 credentials
class CredentialsModel(models.Model):
    id = models.ForeignKey(User, primary_key=True)
    credential = CredentialsField()

# Hack to make oauth2client package work with gdata (from suggestion on http://stackoverflow.com/questions/7359725/google-sites-api-oauth2-on-appengine)
# Monkey patches oauth2client package to be compatible with gdata api
# Gdata api uses this method to modify the headers of http requests
def modify_request(self, http_request):
    self.apply(http_request.headers)
oauth2client.client.OAuth2Credentials.modify_request = modify_request
# Use this function to update the gdata client
def authorize_gclient(self, client):
    client.auth_token = self
    orig_request = client.http_client.request

    def new_request(http_request):
        response = orig_request(http_request)
        if response.status == 401:
            refresh_response = self._refresh(client.http_client.compatible_request)
            if self.invalid:
                return refresh_response
            else:
                self.apply(http_request.headers)
                return orig_request(http_request.headers)
        else:
            return response

    client.http_client.request = new_request
    return client
oauth2client.client.OAuth2Credentials.authorize_gclient = authorize_gclient
# This method matches the atom.http_core.HttpClient.request method signature to the httplib2.Http.request method signature
def compatible_request(self, uri, method, body, headers):
    headers['Content-length'] = len(body)
    response = self._http_request(method, uri, headers, body)
    content = response.read()
    return response, content
atom.http_core.HttpClient.compatible_request = compatible_request
