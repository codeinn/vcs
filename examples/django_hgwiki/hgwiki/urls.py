from django.conf.urls.defaults import *

urlpatterns = patterns('hgwiki.views',
    url(r'^$', 'home', name='hgwiki_home'),
)

