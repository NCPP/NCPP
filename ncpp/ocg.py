import time
import os
from shutil import rmtree
from ncpp.utils import hasText
import re

SLEEP_SECONDS = 1
HEADERS_NOCALC = ['did','ugid','gid','time','year','month','day','variable','value']
HEADERS_CALC = ['did','ugid','gid','year','month','day','variable','calc_name','value']

class OCG(object):
    """Adapter class that invokes the OCGIS library."""
    
    def __init__(self, datasets, geometries, calculations, rootDir, rootUrl, debug=False):
        # object holding datasets
        self.ocgisDatasets = datasets
        # object holding geometries
        self.ocgisGeometries = geometries
        # object holding calculations
        self.ocgisCalculations = calculations
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
        # retrieve dataset URIs, variable from configuration JSON data
        jsonObject = self.ocgisDatasets.datasets[openClimateGisJob.dataset_category][openClimateGisJob.dataset]     
        if jsonObject['type'] == 'datasets': 
            # must sub-select data structure by variable
            jsonData =jsonObject[openClimateGisJob.variable]
        elif jsonObject['type'] == 'package':
            jsonData = jsonObject
        args['uri'] = jsonData['uri']
        args['variable'] = jsonData["variable"]
        args['t_calendar'] = jsonData["t_calendar"]
        args['t_units'] = jsonData["t_units"]
                    
        # class ocgis.OcgOperations(dataset=None, spatial_operation='intersects', geom=None, 
        #                           aggregate=False, calc=None, calc_grouping=None, calc_raw=False, 
        #                           abstraction='polygon', snippet=False, backend='ocg', prefix=None, 
        #                           output_format='numpy', agg_selection=False, select_ugid=None, 
        #                           vector_wrap=True, allow_empty=False, dir_output=None, slice=None, 
        #                           file_only=False, headers=None)
        args['geom'] = None
        args['select_ugid'] = None
        if hasText(openClimateGisJob.geometry):
            args['geom'] = self.ocgisGeometries.getCategoryKey( openClimateGisJob.geometry )
            args['select_ugid'] = []
            # must transform back from string to list of integers
            for geom in openClimateGisJob.geometry_id.split(","):
                args['select_ugid'].append( self.ocgisGeometries.getGuid(openClimateGisJob.geometry, str(geom)))
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
                years = openClimateGisJob.timeregion_year.replace(" ","")
                if re.match('^\d{4}-\d{4}', years):
                    year1 = int(years[0:4])
                    year2 = int(years[5:9])
                    args['time_region']['year'] = range(year1, year2+1)
                else:
                    for i in map(int, openClimateGisJob.timeregion_year.split(",")):
                        args['time_region']['year'].append(i)
        
        args['calc'] = None
        if hasText(openClimateGisJob.calc) and openClimateGisJob.calc.lower() != 'none':
            calc = self.ocgisCalculations.getCalc(str(openClimateGisJob.calc))
            args['calc'] = [ {'func':str(calc["func"]), 'name':str(calc["name"])} ] 
            args['calc'][0]['kwds'] = {}
            # loop over keywords in order
            if "keywords" in calc:
                for i, keyword in enumerate(calc["keywords"]):
                    if i==0:
                        val = openClimateGisJob.par1
                    elif i==1:
                        val = openClimateGisJob.par2
                    elif i==2:
                        val = openClimateGisJob.par3
                    if keyword["type"] == "float":
                        val = float(val)
                    elif keyword["type"] == "string":
                        val = str(val).lower()
                    args['calc'][0]['kwds'][str(keyword[u'name'])] = val 
            args['headers'] = HEADERS_CALC
        else:
            args['headers'] = HEADERS_NOCALC
            
        args['calc_raw'] = openClimateGisJob.calc_raw
        if hasText(openClimateGisJob.calc_group):
            args['calc_grouping'] = map(str, openClimateGisJob.calc_group.split(","))
        else:
            args['calc_grouping'] = None
        
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
            # remove existing directory, generated by previous installation
            if os.path.exists(dir_output):
                rmtree(dir_output)
            # generate empty directory
            os.makedirs(dir_output)             
                                    
            # build up the list of request datasets
            dataset = []
            iter_tuple = [args[key] for key in ['uri', 'variable', 't_calendar', 't_units']]
            time_range=args['time_range']
            time_region=args['time_region']
            for uri,variable,t_calendar,t_units in zip(*iter_tuple):
                rd = ocgis.RequestDataset(uri=uri,variable=variable,t_calendar=t_calendar,t_units=t_units,
                                  time_range=time_range,time_region=time_region)
                dataset.append(rd)

            ## construct the operations call
            ops = ocgis.OcgOperations(dataset=dataset, 
                                      geom=args['geom'],
                                      select_ugid=args['select_ugid'],
                                      aggregate=args['aggregate'], 
                                      spatial_operation=args['spatial_operation'], 
                                      calc=args['calc'], 
                                      calc_grouping=args['calc_grouping'],
                                      calc_raw=args['calc_raw'],
                                      prefix=args['prefix'],
                                      output_format=args['output_format'], 
                                      dir_output=dir_output,
                                      headers=args['headers'])

            # execute the operation
            # 'path' points to the top-level folder containing the output data
            path = ops.execute()
            # 'download_path' points to single file for user to download
            download_path = ocgis.format_return(path, ops, with_auxiliary_files=args['with_auxiliary_files'])

        # return ouput
        url = download_path.replace(self.rootDir, self.rootUrl)
        return url
        
