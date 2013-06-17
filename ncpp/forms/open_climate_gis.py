from django.forms import Form, CharField, ChoiceField, BooleanField

from ncpp.models.open_climate_gis import ocgisChoices, Config



class OpenClimateGisForm1(Form):
    '''Form that backs up the first selection page. 
       The argument passed to ocgisChoices must correspond to a valid key in the file OCGIS configuration file.'''
    
    dataset = ChoiceField(choices=ocgisChoices(Config.DATASET).items(), required=True)
    variable = ChoiceField(choices=ocgisChoices(Config.VARIABLE).items(), required=True)
    geometry = ChoiceField(choices=ocgisChoices(Config.GEOMETRY).items(), required=False)
    geometry_id = ChoiceField(choices=ocgisChoices(Config.GEOMETRY_ID).items(), required=False)
    
    
class OpenClimateGisForm2(Form):
    '''Form that backs up the second selection page.'''
    
    aggregate = BooleanField(required=True, initial=True)
    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass