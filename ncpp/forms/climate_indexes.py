from django.forms import Form, CharField, ChoiceField, MultipleChoiceField, CheckboxSelectMultiple, Select
from django.utils.safestring import mark_safe

from ncpp.constants import (REGION_CHOICES, INDEX_CHOICES, AGGREGATION_CHOICES, START_DATETIME_CHOICES, 
                            DATASET_CHOICES, OUTPUT_FORMAT_CHOICES, SUPPORTING_INFO_CHOICES)

class MyCheckboxSelectMultiple(CheckboxSelectMultiple):
    
    '''Custom widget class that removes the <ul> markup when rendering the HTML tag.'''
    def render(self, name, value, attrs=None, choices=()):
        html = super(MyCheckboxSelectMultiple, self).render(name, value, attrs, choices)
        return mark_safe(html.replace('<ul>', '').replace('</ul>','').replace('<li>','').replace('</li>',''))
    
class ClimateIndexesForm1(Form):
    '''Form to select the geographic region.'''
    
    choices = { '':'-----' }
    choices.update( REGION_CHOICES )
    # note the 'onclick' event handler that triggers a Javascript function
    region = ChoiceField(choices=choices.items(), required=True, widget=Select(attrs={'onclick': 'selectMapFeature();'}))
            
class ClimateIndexesForm2(Form):
    ''' Form to select all other job parameters.'''
    
    index = ChoiceField(choices=INDEX_CHOICES.items(), required=True)
    #aggregation = ChoiceField(choices=AGGREGATION_CHOICES.items(), required=False)
    startDateTime = ChoiceField(choices=START_DATETIME_CHOICES, required=True)
    dataset = ChoiceField(choices=DATASET_CHOICES.items(), required=True)
    outputFormat = ChoiceField(choices=OUTPUT_FORMAT_CHOICES.items(), required=True)
    supportingInfo = MultipleChoiceField(widget=CheckboxSelectMultiple,choices=SUPPORTING_INFO_CHOICES.items(), required=False)
    # use custom widget with no <ul> markup
    #supportingInfo = MultipleChoiceField(widget=MyCheckboxSelectMultiple,choices=SUPPORTING_INFO_CHOICES.items(), required=False)
    
class ClimateIndexesForm3(Form):
    '''Dummy form that presents a summary of all previous choices'''
    
    pass