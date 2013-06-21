# Fake Open Climate GIS library
import time
import os

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
    
    def run(self, 
            dataset=None, variable=None, geometry=None, geometry_id=None, 
            latmin=None, latmax=None, lonmin=None, lonmax=None, lat=None, lon=None,
            datetime_start=None, datetime_stop=None,
            calc=None, par1=None, par2=None, calc_raw=False, calc_group=[],
            spatial_operation='intersects', aggregate=True, output_format=None, prefix=None):
        
        # fake invocation on laptop
        if self.debug:
            time.sleep(SLEEP_SECONDS)
            path = "/usr/NCPP/static/ocgis/ocgis_output/MaurerNew_ARRM-CGCM3_bias_tasmax_mean_mon1_1971-2000_US48.jpg"
           
         # real invocation on NOAA servers 
        else:
            import ocgis
            
            DIR_OUTPUT = "/usr/NCPP/static/ocgis"
            DIR_DATA = '/home/local/WX/ben.koziol/links/ocgis/bin/nc'
            FILENAME = 'rhs_day_CanCM4_decadal2010_r2i1p1_20110101-20201231.nc'
            VARIABLE = 'rhs'
            AGGREGATE = False #True
            SPATIAL_OPERATION = 'intersects' #'clip'
            GEOM = 'state_boundaries'
            STATES = {'CO':[32],'CA':[25]}
            OUTPUT_FORMAT = 'csv+' #'csv' #'nc' #'shp'
            PREFIX = 'ocgis_output'
            TIME_REGION = {'month':[6,7],'year':[2011]}

            # output location
            ocgis.env.DIR_OUTPUT = DIR_OUTPUT
            ocgis.env.OVERWRITE = True
            
            rd = ocgis.RequestDataset(uri=os.path.join(DIR_DATA,FILENAME),
                          variable=VARIABLE,time_range=None,
                          time_region=TIME_REGION)

            ## construct the operations call
            ops = ocgis.OcgOperations(dataset=rd,geom=GEOM,select_ugid=STATES['CO'],
                                      aggregate=AGGREGATE,spatial_operation=SPATIAL_OPERATION,prefix=PREFIX,
                                      output_format=OUTPUT_FORMAT)

            ## return the path to the folder containing the output data
            path = ops.execute()

        # return ouput
        url = path.replace(self.rootDir, self.rootUrl)
        return url
        
