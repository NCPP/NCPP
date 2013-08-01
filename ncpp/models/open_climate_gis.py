from django.db import models
from threading import Thread
from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS, NO_VALUE_OPTION
from ncpp.config import ocgisDatasets
from ncpp.utils import str2bool, get_month_string, hasText
from ncpp.ocg import OCG
import json

from ncpp.config import ocgisDatasets, ocgisGeometries, ocgisConfig, Config, ocgisChoices, ocgisCalculations

class OpenClimateGisJob(Job):
    """Class that represents the execution of an Open Climate GIS job."""
    
    dataset_category = models.CharField(max_length=200, verbose_name='Dataset Category', blank=False)
    dataset = models.CharField(max_length=200, verbose_name='Dataset', blank=False)
    variable = models.CharField(max_length=200, verbose_name='Variable', blank=False)
    geometry = models.CharField(max_length=200, verbose_name='Geometry', null=True, blank=True)
    geometry_id = models.CharField(max_length=200, verbose_name='Geometry ID', null=True, blank=True)
    latmin = models.FloatField(verbose_name='Latitude Minimum', blank=True, null=True)
    latmax = models.FloatField(verbose_name='Latitude Maximum', blank=True, null=True)
    lonmin = models.FloatField(verbose_name='Longitude Minimum', blank=True, null=True)
    lonmax = models.FloatField(verbose_name='Longitude Maximum', blank=True, null=True)

    lat = models.FloatField(verbose_name='Latitude', blank=True, null=True)
    lon = models.FloatField(verbose_name='Longitude', blank=True, null=True)
    
    datetime_start = models.DateTimeField(verbose_name='Start Date Time', blank=True, null=True)
    datetime_stop = models.DateTimeField(verbose_name='Stop Date Time', blank=True, null=True)
    timeregion_month = models.CharField(max_length=200, verbose_name='Time Region: Month', null=True, blank=True)
    timeregion_year = models.CharField(max_length=200, verbose_name='Time Region: Year', null=True, blank=True)
        
    calc = models.CharField(max_length=50, verbose_name='Calculation', null=True, blank=True)
    par1 = models.FloatField(verbose_name='Calculation Parameter 1', blank=True, null=True)
    par2 = models.FloatField(verbose_name='Calculation Parameter 2', blank=True, null=True)
    calc_group = models.CharField(max_length=100, verbose_name='Calculation Group', null=False, blank=False)
    calc_raw = models.BooleanField(verbose_name='Calculate Raw ?')
    spatial_operation = models.CharField(max_length=50, verbose_name='Spatial Operation', blank=False)
    
    aggregate = models.BooleanField(verbose_name='Aggregate ?')
    output_format = models.CharField(max_length=20, verbose_name='Output Format', blank=False)
    prefix = models.CharField(max_length=50, verbose_name='Prefix', blank=False, default='ocgis_output')
    with_auxiliary_files = models.BooleanField(verbose_name='Include auxiliary files ?')
    
    def __init__(self, *args, **kwargs):
        
        super(OpenClimateGisJob, self).__init__(*args, **kwargs)
                
        # instantiate Open Climate GIS adapter
        self.ocg = OCG(ocgisDatasets, ocgisGeometries, ocgisCalculations,
                       ocgisConfig.get(Config.DEFAULT, "rootDir"),
                       ocgisConfig.get(Config.DEFAULT, "rootUrl"),
                       debug=str2bool( ocgisConfig.get(Config.DEFAULT, "debug")) )
        
    def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
        
    def submit(self):
        """This method submits the job in a separate thread."""
        
        print 'Submitting the job'
        runner = Runner(self)
        runner.start()
        
    def _submit(self):
        """Method that contains the logic to run the job. It may be executed in a separate thread,"""
        
        args = self.ocg.encodeArgs(self)
        self.request = self._encode_request(args)
        self.status = JOB_STATUS.STARTED
        self.save()
        
        try:
            # submit the job synchronously, wait for output
            self.url = self.ocg.run(args)
            
            # job terminated successfully
            self.status = JOB_STATUS.SUCCESS
            self._encode_response()
            
        except Exception as e:
            print e
            # job terminated in error
            self.status = JOB_STATUS.FAILED
            self.error = e
            self._encode_response()    
            
        self.save()   
        
    def _encode_request(self, args):
        """Utility method to build the job request document."""
        
        request = "<request>\n"
        for k, v in sorted(args.items()):
            request += "\t<%s>%s</%s>\n" % (k, v, k)
        request += "</request>\n" 
        return request
        
        
    def _encode_response(self):
        """Utility method to build the job response field."""
        
        self.response  = '<response job_id="%s">' % self.id
        self.response += '<status>%s</status>' % self.status
        self.response += '<url>%s</url>' % self.url
        self.response += '<error>%s</error>' % self.error
        self.response += '</response>'
        
        
    def getFormData(self):
        """Returns an ordered list of (choice label, choice value) for display to the user."""
        
        job_data = []
        job_data.append( ('Dataset Category', self.dataset_category) )
        job_data.append( ('Dataset', self.dataset) )
        job_data.append( ('Variable', self.variable) )
        if hasText(self.geometry):
            job_data.append( ('Shape Type', self.geometry) )
        if self.geometry_id is not None and len(self.geometry_id)>0:
            job_data.append( ('Shape Geometry', self.geometry_id.replace(",",", ")) )
        if hasText(self.latmin):
            job_data.append( ('Latitude Minimum', self.latmin) )
        if hasText(self.latmax):
            job_data.append( ('Latitude Maximum', self.latmax) )
        if hasText(self.lonmin):
            job_data.append( ('Longitude Minimum', self.lonmin) )
        if hasText(self.lonmax):
            job_data.append( ('Longitude Maximum', self.lonmax) )
        
        if hasText(self.lat):
            job_data.append( ('Latitude', self.lat) )
        if hasText(self.lon):
            job_data.append( ('Longitude', self.lon) )
        
        job_data.append( ('Start Date Time', self.datetime_start) )
        job_data.append( ('Stop Date Time', self.datetime_stop) )
        if self.timeregion_month is not None and len(self.timeregion_month)>0:
            job_data.append( ('Time Region: Months', get_month_string( map(int, self.timeregion_month.split(",")) ) ))
        if self.timeregion_year is not None and hasText(self.timeregion_year):
            job_data.append( ('Time Region: Years', self.timeregion_year) )
        
        if self.calc is not None:
            job_data.append( ('Calculation', self.calc) )
        if self.par1 is not None:
            job_data.append( ('Calculation Parameter 1', self.par1) )
        if self.par2 is not None:
            job_data.append( ('Calculation Parameter 2', self.par2) )
            
        if self.calc_group is not None and len(self.calc_group)>0:
            job_data.append( ('Calculation Group', self.calc_group.replace(",",", ")) )
        job_data.append( ('Calculate Raw?', self.calc_raw) )
        
        job_data.append( ('Spatial Operation', ocgisChoices(Config.SPATIAL_OPERATION)[self.spatial_operation]) )
        job_data.append( ('Aggregate', self.aggregate) )
        job_data.append( ('Output Format', ocgisChoices(Config.OUTPUT_FORMAT)[self.output_format]) )
        job_data.append( ('Prefix', self.prefix) )
        job_data.append( ('Include Auxiliary Files', self.with_auxiliary_files) )
                 
        return job_data				  
        
    class Meta:
		app_label= APPLICATION_LABEL

class Runner(Thread):
    """Class to execute an Open Climate GIS job in a separate thread."""
    
    def __init__ (self, job):
        Thread.__init__(self)
        self.job = job
        
    def run(self):
        print "Running the job"
        self.job._submit()