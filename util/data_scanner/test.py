from ocgis.test.base import TestBase
from datasets.base import AbstractHarvestDataset
import datetime
import db
import query
import os
from unittest.case import SkipTest
from sqlalchemy.orm.exc import NoResultFound
import ocgis
from db import get_or_create
from NCPP.util.data_scanner import harvest


tdata = TestBase.get_tdata()
class CanCM4TestDataset(AbstractHarvestDataset):
    uri = [tdata.get_uri('cancm4_tas')]
    variables = ['tas']
    clean_units = [{'standard_name':'K','long_name':'Kelvin'}]
    clean_variable = [dict(standard_name='air_temperature',long_name='Near-Surface Air Temperature',description='Fill it in!')]
    dataset_category = dict(name='GCMs',description='Global Circulation Models')
    dataset = dict(name='CanCM4',description='Canadian Circulation Model 4')
    type = 'variable'
    
    
class AbstractMaurerDataset(AbstractHarvestDataset):
    dataset = dict(name='Maurer 2010',description='Amazing dataset!')
    dataset_category = dict(name='Observational',description='Some observational datasets.')
    
    
class MaurerTas(AbstractMaurerDataset):
    uri = ['/home/local/WX/ben.koziol/climate_data/maurer/2010-concatenated/Maurer02new_OBS_tas_daily.1971-2000.nc']
    variables = ['tas']
    clean_units = [{'standard_name':'C','long_name':'Celsius'}]
    clean_variable = [dict(standard_name='air_temperature',long_name='Near-Surface Air Temperature',description='Fill it in!')]
    type = 'variable'
    
    
class MaurerTasmax(AbstractMaurerDataset):
    uri = ['/home/local/WX/ben.koziol/climate_data/maurer/2010-concatenated/Maurer02new_OBS_tasmax_daily.1971-2000.nc']
    variables = ['tasmax']
    clean_units = [{'standard_name':'C','long_name':'Celsius'}]
    clean_variable = [dict(standard_name='maximum_air_temperature',long_name='Near-Surface Maximum Air Temperature',description='Fill it in!')]
    type = 'variable'
    

mmf_uri = tdata.get_uri('maurer_2010_tasmin')
mmf_uri.reverse()
class MaurerMultiFile(AbstractMaurerDataset):
    uri = mmf_uri
    variables = ['tasmin']
    clean_units = [{'standard_name':'C','long_name':'Celsius'}]
    clean_variable = [dict(standard_name='minimum_air_temperature',long_name='Near-Surface Minimum Air Temperature',description='Fill it in!')]
    type = 'variable'


