from ocgis.interface.nc.dataset import NcDataset
import datetime
import ocgis
from collections import OrderedDict
import json
import webbrowser
import numpy as np
from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData, Column, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative.api import declarative_base
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.types import Integer, Float, String, DateTime
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import relationship, backref
from tempfile import NamedTemporaryFile, mkstemp
import os
import csv
from argparse import ArgumentParser


'''
Module provides functionality to generate JSON representations for dataset selections
on the CT interface.
'''

connstr = 'sqlite://'
engine = create_engine(connstr)
metadata = MetaData(bind=engine)
Base = declarative_base(metadata=metadata)
Session = sessionmaker(bind=engine)


def get_or_create(session,Model,**kwargs):
    try:
        obj = session.query(Model).filter_by(**kwargs).one()
    except NoResultFound:
        obj = Model(**kwargs)
        session.add(obj)
        session.commit()
    return(obj)


class Category(Base):
    __tablename__ = 'category'
    __table_args__ = (UniqueConstraint('name'),)
        
    cid = Column(Integer,primary_key=True)
    name = Column(String,nullable=False)
    
    
class Subcategory(Base):
    __tablename__ = 'subcategory'
    __table_args__ = (UniqueConstraint('name'),)
    
    sid = Column(Integer,primary_key=True)
    cid = Column(ForeignKey(Category.cid))
    name = Column(String,nullable=False)
    
    category = relationship(Category,backref='subcategory')
    
    
class Package(Base):
    __tablename__ = 'package'
    __table_args__ = (UniqueConstraint('name'),)
    
    pid = Column(Integer,primary_key=True)
    cid = Column(ForeignKey(Category.cid),nullable=False)
    name = Column(String,nullable=False)
    
    category = relationship(Category,backref='package',order_by='Package.name')
    
    
class Variable(Base):
    __tablename__ = 'variable'
    __table_args__ = (UniqueConstraint('name'),)
    
    vid = Column(Integer,primary_key=True)
    name = Column(String,nullable=False)
    long_name = Column(String,nullable=False)
    
    
class Dataset(Base):
    __tablename__ = 'dataset_name'
    
    did = Column(Integer,primary_key=True)
    sid = Column(ForeignKey(Subcategory.sid))
    vid = Column(ForeignKey(Variable.vid))
    pid = Column(ForeignKey(Package.pid))
    time_start = Column(DateTime,nullable=False)
    time_stop = Column(DateTime,nullable=False)
    time_calendar = Column(String,nullable=False)
    time_units = Column(String,nullable=False)
    
    variable = relationship(Variable,backref='dataset')
    subcategory = relationship(Subcategory,backref='dataset')
    package = relationship(Package,backref='dataset')
    
    @property
    def name(self):
        msg = '{0} ({1}-{2})'.format(self.variable.long_name,self.time_start.year,self.time_stop.year)
        return(msg)


class Uri(Base):
    __tablename__ = 'uri'
#    __table_args__ = (UniqueConstraint('value'),)
    
    uid = Column(Integer,primary_key=True)
    did = Column(ForeignKey(Dataset.did))
    value = Column(String,nullable=False)
    
    dataset = relationship(Dataset,backref='uri',order_by='Uri.value')
    

def get_or_create_dict(target,key,default=None):
    try:
        ret = target[key]
    except KeyError:
        if default is None:
            default = OrderedDict()
        target.update({key:default})
        ret = target[key]
    return(ret)


