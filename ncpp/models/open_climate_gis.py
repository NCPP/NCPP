from django.db import models

from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL, JOB_STATUS

from ncpp.ocg import ocg # FIXME

DATASET_CHOICES = { 'dataset1' : 'Dataset 1',
				    'dataset2' : 'Dataset 2' }

VARIABLE_CHOICES = { 'v1' : 'Variable 1',
				     'v2' : 'Variable 2'}

class OpenClimateGisJob(Job):
	"""Class that represents the execution of an Open Climate GIS job."""
	
	dataset = models.CharField(max_length=200, verbose_name='Dataset', blank=False)
	variable = models.CharField(max_length=200, verbose_name='Variable', blank=False)
	
	def __unicode__(self):
		return 'Open Climate GIS Job id=%s status=%s' % (self.id, self.status)
	
	def getInputData(self):
		"""Returns an ordered list of (choice label, choice value)."""
		
		job_data = []
		job_data.append( ('Dataset', DATASET_CHOICES[self.dataset]) )
		job_data.append( ('Variable', VARIABLE_CHOICES[self.variable]) )
		return job_data				  

	def submit(self):
		print 'Submitting Open Climate GIS job'
		
		# submit the job synchronously, wait for output
		self.url = ocg(dataset=self.dataset, variable=self.variable)
		self.request = "<request>"+str( self.getInputData )+"</request>"
		self.response = "<response>"+self.url+"</response>"
		self.status = JOB_STATUS.SUCCESS
		self.save()

	class Meta:
		app_label= APPLICATION_LABEL
