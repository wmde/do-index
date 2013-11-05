from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.db import IntegrityError

from crowdsourcing.models import Survey, Submission
from crowdsourcing import forms
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_user
from django.contrib.auth import logout 
from .models import Preliminary, User
from collections import defaultdict
import json, urlparse, re

maintenance= ["staedtetag_test", "probewien", "Austria", "Graz-OpenData", "testing", "teststadt", "test", "test2", "test3", "test4", "test5", "test8", "test9", "testjohl", "walter", "root", "Nikita", "Eva", "Daniela", "Stephan"]

class LoginForm(forms.Form):
        email = forms.CharField(label=(u'Email'), max_length=30)
	password = forms.CharField(label=(u'Pass'), max_length=30)

def to_dict(d):
    """
    Transform defaultdict to nested dict
    """
    if isinstance(d, defaultdict):
        return dict((k, to_dict(v)) for k, v in d.items())
    return d

def no_ie(redirect):
    """
    Protects a view from the terror that is Microsoft Internet Explorer
    by redirecting the request to 'redirect'.
    
    Usage:
    
    @no_ie('/ie-compatible-page/')
    def my view(request):
       ...
    
    """
    def view_wrapper(view):
        def dec(request, *args, **kwargs):
            if request.META['HTTP_USER_AGENT'].find('MSIE') > 0:
                return HttpResponseRedirect(redirect)
            return view(request, *args, **kwargs)
        return dec
    return view_wrapper

@no_ie('/update-ie/')
def home(request):
    surveys = Survey.objects.all()
    submitted = []
    if request.user.is_authenticated():
	submitted = Submission.objects.filter(user = request.user)
	if 'city' in [x['name'] for x in request.user.groups.values()]:
	    surveys = surveys.exclude(slug='oe')
    s = []
    for survey in surveys:
	if survey in filter(lambda x: x.id in map(lambda x: x.survey_id, submitted), surveys):
	    survey.completed = True
	else:
	    survey.completed = False
	s.append(survey)
    surveys = s
    return render_to_response(
        "home.html",
        {
	    'surveys':surveys,
	},
        RequestContext(request))

def preliminary(request):
    if request.method == 'POST' and request.POST:
	queryString = request.POST.get('queryString')
	slug = request.POST.get('slug')
    else:
	queryString = request.GET['queryString']
	slug = request.GET['slug']
    qs = dict( ( k, v if len(v)>1 else v[0] ) for k, v in urlparse.parse_qs(queryString.encode('utf-8')).iteritems() )
    data = json.dumps(qs)
    try:
	old_data = Preliminary.objects.filter(user = request.user, slug = slug)
	for o in old_data:
	    o.delete()
    except:
	# First save
	pass
    preliminary_data = Preliminary(user = request.user, save_string = data, slug = slug)
    preliminary_data.save(force_insert=True)
    return HttpResponse("Got json data", content_type="text/plain")

def getPreliminary(request):
    try:
	string = Preliminary.objects.get(user = request.user, slug = request.GET['slug']).save_string
    except Preliminary.DoesNotExist:
	string = '{}'
    except Preliminary.MultipleObjectsReturned:
	string = '{}'
    return HttpResponse(string, content_type="application/json; charset=utf-8")

def completed_surveys(user):
    all_submissions = sorted([submission.survey.title for submission in filter(lambda x: x.user_id == user, Submission.objects.all())])
    all_surveys = sorted([survey.title for survey in Survey.objects.all()])
    return (all_submissions == all_surveys)

def finalize(request):
    if request.user.is_authenticated():
	user = request.user
	if (completed_surveys(user.id)):
	    request.user.is_active = False
	    request.user.is_staff = False
	    request.user.set_unusable_password()
	    request.user.save()	
	    logout(request)
	    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
	else:
	    final = {}
	    final['final'] = False
	    return HttpResponse(json.dumps(final), content_type="application/json; charset=utf-8")

def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    if request.method == 'POST':
	form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(username=email, password=password)
            if (user is not None) and (user.has_usable_password()):
                login_user(request, user)
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            else:
                return render_to_response('home.html', context_instance=RequestContext(request))
        else:
            return render_to_response('home.html', context_instance=RequestContext(request))
    else:
        return render_to_response('home.html', context_instance=RequestContext(request))

def overview(request):
    last_logins = filter(lambda x: x[1] not in maintenance, sorted([(u.last_login.isoformat(), u.username) for u in User.objects.all()], key=lambda x:x[0], reverse=True))
    completed_surveys = [(s.user.username, s.survey.title)  for s in Submission.objects.all()]
    dictionary  = {'logins': last_logins, 'surveys': completed_surveys}
    return render_to_response('overview.html', dictionary)

def status(request):
    completed_surveys = [(s.user.username, s.survey.slug) for s in filter(lambda x: x.user.username not in maintenance, Submission.objects.all())]
    incomplete_surveys = [(s.user.username, s.slug) for s in filter(lambda x: x.user.username not in maintenance, Preliminary.objects.all())]
    users = sorted([u.username for u in filter(lambda x: x.username not in maintenance, User.objects.all())])
    areas = sorted([u.username for u in filter(lambda x: x.username not in maintenance and str(x.groups.values_list()[0][1]) != 'city', User.objects.all())])
    Tree = lambda: defaultdict(Tree)
    stats = Tree() # autovivification
    surveys = [s.slug for s in Survey.objects.all()]
    for u in users:
	for s in surveys:
	    stats[u][s] = "danger" # default: not completed, not started
	    if (u, s) in completed_surveys:
		stats[u][s] = "success"
	    if (u, s) in incomplete_surveys:
		stats[u][s] = "warning"
    stats = to_dict(stats)
    cities = filter(lambda x: x not in areas, users)     
    cities_at = sorted(["Wien", "Salzburg", "Linz", "Innsbruck", "Graz"])
    cities_de = sorted(filter(lambda x: x not in cities_at, cities))
    return render_to_response('status.html', 
    {
	'stats': stats,
	'areas': areas,
	'cities_de': cities_de,
	'cities_at': cities_at,
    }, context_instance=RequestContext(request))					

def update_ie(request):
    return render_to_response('ie.html')

def create_new_user(request):
    if request.POST and request.method == 'POST':
	data = json.loads(request.POST.keys()[0])
 	try:
 	  username = data['username']
 	  email = data.get('email')
 	  password = data['password']
	  if email == None:
	    email = ''
	  user = User.objects.create_user(username=username, email=email, password=password)
	  user.is_active = True
	  user.is_staff = True
	  user.save() 
	  return HttpResponse("User created.")
 	except KeyError:
 	  HttpResponseServerError("Malformed data!")
	#except IntegrityError:
	#  HttpResponseServerError("Unable to create user!")
    return HttpResponse("Got json data")

  
