from django.db import models
import os, ConfigParser
from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS
from ncpp.utils import str2bool, get_month_string
from ncpp.ocg import OCG
#from collections import OrderedDict

# read choices from configuration when module is first loaded (once per application)
from ncpp.constants import CONFIG_FILEPATH
#ocgisConfig = ConfigParser.RawConfigParser(dict_type=OrderedDict)
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
    
    DEFAULT = 'default'
    DATASET = 'dataset'
    VARIABLE = 'variable'
    GEOMETRY = 'geometry'
    GEOMETRY_ID = 'geometry_id'
    OUTPUT_FORMAT = 'output_format'
    CALCULATION = 'calculation'
    CALCULATION_GROUP = 'calculation_group'
    SPATIAL_OPERATION = 'spatial_operation'
    
    
def ocgisChoices(section, nochoice=False):
    choices = {}
    # add empty choice 
    if nochoice:
        choices[""] = "-- Please Select --"
    choices.update( dict( ocgisConfig.items(section) ) )
    return choices


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
    timeregion_month = models.CharField(max_length=200, verbose_name='Time Region: Month', null=True, blank=True)
    timeregion_year = models.CharField(max_length=200, verbose_name='Time Region: Year', null=True, blank=True)
        
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
        self.ocg = OCG(ocgisConfig.get(Config.DEFAULT, "rootDir"),
                       ocgisConfig.get(Config.DEFAULT, "rootUrl"),
                       debug=str2bool( ocgisConfig.get(Config.DEFAULT, "debug")) )
        
    def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
        
    def submit(self):
        print 'Submitting Open Climate GIS job'
        
        args = self.ocg.encodeArgs(self)
        self.request = self._encode_request(args)
        
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
        
        print "arga=%s" % args
        return "<request>%s</request>" % sorted(args, key=lambda key: args[key])
        
        
    def _encode_response(self):
        """Utility method to build the job response field."""
        
        self.response  = '<response job_id="%s">' % self.id
        self.response += '<status>%s</status>' % self.status
        self.response += '<url>%s</url>' % self.url
        self.response += '<error>%s</error>' % self.error
        self.response += '</response>'
        
        
    def getFormData(self):
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
        print 'timeregion_month=%s' % self.timeregion_month
        if self.timeregion_month is not None and len(self.timeregion_month)>0:
            job_data.append( ('Selected Months', get_month_string( map(int, self.timeregion_month.split(",")) ) ))
        job_data.append( ('Selected Years', self.timeregion_year) )
        
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
