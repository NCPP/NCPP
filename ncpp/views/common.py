from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render_to_response
from django.conf import settings
from django.template import RequestContext

from ncpp.models.climate_indexes import ClimateIndexJob

# URL for user login: use project setting or default to application specific value.
LOGIN_URL = getattr(settings, "LOGIN_URL", "/ncpp/login/")


@login_required(login_url=LOGIN_URL)
def job_detail(request, job_id):
    '''View to display detailed information about a single job.'''
    
    # retrieve job of specified type
    job = get_object_or_404(ClimateIndexJob, pk=job_id)
    
    # retrieve job-specific submission data
    job_data = job.getInputData()

    return render_to_response('ncpp/common/job_detail.html',
                              {'job':job, 'job_data':job_data },
                              context_instance=RequestContext(request))
