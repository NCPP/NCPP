from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from ncpp.utils import get_class
from ncpp.models.common import Job

# FIXME
from owslib.wps import WPSExecution

# URL for user login: use project setting or default to application specific value.
LOGIN_URL = getattr(settings, "LOGIN_URL", "/ncpp/login/")

@login_required(login_url=LOGIN_URL)
def job_detail(request, job_id, job_class):
    '''View to display detailed information about a single job.'''
    
    # retrieve job of specified type
    kls = get_class(job_class)
    job = get_object_or_404(kls, pk=job_id)
    
    # retrieve job-specific submission data
    job_data = job.getFormData()

    return render_to_response('ncpp/common/job_detail.html',
                              {'job':job, 'job_data':job_data },
                              context_instance=RequestContext(request))
 
@login_required(login_url=LOGIN_URL)   
def job_request(request, job_id, job_class):
    '''View to display job request XML.'''
    
    # retrieve job of specified type
    kls = get_class(job_class)
    job = get_object_or_404(kls, pk=job_id)
    return HttpResponse(job.request, mimetype="text/plain") # FIXME: change to "text/xml" ?

@login_required(login_url=LOGIN_URL)
def job_response(request, job_id, job_class):
    '''View to display job response XML.'''
    
    # retrieve job of specified type
    kls = get_class(job_class)
    job = get_object_or_404(kls, pk=job_id)
    return HttpResponse(job.response, mimetype="text/plain")  # FIXME: change to "text/xml" ?

@login_required(login_url=LOGIN_URL)
def jobs_list(request, username, job_class):
    '''View to list the user's jobs of a specific type.'''
    
    # FIXME: check that username==request.user.username or request.username='admin'
    user = get_object_or_404(User, username=username)
    
    # Note: retrieve all instances of Job *subclass*, not 'Job' class
    kls = get_class(job_class)
    jobs = kls.objects.filter(user=user).order_by('-submissionDateTime')
    
    return render_to_response('ncpp/common/jobs_list.html',
                              {'jobs':jobs },
                              context_instance=RequestContext(request))
    
@login_required(login_url=LOGIN_URL)
def job_check(request, job_id, job_class):
    '''View to check the status of a job.'''
    
    # retrieve job of specified type
    job = get_object_or_404(get_class(job_class), pk=job_id)
        
    # update the job in the database
    job.update()
    
    # redirect to job listing
    return HttpResponseRedirect(reverse('jobs_list', args=[request.user.username, job_class]))
        
