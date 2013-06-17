from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.formtools.wizard.views import SessionWizardView

from django.contrib.auth.models import User

from ncpp.models.common import JOB_STATUS
from ncpp.models.open_climate_gis import OpenClimateGisJob, ocgisChoices, Config
from ncpp.utils import get_full_class_name


class OpenClimateGisWizard(SessionWizardView):
    '''Set of views to submit an Open Climate GIS request.'''
    
    template_name = "ncpp/open_climate_gis/wizard_form.html"

    # method called at every step after the form data has been validated, before rendering of the view
    # overridden here to aggregate user choices from all steps before the last one
    def get_context_data(self, form, **kwargs):
        
        context = super(OpenClimateGisWizard, self).get_context_data(form=form, **kwargs)              
        
        # before very last view: create summary of user choices
        if self.steps.current == self.steps.last:
            job_data = {}
            # retrieve form data for all previous views
            for step in self.steps.all:
                if step != self.steps.current:                    
                    cleaned_data = self.get_cleaned_data_for_step(step)                  
                    if cleaned_data.has_key("dataset"):
                        job_data['dataset'] = ocgisChoices(Config.DATASET)[cleaned_data['dataset']]
                    if cleaned_data.has_key('variable'):
                        job_data['variable'] = ocgisChoices(Config.VARIABLE)[cleaned_data['variable']]    
                    if cleaned_data.has_key('geometry'):
                        job_data['geometry'] = ocgisChoices(Config.GEOMETRY)[cleaned_data['geometry']]    
                    if cleaned_data.has_key('geometry_id'):
                        job_data['geometry_id'] =[]
                        for id in cleaned_data['geometry_id']:
                            job_data['geometry_id'].append(ocgisChoices(Config.GEOMETRY_ID)[id])  
                    if cleaned_data.has_key('aggregate'):
                        job_data['aggregate'] = bool(cleaned_data['aggregate'])       
            context.update({'job_data': job_data})
        
        return context
    
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
        job = OpenClimateGisJob.objects.create(status=JOB_STATUS.UNKNOWN,
                                               user=user,
                                               dataset=form_data['dataset'],
                                               variable=form_data['variable'],
                                               geometry=form_data['geometry'],
                                               # must transform list of integers into string
                                               geometry_id=",".join(form_data['geometry_id']),
                                               aggregate=form_data['aggregate'])
        
        # submit OCG job
        job.submit()
        
        # FIXME: pass OCG as additional argument to select jobs
        return HttpResponseRedirect(reverse('job_detail', args=[job.id, get_full_class_name(job)]))