def write_json_from_csv(out_path,in_csv,debug=False):
    ## if we are debugging, we needs to search through local data folder
    if debug:
        ocgis.env.DIR_DATA = '/usr/local/climate_data'
    
    metadata.create_all()
    session = Session()
    
    with open(in_csv,'r') as f:
        reader = csv.DictReader(f,delimiter=';')
        for row in reader:
            if debug and row['Debug'] != '1':
                continue
            if row['Enable'] != '1':
                continue
            category = get_or_create(session,Category,name=row['Category'])
            subcategory = get_or_create(session,Subcategory,name=row['Subcategory'],cid=category.cid)
            if row['Package Name'] != '':
                package = get_or_create(session,Package,name=row['Package Name'],cid=category.cid)
            else:
                package = None
            if debug:
                if not row['Directory Path'].startswith('http'):
                    uri = row['Filename']
                else:
                    uri = row['Directory Path']
            else:
                uri = os.path.join(row['Directory Path'],row['Filename'])
            print('processing URI: {0}'.format(uri))
            if row['Calendar'] == '':
                t_calendar = None
            else:
                t_calendar = row['Calendar']
            if row['Units'] == '':
                t_units = None
            else:
                t_units = row['Units']
            rd = ocgis.RequestDataset(uri,row['Variable'],t_calendar=t_calendar,t_units=t_units)
            try:
                long_name = rd.ds.metadata['variables'][rd.variable]['attrs']['long_name']
            except KeyError:
                long_name = row['Long Name'].strip()
                assert(long_name != '')
            variable = get_or_create(session,Variable,name=rd.variable,
                                     long_name=long_name.title())
            time_start,time_stop = rd.ds.temporal.extent
            time_calendar,time_units = rd.ds.temporal.calendar,rd.ds.temporal.units
            dataset = Dataset(variable=variable,subcategory=subcategory,time_start=time_start,time_stop=time_stop,
                              package=package,time_calendar=time_calendar,time_units=time_units)
            uris = rd.uri
            if isinstance(uris,basestring):
                uris = [uris]
            db_uris = [get_or_create(session,Uri,value=uri,dataset=dataset) for uri in uris]
            session.add_all(db_uris)
    session.commit()       
    
    data = OrderedDict()
    for cat in session.query(Category).order_by(Category.name):
        dcat = get_or_create_dict(data,cat.name)
        ## write the subcategories of datasets first
        for subcat in cat.subcategory:
            dsubcat = get_or_create_dict(dcat,subcat.name)
            dsubcat['type'] = 'datasets'
            for dataset in subcat.dataset:
                dvariable = get_or_create_dict(dsubcat,dataset.name)
                dvariable['variable'] = [dataset.variable.name]
                dvariable['time_range'] = map(str,[dataset.time_start,dataset.time_stop])
                dvariable['uri'] = [[uri.value for uri in dataset.uri]]
                dvariable['t_calendar'] = [dataset.time_calendar]
                dvariable['t_units'] = [dataset.time_units]
        ## now write the data packages
        for package in cat.package:
            ## assume the time dimension is the same for all datasets
            time_range = [package.dataset[0].time_start,package.dataset[0].time_stop]
            package_name = '{0} ({1}-{2})'.format(package.name,time_range[0].year,time_range[1].year)
            dpackage = get_or_create_dict(dcat,package_name)
            dpackage['type'] = 'package'
            dpackage['time_range'] = map(str,time_range)
            dpackage['uri'] = [[uri.value for uri in dataset.uri] for dataset in package.dataset]
            dpackage['variable'] = [dataset.variable.name for dataset in package.dataset]
            dpackage['t_calendar'] = [dataset.time_calendar for dataset in package.dataset]
            dpackage['t_units'] = [dataset.time_units for dataset in package.dataset]
            ## assume the time dimension is the same for all datasets
            dpackage['time_range'] = map(str,[package.dataset[0].time_start,package.dataset[0].time_stop])
    
    ret = json.dumps(data)
    
    session.close()
    
    with open(out_path,'w') as f:
        f.write(ret)
        
    return(ret)    
    
def test_write_json_from_csv():
    out_path = mkstemp()[1]
    in_csv = '/home/local/WX/ben.koziol/links/ClimateTranslator/git/NCPP/contrib/ct_datasets.csv'
    
    write_json_from_csv(out_path,in_csv,debug=True)
    
    webbrowser.open(out_path)
    
