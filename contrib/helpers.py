from copy import deepcopy
import datetime


def validate_time_subset(time_range,time_region):
    '''
    Ensure `time_range` and `time_region` overlap. If one of the values is `None`, the
    function always returns `True`. Function will return `False` if the two time range
    descriptions do not overlap.
    
    :param time_range: Sequence with two datetime elements.
    :type time_range: sequence
    :param time_region: Dictionary with two keys 'month' and 'year' each containing
    an integer sequence corresponding to the respective time parts. For example:
    >>> time_region = {'month':[1,2],'year':[2013]}
    If a 'month' or 'year' key is missing, the key will be added with a default of `None`.
    :type time_region: dict
    :rtype: bool
    '''
    
    def _between_(target,lower,upper):
        if target >= lower and target <= upper:
            ret = True
        else:
            ret = False
        return(ret)
    
    def _check_months_(targets,months):
        check = [target in months for target in targets]
        if all(check):
            ret = True
        else:
            ret = False
        return(ret)
    
    def _check_years_(targets,min_range_year,max_range_year):
        if all([_between_(year_bound,min_range_year,max_range_year) for year_bound in targets]):
            ret = True
        else:
            ret = False
        return(ret)
    
    ## by default we return that it does not validate
    ret = False
    ## if any of the parameters are none, then it will validate True
    if any([t is None for t in [time_range,time_region]]):
        ret = True
    else:
        ## ensure time region has the necessary keys
        copy_time_region = deepcopy(time_region)
        for key in ['month','year']:
            if key not in copy_time_region:
                copy_time_region[key] = None
        ## pull basic date information from the time range
        min_range_year,max_range_year = time_range[0].year,time_range[1].year
        delta = datetime.timedelta(days=29,hours=12)
        months = set()
        current = time_range[0]
        while current <= time_range[1]:
            current += delta
            months.update([current.month])
            if len(months) == 12:
                break
        ## construct boundaries from time region. first, the case of only months.
        if copy_time_region['month'] is not None and copy_time_region['year'] is None:
            month_bounds = min(copy_time_region['month']),max(copy_time_region['month'])
            ret = _check_months_(month_bounds,months)
        ## case of only years
        elif copy_time_region['month'] is None and copy_time_region['year'] is not None:
            year_bounds = min(copy_time_region['year']),max(copy_time_region['year'])
            ret = _check_years_(year_bounds,min_range_year,max_range_year)
        ## case with both years and months
        else:
            month_bounds = min(copy_time_region['month']),max(copy_time_region['month'])
            year_bounds = min(copy_time_region['year']),max(copy_time_region['year'])
            ret_months = _check_months_(month_bounds,months)
            ret_years = _check_years_(year_bounds,min_range_year,max_range_year)
            if all([ret_months,ret_years]):
                ret = True
    return(ret)