from django.forms import Form, CharField, ChoiceField

from ncpp.models.open_climate_gis import DATASET_CHOICES, VARIABLE_CHOICES

class OpenClimateGisForm1(Form):
    '''Form to select the dataset.'''
    
    dataset = ChoiceField(choices=DATASET_CHOICES.items(), required=True)
    
class OpenClimateGisForm2(Form):
    '''Form to select the dataset.'''
    
    variable = ChoiceField(choices=VARIABLE_CHOICES.items(), required=True)
    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass