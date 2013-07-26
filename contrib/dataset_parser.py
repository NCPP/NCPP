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
    time_start = Column(DateTime,nullable=False)
    time_stop = Column(DateTime,nullable=False)
    
    variable = relationship(Variable,backref='dataset')
    subcategory = relationship(Subcategory,backref='dataset')


class Uri(Base):
    __tablename__ = 'uri'
    __table_args__ = (UniqueConstraint('value'),)
    
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
        target[key] = default
        ret = target[key]
    return(ret)


def write_json_from_csv(out_path,in_csv):
    metadata.create_all()
    session = Session()
    
    with open(in_csv,'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = get_or_create(session,Category,name=row['Category'])
            subcategory = get_or_create(session,Subcategory,name=row['Subcategory'],cid=category.cid)
            if row['Dataset Group'] != '':
                raise(NotImplementedError)
#            uri = os.path.join(row['Directory Path'],row['Filename'])
            uri = os.path.join('/usr/local/climate_data/CanCM4',row['Filename'])
            rd = ocgis.RequestDataset(uri,row['Variable'])
            variable = get_or_create(session,Variable,name=rd.variable,long_name=rd.ds.metadata['variables'][rd.variable]['attrs']['long_name'])
            time_start,time_stop = rd.ds.temporal.extent
            dataset = Dataset(variable=variable,subcategory=subcategory,time_start=time_start,time_stop=time_stop)
            uris = rd.uri
            if isinstance(uris,basestring):
                uris = [uris]
            db_uris = [get_or_create(session,Uri,value=uri,dataset=dataset) for uri in uris]
            session.add_all(db_uris)
    session.commit()       
    
    data = OrderedDict()
    for cat in session.query(Category).order_by(Category.name):
        dcat = get_or_create_dict(data,cat.name)
        for subcat in cat.subcategory:
            dsubcat = get_or_create_dict(dcat,subcat.name)
            for dataset in subcat.dataset:
                dvariable = get_or_create_dict(dsubcat,dataset.variable.long_name)
                dvariable['variable'] = dataset.variable.name
                dvariable['time_range'] = map(str,[dataset.time_start,dataset.time_stop])
                dvariable['uri'] = [uri.value for uri in dataset.uri]
                
    ret = json.dumps(data)
    
    session.close()
    
    with open(out_path,'w') as f:
        f.write(ret)
        
    return(ret)    
    
def test_write_json_for_folder():
    out_path = mkstemp()[1]
    in_csv = '/home/local/WX/ben.koziol/Downloads/ClimateTranslator Datasets - Sheet1.csv'
    
    write_json_from_csv(out_path,in_csv)
    
    webbrowser.open(out_path)


def test():
    metadata.create_all()
    
    ocgis.env.DIR_DATA = '/usr/local/climate_data/CanCM4'
    
    session = Session()
    category = Category(name='Simulations')
    subcategory = Subcategory(name='CanCM4',category=category)
    
    rd1 = ocgis.RequestDataset('rhs_day_CanCM4_decadal2010_r2i1p1_20110101-20201231.nc',
                              'rhs')
    rd2 = ocgis.RequestDataset(['tasmax_day_CanCM4_decadal2000_r2i1p1_20010101-20101231.nc',
                                'tasmax_day_CanCM4_decadal2010_r2i1p1_20110101-20201231.nc'],
                               'tasmax')
    rds = [rd1,rd2]
    
    for rd in rds:
        variable = Variable(name=rd.variable,
                            long_name=rd.ds.metadata['variables'][rd.variable]['attrs']['long_name'])
        time_start,time_stop = rd.ds.temporal.extent
        dataset = Dataset(variable=variable,subcategory=subcategory,time_start=time_start,time_stop=time_stop)
        uris = rd.uri
        if isinstance(uris,basestring):
            uris = [uris]
        db_uris = [get_or_create(session,Uri,value=uri,dataset=dataset) for uri in uris]
        session.add_all(db_uris)
    
    session.commit()

    data = OrderedDict()
    for cat in session.query(Category).order_by(Category.name):
        dcat = get_or_create_dict(data,cat.name)
        for subcat in cat.subcategory:
            dsubcat = get_or_create_dict(dcat,subcat.name)
            for dataset in subcat.dataset:
                dvariable = get_or_create_dict(dsubcat,dataset.variable.long_name)
                dvariable['variable'] = dataset.variable.name
                dvariable['time_range'] = map(str,[dataset.time_start,dataset.time_stop])
                dvariable['uri'] = [uri.value for uri in dataset.uri]
                
    ret = json.dumps(data)
    
    session.close()