class Test(TestBase):
            
    def setUp(self):
        TestBase.setUp(self)
        db.build_database(in_memory=True)
        
    def test_harvest(self):
        with self.assertRaises(ValueError):
            harvest.main()
        
    def test_query_data_package(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
        
            dataset = session.query(db.Dataset).filter_by(name='Maurer 2010').one()
            category = session.query(db.DatasetCategory).filter_by(name='Observational').one()
            fields = [c.field[0] for c in dataset.container]
            dp = db.DataPackage(field=fields,name='Test Package',description='For testing! Duh...',dataset_category=category)
            session.add(dp)
            
            dataset = session.query(db.Dataset).filter_by(name='Maurer 2010').one()
            category = session.query(db.DatasetCategory).filter_by(name='GCMs').one()
            fields = [c.field[0] for c in dataset.container]
            dp = db.DataPackage(field=fields,name='Test Package GCMs',description='For testing! Duh...',dataset_category=category)
            session.add(dp)
            
            session.commit()
            
            dq = query.DataQuery()
            ret = dq.get_package()
            self.assertEqual(ret,{'dataset_category': [u'GCMs', u'Observational'], 'package_name': [u'Test Package', u'Test Package GCMs']})
            
            with self.assertRaises(NoResultFound):
                dq.get_package(package_name='foo')
            
            ret = dq.get_package(package_name='Test Package GCMs')
            rds = [ocgis.RequestDataset(**k) for k in ret]
            for rd in rds: rd.inspect_as_dct()
            
            ret = dq.get_package(time_range=[datetime.datetime(1980,2,1),datetime.datetime(1985,3,4)])
            self.assertEqual(ret,{'dataset_category': [u'GCMs', u'Observational'], 'package_name': [u'Test Package', u'Test Package GCMs']})
            
            with self.assertRaises(NoResultFound):
                dq.get_package(time_range=[datetime.datetime(1900,2,1),datetime.datetime(1901,3,4)])
        
    def test_data_package(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
            
            dataset = session.query(db.Dataset).filter_by(name='Maurer 2010').one()
            category = session.query(db.DatasetCategory).filter_by(name='Observational').one()
            fields = [c.field[0] for c in dataset.container]
            dp = db.DataPackage(field=fields,name='Test Package',description='For testing! Duh...',dataset_category=category)
            session.add(dp)
            
            session.commit()
            
            kwargs = [f.get_request_dataset_kwargs() for f in dp.field]
            rds = [ocgis.RequestDataset(**k) for k in kwargs]
            for rd in rds: rd.inspect_as_dct()
            
    def test_data_package_bad(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
            
            dataset = session.query(db.Dataset)
            fields = []
            for d in dataset:
                for c in d.container:
                    fields.append(c.field[0])
            with self.assertRaises(ValueError):
                db.DataPackage(field=fields,name='Test Package',description='For testing! Duh...')
        
    def test_query_all(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
            
        dq = query.DataQuery()
        state = dq.get_variable_or_index('variable')
        target = {'long_name': [u'Near-Surface Air Temperature', u'Near-Surface Maximum Air Temperature'], 'time_frequency': [u'day'], 'dataset_category': [u'GCMs', u'Observational'], 'dataset': [u'CanCM4', u'Maurer 2010']}
        self.assertDictEqual(state,target)

    def test_query_limiting_all(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
        dq = query.DataQuery()
        ret = dq.get_variable_or_index('variable',
                                       long_name='Near-Surface Air Temperature',
                                       time_frequency='day',
                                       dataset_category='Observational',
                                       dataset='Maurer 2010')
        self.assertDictEqual(ret,{'variable': u'tas', 'alias': u'tas', 't_calendar': u'standard', 'uri': [u'/home/local/WX/ben.koziol/climate_data/maurer/2010-concatenated/Maurer02new_OBS_tas_daily.1971-2000.nc'], 't_units': u'days since 1940-01-01 00:00:00'})    
        rd = ocgis.RequestDataset(**ret)
        rd.inspect_as_dct()
        
    def test_query_limiting(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
        dq = query.DataQuery()
        ret = dq.get_variable_or_index('variable',
                                       long_name='Near-Surface Air Temperature')
        self.assertDictEqual(ret,{'long_name': [u'Near-Surface Air Temperature'], 'time_frequency': [u'day'], 'dataset_category': [u'GCMs', u'Observational'], 'dataset': [u'CanCM4', u'Maurer 2010']})

    def test_query_time_range(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
        dq = query.DataQuery()
        ret = dq.get_variable_or_index('variable',
                                       time_range=[datetime.datetime(1980,2,3),
                                                   datetime.datetime(1990,3,4)])
        target = {'long_name': [u'Near-Surface Air Temperature', u'Near-Surface Maximum Air Temperature'], 'time_frequency': [u'day'], 'dataset_category': [u'Observational'], 'dataset': [u'Maurer 2010']}
        self.assertDictEqual(ret,target)
        
    def test_query_empty(self):
        models = [CanCM4TestDataset,MaurerTas,MaurerTasmax]
        with db.session_scope() as session:
            for m in models: m().insert(session)
        dq = query.DataQuery()
        
        with self.assertRaises(NoResultFound):
            ret = dq.get_variable_or_index('variable',
                                           time_range=[datetime.datetime(1900,2,3),
                                                       datetime.datetime(1901,3,4)])

    def test_container(self):
        session = db.Session()
        try:
            container = db.Container(session,CanCM4TestDataset())
            session.add(container)
            session.commit()
            container = session.query(db.Container).one()
            self.assertEqual(container.dataset.name,'CanCM4')
            objects,simple = container.as_dict()
            self.assertEqual(simple,{'time_calendar': u'365_day', 'time_start': datetime.datetime(2001, 1, 1, 0, 0), 'description': None, 'spatial_abstraction': u'polygon', 'cid': 1, 'did': 1, 'spatial_proj4': u'+proj=longlat +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +no_defs ', 'time_stop': datetime.datetime(2011, 1, 1, 0, 0), 'time_units': u'days since 1850-1-1', 'spatial_envelope': u'POLYGON ((-1.4062500000000000 -90.0000000000000000, -1.4062500000000000 90.0000000000000000, 358.5937500000000000 90.0000000000000000, 358.5937500000000000 -90.0000000000000000, -1.4062500000000000 -90.0000000000000000))', 'spatial_res': u'2.8125', 'field': [], 'time_frequency': u'day', 'field_shape': u'(1, 3650, 1, 64, 128)', 'time_res_days': 1.0})
            self.assertEqual(objects['uri'][0].value,self.test_data.get_uri('cancm4_tas'))
            self.assertEqual(objects['dataset'].name,'CanCM4')
        finally:
            session.close()
            
    def test_container_multifile(self):
        with db.session_scope() as session:
            container = db.Container(session,MaurerMultiFile())
            session.add(container)
            session.commit()
            self.assertEqual([u.value for u in container.uri],self.test_data.get_uri('maurer_2010_tasmin'))
        
    def test_raw_variable(self):
        session = db.Session()
        try:
            hd = CanCM4TestDataset()
            container = db.Container(session,hd)
            clean_units = get_or_create(session,db.CleanUnits,**hd.clean_units[0])
            clean_variable = get_or_create(session,db.CleanVariable,**hd.clean_variable[0])
            raw_variable = db.Field(hd,container,hd.variables[0],clean_units,clean_variable)
            session.add(raw_variable)
            session.commit()
            obj = session.query(db.Field).one()
            objects,simple = obj.as_dict()
            target = {'name': u'tas', 'cid': 1, 'cvid': 1, 'long_name': u'Near-Surface Air Temperature', 'standard_name': u'air_temperature', 'fid': 1, 'cuid': 1, 'units': u'K', 'type': u'variable', 'description': None}
            self.assertDictEqual(simple,target)
            self.assertEqual(obj.clean_units.standard_name,'K')
        finally:
            session.close()
        
    def test_insert(self):
        session = db.Session()
        try:
            CanCM4TestDataset().insert(session)
            self.assertEqual(1,session.query(db.Container).count())
            container = session.query(db.Container).one()
            self.assertEqual(container.dataset.name,'CanCM4')
            self.assertEqual(container.dataset.dataset_category.name,'GCMs')
        finally:
            session.close()
            
    def test_to_disk(self):
        raise(SkipTest('dev'))
        path = os.path.join(self._test_dir,'test.sqlite')
        db.build_database(db_path=path)
        session = db.Session()
        try:
            CanCM4TestDataset().insert(session)
        finally:
            session.close()
