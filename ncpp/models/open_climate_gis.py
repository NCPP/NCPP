from django.db import models
import os, ConfigParser
from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS, NO_VALUE_OPTION
from ncpp.utils import str2bool, get_month_string, hasText
from ncpp.ocg import OCG
import json
#from collections import OrderedDict

# read choices from configuration when module is first loaded (once per application)
from ncpp.constants import CONFIG_FILEPATH, GEOMETRIES_FILEPATH, NO_VALUE_OPTION

#ocgisConfig = ConfigParser.RawConfigParser(dict_type=OrderedDict)
ocgisConfig = ConfigParser.RawConfigParser()
# must set following line explicitely to preserve the case of configuration keys
ocgisConfig.optionxform = str 
try:
    ocgisConfig.read( os.path.expanduser(CONFIG_FILEPATH) )
except Exception as e:
    print "Configuration file %s not found" % CONFIG_FILEPATH
    raise e

class Geometries(object):
    """Class holding OCGIS geometries."""
    
    def __init__(self, filepath):
        
        # read geometries from JSON file
        try:
            with open(filepath,'r') as f:
                self.geometries = json.load(f)
        except Exception as e:
            print "Error reading geometry file: %s" % GEOMETRIES_FILEPATH
            raise e
        
    def getCategories(self):
        # no option selected
        tuples = [ NO_VALUE_OPTION ]
        # first option is US States
        tuples.append( ('US State Boundaries', 'US State Boundaries') )
        # then all US counties
        for category in sorted( self.geometries.keys() ):
            if category != 'US State Boundaries':
                tuples.append( (category, category) )
        return tuples
    
    def getGeometries(self, type):
        
        tuples = []
        for k,v in self.geometries[type]['geometries'].items():
            #tuples.append( (int(v), k) )
            tuples.append( (k,k) )
        return sorted(tuples, key=lambda t: t[1])
    
    def getGuid(self, category, geometry):
        return self.geometries[category]['geometries'][geometry]
    
    def getCategoryKey(self, category):
        return self.geometries[category]['key']

ocgisGeometries = Geometries(GEOMETRIES_FILEPATH)     

class Config():
    '''Class holding keys into configuration file.'''
    
    DEFAULT = 'default'
    DATASET = 'dataset'
    VARIABLE = 'variable'
    OUTPUT_FORMAT = 'output_format'
    CALCULATION = 'calculation'
    CALCULATION_GROUP = 'calculation_group'
    SPATIAL_OPERATION = 'spatial_operation'
    
    
def ocgisChoices(section, nochoice=False):
    choices = {}
    # add empty choice 
    if nochoice:
        choices[ NO_VALUE_OPTION[0] ] = NO_VALUE_OPTION[1]
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
        self.ocg = OCG(ocgisGeometries,
                       ocgisConfig.get(Config.DEFAULT, "rootDir"),
                       ocgisConfig.get(Config.DEFAULT, "rootUrl"),
                       debug=str2bool( ocgisConfig.get(Config.DEFAULT, "debug")) )
        
    def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
        
    def submit(self):
        
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
        job_data.append( ('Dataset', ocgisChoices(Config.DATASET)[self.dataset]) )
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
