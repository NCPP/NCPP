from django.forms import (Form, CharField, ChoiceField, BooleanField, MultipleChoiceField, SelectMultiple, FloatField,
                          TextInput, RadioSelect, DateTimeField, Select, CheckboxSelectMultiple, ValidationError)

from ncpp.config.open_climate_gis import ocgisChoices, Config, ocgisGeometries, ocgisDatasets, ocgisCalculations
from ncpp.constants import MONTH_CHOICES, NO_VALUE_OPTION
from ncpp.utils import hasText
import re

# list of invalid characters for 'prefix' field
INVALID_CHARS = "[^a-zA-Z0-9_\-]"

class DynamicChoiceField(ChoiceField):
   """ Class that extends the ChoiceField to suppress validation on valid choices, 
       to support the case when they are assigned dynamically."""
       
   def validate(self, value):
       """This method only checks that a value exist, not which value it is."""
       
       if self.required and not value:
           raise ValidationError(self.error_messages['required'])
       
class DynamicMultipleChoiceField(MultipleChoiceField):
   """ Class that extends MultipleChoiceField to suppress validation on valid choices, 
       to support the case when they are assigned dynamically."""
       
   def validate(self, value):
       """This method only checks that a value exist, not which value it is."""
       
       if self.required and not value:
           raise ValidationError(self.error_messages['required'])

class OpenClimateGisForm1(Form):
    '''Form that backs up the first selection page. 
       The argument passed to ocgisChoices must correspond to a valid key in the file OCGIS configuration file.'''
           
    # data selection
    dataset_category = ChoiceField(choices=ocgisDatasets.getChoices(), required=True,
                          widget=Select(attrs={'onchange': 'populateDatasets();'}))
    # no initial values for 'datasets' widget. The choices are assigned dynamically through Ajax
    dataset = DynamicChoiceField(choices=[ NO_VALUE_OPTION ], required=True,
                          widget=Select(attrs={'onchange': 'populateVariables();'}))
    # no initial values for 'variables' widget. The choices are assigned dynamically through Ajax
    variable = DynamicChoiceField(choices=[ NO_VALUE_OPTION ], required=True,
                                  widget=Select(attrs={'onchange': 'populateDateTimes();'}))
    
    # geometry selection
    geometry = ChoiceField(choices=ocgisGeometries.getChoices(), required=False, 
                           widget=Select(attrs={'onchange': 'populateGeometries();'}))
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
        # NOTE: invalid float values in form result in cleaned_data not being populated for that key
        if (    ('latmin' in self.cleaned_data and hasText(self.cleaned_data['latmin']))
             or ('latmax' in self.cleaned_data and hasText(self.cleaned_data['latmax']))
             or ('lonmin' in self.cleaned_data and hasText(self.cleaned_data['lonmin']))
             or ('lonmax' in self.cleaned_data and hasText(self.cleaned_data['lonmax'])) ):
            ngeometries += 1
            geometry = 'box'
        if (   ('lat' in self.cleaned_data and hasText(self.cleaned_data['lat']))
            or ('lon' in self.cleaned_data and hasText(self.cleaned_data['lon'])) ):
             ngeometries += 1
             geometry = 'point'
        if ngeometries > 1:
            self._errors["geometry"] = self.error_class(["Please choose only one geometry: shape, bounding box or point."]) 
       
        elif ngeometries==1:
            if geometry =='shape':
              if not hasText(self.cleaned_data['geometry']):
                  self._errors["geometry_id"] = self.error_class(["Please select a shape type"]) 
              if len(self.cleaned_data['geometry_id'])==0:
                  self._errors["geometry_id"] = self.error_class(["Please select a shape geometry"])
            elif geometry == 'box':
                if (   not 'latmin' in self.cleaned_data or not hasText(self.cleaned_data['latmin']) 
                    or not 'latmax' in self.cleaned_data or not hasText(self.cleaned_data['latmax'])
                    or not 'lonmin' in self.cleaned_data or not hasText(self.cleaned_data['lonmin']) 
                    or not 'lonmax' in self.cleaned_data or not hasText(self.cleaned_data['lonmax']) ):
                    self._errors["latmin"] = self.error_class(["Invalid bounding box latitude or longitude values."])                    
            elif geometry == 'point':
                if not 'lat' in self.cleaned_data or not hasText(self.cleaned_data['lat']):
                    self._errors["lat"] = self.error_class(["Invalid point latitude."])   
                if not 'lon' in self.cleaned_data or not hasText(self.cleaned_data['lon']):
                     self._errors["lon"] = self.error_class(["Invalid point longitude."])   
                     
        # validate times
        if (   ('datetime_start' in self.cleaned_data and self.cleaned_data['datetime_start'] is not None)
            or ('datetime_stop'  in self.cleaned_data and self.cleaned_data['datetime_stop']  is not None) ):
            if (   ('timeregion_month' in self.cleaned_data and len(self.cleaned_data['timeregion_month'])>0)
                or ('timeregion_year' in self.cleaned_data and hasText(self.cleaned_data['timeregion_year'])) ):
                self._errors["timeregion_year"] = self.error_class(["Please use a time range OR a time selection."])
                
        if 'timeregion_year' in self.cleaned_data and hasText(self.cleaned_data['timeregion_year']):
            years = self.cleaned_data['timeregion_year'].split(',')
            for year in years:
                year = year.replace(" ","")
                if not re.match('^\d{4}$', year):
                    self._errors["timeregion_year"] = self.error_class(["Invalid year selection"])
                    break
        
        if not self.is_valid():
            print 'VALIDATION ERRORS: %s' % self.errors
        
        # return cleaned data
        return self.cleaned_data

    
