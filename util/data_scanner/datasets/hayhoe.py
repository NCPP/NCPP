import base
import abc


class AbstractHayhoeGFDLDataset(base.AbstractFolderHarvestDataset):
    __metaclass__ = abc.ABCMeta
    folder = '/data/downscaled/arrm'
    dataset_category = dict(name='Gridded Downscaled',description='<tdk>')
    dataset = dict(name='Hayhoe ARRM-GFDL',description='Hayhoe ARRM-GFDL')
    type = 'variable'
    time_calendar = '365_day'
    
    
class HayhoeGFDLTasmin(AbstractHayhoeGFDLDataset):
    _uri = 'arrm_gfdl_2.1.20c3m.tasmin.NAm.1971-2000.nc'
    variables = ['tasmin']
    clean_variable = [base.VAR_AIR_TEMPERATURE_MIN]
    clean_units = [base.UNITS_CELSIUS]


class HayhoeGFDLTasmax(AbstractHayhoeGFDLDataset):
    _uri = 'arrm_gfdl_2.1.20c3m.tasmax.NAm.1971-2000.nc'
    variables = ['tasmax']
    clean_variable = [base.VAR_AIR_TEMPERATURE_MAX]
    clean_units = [base.UNITS_CELSIUS]
    
    
class HayhoeGFDLPr(AbstractHayhoeGFDLDataset):
    _uri = 'arrm_gfdl_2.1.20c3m.pr.NAm.1971-2000.nc'
    variables = ['pr']
    clean_variable = [base.VAR_PRECIPITATION]
    clean_units = [base.UNITS_MM_PER_DAY]
