from __future__ import absolute_import

from django.conf.urls.defaults import patterns, url

from .views import home, login, finalize, preliminary, getPreliminary, overview

urlpatterns = patterns(
    "",
    url(r'^$', home),
    url(r'^finalize/$', finalize),
    url(r'^preliminary/$', preliminary),
    url(r'^getPreliminary/$', getPreliminary),
    url(r'^login/$', login),
    url(r'^overview/$', overview),
    )
