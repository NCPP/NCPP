from django.forms import (Form, CharField, ChoiceField, BooleanField, MultipleChoiceField, SelectMultiple, FloatField,
                          TextInput, RadioSelect, DateTimeField, Select, CheckboxSelectMultiple, ValidationError)

from ncpp.models.open_climate_gis import ocgisChoices, Config, ocgisGeometries
from ncpp.constants import MONTH_CHOICES, NO_VALUE_OPTION
from ncpp.utils import hasText

class DynamicChoiceField(ChoiceField):
   """ Class that extends the ChoiceField to suppress validation on valid choices, 
       to support the case when they are assigned dynamically through Ajax calls."""
       
   def validate(self, value):
       """This method only checks that a value exist, not which value it is."""
       
       if self.required and not value:
           raise ValidationError(self.error_messages['required'])
       
class DynamicMultipleChoiceField(MultipleChoiceField):
   """ Class that extends MultipleChoiceField to suppress validation on valid choices, 
       to support the case when they are assigned dynamically through Ajax calls."""
       
   def validate(self, value):
       """This method only checks that a value exist, not which value it is."""
       
       if self.required and not value:
           raise ValidationError(self.error_messages['required'])

class OpenClimateGisForm1(Form):
    '''Form that backs up the first selection page. 
       The argument passed to ocgisChoices must correspond to a valid key in the file OCGIS configuration file.'''
    
    # data selection
    dataset = ChoiceField(choices=ocgisChoices(Config.DATASET, nochoice=True).items(), required=True,
                          widget=Select(attrs={'onchange': 'inspectDataset();'}))
    # no initial values for 'variables' widget. The choices are assigned dynamically through Ajax
    variable = DynamicChoiceField(choices=[ NO_VALUE_OPTION ], required=True)
    
    # geometry selection
    geometry = ChoiceField(choices=ocgisGeometries.getCategories(), required=False, widget=Select(attrs={'onchange': 'populateGeometries();'}))
    geometry_id = DynamicMultipleChoiceField(choices=[ NO_VALUE_OPTION ], required=False, widget=SelectMultiple(attrs={'size':6}))
    
    latmin = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    latmax = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lonmin = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    lonmax = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))
    
    lat = FloatField(required=False, min_value=-90, max_value=+90, widget=TextInput(attrs={'size':6}))
    lon = FloatField(required=False, min_value=-180, max_value=+180, widget=TextInput(attrs={'size':6}))   
    
    datetime_start = DateTimeField(required=False, widget=TextInput(attrs={'size':24}))
    datetime_stop = DateTimeField(required=False, widget=TextInput(attrs={'size':24}))
    
    timeregion_month = MultipleChoiceField(choices=MONTH_CHOICES, required=False, widget=CheckboxSelectMultiple)                                    #initial = range(12))
    timeregion_year = CharField(required=False, widget=TextInput(attrs={'size':60}))
    
    # custom validation
    def clean(self):
        
        # invoke superclass cleaning method
        super(OpenClimateGisForm1, self).clean()
                
        # validate geometry
        ngeometries = 0
        geometry = None
        if (hasText(self.cleaned_data['geometry']) or len(self.cleaned_data['geometry_id']) ):
            ngeometries += 1
            geometry = 'shape'
        if (    hasText(self.cleaned_data['latmin']) or hasText(self.cleaned_data['latmax']) 
             or hasText(self.cleaned_data['lonmin']) or hasText(self.cleaned_data['lonmax']) ):
            ngeometries += 1
            geometry = 'box'
        if (hasText(self.cleaned_data['lat']) or hasText(self.cleaned_data['lon'])):
             ngeometries += 1
             geometry = 'point'
        if ngeometries > 1:
            self._errors["geometry"] = self.error_class(["Please choose only one geometry: shape, bounding box or point"]) 
       
        elif ngeometries==1:
            if geometry =='shape':
              if not hasText(self.cleaned_data['geometry']):
                  self._errors["geometry_id"] = self.error_class(["Please select a shape type"]) 
              if len(self.cleaned_data['geometry_id'])==0:
                  self._errors["geometry_id"] = self.error_class(["Please select a shape geometry"])
            elif geometry == 'box':
                if (   not hasText(self.cleaned_data['latmin']) or not hasText(self.cleaned_data['latmax'])
                    or not hasText(self.cleaned_data['lonmin']) or not hasText(self.cleaned_data['lonmax']) ):
                    self._errors["latmin"] = self.error_class(["Invalid bounding box latitude or longitude values"])                    
            elif geometry == 'point':
                if not hasText(self.cleaned_data['lat']):
                    self._errors["lat"] = self.error_class(["Invalid point latitude"])   
                if not hasText(self.cleaned_data['lon']):
                     self._errors["lon"] = self.error_class(["Invalid point longitude"])   
                     
        # validate times
        if self.cleaned_data['datetime_start'] is not None or self.cleaned_data['datetime_stop']:
            if len(self.cleaned_data['timeregion_month'])>0 or hasText(self.cleaned_data['timeregion_year']):
                self._errors["timeregion_year"] = self.error_class(["Please select a time range OR a time region"])
        
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