# Module holding application constants.
from datetime import date

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


JOB_STATUS = enum(UNKNOWN='StatusUnknown', STARTED='ProcessStarted', SUCCESS='ProcessSucceeded', 
                  FAILED='ProcessFailed', ACCEPTED='ProcessAccepted', PAUSED='ProcessPaused', ERROR='Exception')
