# Module holding application constants.

APPLICATION_LABEL = 'ncpp'
CONFIG_FILEPATH = '/usr/local/ocgis/ocgis.cfg'

def enum(**enums):
    return type('Enum', (), enums)

    def isComplete(self):
        if (self.status=='ProcessSucceeded' or self.status=='ProcessFailed' or self.status=='Exception'):
            return True
        elif (self.status=='ProcessStarted'):
            return False
        elif (self.status=='ProcessAccepted' or self.status=='ProcessPaused'):
            return False
        else:
            raise Exception('Unknown process execution status: %s' % self.status)


JOB_STATUS = enum(UNKNOWN='Status Unknown', STARTED='Process Started', RUNNING='Process Running', SUCCESS='Process Succeeded', 
                  FAILED='Process Failed', ACCEPTED='Process Accepted', PAUSED='ProcessPaused', ERROR='Error')

MONTH_CHOICES = ( (0,'Jan'), (1,'Feb'), (2,'Mar'), (3,'Apr'), (4,'May'), (5,'Jun'),
                  (6,'Jul'), (7,'Aug'), (8,'Sep'), (9,'Oct'), (10,'Nov'), (11,'Dec'))
MONTH_DICT = dict(MONTH_CHOICES) # transform tuples to dictionary for easy indexing of keys

NO_VALUE_OPTION = ("","-- Please Select --")