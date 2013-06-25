import time
import os
from ncpp.utils import hasText

SLEEP_SECONDS = 1

class OCG(object):
    """Adapter class that invokes the ocgis library."""
    
    def __init__(self, rootDir, rootUrl, debug=False):
        # root directory where output is written
        self.rootDir = rootDir
        # root URL for generated products
        self.rootUrl = rootUrl
        # flag to execute dummy run while developing
        self.debug = debug
        
    def encodeArgs(self, openClimateGisJob):
        """Method to transfor the OpenClimateGisJob instance into a dictionary of arguments passed on to the ocgis library."""
        
        args = {}
        # ocgis.RequestDataset(uri=None, variable=None, alias=None, time_range=None, time_region=None, 
        #                      level_range=None, s_proj=None, t_units=None, t_calendar=None, did=None, meta=None)
        args['uri'] = openClimateGisJob.dataset
        args['variable'] = openClimateGisJob.variable
        
        # class ocgis.OcgOperations(dataset=None, spatial_operation='intersects', geom=None, 
        #                           aggregate=False, calc=None, calc_grouping=None, calc_raw=False, 
        #                           abstraction='polygon', snippet=False, backend='ocg', prefix=None, 
        #                           output_format='numpy', agg_selection=False, select_ugid=None, 
        #                           vector_wrap=True, allow_empty=False, dir_output=None, slice=None, 
        #                           file_only=False, headers=None)
        args['geom'] = None
        args['select_ugid'] = None
        if hasText(openClimateGisJob.geometry):
            args['geom'] = openClimateGisJob.geometry
            args['select_ugid'] = openClimateGisJob.geometry_id
        elif (    hasText(openClimateGisJob.latmin) and hasText(openClimateGisJob.latmax) 
              and hasText(openClimateGisJob.lonmin) and hasText(openClimateGisJob.lonmax)):
            args['geom'] = [openClimateGisJob.lonmin, openClimateGisJob.lonmax, openClimateGisJob.latmin,  openClimateGisJob.latmax]
        elif hasText(openClimateGisJob.lat) and hasText(openClimateGisJob.lon):
            args['geom'] = [openClimateGisJob.lon, openClimateGisJob.lat]

        args['datetime_start'] = openClimateGisJob.datetime_start
        args['datetime_stop'] = openClimateGisJob.datetime_stop
        args['timeregion_month'] = openClimateGisJob.timeregion_month
        args['timeregion_year'] = openClimateGisJob.timeregion_year
        args['calc'] = openClimateGisJob.calc
        args['par1'] = openClimateGisJob.par1
        args['par2'] = openClimateGisJob.par2
        args['calc_raw'] = openClimateGisJob.calc_raw
        args['calc_group'] = openClimateGisJob.calc_group
        args['spatial_operation'] = openClimateGisJob.spatial_operation
        args['aggregate'] = openClimateGisJob.aggregate
        args['output_format'] = openClimateGisJob.output_format
        args['prefix'] = openClimateGisJob.prefix
        args['dir_output'] = str( openClimateGisJob.id )
            
        return args
        
    def run(self, args):

        # fake invocation on laptop
        if self.debug:
            time.sleep(SLEEP_SECONDS)
            path = "/usr/NCPP/static/ocgis/ocgis_output/MaurerNew_ARRM-CGCM3_bias_tasmax_mean_mon1_1971-2000_US48.jpg"
           
         # real invocation on NOAA servers 
        else:
            import ocgis
            
            # create output directory
            dir_output = os.path.join(self.rootDir, dir_output)
            if not os.path.exists(dir_output):
                os.makedirs(dir_output)
            
            #DIR_DATA = '/home/local/WX/ben.koziol/links/ocgis/bin/nc'
            #FILENAME = 'rhs_day_CanCM4_decadal2010_r2i1p1_20110101-20201231.nc'
            #VARIABLE = 'rhs'
            #AGGREGATE = False #True
            #SPATIAL_OPERATION = 'intersects' #'clip'
            #GEOM = 'state_boundaries'
            #STATES = {'CO':[32],'CA':[25]}
            #OUTPUT_FORMAT = 'csv+' #'csv' #'nc' #'shp'
            #PREFIX = 'ocgis_output'
            TIME_REGION = {'month':[6,7],'year':[2011]}
            
            rd = ocgis.RequestDataset(uri=args['uri'],
                                      variable=args['variable'], 
                                      time_range=None,
                                      time_region=args['time_region'])

            ## construct the operations call
            ops = ocgis.OcgOperations(dataset=rd, 
                                      geom=args['geom'],
                                      select_ugid=args['select_ugid'],
                                      aggregate=args['aggregate'], 
                                      spatial_operation=args['spatial_operation'], 
                                      prefix=args['prefix'],
                                      output_format=args['output_format'], 
                                      dir_output=args['dir_output'])

            ## return the path to the folder containing the output data
            path = ops.execute()

        # return ouput
        url = path.replace(self.rootDir, self.rootUrl)
        return url
        
