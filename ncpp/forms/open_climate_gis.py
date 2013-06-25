from django.forms import (Form, CharField, ChoiceField, BooleanField, MultipleChoiceField, SelectMultiple, FloatField,
                          TextInput, RadioSelect, DateTimeField, Select, CheckboxSelectMultiple)

from ncpp.models.open_climate_gis import ocgisChoices, Config
from ncpp.constants import MONTH_CHOICES

class OpenClimateGisForm1(Form):
    '''Form that backs up the first selection page. 
       The argument passed to ocgisChoices must correspond to a valid key in the file OCGIS configuration file.'''
    
    dataset = ChoiceField(choices=ocgisChoices(Config.DATASET, nochoice=True).items(), required=True,
                          widget=Select(attrs={'onchange': 'inspectDataset();'}))
    variable = ChoiceField(choices=ocgisChoices(Config.VARIABLE, nochoice=True).items(), required=True)
    geometry = ChoiceField(choices=ocgisChoices(Config.GEOMETRY).items(), required=False)
    geometry_id = MultipleChoiceField(choices=ocgisChoices(Config.GEOMETRY_ID).items(), required=False,
                                      widget=SelectMultiple(attrs={'size':6}))
    
    latmin = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    latmax = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lonmin = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    lonmax = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    
    lat = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lon = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))   
    
    datetime_start = DateTimeField(required=False)
    datetime_stop = DateTimeField(required=False)
    
    timeregion_month = MultipleChoiceField(choices=MONTH_CHOICES, required=False, widget=CheckboxSelectMultiple)                                    #initial = range(12))
    timeregion_year = CharField(required=False, widget=TextInput(attrs={'size':60}))
    
    # custom validation
    def clean(self):
        
        # invoke superclass cleaning method
        super(OpenClimateGisForm1, self).clean()
        
        if not self.is_valid():
            print 'VALIDATION ERRORS: %s' % self.errors
        
        # return cleaned data
        return self.cleaned_data

    
class OpenClimateGisForm2(Form):
    '''Form that backs up the second selection page.'''
    
    calc = ChoiceField(choices=ocgisChoices(Config.CALCULATION).items(), required=True)
    par1 = FloatField(required=False, widget=TextInput(attrs={'size':6}))
    par2 = FloatField(required=False, widget=TextInput(attrs={'size':6}))
    calc_group = MultipleChoiceField(choices=ocgisChoices(Config.CALCULATION_GROUP).items(), required=False)
    calc_raw = BooleanField(initial=False, required=False)
    aggregate = BooleanField(initial=True, required=False)
    spatial_operation = ChoiceField(required=True, choices=ocgisChoices(Config.SPATIAL_OPERATION).items(),
                                    widget=RadioSelect, initial='intersects')
    output_format = ChoiceField(choices=ocgisChoices(Config.OUTPUT_FORMAT).items(), required=True)
    prefix = CharField(required=True, widget=TextInput(attrs={'size':20}), initial='ocgis_output')
    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass