from django.forms import (Form, CharField, ChoiceField, BooleanField, MultipleChoiceField, SelectMultiple, FloatField,
                          TextInput)

from ncpp.models.open_climate_gis import ocgisChoices, Config



class OpenClimateGisForm1(Form):
    '''Form that backs up the first selection page. 
       The argument passed to ocgisChoices must correspond to a valid key in the file OCGIS configuration file.'''
    
    dataset = ChoiceField(choices=ocgisChoices(Config.DATASET).items(), required=True)
    variable = ChoiceField(choices=ocgisChoices(Config.VARIABLE).items(), required=True)
    geometry = ChoiceField(choices=ocgisChoices(Config.GEOMETRY).items(), required=False)
    geometry_id = MultipleChoiceField(choices=ocgisChoices(Config.GEOMETRY_ID).items(), required=False,
                                      widget=SelectMultiple(attrs={'size':6}))
    
    latmin = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    latmax = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lonmin = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    lonmax = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    
    lat = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lon = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    
    
class OpenClimateGisForm2(Form):
    '''Form that backs up the second selection page.'''
    
    aggregate = BooleanField(required=True, initial=True)
    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass