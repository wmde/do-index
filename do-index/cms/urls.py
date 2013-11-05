from __future__ import absolute_import

from django.conf.urls.defaults import patterns, url

from .views import home, login, finalize, preliminary, getPreliminary, overview, status, update_ie, create_new_user

urlpatterns = patterns(
    "",
    url(r'^$', home),
    url(r'^finalize/$', finalize),
    url(r'^preliminary/$', preliminary),
    url(r'^getPreliminary/$', getPreliminary),
    url(r'^login/$', login),
    url(r'^overview/$', overview),
    url(r'^status/$', status),
    url(r'^update-ie/$', update_ie),
    url(r'^create-user/$', create_new_user),
    )
