from django.conf import settings
from celery.task import task
import cStringIO as StringIO
import re
import csv
import os
import urlparse
import urllib2
import httplib
import httplib2
import tempfile
import simplejson
import math

from django.contrib.auth.models import User

from oauth2client.django_orm import Storage
import gdata.docs
import gdata.docs.client
import gdata.docs.data
from captricity_cloud_io.models import CredentialsModel, FlowModel, UserProfile

def upload_to_captricity_by_url(source_urls, job_id, user_profile_id):
    _upload_to_captricity_by_url.delay(source_urls, job_id, user_profile_id)

@task(ignore_result=True)
def _upload_to_captricity_by_url(source_urls, job_id, user_profile_id):
    """Pull resource from url and upload to captricity"""
    client = UserProfile.objects.get(id=user_profile_id).get_captricity_client()
    # First find out how many pages there are in the document, so that we know how to group the list of images into image sets
    page_count = client.read_job(job_id)['document']['sheet_count']
    # Assume the images are in order, neatly sorted into image sets
    for i in range(int(math.ceil(len(source_urls) / float(page_count)))):
        # For each group of images in a image set, create the instance set on the captricity server
        iset = client.update_instance_sets(job_id, {'name':'iset '+str(i)})
        # Then upload in order, assuming they are in page number order
        for page_number,file_data in enumerate(source_urls[i:i+page_count]):
            # Since we can't upload a url, and since the captricity python client is not compatible with "file-like" objects, so first retrieve the file from the url on to disk, then pass the local file to captricity python client to upload
            os_handle, path = tempfile.mkstemp()
            os.close(os_handle)
            f = open(path, "w+")
            f.write(urllib2.urlopen(file_data['url']).read())
            f.close()
            client.update_iset_instance(iset['id'], page_number, {'image':open(path), 'image_name':os.path.splitext(os.path.basename(path))[0]})
            os.remove(path)

def upload_to_google(job_id, user_id):
    _upload_to_google.delay(job_id, user_id)

@task(ignore_result=True)
def _upload_to_google(job_id, user_id):
    """Pull csv output from Captricity and pass onto google spreadsheets"""
    user = User.objects.get(id=user_id)

    # Get csv
    # We must first get the job, then get all datasets associated with the job. This is so that we get the metadata for datasets so we know which one to pull from captricity. We always pick the first one in the list. Once selected and we know the dataset id, retrieve the csv file
    client = user.get_profile().get_captricity_client()
    job = client.read_job(job_id)
    datasets = client.read_datasets(job_id)
    dataset_id = datasets[0]['id']
    csv_data = client.read_dataset(dataset_id, accept="text/csv")

    gclient = gdata.docs.client.DocsClient()
    gclient = _authorize_client(user, gclient)

    # write csv to file and upload to google spreadsheets
    os_handle, path = tempfile.mkstemp(suffix=".csv")
    os.close(os_handle)
    f = open(path, "w+")
    csv_fake_file = StringIO.StringIO(csv_data)
    csv_reader = csv.reader(csv_fake_file)
    field_names = csv_reader.next()
    csv_dict_reader = csv.DictReader(csv_fake_file, fieldnames=field_names)
    csv_dict_writer = csv.DictWriter(f, fieldnames=field_names)
    headers = dict( (n,n) for n in field_names )
    csv_dict_writer.writerow(headers)
    for row in csv_dict_reader:
        csv_dict_writer.writerow(row)
    f.close()

    csv_gfile = gdata.docs.data.Resource(type='spreadsheet', title='Sample Captricity CSV Results')
    media = gdata.data.MediaSource()
    media.SetFileHandle(path, 'text/csv')
    gfile = gclient.CreateResource(csv_gfile, media=media)

def _authorize_client(user, gclient):
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        raise Exception("Invalid credentials")
    gclient = credential.authorize_gclient(gclient)
    return gclient

