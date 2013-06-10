from threading import Thread
from django.db import models
from datetime import datetime, timedelta, date
from owslib.wps import WebProcessingService, GMLMultiPolygonFeatureCollection, WFSQuery, WFSFeatureCollection

from ncpp.constants import APPLICATION_LABEL, JOB_STATUS

from ncpp.models.common import Job

from owslib.wps import WPSExecution

#REGION_CHOICES = (('','--- Choose ---'), 
#                  ('NCCSC','North Central Climate Science Center Region'), )

REGION_CHOICES = { 
                   'CSC_Boundaries.1':'North-East',
                   'CSC_Boundaries.2':'North-West', 
                   'CSC_Boundaries.3':'South-West',
                   'CSC_Boundaries.4':'South-Central', 
                   'CSC_Boundaries.5':'North-Central',
                   'CSC_Boundaries.6':'South-East',
                 }

INDEX_CHOICES = {'tmin-days_below_threshold': 'Number of days with Minimum Temperature below threshold',
                 'tmax-days_above_threshold': 'Number of days with Maximum Temperature above threshold',
                 'pr-days_above_threshold'  : 'Number of days with Precipitation above threshold' }

AGGREGATION_CHOICES = { 'GridPointIndexes':'Grid Point Indexes',
                        'IndexesAggregatedByRegion':'Indexes Aggregated by Region' }

# model data
#START_DATETIME_CHOICES = [ (date(year,1,1).isoformat(), date(year,1,1).isoformat()) for year in range(2010, 2091, 5)]
# observations data
START_DATETIME_CHOICES = [ (date(year,1,1).isoformat(), date(year,1,1).isoformat()) for year in range(1950, 2000, 5)]

#DATASET_CHOICES = { 'a1b':'Gridded Metereological Observations, Annual Averages, CO2 Emission Scenario: SRES A1B',
#                    'a1fi':'Gridded Metereological Observations, Annual Averages, CO2 Emission Scenario: SRES A1FI',
#                    'a2':'Gridded Metereological Observations, Annual Averages, CO2 Emission Scenario: SRES A2',
#                    'b1':'Gridded Metereological Observations, Annual Averages, CO2 Emission Scenario: SRES B1' }
DATASET_CHOICES = { 'Maurer':'Gridded Metereological Observations, Maurer 2002, Annual Averages' }

OUTPUT_FORMAT_CHOICES = {'CSV':'CSV (comma-separated, indexes aggregated by region)', 
                         'NetCDF':'NetCDF (grid point indexes)' }

SUPPORTING_INFO_CHOICES = { 'Metadata':'Metadata',
                            'TranslationalInfo':'Translational Information' }

    
class ClimateIndexJob(Job):
    '''Job that retrieves a climate index over a specified geographic region.'''
    
    region = models.CharField(max_length=200, verbose_name='Geographic Region', blank=False)
    index = models.CharField(max_length=200, verbose_name='Index', blank=False)
    #aggregation = models.CharField(max_length=200, verbose_name='Aggregation', blank=False)
    startDateTime = models.DateField(verbose_name='Start Date', blank=False)
    dataset = models.CharField(max_length=200, verbose_name='Observed Dataset', blank=False)
    outputFormat = models.CharField(max_length=200, verbose_name='Output Format', blank=False)
    
    def __unicode__(self):
        return 'Climate Index Job id=%s status=%s' % (self.id, self.status)
    
    def submit(self):
        print 'Submitting the job'
        runner = Runner(self)
        runner.start()
        
    def getInputData(self):
        """Returns an ordered list of (choice label, choice value)."""
        
        job_data = []
        job_data.append( ('Region', REGION_CHOICES[self.region]) )
        job_data.append( ('Climate Index', INDEX_CHOICES[self.index]) )
        job_data.append( ('Start Date Time', self.startDateTime) )
        job_data.append( ('Dataset', DATASET_CHOICES[self.dataset]) )
        job_data.append( ('Output Format', OUTPUT_FORMAT_CHOICES[self.outputFormat]) )
        supportingInfo = []
        for info in self.supportinginfo_set.all():
            supportingInfo.append( SUPPORTING_INFO_CHOICES[info.info] )   
        job_data.append( ('Supporting Information', supportingInfo) )
        return job_data                  
        
    def update(self):
        '''Updates the job in the database from the latest WPS execution status.'''
        
        # create a new execution from the job status URL
        execution = WPSExecution()
        execution.checkStatus(url=self.statusLocation, sleepSecs=0)       
        self._update(execution)

    def _update(self, execution, first=False):
        """Internal method to update the job state from an existing WPS execution."""
                
        if first:
            self.request = execution.request
            self.statusLocation = execution.statusLocation
        self.status = execution.status
        self.response = execution.response
        
        if execution.isComplete():
            # success
            if execution.isSucceded():
                for output in execution.processOutputs:               
                    if output.reference is not None:
                        print 'Output URL=%s' % output.reference
                        self.url = output.reference
            else:
                for ex in execution.errors:
                    print 'Error: code=%s, locator=%s, text=%s' % (ex.code, ex.locator, ex.text)
                    self.error = ex.text

        
        self.save()
        print 'Job status=%s' % self.status

    class Meta:
        app_label= APPLICATION_LABEL

 

