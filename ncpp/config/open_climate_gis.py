# module containing configuration classes for Open Climate GIS application
from ncpp.constants import CONFIG_FILEPATH, GEOMETRIES_FILEPATH, DATASETS_FILEPATH, CALCULATIONS_FILEPATH, NO_VALUE_OPTION
import json
import os, ConfigParser
import abc

class ConfigBase(object):
    """Abstract Base Class for Climate Translator configuration."""
    
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def getChoices(self):
        """Returns a list of choices for selection in the web interface.
           Each tuple has the form (choice value, choice label).""" 
        return []
    

#ocgisConfig = ConfigParser.RawConfigParser(dict_type=OrderedDict)
ocgisConfig = ConfigParser.RawConfigParser()
# must set following line explicitely to preserve the case of configuration keys
ocgisConfig.optionxform = str 
try:
    ocgisConfig.read( os.path.expanduser(CONFIG_FILEPATH) )
except Exception as e:
    print "Configuration file %s not found" % CONFIG_FILEPATH
    raise e

class Config():
    '''Class holding keys into configuration file.'''
    
    DEFAULT = 'default'
    VARIABLE = 'variable'
    OUTPUT_FORMAT = 'output_format'
    CALCULATION_GROUP = 'calculation_group'
    SPATIAL_OPERATION = 'spatial_operation'
    
    
def ocgisChoices(section, nochoice=False):
    choices = {}
    # add empty choice 
    if nochoice:
        choices[ NO_VALUE_OPTION[0] ] = NO_VALUE_OPTION[1]
    choices.update( dict( ocgisConfig.items(section) ) )
    return choices

class Calculations(ConfigBase):
    """Class holding Climate Translator choices for calculations."""
    
    def __init__(self):
        # read calculations from JSON file
        try:
            with open(CALCULATIONS_FILEPATH,'r') as f:
                self.calcs = json.load(f)
        except Exception as e:
            print "Error reading calculations file: %s" % CALCULATIONS_FILEPATH
            raise e
            
    def getChoices(self):
        
        # no option selected
        choices = [ NO_VALUE_OPTION ]
        # then all US counties
        for key in sorted( self.calcs, key=lambda key: self.calcs[key]["order"] ):
            calc = self.calcs[key]
            choices.append( (key, calc["name"]) )
        return choices
    
    def getCalc(self, key):
        return self.calcs[key]
    
    def _print(self):
        for key in sorted( self.calcs, key=lambda key: self.calcs[key]["order"] ):
            print "calculation=%s" % self.calcs[key]
        
ocgisCalculations = Calculations()   

class Geometries(ConfigBase):
    """Class holding Climate Translator supported geometries."""
    
    def __init__(self, filepath):
        
        # read geometries from JSON file
        try:
            with open(filepath,'r') as f:
                self.geometries = json.load(f)
        except Exception as e:
            print "Error reading geometry file: %s" % GEOMETRIES_FILEPATH
            raise e
        
    def getChoices(self):
        # no option selected
        tuples = [ NO_VALUE_OPTION ]
        # first option is US States
        tuples.append( ('US State Boundaries', 'US State Boundaries') )
        # then all US counties
        for category in sorted( self.geometries.keys() ):
            if category != 'US State Boundaries':
                tuples.append( (category, category) )
        return tuples
    
    def getGeometries(self, type):
        
        tuples = []
        for k,v in self.geometries[type]['geometries'].items():
            #tuples.append( (int(v), k) )
            tuples.append( (k,k) )
        return sorted(tuples, key=lambda t: t[1])
    
    def getGuid(self, category, geometry):
        return self.geometries[category]['geometries'][geometry]
    
    def getCategoryKey(self, category):
        return self.geometries[category]['key']

ocgisGeometries = Geometries(GEOMETRIES_FILEPATH)     

class Datasets(ConfigBase):
    """Class holding Climate Translator dataset choices."""
    
    def __init__(self, filepath):
        
        # read datasets from JSON file
        try:
            with open(filepath,'r') as f:
                self.datasets = json.load(f)
        except Exception as e:
            print "Error reading datasets file: %s" % DATASETS_FILEPATH
            raise e
        
    def getChoices(self):
        # no option selected
        tuples = [ NO_VALUE_OPTION ]
        # read all keys from JSON file
        for category in sorted( self.datasets.keys() ):
            tuples.append( (category, category) )
        return tuples
    
ocgisDatasets = Datasets(DATASETS_FILEPATH)  

