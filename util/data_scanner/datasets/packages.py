import base
import maurer
import hayhoe


class MaurerPackage(base.AbstractDataPackage):
    name = 'Maurer 2010'
    description = '<tdk>'
    fields = [maurer.MaurerTas,
              maurer.MaurerTasmax,
              maurer.MaurerTasmin,
              maurer.MaurerPrecip]
    dataset_category = base.CATEGORY_GRIDDED_OBS
    
    
class HayhoeGFDLPackage(base.AbstractDataPackage):
    name = 'Hayhoe GFDL'
    description = '<tdk>'
    fields = [hayhoe.HayhoeGFDLPr,
              hayhoe.HayhoeGFDLTasmax,
              hayhoe.HayhoeGFDLTasmin]
    dataset_category = dict(name='Downscaled',description='<tdk>')