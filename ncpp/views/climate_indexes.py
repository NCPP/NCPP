from datetime import datetime
from django.contrib.auth.decorators import login_required
from ncpp.models.climate_indexes import (REGION_CHOICES, INDEX_CHOICES, AGGREGATION_CHOICES, START_DATETIME_CHOICES,
                                         DATASET_CHOICES, OUTPUT_FORMAT_CHOICES, SUPPORTING_INFO_CHOICES, JOB_STATUS)
                            

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.views import SessionWizardView
from django.contrib.auth.models import User


from owslib.wps import WPSExecution

from ncpp.models import ClimateIndexJob, SupportingInfo, Job

from ncpp.views.common import LOGIN_URL
    
class ClimateIndexesWizard(SessionWizardView):
    '''Set of views to submit a climate indexes request.'''
    
    template_name = "ncpp/climate_indexes/wizard_form.html"
        
    # method called after all forms have been processed and validated
    def done(self, form_list, **kwargs):
        
        # merge data from all forms
        form_data = {}
        for form in form_list:
            form_data.update( form.cleaned_data )
        print form_data
            
        # FIXME
        user = User.objects.get(username='admin')
            
        # persist job specification to database
        job = ClimateIndexJob.objects.create(status=JOB_STATUS.UNKNOWN,
                                             user=user,
                                             region=form_data['region'],
                                             index=form_data['index'],
                                             #aggregation=form_data['aggregation'],
                                             dataset=form_data['dataset'],
                                             outputFormat=form_data['outputFormat'],
                                             startDateTime=datetime.strptime(form_data['startDateTime'],'%Y-%m-%d'))
        for info in form_data['supportingInfo']:
            supportingInfo = SupportingInfo(job=job, info=info)
            supportingInfo.save()       
            
        # submit job
        job.submit()                     
    
        # redirect to job submission confirmation page (GET-POST-REDIRECT)
        #return HttpResponseRedirect(reverse('job_detail', args=[job.id]))
        return HttpResponseRedirect(reverse('jobs_list', args=[user.username]))
    
    # method called at every step after the form data has been validated, before rendering of the view
    # overridden here to aggregate user choices from all steps before the last one
    def get_context_data(self, form, **kwargs):
        
        context = super(ClimateIndexesWizard, self).get_context_data(form=form, **kwargs)              
        
        if self.steps.current == self.steps.last:
            # create summary of user choices
            job_data = {}
            for step in self.steps.all:
                if step != self.steps.current:                    
                    cleaned_data = self.get_cleaned_data_for_step(step)                  
                    if cleaned_data.has_key('region'):
                        job_data['region'] = REGION_CHOICES[cleaned_data['region']]
                    if cleaned_data.has_key('index'):
                        job_data['index'] = INDEX_CHOICES[cleaned_data['index']]
                    #if cleaned_data.has_key('aggregation'):
                    #    job_data['aggregation'] = AGGREGATION_CHOICES[cleaned_data['aggregation']]
                    if cleaned_data.has_key('startDateTime'):
                        job_data['startDateTime'] = cleaned_data['startDateTime']
                    if cleaned_data.has_key('dataset'):
                        job_data['dataset'] = DATASET_CHOICES[cleaned_data['dataset']]
                    if cleaned_data.has_key('outputFormat'):
                        job_data['outputFormat'] = OUTPUT_FORMAT_CHOICES[cleaned_data['outputFormat']]
                    if cleaned_data.has_key('supportingInfo'):
                        job_data['supportingInfo'] = []
                        for info in cleaned_data['supportingInfo']:
                            job_data['supportingInfo'].append( SUPPORTING_INFO_CHOICES[info] )                       
            context.update({'job_data': job_data})
        
        return context

@login_required(login_url=LOGIN_URL)
def jobs_list(request, username):
    '''View to list a user's jobs.'''
    
    # FIXME: check that username==request.user.username or request.username='admin'
    user = get_object_or_404(User, username=username)
    
    jobs = Job.objects.filter(user=user).order_by('-submissionDateTime')
    
    return render_to_response('ncpp/common/jobs_list.html',
                              {'jobs':jobs },
                              context_instance=RequestContext(request))
    
def job_request(request, job_id):
    '''View to display job request XML.'''
    
    job = get_object_or_404(ClimateIndexJob, pk=job_id)
    return HttpResponse(job.request, mimetype="text/xml")

def job_response(request, job_id):
    '''View to display job response XML.'''
    
    job = get_object_or_404(ClimateIndexJob, pk=job_id)
    return HttpResponse(job.response, mimetype="text/xml")

@login_required(login_url=LOGIN_URL)
def job_check(request, job_id):
    '''View to check the status of a job.'''
    
    job = get_object_or_404(ClimateIndexJob, pk=job_id)
    
    # create a new execution from the job status URL
    execution = WPSExecution()
    
    # check the remote job status
    execution.checkStatus(url=job.statusLocation, sleepSecs=0)
    
    # update the job in the database
    job.update(execution)
    
    # redirect to job listing
    # FIXME
    return HttpResponseRedirect(reverse('jobs_list', args=['admin']))
    #return HttpResponseRedirect(reverse('jobs_list', args=[request.user.username]))
        
