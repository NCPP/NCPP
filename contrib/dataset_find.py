import re
import os
import netCDF4 as nc
import csv
import logging

logging.basicConfig(filename='_dc_info_.log',
                    filemode='w',
                    level=logging.INFO)

HEADDIRS = ['/data/ncpp','/data/downscaled','/data/staging/jvigh']


def iter_nc():
    for headdir in HEADDIRS:
        for dirpath,dirnames,filenames in os.walk(headdir,followlinks=True):
            for filename in filenames:
                if filename.endswith('.nc'):
                    yield(os.path.join(dirpath,filename))
            

class NoMatch(Exception):
    pass


class DataCategory(object):
    
    def __init__(self,expr,category,subcategory,add_period=False):
        self.expr = re.compile(expr)
        self.expr_period = re.compile('.*_(monthly|annual|seasonal)_.*')
        self.category = category
        self.subcategory = subcategory
        self.add_period = add_period
        self.count = 0
        
    def get(self,path):
        reobj = re.match(self.expr,path.lower())
        if reobj is None:
            raise(NoMatch)
        else:
            ## try to get the parameter
            ds = nc.Dataset(path,'r')
            try:
                variable = ds.parameter
            except AttributeError:
                try:
                    filename = os.path.splitext(os.path.split(path)[1])[0]
                    variable = ds.variables[filename]
                    variable = filename
                except KeyError:
                    variable = None
            finally:
                ds.close()
                
            if self.add_period:
                match = re.match(self.expr,path.lower())
                period = match.group(0)[0].title()
                subcat = '{0} {1}'.format(self.subcategory,period)
            else:
                subcat = self.subcategory
                
            ret = {'Category':self.category,
                   'Subcategory':subcat,
                   'Directory Path':os.path.split(path)[0],
                   'Filename':os.path.split(path)[1],
                   'Variable':variable}
            self.count += 1
            return(ret)


def get_categories():
    dcs = []
    dcs.append(DataCategory('/data/staging/jvigh/climatology_txx.*','QED-2013 Indices','Maurer02v2 TXx',add_period=True))
    dcs.append(DataCategory('/data/staging/jvigh/climatology_txn.*','QED-2013 Indices','Maurer02v2 TXn',add_period=True))
    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnx.*','QED-2013 Indices','Maurer02v2 TNx',add_period=True))
    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnn.*','QED-2013 Indices','Maurer02v2 TNn',add_period=True))
    dcs.append(DataCategory('/data/staging/jvigh/climatology_fd/.*','QED-2013 Indices','Maurer02v2 FD',add_period=True))
    dcs.append(DataCategory('/data/staging/jvigh/climatology_r20mm/.*','QED-2013 Indices','Maurer02v2 R20mm',add_period=True))
    dcs.append(DataCategory('/data/stagin/jvigh/climatology_(tasmax|tasmin|pr).*p90.*','QED-2013 Indices','Maurer02v2',add_period=True))
    dcs.append(DataCategory('/data/downscaled/bcca/bcca_gfdl_cm2_1.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-GFDL'))
    dcs.append(DataCategory('/data/downscaled/bcca/bcca_cccma_cgcm3_1.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-CCCMA-CGCM'))
    dcs.append(DataCategory('/data/downscaled/arrm/arrm_cgcm3.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-CGCM (Hayhoe)'))
    dcs.append(DataCategory('/data/downscaled/arrm/arrm_gfdl.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-GFDL (Hayhoe)'))
    
    with open('_dc_info_.csv','w') as f:
        writer = csv.DictWriter(f,['Category','Subcategory','Directory Path','Filename','Variable'])
        writer.writeheader()
        for nc_path in iter_nc():
            for dc in dcs:
                try:
                    row = dc.get(nc_path)
                    print row['Directory Path']
                    writer.writerow(row)
                except NoMatch:
                    continue
    
    for dc in dcs:
        if dc.count == 0:
            logging.error('no datasets found for expr: {0}'.format(dc.expr))


def test_DataCategory():
    expr = '.*Maurer02.*(tasmax|tasmin)'
    category = 'Observational Data'
    subcategory = 'M Data'
    dc = DataCategory(expr,category,subcategory)
    for row in dc:
        print row
        
def test_group():
    target = 'maurer02v2_median_txxmmedm_january_1971-2000.nc'
    expr = '.*_(january|february|march|april|may|june|july|august|september|october|november|december|annual)_.*'
    match = re.match(expr,target)
    assert(match.group(0)[0].title() == 'January')
        
if __name__ == '__main__':
    get_categories()