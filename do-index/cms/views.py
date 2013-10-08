from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse

from crowdsourcing.models import Survey, Submission
from crowdsourcing import forms
from django.contrib.auth import authenticate
from django.contrib.auth import login as login_user
from django.contrib.auth import logout 
from .models import Preliminary, User
import json, urlparse, re

class LoginForm(forms.Form):
        email = forms.CharField(label=(u'Email'), max_length=30)
	password = forms.CharField(label=(u'Pass'), max_length=30)

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
    qs = dict( ( k, v if len(v)>1 else v[0] ) for k, v in urlparse.parse_qs(request.GET['queryString']).iteritems() )
    data = json.dumps(qs)
    slug = request.GET['slug']
    try:
	old_data = Preliminary.objects.get(user = request.user, slug = slug)
	old_data.delete()
    except:
	# First save
	pass
    preliminary_data = Preliminary(user = request.user, save_string = data, slug = slug)
    preliminary_data.save()
    return HttpResponse("Got json data")

def getPreliminary(request):
    try:
	string = Preliminary.objects.get(user = request.user, slug = request.GET['slug']).save_string
    except Preliminary.DoesNotExist:
	string = '{}'
    return HttpResponse(string, content_type="application/json")

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
	    return HttpResponse(json.dumps(final), content_type="application/json")

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
    maintenance= ["staedtetag_test", "probewien", "testing", "teststadt", "test", "test2", "test3", "test4", "testjohl", "walter", "root", "Nikita", "Eva", "Daniela", "Stephan"]
    last_logins = filter(lambda x: x[1] not in maintenance, sorted([(u.last_login.isoformat(), u.username) for u in User.objects.all()], key=lambda x:x[0], reverse=True))
    completed_surveys = [(s.user.username, s.survey.title)  for s in Submission.objects.all()]
    dictionary  = {'logins': last_logins, 'surveys': completed_surveys}
    return render_to_response('overview.html', dictionary)

def overview_public(request):
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def update_ie(request):
    return render_to_response('ie.html')



