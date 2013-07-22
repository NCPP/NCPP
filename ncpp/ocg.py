import time
import os
from shutil import rmtree
from ncpp.utils import hasText

SLEEP_SECONDS = 1

class OCG(object):
    """Adapter class that invokes the ocgis library."""
    
    def __init__(self, geometries, rootDir, rootUrl, debug=False):
        # object holding geometries
        self.geometries = geometries
        # root directory where output is written
        self.rootDir = rootDir
        # root URL for generated products
        self.rootUrl = rootUrl
        # flag to execute dummy run while developing
        self.debug = debug
        
    def encodeArgs(self, openClimateGisJob):
        """Method to transform the OpenClimateGisJob instance into a dictionary of arguments passed on to the ocgis library."""
        
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
            args['geom'] = self.geometries.getCategoryKey( openClimateGisJob.geometry )
            args['select_ugid'] = []
            # must transform back from string to list of integers
            for geom in openClimateGisJob.geometry_id.split(","):
                args['select_ugid'].append( self.geometries.getGuid(openClimateGisJob.geometry, geom))
        elif (    hasText(openClimateGisJob.latmin) and hasText(openClimateGisJob.latmax) 
              and hasText(openClimateGisJob.lonmin) and hasText(openClimateGisJob.lonmax)):
            args['geom'] = [openClimateGisJob.lonmin, openClimateGisJob.lonmax, openClimateGisJob.latmin,  openClimateGisJob.latmax]
        elif hasText(openClimateGisJob.lat) and hasText(openClimateGisJob.lon):
            args['geom'] = [openClimateGisJob.lon, openClimateGisJob.lat]

        if openClimateGisJob.datetime_start is not None and openClimateGisJob.datetime_stop is not None:
            args['time_range'] = [openClimateGisJob.datetime_start, openClimateGisJob.datetime_stop]
        else:
            args['time_range'] = None
            
        args['time_region'] = None
        if hasText(openClimateGisJob.timeregion_month) or hasText(openClimateGisJob.timeregion_year):
            args['time_region'] = { 'month':None, 'year':None }
            if hasText(openClimateGisJob.timeregion_month):
                args['time_region']['month'] = []
                for i in map(int, openClimateGisJob.timeregion_month.split(",")):
                    args['time_region']['month'].append(i)
            if hasText(openClimateGisJob.timeregion_year):
                args['time_region']['year'] = []
                for i in map(int, openClimateGisJob.timeregion_year.split(",")):
                    args['time_region']['year'].append(i)
        
        args['calc'] = None
        if hasText(openClimateGisJob.calc) and openClimateGisJob.calc.lower() != 'none':
            args['calc'] = [ {'func':str(openClimateGisJob.calc), 'name':str(openClimateGisJob.calc)} ] 
            if openClimateGisJob.calc == 'threshold':
                args['calc'][0]['kwds'] = {'lower':openClimateGisJob.par1, 'operation':'gte'}
            elif openClimateGisJob.calc == 'between':
                args['calc'][0]['kwds'] = {'lower':openClimateGisJob.par1, 'upper':openClimateGisJob.par2}
            
        args['calc_raw'] = openClimateGisJob.calc_raw
        args['calc_grouping'] = map(str, openClimateGisJob.calc_group.split(","))
        
        args['spatial_operation'] = openClimateGisJob.spatial_operation
        args['aggregate'] = openClimateGisJob.aggregate
        args['output_format'] = openClimateGisJob.output_format
        args['prefix'] = openClimateGisJob.prefix
        args['dir_output'] = str( openClimateGisJob.id )
        args['with_auxiliary_files'] = openClimateGisJob.with_auxiliary_files
            
        return args
        
    def run(self, args):
        
        print 'Running OCGIS job with arguments=%s' % args

        # fake invocation on laptop
        if self.debug:
            time.sleep(SLEEP_SECONDS)
            download_path = "/usr/NCPP/static/ocgis/ocgis_output/MaurerNew_ARRM-CGCM3_bias_tasmax_mean_mon1_1971-2000_US48.jpg"
           
         # real invocation on NOAA servers 
        else:
            import ocgis
            
            # create output directory
            dir_output = os.path.join(self.rootDir, args['dir_output'])
            if not os.path.exists(dir_output):
                os.makedirs(dir_output)
            # remove existing directory, generated by previous installation
            else:
                rmtree(dir_output)
                                    
            # define dataset
            rd = ocgis.RequestDataset(uri=args['uri'],
                                      variable=str(args['variable']), 
                                      time_range=args['time_range'],
                                      time_region=args['time_region'])

            ## construct the operations call
            ops = ocgis.OcgOperations(dataset=rd, 
                                      geom=args['geom'],
                                      select_ugid=args['select_ugid'],
                                      aggregate=args['aggregate'], 
                                      spatial_operation=args['spatial_operation'], 
                                      prefix=args['prefix'],
                                      output_format=args['output_format'], 
                                      dir_output=dir_output)

            # execute the operation
            # 'path' points to the top-level folder containing the output data
            path = ops.execute()
            # 'download_path' points to single file for user to download
            download_path = ocgis.format_return(path, ops, with_auxiliary_files=args['with_auxiliary_files'])

        # return ouput
        url = download_path.replace(self.rootDir, self.rootUrl)
        return url
        
