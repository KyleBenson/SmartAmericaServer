from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
      url(r'^$', 'app.env.print_environment'),
      url(r'^hello_call$', 'django_twilio.views.say', {
          'text' : 'Hello, world!  This is Twilio.'
          }),
       url(r'^hello_sms$', 'django_twilio.views.sms', {
          'message' : 'Thank you for your message!\n-SmartAmerica SCALE Server'
          }),
    # url(r'^$', 'app.twilio.text'),
    # url(r'^text$', 'app.twilio.text'),
    # url(r'^app/', include('app.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

     url(r'^admin/', include(admin.site.urls)),
    
)
