from django.conf.urls.defaults import *

urlpatterns = patterns('hgwiki.views',
    url(r'^$', 'home', name='hgwiki_home'),
    url(r'^list/$', 'wiki_list', name='hgwiki_wiki_list'),
    url(r'^(?P<slug>[-\w]+)/$', 'wiki_detail', name='hgwiki_wiki_detail'),
)

