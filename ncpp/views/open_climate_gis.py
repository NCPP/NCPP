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
                    if cleaned_data.has_key('latmin') and cleaned_data['latmin'] is not None:
                        job_data['latmin'] = float( cleaned_data['latmin'] )
                    if cleaned_data.has_key('latmax') and cleaned_data['latmax'] is not None:
                        job_data['latmax'] = float( cleaned_data['latmax'] )
                    if cleaned_data.has_key('lonmin') and cleaned_data['lonmin'] is not None:
                        job_data['lonmin'] = float( cleaned_data['lonmin'] )
                    if cleaned_data.has_key('lonmax') and cleaned_data['lonmax'] is not None:
                        job_data['lonmax'] = float( cleaned_data['lonmax'] )
                    if cleaned_data.has_key('lat') and cleaned_data['lat'] is not None:
                        job_data['lat'] = float( cleaned_data['lat'] )
                    if cleaned_data.has_key('lon') and cleaned_data['lon'] is not None:
                        job_data['lon'] = float( cleaned_data['lon'] )
                    if cleaned_data.has_key('datetime_start') and cleaned_data['datetime_start'] is not None:
                        job_data['datetime_start'] = cleaned_data['datetime_start']
                    if cleaned_data.has_key('datetime_stop') and cleaned_data['datetime_stop'] is not None:
                        job_data['datetime_stop'] = cleaned_data['datetime_stop']
                    if cleaned_data.has_key('calc'):
                        job_data['calc'] = ocgisChoices(Config.CALCULATION)[cleaned_data['calc']]
                    if cleaned_data.has_key('par1') and cleaned_data['par1'] is not None:
                        job_data['par1'] = float( cleaned_data['par1'] )
                    if cleaned_data.has_key('par2') and cleaned_data['par2'] is not None:
                        job_data['par2'] = float( cleaned_data['par2'] )
                    if cleaned_data.has_key('calc_group'):
                        job_data['calc_group'] =[]
                        for group in cleaned_data['calc_group']:
                            job_data['calc_group'].append(ocgisChoices(Config.CALCULATION_GROUP)[group])                             
                    if cleaned_data.has_key('calc_raw'):
                        job_data['calc_raw'] = bool(cleaned_data['calc_raw'])   
                    if cleaned_data.has_key('spatial_operation'):
                        job_data['spatial_operation'] = ocgisChoices(Config.SPATIAL_OPERATION)[cleaned_data['spatial_operation']]
                    if cleaned_data.has_key('aggregate'):
                        job_data['aggregate'] = bool(cleaned_data['aggregate'])       
                    if cleaned_data.has_key('output_format'):
                        job_data['output_format'] = ocgisChoices(Config.OUTPUT_FORMAT)[cleaned_data['output_format']]   
                    if cleaned_data.has_key('prefix'):
                        job_data['prefix'] = cleaned_data['prefix']       
                            
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
                                               latmin=form_data['latmin'],
                                               latmax=form_data['latmax'],
                                               lonmin=form_data['lonmin'],
                                               lonmax=form_data['lonmax'],
                                               lat=form_data['lat'],
                                               lon=form_data['lon'],
                                               datetime_start=form_data['datetime_start'],
                                               datetime_stop=form_data['datetime_stop'],
                                               calc=form_data['calc'],
                                               par1=form_data['par1'],
                                               par2=form_data['par2'],
                                               calc_raw=form_data['calc_raw'],
                                               calc_group=form_data['calc_group'],
                                               spatial_operation=form_data['spatial_operation'],
                                               aggregate=bool(form_data['aggregate']),
                                               output_format=form_data['output_format'],
                                               prefix=form_data['prefix'] )
        
        # submit OCG job
        job.submit()
        
        # FIXME: pass OCG as additional argument to select jobs
        return HttpResponseRedirect(reverse('job_detail', args=[job.id, get_full_class_name(job)]))