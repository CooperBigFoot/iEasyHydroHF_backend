#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os.path
from distutils.util import strtobool
from xml.etree import cElementTree as ET
from pysimplesoap.client import SoapClient

from imomo import models, ROOT_PATH

ODM_CV_LOCATION = 'http://his.cuahsi.org/odmcv_1_1/odmcv_1_1.asmx'
ODM_CV_ACTION = 'http://his.cuahsi.org/his/1.1/ws/'

DATA_DIR = 'data'
ODM_DIR = 'odm-1.1'

CV_NAMES = ['CensorCodeCV', 'DataTypeCV', 'GeneralCategoryCV',
            'SampleMediumCV', 'SampleTypeCV',
            'SpeciationCV', 'TopicCategoryCV', 'ValueTypeCV',
            'VariableNameCV', 'VerticalDatumCV']

RESTART_SEQ_SQL = """SELECT setval('%s', %d, false)"""
MAX_TRIES = -1


def _controlled_vocabulary_path(cv_name):
    return os.path.abspath(os.path.join(ROOT_PATH, os.path.pardir, DATA_DIR,
                                        ODM_DIR, '%s.xml' % cv_name.lower()))

UNITS_PATH = os.path.abspath(os.path.join(ROOT_PATH, os.path.pardir, DATA_DIR,
                                          ODM_DIR, 'units.xml'))
SPATIAL_REFERENCES_PATH = os.path.abspath(os.path.join(
    ROOT_PATH, os.path.pardir, DATA_DIR, ODM_DIR, 'spatial-references.xml'))


def _download_controlled_vocabulary(cv_name):
    soap_client = SoapClient(location=ODM_CV_LOCATION, action=ODM_CV_ACTION)
    soap_result = soap_client.call(method='Get%s' % cv_name)
    text = unicode(soap_result.children().children().children())
    with open(_controlled_vocabulary_path(cv_name), 'w') as f:
        f.write(text.encode('utf-8'))


def _download_units():
    soap_client = SoapClient(location=ODM_CV_LOCATION, action=ODM_CV_ACTION)
    soap_result = soap_client.call(method='GetUnits')
    text = unicode(soap_result.children().children().children())
    with open(UNITS_PATH, 'w') as f:
        f.write(text.encode('utf-8'))


def _download_spatial_references():
    soap_client = SoapClient(location=ODM_CV_LOCATION, action=ODM_CV_ACTION)
    soap_result = soap_client.call(method='GetSpatialReferences')
    text = unicode(soap_result.children().children().children())
    with open(SPATIAL_REFERENCES_PATH, 'w') as f:
        f.write(text.encode('utf-8'))


def load_controlled_vocabulary(imomo_init, cv_name, tries=0):
    cv_model = getattr(models, cv_name)
    try:
        tree = ET.parse(_controlled_vocabulary_path(cv_name))
        root = tree.getroot()
        records = root[0]
        for record in records:
            imomo_init.session.add(cv_model(term=record[0].text,
                                            definition=record[1].text))
        imomo_init.commit()
    except:
        if tries > MAX_TRIES:
            raise
        _download_controlled_vocabulary(cv_name)
        load_controlled_vocabulary(imomo_init, cv_name, tries=tries+1)


def load_units(imomo_init, tries=0):
    try:
        tree = ET.parse(UNITS_PATH)
        root = tree.getroot()
        records = root[0]
        max_id = -1
        for record in records:
            imomo_init.session.add(models.Unit(
                id=record[0].text,
                unit_name=record[1].text.strip(),
                unit_type=record[2].text.strip(),
                unit_abbv=record[3].text.strip()))
            max_id = max(int(record[0].text), max_id)
        imomo_init.commit()
        imomo_init.engine.execute(RESTART_SEQ_SQL % ('unit_id_seq', max_id+1))
    except:
        if tries > MAX_TRIES:
            raise
        _download_units()
        load_units(imomo_init, tries=tries+1)


def load_spatial_references(imomo_init, tries=0):
    try:
        tree = ET.parse(SPATIAL_REFERENCES_PATH)
        root = tree.getroot()
        records = root[0]
        max_id = -1
        for record in records:
            imomo_init.session.add(models.SpatialReference(
                id=record[0].text,
                srs_id=record[1].text.strip(),
                srs_name=record[2].text.strip(),
                is_geographic=strtobool(record[3].text.strip()),
                notes=record[4].text))
            max_id = max(int(record[0].text), max_id)
        imomo_init.commit()
        imomo_init.engine.execute(RESTART_SEQ_SQL %
                                  ('spatialreference_id_seq', max_id+1))
    except:
        if tries > MAX_TRIES:
            raise
        _download_spatial_references()
        load_spatial_references(imomo_init, tries=tries+1)


def default_odm_objects(imomo_init):
    odm_version = models.ODMVersion()
    imomo_init.session.add(odm_version)
    topic_category = imomo_init.session.query(models.TopicCategoryCV).filter(
        models.TopicCategoryCV.term == 'Unknown').one()
    iso_metadata_default = models.ISOMetadata(
        id=0, topic_category_id=topic_category.id)
    imomo_init.session.add(iso_metadata_default)
    lab_method_default = models.LabMethod(id=0)
    imomo_init.session.add(lab_method_default)
    method_default = models.Method(id=0, method_description='Unknown')
    imomo_init.session.add(method_default)
    imomo_init.commit()


def preload(imomo_init):
    for cv_name in CV_NAMES:
        load_controlled_vocabulary(imomo_init, cv_name)
    load_units(imomo_init)
    load_spatial_references(imomo_init)
    default_odm_objects(imomo_init)


if __name__ == '__main__':
    preload()