class OpenClimateGisForm2(Form):
    '''Form that backs up the second selection page.'''
    
    calc = ChoiceField(choices=ocgisCalculations.getChoices(), required=True, initial='none',
                       widget=Select(attrs={'onchange': 'populateParameters();'}))
    par1 = CharField(required=False, widget=TextInput(attrs={'size':6}), initial="")
    par2 = CharField(required=False, widget=TextInput(attrs={'size':6}), initial="")
    par3 = CharField(required=False, widget=TextInput(attrs={'size':6}), initial="")
    calc_group = MultipleChoiceField(choices=ocgisChoices(Config.CALCULATION_GROUP).items(), required=False)
    calc_raw = BooleanField(initial=False, required=False)
    aggregate = BooleanField(initial=True, required=False)
    spatial_operation = ChoiceField(required=True, choices=ocgisChoices(Config.SPATIAL_OPERATION).items(),
                                    widget=RadioSelect, initial='intersects')
    output_format = ChoiceField(choices=ocgisChoices(Config.OUTPUT_FORMAT).items(), required=True, initial='csv')
    prefix = CharField(required=True, widget=TextInput(attrs={'size':20}), initial='ocgis_output')
    with_auxiliary_files = BooleanField(initial=False, required=False)
    
    # custom validation
    def clean(self):
        
        # invoke superclass cleaning method
        super(OpenClimateGisForm2, self).clean()
        
        # validate calculation
        if hasText(self.cleaned_data['calc']) and self.cleaned_data['calc'].lower() != 'none':
            
            # calculation group must be selected
            if len( self.cleaned_data['calc_group'] ) == 0:
                self._errors["calc_group"] = self.error_class(["Calculation Group(s) not selected."]) 
            
            # validate keyword values
            func = self.cleaned_data['calc']
            calc = ocgisCalculations.getCalc(func)
            if 'keywords' in calc:
                for i, keyword in enumerate(calc["keywords"]):
                    parN = 'par%s' % (i+1)
                    value = self.cleaned_data[parN]
                    if keyword["type"]=="float":
                        try:
                            x = float(value)
                        except ValueError:
                            self._errors[parN] = self.error_class(["Invalid float value for keyword: "+keyword["name"]])
                    elif keyword["type"] == "string":
                        if "values" in keyword:
                            if not value.lower() in keyword["values"]:
                                self._errors[parN] = self.error_class(["Invalid string value for keyword: "+keyword["name"]])
        if 'prefix' in self.cleaned_data and re.search(INVALID_CHARS, self.cleaned_data['prefix']):
            self._errors['prefix'] = self.error_class(["The prefix contains invalid characters."])
        
        # return cleaned data
        return self.cleaned_data


    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass