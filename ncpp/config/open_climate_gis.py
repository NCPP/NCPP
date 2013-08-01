# module containing configuration classes for Open Climate GIS application
from ncpp.constants import CONFIG_FILEPATH, GEOMETRIES_FILEPATH, DATASETS_FILEPATH, CALCULATIONS_FILEPATH, NO_VALUE_OPTION
import json
import os, ConfigParser

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

class Calc(object):
    """Class holding the specification for a single OCGIS calculation."""
    
    def __init__(self, func, name, order, description, kwds={}):
        self.func = func
        self.name = name
        self.order = order
        self.description = description
        self.kwds = kwds
        
    def _print(self):
        print "Calculation func=%s name=%s order=%s" % (self.func, self.name, self.order)
        print "\tdescription=%s" % self.description
        print "\tkeywords=%s" % self.kwds

class Calculations(object):
    """Class holding OCGIS calculation choices."""
    
    def __init__(self):
        parser = ConfigParser.RawConfigParser()
        # must set following line explicitely to preserve the case of configuration keys
        parser.optionxform = str 
        try:
            print 'parsing %s' % CALCULATIONS_FILEPATH
            parser.read( CALCULATIONS_FILEPATH )
            self._parse(parser)
            self._print()
        except Exception as e:
            print "Configuration file %s not found" % CALCULATIONS_FILEPATH
            raise e
        
    def _parse(self, parser):
        
        self.calcs = {}
        
        # loop over sections
        for section in parser.sections():
            
            # parse section header
            # example: ['6', 'threshold', 'Threshold', 'desc']
            parts = section.split("|")
            order = int(parts[0])
            func = parts[1]
            name = parts[2]
            description = parts[3]
            
            # parse section options
            kwds = {}
            for option in parser.options(section):
                kwds[option] = parser.get(section, option)
            
            # store dictionary of calculations
            self.calcs[ func ] = Calc(func, name, order, description, kwds=kwds) 
            
    def getChoices(self):
        choices = []
        for key in sorted( self.calcs, key=lambda key: self.calcs[key].order ):
            calc = self.calcs[key]
            choices.append( (calc.func, calc.name) )
        return choices
    
    def getCalc(self, key):
        return self.calcs[key]
    
    def _print(self):
        for key in sorted( self.calcs, key=lambda key: self.calcs[key] ):
            self.calcs[key]._print()
        
ocgisCalculations = Calculations()   

class Geometries(object):
    """Class holding OCGIS geometries."""
    
    def __init__(self, filepath):
        
        # read geometries from JSON file
        try:
            with open(filepath,'r') as f:
                self.geometries = json.load(f)
        except Exception as e:
            print "Error reading geometry file: %s" % GEOMETRIES_FILEPATH
            raise e
        
    def getCategories(self):
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

class Datasets(object):
    """Class holding OCGIS dataset choices."""
    
    def __init__(self, filepath):
        
        # read datasets from JSON file
        try:
            with open(filepath,'r') as f:
                self.datasets = json.load(f)
        except Exception as e:
            print "Error reading datasets file: %s" % DATASETS_FILEPATH
            raise e
        
    def getDatasetCategories(self):
        # no option selected
        tuples = [ NO_VALUE_OPTION ]
        # read all keys from JSON file
        for category in sorted( self.datasets.keys() ):
            tuples.append( (category, category) )
        return tuples
    
ocgisDatasets = Datasets(DATASETS_FILEPATH)  

