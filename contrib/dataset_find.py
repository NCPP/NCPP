import re
import os
import netCDF4 as nc
import csv
import logging

logging.basicConfig(filename='_dc_info_.log',
                    filemode='w',
                    level=logging.INFO)

HEADDIR = '/data/ncpp'


class DataCategory(object):
    
    def __init__(self,expr,category,subcategory):
        self.expr = expr
        self.category = category
        self.subcategory = subcategory
        
    def __iter__(self):
        expr = re.compile(self.expr)
        for nc_path in self.iter_nc():
            reobj = re.match(expr,nc_path)
            if reobj is not None:
                ## try to get the parameter
                ds = nc.Dataset(nc_path,'r')
                try:
                    variable = ds.parameter
                except AttributeError:
                    variable = None
                finally:
                    ds.close()
                yld = {'Category':self.category,
                       'Subcategory':self.subcategory,
                       'Directory Path':os.path.split(nc_path)[0],
                       'Filename':os.path.split(nc_path)[1],
                       'Variable':variable}
                yield(yld)
            
    def iter_nc(self):
        ctr = 0
        for dirpath,dirnames,filenames in os.walk(HEADDIR,followlinks=True):
            for filename in filenames:
                if filename.endswith('.nc'):
                    yield(os.path.join(dirpath,filename))
                    ctr += 1
        if ctr == 0:
            logging.error(self.expr)


def get_categories():
    dcs = []
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/txx.*','QED-2013 Indices','Maurer02v2'))
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/txn.*','QED-2013 Indices','Maurer02v2'))
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/tnx.*','QED-2013 Indices','Maurer02v2'))
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/tnn.*','QED-2013 Indices','Maurer02v2'))
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/fd/.*/annual.*','QED-2013 Indices','Maurer02v2'))
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/r20mm/.*/annual.*','QED-2013 Indices','Maurer02v2'))
#    /data/ncpp/eval/maurer02v2/tasmax/p90/tasmaxap90a/annual/1971-2000/us48
    dcs.append(DataCategory('/data/ncpp/eval/maurer02v2/(tasmax|tasmin|pr)/p90/.*/annual.*','QED-2013 Indices','Maurer02v2'))
    
    with open('_dc_info_.csv','w') as f:
        writer = csv.DictWriter(f,['Category','Subcategory','Directory Path','Filename','Variable'])
        writer.writeheader()
        for dc in dcs:
            for row in dc:
                print row['Directory Path']
                writer.writerow(row)


def test_DataCategory():
    expr = '.*Maurer02.*(tasmax|tasmin)'
    category = 'Observational Data'
    subcategory = 'M Data'
    dc = DataCategory(expr,category,subcategory)
    for row in dc:
        print row
        
        
if __name__ == '__main__':
    get_categories()