from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponse
from django.contrib.auth.models import User

from ncpp.models.common import JOB_STATUS
from ncpp.models.open_climate_gis import OpenClimateGisJob
from ncpp.config.open_climate_gis import ocgisChoices, Config, ocgisConfig, ocgisGeometries
from ncpp.config import ocgisDatasets
from ncpp.utils import get_full_class_name, str2bool, hasText
from ncpp.utils import get_month_string
from django.utils import simplejson  

from datetime import datetime
import json

class OpenClimateGisWizard(SessionWizardView):
    '''Set of views to submit an Open Climate GIS request.'''
    
    template_name = "ncpp/open_climate_gis/wizard_form.html"

    # method called at every step after the form data has been validated, before rendering of the view
    # overridden here to aggregate user choices from all steps before the last one
    def get_context_data(self, form, **kwargs):
        
        context = super(OpenClimateGisWizard, self).get_context_data(form=form, **kwargs)
          
        # before rendering of first form: send data and geometry choices 
        if self.steps.current == self.steps.first:
            context.update({'datasets':  json.dumps(ocgisDatasets.datasets) })
            context.update({'geometries':  json.dumps(ocgisGeometries.geometries) })
                 
        # before very last view: create summary of user choices
        elif self.steps.current == self.steps.last:
            job_data = {}
            # retrieve form data for all previous views
            for step in self.steps.all:
                if step != self.steps.current:                    
                    cleaned_data = self.get_cleaned_data_for_step(step)   
                    if cleaned_data.has_key("dataset_category"):
                        job_data['dataset_category'] = cleaned_data['dataset_category'] 
                    if cleaned_data.has_key("dataset"):
                        job_data['dataset'] = cleaned_data['dataset'] 
                    if cleaned_data.has_key('variable'):
                        job_data['variable'] = cleaned_data['variable']  
                    if cleaned_data.has_key('geometry') and hasText(cleaned_data['geometry']):
                        job_data['geometry'] = cleaned_data['geometry']
                    if cleaned_data.has_key('geometry_id') and len( cleaned_data['geometry_id'] )>0:
                        job_data['geometry_id'] = cleaned_data['geometry_id']
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
                    if cleaned_data.has_key('timeregion_month') and cleaned_data['timeregion_month'] is not None:
                        job_data['timeregion_month'] = get_month_string( cleaned_data['timeregion_month'] )
                    if cleaned_data.has_key('timeregion_year') and cleaned_data['timeregion_year'] is not None:
                        job_data['timeregion_year'] = cleaned_data['timeregion_year']
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
                    if cleaned_data.has_key('with_auxiliary_files'):
                        job_data['with_auxiliary_files'] = bool(cleaned_data['with_auxiliary_files'])                       
                            
            context.update({'job_data': job_data})
        
        return context
    
    # method called after all forms have been processed and validated
    def done(self, form_list, **kwargs):
        
        # merge data from all forms
        form_data = {}
        for form in form_list:
            form_data.update( form.cleaned_data )
            
        # retrieve user from request context
        user = self.request.user
            
        # persist job specification to database
        job = OpenClimateGisJob.objects.create(status=JOB_STATUS.UNKNOWN,
                                               user=user,
                                               dataset_category=form_data['dataset_category'],
                                               dataset=form_data['dataset'],
                                               variable=form_data['variable'],
                                               geometry=form_data['geometry'],
                                               # must transform list of integers into string
                                               geometry_id = ",".join(form_data['geometry_id']) if len(form_data['geometry_id'])>0 else None,
                                               latmin=form_data['latmin'],
                                               latmax=form_data['latmax'],
                                               lonmin=form_data['lonmin'],
                                               lonmax=form_data['lonmax'],
                                               lat=form_data['lat'],
                                               lon=form_data['lon'],
                                               datetime_start=form_data['datetime_start'],
                                               datetime_stop=form_data['datetime_stop'],
                                               timeregion_month=",".join(form_data['timeregion_month']),
                                               timeregion_year=form_data['timeregion_year'],
                                               calc=form_data['calc'],
                                               par1=form_data['par1'],
                                               par2=form_data['par2'],
                                               calc_raw=form_data['calc_raw'],
                                               calc_group=",".join(form_data['calc_group']),
                                               spatial_operation=form_data['spatial_operation'],
                                               aggregate=bool(form_data['aggregate']),
                                               output_format=form_data['output_format'],
                                               prefix=form_data['prefix'],
                                               with_auxiliary_files=form_data['with_auxiliary_files'] )
        
        # submit OCG job
        job.submit()
        
        # FIXME: pass OCG as additional argument to select jobs
        return HttpResponseRedirect(reverse('job_detail', args=[job.id, get_full_class_name(job)]))    