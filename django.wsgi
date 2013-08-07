import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'do-index.settings'
paths= ('/var/domains/webs/walterp/do-index/django-crowdsourcing/do-index', 
	'/var/domains/webs/walterp/do-index/django-crowdsourcing/',
	'/var/domains/webs/walterp/do-index/django-crowdsourcing/crowdsourcing',
	)
for path in paths:
    if path not in sys.path:
	    sys.path.append(path)
import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
