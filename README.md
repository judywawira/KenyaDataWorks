captricity-cloud-io
===================

The Cloud IO example app allows users to:

* Authorize the Cloud IO app to manipulate their Captricity account
* Upload images from box.net to their Captricity account
* Export Captricity job results as Google spreadsheets

The Cloud IO app is built in the <a href="https://www.djangoproject.com/" target="_blank">Django web framework</a> and is a good example of using the Captricity Python client to interact with the Captricity API.


## Setup
This is a standalone django app that depends on some libraries. They are all defined in the root requirements.txt, so use pip to install them.

    pip install -r requirements.txt

Once the dependencies are installed, you need to define some of the API keys used to access the external APIs for Captricity, Google and box.net.
First copy local_settings.py.example:
    
    cp captricity_cloud_io/settings/local_settings.py.example captricity_cloud_io/settings/local_settings.py

Then specify each of the variables:
- API_TARGET refers to the target server for the captricity api. The default server is a sandbox server available for use by developers.
- CAPTRICITY_SCHEMA_URL refers to the url endpoint for the schema definition of Captricity resources.
- CAPTRICITY_CLIENTID, CAPTRICITY_SECRET_KEY refers to client information for this third party app. View the [API reference](https://shreddr.captricity.com) for more information.
- BOX_API_KEY refers to api keys to access the box.net API. See [box.net developer info](http://developers.box.net/w/page/12923958/Welcome%20to%20the%20Box%20Platform) for more information on how to obtain one.
- GOOG_CLIENTID, GOOG_SECRET_KEY refer to oauth2.0 client information for the google api. Visit [google api console](https://code.google.com/apis/console/b/0/#project:353663790589) to generate one.

Once the variables are set, use the install_demouser manage.py command to install a demo user (username alice, password 1234), runserver to start the server, and celeryd to start the asynchronous task manager

    ./manage.py install_demouser
    ./manage.py set_site_domain
    ./manage.py runserver
    ./manage.py celeryd -B

##Authentication
As documented in the <a href="https://shreddr.captricity.com/developer/#authentication">overview page</a>, authentication happens in a two step process. The third-party application must first request access to the user's Captricity account by redirecting the user to the request access page. If and when the user grants access, the user will be redirected to a specified url with an API token to access the user's data on Captricity.

In this app, we break out the two steps into two separate views. The <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/views.py#L88">login view</a> handles redirecting the user to the Captricity request access page with the necessary GET parameters. Once the user grants or denies access, the user is redirected to the <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/views.py#L54">callback view</a>.  
First the app verifies the response signature to ensure the response is from Captricity. Then:

* If the user granted access, the app will store the API token to later access the user's data on Captricity.</li> 
* If the user denied access, the app will alert the user that the Cloud IO app functionality will be limited.</li> 


##Listing Jobs
This example app uses the Captricity <a href="https://shreddr.captricity.com/static/backbone/schema.js">schema.js</a> javascript library to autogenerate <a href="http://backbonejs.org" target="_blank">backbone models and views</a> to access Captricity objects. See <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/templates/captricity_cloud_io/boxcap_list.html#L95">here</a> and <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/templates/captricity_cloud_io/dataset_export.html#L43">here</a> for examples on how it is used.

##Uploading image sets
Once a user selects a list of files to upload from the <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/templates/captricity_cloud_io/boxcap_list.html">box file browser</a>, the app triggers a <a href="https://github.com/Captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/tasks.py#L27">celery task for uploading those files to Captricity</a>. The app uses the update_instance_sets method of the Captricity python client to create an image set object for each set of images that correspond to one completed form (instance set) on Captricity, and then uses the update_iset_instance method to post images to the created image set.

##Serving sheet images
The app uses the read_sheet_image method of Captricity python client to <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/views.py#L39">download and serve the blank template page images</a> associated with the Captricity job.

##Downloading Job results
To download a job's results from Captricity, the app first uses the read_datasets method to get a list of datasets associated with a job.  The app then uses the read_dataset method of the Captricity python client to <a href="https://github.com/captricity/captricity-cloud-io/blob/master/captricity_cloud_io/captricity_cloud_io/tasks.py#L56">download the job results as a CSV file</a> before pushing it to Google.

## License
This is licensed under the MIT license. See LICENSE.txt.
