from django.db import models

from ncpp.models.common import Job
from ncpp.constants import APPLICATION_LABEL

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

	class Meta:
		app_label= APPLICATION_LABEL
