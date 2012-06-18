from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    (r'^$', 'captricity_cloud_io.views.home'),

    (r'^captricity_api/$', 'captricity_cloud_io.views.captricity_api'),
    (r'^cap-sheet-image/(?P<sheet_id>[\d]+)/$', 'captricity_cloud_io.views.cap_sheet_image'),
    (r'^cap-callback/$', 'captricity_cloud_io.views.captricity_callback'),
    (r'^cap-login/$', 'captricity_cloud_io.views.captricity_login'),

    (r'^boxcap/list/$', 'captricity_cloud_io.views.boxcap_list'),
    (r'^boxcap/upload/$', 'captricity_cloud_io.views.upload'),

    (r'^gdata-login/$', 'captricity_cloud_io.views.gdata_login'),
    (r'^gdata-oauth-callback/$', 'captricity_cloud_io.views.oauth2_callback'),
    (r'^dataset-export/$', 'captricity_cloud_io.views.dataset_export'),
    (r'^queue-for-gdata-upload/$', 'captricity_cloud_io.views.queue_for_gdata_upload'),
    (r'^test-gdata-token/$', 'captricity_cloud_io.views.test_gdata_token'),
    (r'^gdata-resources/$', 'captricity_cloud_io.views.gdata_list'),

    (r'^accounts/login/$', 'django.contrib.auth.views.login',
                                {'template_name': 'captricity_cloud_io/login.html'}),
)
