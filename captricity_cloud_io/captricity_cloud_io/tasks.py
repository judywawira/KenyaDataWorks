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
import gdata.spreadsheets.client
import gdata.spreadsheets.data
from captricity_cloud_io.models import CredentialsModel, FlowModel, SyncedDocument, UserProfile

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

def upload_to_google(job_id, user_id, sync_task):
    _upload_to_google.delay(job_id, user_id, sync_task)

@task(ignore_result=True)
def _upload_to_google(job_id, user_id, sync_task):
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
        if sync_task:
            row['name'] = str(job_id) + ":" + row['name']
        csv_dict_writer.writerow(row)
    f.close()

    csv_gfile = gdata.docs.data.Resource(type='spreadsheet', title='Sample Captricity CSV Results')
    media = gdata.data.MediaSource()
    media.SetFileHandle(path, 'text/csv')
    gfile = gclient.CreateResource(csv_gfile, media=media)

    if sync_task:
        SyncedDocument.objects.get_or_create(user=user, document=job['document']['name'], spreadsheet=gfile.GetId().split("%3A")[1])

@task(ignore_result=True)
def periodic_sync_task():
    for synced_doc in SyncedDocument.objects.all():
        sync_job_document(synced_doc.document, synced_doc.user.id, synced_doc.spreadsheet)

def sync_job_document(document_name, user_id, spreadsheet_key):
    _sync_job_document.delay(document_name, user_id, spreadsheet_key)

@task(ignore_result=True)
def _sync_job_document(document_name, user_id, spreadsheet_key):
    """Sync up captricity datasets with google spreadsheets"""
    document_name = re.sub(r'\ revision\ [\d]+$', '', document_name)
    user = User.objects.get(id=user_id)
    client = user.get_profile().get_captricity_client()
    jobs = client.read_jobs()
    candidates = [str(job['id']) for job in jobs if re.sub(r'\ revision\ [\d]+$', '', job['document']['name']) == document_name and job['status'] == 'completed']
    synced_jobs = set()

    gclient = gdata.spreadsheets.client.SpreadsheetsClient()
    gclient = _authorize_client(user, gclient)

    worksheet_key = gclient.GetWorksheets(spreadsheet_key).entry[0].GetWorksheetId()
    for row in gclient.GetListFeed(spreadsheet_key, worksheet_key).entry:
        synced_job_id = row.title.text.split(':')[0]
        synced_jobs.add(synced_job_id)

    for job_id in candidates:
        if job_id in synced_jobs:
            continue
        # get csv in a similar manner as upload to google task
        datasets = client.read_datasets(job_id)
        dataset_id = datasets[0]['id']
        csv_data = client.read_dataset(dataset_id, accept="text/csv")
        csv_fake_file = StringIO.StringIO(csv_data)
        csv_reader = csv.reader(csv_fake_file)
        field_names = csv_reader.next()
        csv_dict_reader = csv.DictReader(csv_fake_file, fieldnames=field_names)

        for row in csv_dict_reader:
            row['name'] = job_id + ":" + row['name']
            old_keys = row.keys()
            for key in old_keys:
                new_key = re.sub(r'[\:\s]', '', key)
                row[new_key] = row[key]
                if key != new_key:
                    del row[key]
            new_row = gdata.spreadsheets.data.ListEntry()
            new_row.from_dict(row)
            gclient.AddListEntry(new_row, spreadsheet_key, worksheet_key)

def _authorize_client(user, gclient):
    storage = Storage(CredentialsModel, 'id', user, 'credential')
    credential = storage.get()
    if credential is None or credential.invalid == True:
        raise Exception("Invalid credentials")
    gclient = credential.authorize_gclient(gclient)
    return gclient

