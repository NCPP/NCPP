import re
import os
import netCDF4 as nc
import csv
import logging

logging.basicConfig(filename='log_df_info.log',
                    filemode='w',
                    level=logging.INFO)

HEADDIRS = [
#            '/data/downscaled',
#            '/data/staging/jvigh',
            '/data/ncpp/eval'
            ]


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
        self._raw_expr = expr
        self.expr = re.compile(expr)
        self.expr_period = re.compile('.*_(monthly|annual|seasonal)_')
        self.category = category
        self.subcategory = subcategory
        self.add_period = False
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
                match = re.search(self.expr,path.lower())
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
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_txx.*','QED-2013 Indices','Maurer02v2 TXx',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_txn.*','QED-2013 Indices','Maurer02v2 TXn',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnx.*','QED-2013 Indices','Maurer02v2 TNx',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnn.*','QED-2013 Indices','Maurer02v2 TNn',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_fd.*','QED-2013 Indices','Maurer02v2 FD',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_r20mm.*','QED-2013 Indices','Maurer02v2 R20mm',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tasmax.*p90.*','QED-2013 Indices','Maurer02v2 TasMax p90',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tasmin.*p90.*','QED-2013 Indices','Maurer02v2 TasMin p90',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_pr.*p90.*','QED-2013 Indices','Maurer02v2 Pr p90',add_period=True))
#    dcs.append(DataCategory('/data/downscaled/bcca/bcca_gfdl_.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-GFDL'))
#    dcs.append(DataCategory('/data/downscaled/bcca/bcca_cccma_.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-CCCMA-CGCM'))
#    dcs.append(DataCategory('/data/downscaled/arrm/arrm_cgcm3_.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-CGCM (Hayhoe)'))
#    dcs.append(DataCategory('/data/downscaled/arrm/arrm_gfdl_.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-GFDL (Hayhoe)'))
    dcs.append(DataCategory('.*maurer02v2/bio.*\.nc','QED-2013 Indices','Bioclim Indices (Maurer02v2)'))
    dcs.append(DataCategory('.*bcca_gfdl_cm2_1/bio.*\.nc','QED-2013 Indices','Bioclim Indices (BCCA-GFDL-CM-2.1)'))
    dcs.append(DataCategory('.*bcca_cccma.*/bio.*\.nc','QED-2013 Indices','Bioclim Indices (BCCA-CCCMA-CGCM-3.1)'))
    dcs.append(DataCategory('.*arrm_cgcm3_t47/bio.*\.nc','QED-2013 Indices','Bioclim Indices (ARMM-CGCM-3-t47)'))
    dcs.append(DataCategory('.*arrm_cgcm3_t63/bio.*\.nc','QED-2013 Indices','Bioclim Indices (ARMM-CGCM-3-t63)'))
    dcs.append(DataCategory('.*arrm_gfdl_2\.1/bio.*\.nc','QED-2013 Indices','Bioclim Indices (ARMM-GFDL-2.1)'))
    
    with open('df_info.csv','w') as f:
        writer = csv.DictWriter(f,['Category','Subcategory','Directory Path','Filename','Variable'])
        writer.writeheader()#    dcs.append(DataCategory('/data/staging/jvigh/climatology_txx.*','QED-2013 Indices','Maurer02v2 TXx',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_txn.*','QED-2013 Indices','Maurer02v2 TXn',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnx.*','QED-2013 Indices','Maurer02v2 TNx',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tnn.*','QED-2013 Indices','Maurer02v2 TNn',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_fd.*','QED-2013 Indices','Maurer02v2 FD',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_r20mm.*','QED-2013 Indices','Maurer02v2 R20mm',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tasmax.*p90.*','QED-2013 Indices','Maurer02v2 TasMax p90',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_tasmin.*p90.*','QED-2013 Indices','Maurer02v2 TasMin p90',add_period=True))
#    dcs.append(DataCategory('/data/staging/jvigh/climatology_pr.*p90.*','QED-2013 Indices','Maurer02v2 Pr p90',add_period=True))
#    dcs.append(DataCategory('/data/downscaled/bcca/bcca_gfdl_.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-GFDL'))
#    dcs.append(DataCategory('/data/downscaled/bcca/bcca_cccma_.*(tasmax|tasmin|pr).*','Downscaled Datasets','BCCA-CCCMA-CGCM'))
#    dcs.append(DataCategory('/data/downscaled/arrm/arrm_cgcm3_.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-CGCM (Hayhoe)'))
#    dcs.append(DataCategory('/data/downscaled/arrm/arrm_gfdl_.*(tasmax|tasmin|pr).*','Downscaled Datasets','ARRM-GFDL (Hayhoe)'))
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
            logging.error('no datasets found for expr: {0}'.format(dc._raw_expr))


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