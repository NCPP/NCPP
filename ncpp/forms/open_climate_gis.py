from django.forms import (Form, CharField, ChoiceField, BooleanField, MultipleChoiceField, SelectMultiple, FloatField,
                          TextInput, RadioSelect, DateTimeField, Select, CheckboxSelectMultiple, ValidationError)

from ncpp.config.open_climate_gis import ocgisChoices, Config, ocgisGeometries, ocgisDatasets, ocgisCalculations
from ncpp.constants import MONTH_CHOICES, NO_VALUE_OPTION
from ncpp.utils import hasText
from contrib.helpers import validate_time_subset
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
    variable = DynamicChoiceField(choices=[ NO_VALUE_OPTION ], required=False,
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
        
        # validate data selection
        if 'dataset_category' in self.cleaned_data and hasText(self.cleaned_data['dataset_category']):
            if 'dataset' in self.cleaned_data and hasText(self.cleaned_data['dataset']):
                jsonData = ocgisDatasets.datasets[self.cleaned_data['dataset_category']][self.cleaned_data['dataset']] 
                if jsonData['type'] == 'datasets':
                    if not 'variable' in self.cleaned_data or not hasText(self.cleaned_data['variable']):
                         self._errors["variable"] = self.error_class(["A variable must be selected when the dataset is not a package."]) 
                
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
                     
        # validate time range
        datetime_start = None
        datetime_stop = None
        if 'datetime_start' in self.cleaned_data and hasText(self.cleaned_data['datetime_start']):
            datetime_start = self.cleaned_data['datetime_start']
        if 'datetime_stop' in self.cleaned_data and hasText(self.cleaned_data['datetime_stop']):
            datetime_stop = self.cleaned_data['datetime_stop']
        if datetime_start is not None and datetime_stop is None:
            self._errors["datetime_stop"] = self.error_class(["Invalid value for 'Time Range Stop'"])
        if datetime_start is  None and datetime_stop is not None:
            self._errors["datetime_start"] = self.error_class(["Invalid value for 'Time Range Start'"])
        if datetime_start is not None and datetime_stop is not None:
            if datetime_start > datetime_stop:
                self._errors["datetime_start"] = self.error_class(["'Time Range Start' must be less than 'Time Range Stop'"])
            time_range = [datetime_start, datetime_stop]
        else:
            time_range = None
                
        # validate years time region 
        time_region = {}
        if 'timeregion_year' in self.cleaned_data and hasText(self.cleaned_data['timeregion_year']):
            years = str(self.cleaned_data['timeregion_year'].replace(" ","")) # remove blanks
            if re.match('^\d{4}-\d{4}', years):
                year1 = int(years[0:4])
                year2 = int(years[5:9])
                if year1 >= year2:
                    self._errors["timeregion_year"] = self.error_class(["Invalid year selection: must be year1 < year2"])
                time_region['year'] = range(year1, year2+1)
            else:
                years = years.split(',')
                time_region['year'] = []
                for year in years:
                    if not re.match('^\d{4}$', year):
                        self._errors["timeregion_year"] = self.error_class(["Invalid year selection"])
                        break
                    time_region['year'].append( int(year) )
        
        # validate months time region
        if 'timeregion_month' in self.cleaned_data and len(self.cleaned_data['timeregion_month'])>0:
            time_region['month'] = map(int, self.cleaned_data['timeregion_month'])

        # validate time range + time region
        if time_range is not None and len(time_region)>0:
            if not validate_time_subset(time_range, time_region):
                self._errors["timeregion_year"] = self.error_class(["Time Range must contain Time Region."])
                    
         
        if not self.is_valid():
            print 'VALIDATION ERRORS: %s' % self.errors
        
        # return cleaned data
        return self.cleaned_data

    
class OpenClimateGisForm2(Form):
    '''Form that backs up the second selection page.'''
    
    calc = ChoiceField(choices=ocgisCalculations.getChoices(), required=False, initial='none',
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
    with_auxiliary_files = BooleanField(initial=True, required=False)
    
    # custom validation
    def clean(self):
        
        # invoke superclass cleaning method
        super(OpenClimateGisForm2, self).clean()
        
        # validate calculation
        if 'calc' in self.cleaned_data and hasText(self.cleaned_data['calc']) and self.cleaned_data['calc'].lower() != 'none':
            
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
        
        if not self.is_valid():
            print 'VALIDATION ERRORS: %s' % self.errors

        # return cleaned data
        return self.cleaned_data


    
class OpenClimateGisForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass