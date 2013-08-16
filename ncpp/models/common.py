from django.db import models
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class Job(models.Model):
    '''Super class for executable jobs.'''
    
    status = models.CharField(max_length=20, verbose_name='Status', blank=False, default=JOB_STATUS.UNKNOWN)
    user = models.ForeignKey(User, related_name='user', verbose_name='User', blank=False)
    request = models.TextField(blank=True, null=True, help_text='Generic string containing job request')
    response = models.TextField(blank=True, null=True, help_text='Generic string containing job response')
    error = models.TextField(blank=True, null=True, help_text='Generic string containing possible error message')
    statusLocation = models.URLField('URL', help_text='URL to monitor the job status', blank=True, max_length=1000)
    url = models.URLField('URL', help_text='URL to retrieve the job output', blank=True, max_length=1000)
    submissionDateTime = models.DateTimeField('Date Submitted', auto_now_add=True, default=datetime.now())
    updateDateTime = models.DateTimeField('Date Updated', auto_now=True, default=datetime.now())

    def submit(self):
        """Method to submit the job.
           The default implementation sets the job status to STARTED."""        
        print 'Submitting job'
        
        self.status = JOB_STATUS.STARTED
        self.save()
        
    def update(self):
        """Method to update the job status. 
           The default implementation does nothing."""
        pass
    
    def getFormData(self):
        """Method to return all job input parameters as a list of tuples of the form (parameter name, parameter value).
          The default implementation returns an empty list of tuples."""
        
        return []                 


    class Meta:
        app_label= APPLICATION_LABEL
        
    def class_name(self):
        return self.__module__ + "." + self.__class__.__name__