def test_parse_prism_from_json():
    out_path = mkstemp()[1]
    in_csv = '/home/local/WX/ben.koziol/links/ClimateTranslator/git/NCPP/contrib/ct_datasets.csv'
    
    write_json_from_csv(out_path,in_csv,debug=True)
    with open(out_path,'r') as f:
        data = json.load(f)
    
    ref = data['Observational Datasets']['PRISM Package (1895-2013)']
    iter_tuple = [ref[key] for key in ['uri','variable','t_calendar','t_units']]
    ## this will hold output request datasets
    time_region = {'year':[2011]}
    dataset = []
    for uri,variable,t_calendar,t_units in zip(*iter_tuple):
        ## NOTE: we have to pass the time_range and time_region to each dataset
        rd = ocgis.RequestDataset(uri=uri,variable=variable,t_calendar=t_calendar,t_units=t_units,
                                  time_region=time_region)
        dataset.append(rd)
        
    ## do the normal operations
    ops = ocgis.OcgOperations(dataset=dataset,geom='state_boundaries',select_ugid=[25])
    ret = ops.execute()
    
def test_parse_from_json():
    out_path = mkstemp()[1]
    in_csv = '/home/local/WX/ben.koziol/links/ClimateTranslator/git/NCPP/contrib/ct_datasets.csv'
    write_json_from_csv(out_path,in_csv,debug=True)
    with open(out_path,'r') as f:
        data = json.load(f)
        
    ## category is selected
    category = data['Decadal Simulations']
    
    ## a time range and region are passed
    time_range = [datetime.datetime(2012,1,1),datetime.datetime(2012,12,31)]
    time_region = {'month':[6,7,8]}
    
    ## DATASETS SELECTED #######################################################
    
    sub = category['CanCM4 Decadal Datasets']
    ## this will give you the type of selection. 'datasets' or 'package'
    subtype = sub['type']
    ## a variable is selected
    info = sub['Surface Daily Maximum Relative Humidity (2011-2021)']
    ## NOTE: all values except time_range are now sequences to simplify the
    ## the RequestDataset creation. we can just do a loop regardless if it is a
    ## package or single dataset.
    iter_tuple = [info[key] for key in ['uri','variable','t_calendar','t_units']]
    ## this will hold output request datasets
    dataset = []
    for uri,variable,t_calendar,t_units in zip(*iter_tuple):
        ## NOTE: we have to pass the time_range and time_region to each dataset
        rd = ocgis.RequestDataset(uri=uri,variable=variable,t_calendar=t_calendar,t_units=t_units,
                                  time_range=time_range,time_region=time_region)
        dataset.append(rd)
        
    ## do the normal operations
    ops = ocgis.OcgOperations(dataset=dataset,geom='state_boundaries',select_ugid=[25])
    ret = ops.execute()
    
    ## PACKAGE SELECTED ########################################################
    
    ## there is nothing really different for packages except we don't go through
    ## the variable selection process.
    sub = category['CanCM4 Decadal Package (2011-2021)']
    ## NOTE: the |info| dictionary is replaced with the |sub| dictionary
    iter_tuple = [sub[key] for key in ['uri','variable','t_calendar','t_units']]
    dataset = []
    for uri,variable,t_calendar,t_units in zip(*iter_tuple):
        ## NOTE: we have to pass the time_range and time_region to each dataset
        rd = ocgis.RequestDataset(uri=uri,variable=variable,t_calendar=t_calendar,t_units=t_units,
                                  time_range=time_range,time_region=time_region)
        dataset.append(rd)
    ## do the normal operations
    ops = ocgis.OcgOperations(dataset=dataset,geom='state_boundaries',select_ugid=[25])
    ret = ops.execute()

    
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('out_path',help='Path to the output JSON file.')
    parser.add_argument('in_csv',help='Path to the input CSV file.')
    
    pargs = parser.parse_args()
    
    write_json_from_csv(pargs.out_path,pargs.in_csv)
    