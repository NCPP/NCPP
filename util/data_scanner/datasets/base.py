import abc
from ocgis.api.request.nc import NcRequestDataset
from NCPP.util.data_scanner import db
import os


UNITS_CELSIUS = {'standard_name':'C','long_name':'Celsius'}
UNITS_MM_PER_DAY = {'standard_name':'mm/d','long_name':'Millimeters per Day'}

VAR_AIR_TEMPERATURE = dict(standard_name='air_temperature',long_name='Air Temperature',description='Fill it in!')
VAR_AIR_TEMPERATURE_MAX = dict(standard_name='air_temperature',long_name='Maximum Air Temperature',description='Fill it in!')
VAR_AIR_TEMPERATURE_MIN = dict(standard_name='air_temperature',long_name='Minimum Air Temperature',description='Fill it in!')
VAR_PRECIPITATION = dict(standard_name='convective_precipitation_rate',long_name='Daily Precipitation Rate',description='Fill it in!')


class AbstractHarvestDataset(object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractproperty
    def clean_units(self): dict
    @abc.abstractproperty
    def clean_variable(self): dict
    @abc.abstractproperty
    def dataset(self): dict
    @abc.abstractproperty
    def dataset_category(self): dict
    spatial_crs = None
    time_calendar = None
    time_units = None
    @abc.abstractproperty
    def type(self): '"index" or "raw"'
    @abc.abstractproperty
    def uri(self): [str]
    variables = None
    
    def get_field(self,variable=None):
        variable = variable or self.variables[0]
        field = NcRequestDataset(uri=self.uri,variable=variable,t_calendar=self.time_calendar).get()
        return(field)
    
    def insert(self,session):
        container = db.Container(session,self)
        for idx,variable_name in enumerate(self.variables):
            clean_units = db.get_or_create(session,db.CleanUnits,**self.clean_units[idx])
            clean_variable = db.get_or_create(session,db.CleanVariable,**self.clean_variable[idx])
            rv = db.Field(self,container,variable_name,clean_units,clean_variable)
            session.add(rv)
        session.commit()
        
        
class AbstractFolderHarvestDataset(AbstractHarvestDataset):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractproperty
    def folder(self): str
    
    @abc.abstractproperty
    def _uri(self): str
    
    @property
    def uri(self):
        return([os.path.join(self.folder,self._uri)])
    
    
class AbstractDataPackage(object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractproperty
    def description(self): str
    @abc.abstractproperty
    def fields(self): [AbstractHarvestDataset]
    @abc.abstractproperty
    def name(self): str

    def insert(self,session):
        dc = db.get_or_create(session,db.DatasetCategory,**self.dataset_category)
        qq = session.query(db.Field).join(db.Container).join(db.Uri)
        uris = []
        variables = []
        for f in self.fields:
            uris += f().uri
            variables += f.variables
        qq = qq.filter(db.Uri.value.in_(uris))
        qq = qq.filter(db.Field.name.in_(variables))
        assert(qq.count() == len(self.fields))
        dp = db.DataPackage(field=qq.all(),name=self.name,description=self.description,dataset_category=dc)
        session.add(dp)
        session.commit()
