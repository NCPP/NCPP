from base import AbstractDataPackage
import maurer
import hayhoe


class MaurerPackage(AbstractDataPackage):
    name = 'Maurer 2010'
    description = '<tdk>'
    fields = [maurer.MaurerTas,
              maurer.MaurerTasmax,
              maurer.MaurerTasmin,
              maurer.MaurerPrecip]
    dataset_category = dict(name='Gridded Observational Datasets',description='<tdk>')
    
    
class HayhoeGFDLPackage(AbstractDataPackage):
    name = 'Hayhoe GFDL'
    description = '<tdk>'
    fields = [hayhoe.HayhoeGFDLPr,
              hayhoe.HayhoeGFDLTasmax,
              hayhoe.HayhoeGFDLTasmin]
    dataset_category = dict(name='Gridded Observational Datasets',description='<tdk>')