# Fake Open Climate GIS library
import time

SLEEP_SECONDS = 1

OUTPUT = "file:///Users/cinquini/data/NCPP/QED2013/obs/observational/sectorEco/pr/day/US48/19712000/QED2013_evalData_ARRM_CGCM3_P1_G2agro_tasmax_ann_GSL_US48_19712000.jpg"

def ocg(dataset=None, variable=None, geometry=None, geometry_id=None, 
        latmin=None, latmax=None, lonmin=None, lonmax=None, lat=None, lon=None,
        calc=None, par1=None, par2=None, calc_raw=False, calc_group=[],
        aggregate=True, output_format=None, prefix=None):
    
    time.sleep(SLEEP_SECONDS)
    
    return OUTPUT
        