from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    (r'^home/$', 'captricity_cloud_io.views.home'),

    (r'^boxcap/list/$', 'captricity_cloud_io.views.boxcap_list'),
    (r'^boxcap/upload/$', 'captricity_cloud_io.views.upload'),
    (r'^cap-jobs/$', 'captricity_cloud_io.views.cap_jobs'),
    (r'^cap-sheet-image/(?P<sheet_id>[\d]+)/$', 'captricity_cloud_io.views.cap_sheet_image'),

    (r'^gdata-login/$', 'captricity_cloud_io.views.gdata_login'),
    (r'^gdata-oauth-callback/$', 'captricity_cloud_io.views.oauth2_callback'),
    (r'^dataset-export/$', 'captricity_cloud_io.views.dataset_export'),
    (r'^queue-for-gdata-upload/$', 'captricity_cloud_io.views.queue_for_gdata_upload'),
    (r'^test-gdata-token/$', 'captricity_cloud_io.views.test_gdata_token'),
    (r'^gdata-resources/$', 'captricity_cloud_io.views.gdata_list'),
    (r'^register-sync/$', 'captricity_cloud_io.views.register_gdata_sync'),
    (r'^register-create-sync/$', 'captricity_cloud_io.views.register_create_sync'),

    (r'^accounts/profile/$', 'captricity_cloud_io.views.update_tokens'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login',
                                {'template_name': 'captricity_cloud_io/login.html'}),
)
