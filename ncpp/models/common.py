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
    statusLocation = models.URLField('URL', help_text='URL to monitor the job status', blank=True, verify_exists=False, max_length=1000)
    url = models.URLField('URL', help_text='URL to retrieve the job output', blank=True, verify_exists=False, max_length=1000)
    submissionDateTime = models.DateTimeField('Date Submitted', auto_now_add=True, default=datetime.now())
    updateDateTime = models.DateTimeField('Date Updated', auto_now=True, default=datetime.now())

    class Meta:
        app_label= APPLICATION_LABEL
        
    def class_name(self):
        return self.__module__ + "." + self.__class__.__name__
