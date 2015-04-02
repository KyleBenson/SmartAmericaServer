from django.conf.urls import patterns, include, url
from django.shortcuts import redirect
from django.contrib import admin
admin.autodiscover()
import os

EMERGENCY_CONTACT_NUMBER = os.environ.get('EMERGENCY_CONTACT_NUMBER')

urlpatterns = patterns('',
    url(r'^$', lambda x: redirect('http://smartamerica.org/teams/scale-safe-community-alert-network-a-k-a-public-safety-for-smart-communities/')),
    url(r'^fall_app$', lambda x: redirect('/static/SCALEFallDetection.apk')),
    #url(r'^env$', 'scale.views.print_environment'),
    url(r'^demo$', 'scale.views.run_demo'),
    url(r'^dashboard_demo$', 'scale.views.run_dashboard_demo'),

    # phone / alerting stuff
    url(r'^phone$', 'phone.views.phone_call_handler'),
    url(r'^sms$', 'phone.views.sms_handler'),
    url(r'^phone/main_menu_options$', 'phone.views.main_menu_options_handler'),
    url(r'^phone/contact_preference_options$', 'phone.views.contact_preference_options_handler'),
    url(r'^phone/alert_menu_options$', 'phone.views.phone_alert_menu_options_handler'),
    url(r'^phone/alert$', 'phone.views.phone_alert_handler'),

    url(r'^test_rest$', 'scale.test.test_rest'),
    url(r'^sigfox$', 'scale.external_sources.sigfox'),
    url(r'^senseware$', 'scale.external_sources.senseware'),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
