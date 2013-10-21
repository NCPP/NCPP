import base
import abc
import os


class AbstractMaurerDataset(base.AbstractHarvestDataset):
    __metaclass__ = abc.ABCMeta
    folder = '/data/maurer/concatenated'
    dataset_category = dict(name='Gridded Observational',description='Fill it in!')
    dataset = dict(name='Maurer 2010',description='Recent Maurer Dataset')
    type = 'variable'
    
    @abc.abstractproperty
    def _uri(self): str
    
    @property
    def uri(self):
        return(os.path.join(self.folder,self._uri))
    

class MaurerTas(AbstractMaurerDataset):
    _uri = 'Maurer02new_OBS_tas_daily.1971-2000.nc'
    variables = ['tas']
    clean_units = base.UNITS_CELSIUS
    clean_variable = [base.VAR_AIR_TEMPERATURE]


class MaurerTasmax(AbstractMaurerDataset):
    variables = ['tasmax']
    clean_units = base.UNITS_CELSIUS
    clean_variable = [base.VAR_AIR_TEMPERATURE_MAX]