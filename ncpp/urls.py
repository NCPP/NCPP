from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.contrib.auth.decorators import login_required

from ncpp.forms import ClimateIndexesForm1, ClimateIndexesForm2, ClimateIndexesForm3
from ncpp.forms import OpenClimateGisForm1, OpenClimateGisForm2, OpenClimateGisForm3
from ncpp.views import ClimateIndexesWizard, OpenClimateGisWizard


urlpatterns = patterns('',
    
    # top-level url
    url(r'^$', 'django.views.generic.simple.redirect_to', { 'url': '/ncpp/open_climate_gis/'}, name='home' ),
    
    # climate indexes use case
    # note use of 'login_required' decorator directly in URL configuration
    url(r'^climate_indexes/$', login_required(ClimateIndexesWizard.as_view([ClimateIndexesForm1, ClimateIndexesForm2, ClimateIndexesForm3])), name='climate_indexes' ),
       
    # open climate GIS use case
    url(r'^open_climate_gis/$', OpenClimateGisWizard.as_view([OpenClimateGisForm1, OpenClimateGisForm2, OpenClimateGisForm3]), name='open_climate_gis' ),
    url(r'^open_climate_gis/dataset/$', 'ncpp.views.open_climate_gis.inspect_dataset', name='inspect_dataset'),
    url(r'^open_climate_gis/geometries/$', 'ncpp.views.open_climate_gis.get_geometries', name='get_geometries'),
    
    # job display pages
    url(r'^jobs/(?P<username>.+)/(?P<job_class>.+)/$', 'ncpp.views.jobs_list', name='jobs_list' ),
    
    url(r'^job/request/(?P<job_id>.+)/(?P<job_class>.+)/$', 'ncpp.views.job_request', name='job_request' ),
    url(r'^job/response/(?P<job_id>.+)/(?P<job_class>.+)/$', 'ncpp.views.job_response', name='job_response' ),
    url(r'^job/check/(?P<job_id>.+)/(?P<job_class>.+)/$', 'ncpp.views.job_check', name='job_check' ),
    url(r'^job/(?P<job_id>.+)/(?P<job_class>.+)/$', 'ncpp.views.job_detail', name='job_detail' ),
    
    # login/logout using django default authentication views and templates
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', {'login_url': '/ncpp/login/'}, name='logout'),

)