from django.db import models
import os, ConfigParser
from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS
from ncpp.utils import str2bool
from ncpp.ocg import OCG

# read choices from configuration when module is first loaded (once per application)
from ncpp.constants import CONFIG_FILEPATH
ocgisConfig = ConfigParser.RawConfigParser()
# must set following line explicitely to preserve the case of configuration keys
ocgisConfig.optionxform = str 
try:
    ocgisConfig.read( os.path.expanduser(CONFIG_FILEPATH) )
except Exception as e:
    print "Configuration file %s not found" % CONFIG_FILEPATH
    raise e

class Config():
    '''Class holding keys into configuration file.'''
    
    DATASET = 'dataset'
    VARIABLE = 'variable'
    GEOMETRY = 'geometry'
    GEOMETRY_ID = 'geometry_id'
    OUTPUT_FORMAT = 'output_format'
    CALCULATION = 'calculation'
    CALCULATION_GROUP = 'calculation_group'
    SPATIAL_OPERATION = 'spatial_operation'
    
    
def ocgisChoices(section):
    return dict( ocgisConfig.items(section) )

class OpenClimateGisJob(Job):
    """Class that represents the execution of an Open Climate GIS job."""
    
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
    
    calc = models.CharField(max_length=50, verbose_name='Calculation', null=False)
    par1 = models.FloatField(verbose_name='Calculation Parameter 1', blank=True, null=True)
    par2 = models.FloatField(verbose_name='Calculation Parameter 2', blank=True, null=True)
    calc_group = models.CharField(max_length=100, verbose_name='Calculation Group', null=True, blank=True)
    calc_raw = models.BooleanField(verbose_name='Calculate Raw ?')
    spatial_operation = models.CharField(max_length=50, verbose_name='Spatial Operation', blank=False)
    
    aggregate = models.BooleanField(verbose_name='Aggregate ?')
    output_format = models.CharField(max_length=20, verbose_name='Output Format', blank=False)
    prefix = models.CharField(max_length=50, verbose_name='Prefix', blank=False, default='ocgis_output')
    
    def __init__(self, *args, **kwargs):
        
        super(OpenClimateGisJob, self).__init__(*args, **kwargs)
                
        # instantiate Open Climate GIS adapter
        self.ocg = OCG(ocgisConfig.get("default", "rootDir"),
                       ocgisConfig.get("default", "rootUrl"),
                       debug=str2bool( ocgisConfig.get("default", "debug") ))
        
    def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
        
    def submit(self):
        print 'Submitting Open Climate GIS job'
        
        self.request = "<request>"+str( self.getInputData() )+"</request>"
        
        try:
            # submit the job synchronously, wait for output
            self.url = self.ocg.run(dataset=self.dataset, variable=self.variable, 
                                    geometry=self.geometry, geometry_id=self.geometry_id, 
                                    latmin=self.latmin, latmax=self.latmax, lonmin=self.lonmin, lonmax=self.lonmax,
                                    lat=self.lat, lon=self.lon,
                                    datetime_start=self.datetime_start, datetime_stop=self.datetime_stop,
                                    calc=self.calc, par1=self.par1, par2=self.par2, calc_raw=self.calc_raw, calc_group=self.calc_group,
                                    spatial_operation=self.spatial_operation, aggregate=self.aggregate, 
                                    output_format=self.output_format, prefix=self.prefix, dir_output=str(self.id))
            
            # job terminated successfully
            self.status = JOB_STATUS.SUCCESS
            self._encode_response()
            
        except Exception as e:
            print e
            # job terminated in error
            self.status = JOB_STATUS.FAILED
            self.error = e
            self._encode_response()       
        
    def _encode_response(self):
        """Utility method to build the job response field."""
        
        self.response  = '<response job_id="%s">' % self.id
        self.response += '<status>%s</status>' % self.status
        self.response += '<url>%s</url>' % self.url
        self.response += '<error>%s</error>' % self.error
        self.response += '</response>'
        self.save()
        
    def getInputData(self):
        """Returns an ordered list of (choice label, choice value)."""
        
        job_data = []
        job_data.append( ('Dataset', ocgisChoices(Config.DATASET)[self.dataset]) )
        job_data.append( ('Variable', ocgisChoices(Config.VARIABLE)[self.variable]) )
        job_data.append( ('Geometry', ocgisChoices(Config.GEOMETRY)[self.geometry]) )
        # must transform string into list of integers
        geometry_id=[]
        for id in self.geometry_id.split(","):
            if id != '':
                geometry_id.append( ocgisChoices(Config.GEOMETRY_ID)[id] )
        job_data.append( ('Geometry ID', geometry_id) )
        job_data.append( ('Latitude Minimum', self.latmin) )
        job_data.append( ('Latitude Maximum', self.latmax) )
        job_data.append( ('Longitude Minimum', self.lonmin) )
        job_data.append( ('Longitude Maximum', self.lonmax) )
        
        job_data.append( ('Latitude', self.lat) )
        job_data.append( ('Longitude', self.lon) )
        
        job_data.append( ('Start Date Time', self.datetime_start) )
        job_data.append( ('Stop Date Time', self.datetime_stop) )
        
        job_data.append( ('Calculation', self.calc) )
        job_data.append( ('Calculation Parameter 1', self.par1) )
        job_data.append( ('Calculation Parameter 2', self.par2) )
        job_data.append( ('Calculation Group', self.calc_group) )
        job_data.append( ('Calculate Raw?', self.calc_raw) )
        
        job_data.append( ('Spatial Operation', ocgisChoices(Config.SPATIAL_OPERATION)[self.spatial_operation]) )
        job_data.append( ('Aggregate', self.aggregate) )
        job_data.append( ('Output Format', ocgisChoices(Config.OUTPUT_FORMAT)[self.output_format]) )
        job_data.append( ('Prefix', self.prefix) )
                 
        return job_data				  
        
    class Meta:
		app_label= APPLICATION_LABEL
