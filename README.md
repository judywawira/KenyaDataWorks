captricity-cloud-io
===================

Example app for the Captricity API, that integrates Captricity with external apps like Google and Box.net

### Setup
This is a standalone django app that depends on some libraries. They are all defined in the root requirements.txt, so use pip to install them.

    pip install -r requirements.txt

Once the dependencies are installed, you need to define some of the API keys used to access the external APIs for captricity, google and box.net.
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
    ./manage.py runserver
    ./manage.py celeryd -B

