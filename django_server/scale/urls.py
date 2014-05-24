from django.conf.urls import patterns, include, url
from django.shortcuts import redirect
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', lambda x: redirect('http://smartamerica.org/teams/scale-safe-community-alert-network-a-k-a-public-safety-for-smart-communities/')),
    #url(r'^env$', 'scale.views.print_environment'),
    url(r'^demo$', 'scale.views.run_demo'),
    url(r'^phone_call$', 'django_twilio.views.say', {
        'text' : 'Hello, world!  This is Twilio.'
        }),
    url(r'^sms$', 'phone.views.sms_handler'),
    url(r'^test_rest$', 'scale.test.test_rest'),
    url(r'^sigfox$', 'scale.external_sources.sigfox'),
    # url(r'^$', 'app.twilio.text'),
    # url(r'^text$', 'app.twilio.text'),
    # url(r'^app/', include('app.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

     url(r'^admin/', include(admin.site.urls)),
)
