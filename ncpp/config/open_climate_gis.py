# module containing configuration classes for Open Climate GIS application
from ncpp.constants import CONFIG_FILEPATH, GEOMETRIES_FILEPATH, DATASETS_FILEPATH, NO_VALUE_OPTION
import json

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

ocgisDatasets = Datasets(DATASETS_FILEPATH)  

