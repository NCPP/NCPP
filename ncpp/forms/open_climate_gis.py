from django.forms import Form, CharField, ChoiceField

from ncpp.models.open_climate_gis import ocgisChoices


class OpenClimateGisForm1(Form):
    '''Form to select the dataset.'''
    
    dataset = ChoiceField(choices=ocgisChoices('datasets').items(), required=True)
    
class OpenClimateGisForm2(Form):
    '''Form to select the variable.'''
    
    variable = ChoiceField(choices=ocgisChoices('variables').items(), required=True)
    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass