# -*- encoding: UTF-8 -*-
import os

import yaml

from imomo import ROOT_PATH
from imomo.models import Category, Method, QualityControlLevel, Source, User,\
    Variable, VariableNameCV, SpeciationCV, SampleMediumCV, ValueTypeCV,\
    DataTypeCV, GeneralCategoryCV

DATA_DIR = os.path.abspath(os.path.join(ROOT_PATH, os.pardir, 'data'))


def store_all(imomo_init):
    store_minimum(imomo_init)
    store_user_data(imomo_init)


def store_minimum(imomo_init):
    store_quality_control_levels(imomo_init)
    store_variable_names(imomo_init)
    store_variables(imomo_init)
    store_variable_categories(imomo_init)


def store_user_data(imomo_init):
    store_data_sources(imomo_init)
    store_users(imomo_init)
    store_methods(imomo_init)


def store_data_sources(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'data_sources.yaml'), 'r'))
    for document in loaded_documents:
        source = Source(**document)
        imomo_init.session.add(source)
    imomo_init.session.commit()


def store_users(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'users.yaml'), 'r'))
    for document in loaded_documents:
        imomo_init.session.add(User(**document))
    imomo_init.commit()


def store_variable_names(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'variable_names.yaml'), 'r'))
    for document in loaded_documents:
        variable_name = VariableNameCV(**document)
        imomo_init.session.add(variable_name)
    imomo_init.session.commit()


def store_variables(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'variables.yaml'), 'r'))
    for document in loaded_documents:
        document['variable_name_id'] = imomo_init.session.query(
            VariableNameCV.id).filter(
            VariableNameCV.term == document['variable_name']).scalar()
        del document['variable_name']
        document['speciation_id'] = imomo_init.session.query(
            SpeciationCV.id).filter(
            SpeciationCV.term == document['speciation']).scalar()
        del document['speciation']
        document['sample_medium_id'] = imomo_init.session.query(
            SampleMediumCV.id).filter(
            SampleMediumCV.term == document['sample_medium']).scalar()
        del document['sample_medium']
        document['value_type_id'] = imomo_init.session.query(
            ValueTypeCV.id).filter(
            ValueTypeCV.term == document['value_type']).scalar()
        del document['value_type']
        document['data_type_id'] = imomo_init.session.query(
            DataTypeCV.id).filter(
            DataTypeCV.term == document['data_type']).scalar()
        del document['data_type']
        document['general_category_id'] = imomo_init.session.query(
            GeneralCategoryCV.id).filter(
            GeneralCategoryCV.term == document['general_category']).scalar()
        del document['general_category']
        variable = Variable(**document)
        imomo_init.session.add(variable)
    imomo_init.session.commit()


def store_quality_control_levels(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'quality_control_levels.yaml'), 'r'))
    for document in loaded_documents:
        quality_control_level = QualityControlLevel(**document)
        imomo_init.session.add(quality_control_level)
    imomo_init.session.commit()


def store_methods(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'methods.yaml'), 'r'))
    for document in loaded_documents:
        method = Method(**document)
        imomo_init.session.add(method)
    imomo_init.session.commit()


def store_variable_categories(imomo_init):
    loaded_documents = yaml.load_all(
        open(os.path.join(DATA_DIR, 'ice_phenomena_categories.yaml'), 'r'))
    variable_id = imomo_init.session.query(Variable.id).filter(
        Variable.variable_code == '0011').scalar()
    for document in loaded_documents:
        imomo_init.session.add(Category(variable_id=variable_id,
                                        **document))
    imomo_init.session.commit()
