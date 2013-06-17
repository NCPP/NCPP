from django.db import models
import os, ConfigParser
from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS

from ncpp.ocg import ocg # FIXME

# read choices from configuration when module is first loaded (once per application)
from ncpp.constants import CONFIG_FILEPATH
ocgisConfig = ConfigParser.RawConfigParser()
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
    
    aggregate = models.BooleanField(verbose_name='Aggregate ?')
    
    def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
        
    def submit(self):
        print 'Submitting Open Climate GIS job'
        
        # submit the job synchronously, wait for output
        self.url = ocg(dataset=self.dataset, variable=self.variable, 
                       geometry=self.geometry, geometry_id=self.geometry_id, 
                       latmin=self.latmin, latmax=self.latmax, lonmin=self.lonmin, lonmax=self.lonmax,
                       lat=self.lat, lon=self.lon,
                       aggregate=self.aggregate)
        
        self.request = "<request>"+str( self.getInputData )+"</request>"
        self.response = "<response>"+self.url+"</response>"
        self.status = JOB_STATUS.SUCCESS
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
        
         
        return job_data				  
        
    class Meta:
		app_label= APPLICATION_LABEL
