from django.db import models
from django.contrib.auth.models import User
from threading import Thread
from datetime import datetime, timedelta

from owslib.wps import WebProcessingService, GMLMultiPolygonFeatureCollection, WFSQuery, WFSFeatureCollection

from constants import JOB_STATUS

class Job(models.Model):
    '''Super class for executable jobs.'''
    
    status = models.CharField(max_length=20, verbose_name='Status', blank=False, default=JOB_STATUS.UNKNOWN)
    user = models.ForeignKey(User, related_name='user', verbose_name='User', blank=False)
    request = models.TextField(blank=True, null=True, help_text='Generic string containing job request')
    response = models.TextField(blank=True, null=True, help_text='Generic string containing job response')
    error = models.TextField(blank=True, null=True, help_text='Generic string containing possible error message')
    statusLocation = models.URLField('URL', help_text='URL to monitor the job status', blank=True, verify_exists=False, max_length=1000)
    url = models.URLField('URL', help_text='URL to retrieve the job output', blank=True, verify_exists=False, max_length=1000)
    submissionDateTime = models.DateTimeField('Date Submitted', auto_now_add=True, default=datetime.now())
    updateDateTime = models.DateTimeField('Date Updated', auto_now=True, default=datetime.now())

    
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
        
    def update(self, execution, first=False):
        '''Updates the job in the database from the latest WPS execution status.'''
        
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

 

class SupportingInfo(models.Model):
    '''Ancillary information bundled with a climate index job output.'''
    
    job = models.ForeignKey(ClimateIndexJob)    
    info = models.CharField(max_length=200, verbose_name='Supporting Information', blank=False)    
    
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
        self.job.update(execution, first=True)
                 
        # keep monitoring till job completion
        while execution.isComplete()==False:
            execution.checkStatus(sleepSecs=4)
            self.job.update(execution)
            
        print 'Done'
        