class SupportingInfo(models.Model):
    '''Ancillary information bundled with a climate index job output.'''
    
    job = models.ForeignKey(ClimateIndexJob)    
    info = models.CharField(max_length=200, verbose_name='Supporting Information', blank=False)    
    
    class Meta:
        app_label= APPLICATION_LABEL

    
class Runner(Thread):
    
    def __init__ (self, job):
        Thread.__init__(self)
        self.job = job
        
    def run(self):
        
        # submit job
        verbose = True
        wps = WebProcessingService('http://cida.usgs.gov/climate/gdp/process/WebProcessingService', verbose=verbose)
        
        # formula for model data
        #dataset_id = "ensemble_%s_%s" % (self.job.dataset, self.job.index)
        # formula for observational data
        dataset_id = "gmo_%s" % self.job.index
        print 'dataset_id=%s' % dataset_id
        if self.job.index=='tmin-days_below_threshold':
            dataset_uri = 'dods://cida.usgs.gov/qa/thredds/dodsC/derivatives/derivative-days_below_threshold.tmin.ncml'
        elif self.job.index=='tmax-days_above_threshold':
            dataset_uri = 'dods://cida.usgs.gov/qa/thredds/dodsC/derivatives/derivative-days_above_threshold.tmax.ncml'
        elif self.job.index=='pr-days_above_threshold':
            dataset_uri = 'dods://cida.usgs.gov/qa/thredds/dodsC/derivatives/derivative-days_above_threshold.pr.ncml'
        else:
            raise Exception("Unrecognized index choice, cannot select dataset")
        print 'dataset_uri=%s' % dataset_uri
        
        # datetime processing
        #startDateTime = datetime.strptime(self.job.startDateTime, "%Y-%m-%d")
        startDateTime = self.job.startDateTime
        _startDateTime = startDateTime.isoformat()+".000Z"
        # FIXME: 5 year time span
        stopDateTime = datetime(startDateTime.year+5, startDateTime.month, startDateTime.day)
        _stopDateTime = stopDateTime.isoformat()+".000Z"
                
        wfsUrl = "http://cida.usgs.gov/climate/gdp/proxy/http://igsarm-cida-gdp2.er.usgs.gov:8082/geoserver/wfs"
        query = WFSQuery("sample:CSC_Boundaries", propertyNames=["the_geom","area_name"], filters=[self.job.region])
        featureCollection = WFSFeatureCollection(wfsUrl, query)
        print 'outputFormat=%s' % self.job.outputFormat
        if self.job.outputFormat=='CSV':
            processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureWeightedGridStatisticsAlgorithm'
            inputs =  [ ("FEATURE_ATTRIBUTE_NAME","the_geom"),
                        ("DATASET_URI", dataset_uri.encode('utf8')),
                        ("DATASET_ID", dataset_id.encode('utf8')),
                        ("TIME_START", _startDateTime),
                        ("TIME_END", _stopDateTime ),
                        ("REQUIRE_FULL_COVERAGE","false"),
                        ("DELIMITER","COMMA"),
                        ("STATISTICS","MEAN"),
                        ("GROUP_BY","STATISTIC"),
                        ("SUMMARIZE_TIMESTEP","false"),
                        ("SUMMARIZE_FEATURE_ATTRIBUTE","false"),
                        ("FEATURE_COLLECTION", featureCollection)
                       ]
        else:
            processid = 'gov.usgs.cida.gdp.wps.algorithm.FeatureCoverageOPeNDAPIntersectionAlgorithm'
            inputs =  [ ("DATASET_URI", dataset_uri.encode('utf8')),
                        ("DATASET_ID", dataset_id.encode('utf8')),
                        ("TIME_START", _startDateTime),
                        ("TIME_END", _stopDateTime ),
                        ("REQUIRE_FULL_COVERAGE","false"),
                        ("FEATURE_COLLECTION", featureCollection)
                       ]
                        
        output = "OUTPUT"
        
        # submit job
        execution = wps.execute(processid, inputs, output = "OUTPUT")
        self.job._update(execution, first=True)
                 
        # keep monitoring till job completion
        while execution.isComplete()==False:
            execution.checkStatus(sleepSecs=4)
            self.job._update(execution)
            
        print 'Done'