# module containing NCPP utility functions
from ncpp.constants import MONTH_DICT

def get_class( kls ):
    """ Utility function to retrieve a Class object from its fully qualified name as a string.
        Example: ClimateIndexesJob  = get_class('ncpp.models.climate_indexes.ClimateIndexesJob')."""
    
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def get_full_class_name(o):
    """ Utility function to retrieve the full class name of an instance.
        Example: 'ncpp.models.climate_indexes.ClimateIndexesJob' = get_full_class_name(instance)."""
        
    return o.__module__ + "." + o.__class__.__name__

def str2bool(v):
    """Convert a string to a boolean value."""
    return v.lower() in ("yes", "true", "t", "1")

def hasText(value):
    """Checks wether a string is not null."""
    return value is not None and str(value).strip() != ""

def get_month_string(months):
    """Converts a list of integers into a comma-separated list of months."""
    
    list = []
    for month in months:
        list.append(MONTH_DICT[int(month)])
    return ",".join(list)