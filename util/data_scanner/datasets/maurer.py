import base
import abc


class AbstractMaurerDataset(base.AbstractFolderHarvestDataset):
    __metaclass__ = abc.ABCMeta
    folder = '/data/maurer/concatenated'
    dataset_category = dict(name='Gridded Observational',description='Fill it in!')
    dataset = dict(name='Maurer 2010',description='Recent Maurer Dataset')
    type = 'variable'
    

class MaurerTas(AbstractMaurerDataset):
    _uri = 'Maurer02new_OBS_tas_daily.1971-2000.nc'
    variables = ['tas']
    clean_units = [base.UNITS_CELSIUS]
    clean_variable = [base.VAR_AIR_TEMPERATURE]


class MaurerTasmax(AbstractMaurerDataset):
    _uri = 'Maurer02new_OBS_tasmax_daily.1971-2000.nc'
    variables = ['tasmax']
    clean_units = [base.UNITS_CELSIUS]
    clean_variable = [base.VAR_AIR_TEMPERATURE_MAX]
    
    
class MaurerTasmin(AbstractMaurerDataset):
    _uri = 'Maurer02new_OBS_tasmin_daily.1971-2000.nc'
    variables = ['tasmin']
    clean_units = [base.UNITS_CELSIUS]
    clean_variable = [base.VAR_AIR_TEMPERATURE_MIN]
    
    
class MaurerPrecip(AbstractMaurerDataset):
    _uri = 'Maurer02new_OBS_pr_daily.1971-2000.nc'
    variables = ['pr']
    clean_units = [base.UNITS_MM_PER_DAY]
    clean_variable = [base.VAR_PRECIPITATION]
