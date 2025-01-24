from faker import Faker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

from sapphire_backend.imomo.old_models import (
    Source as OldSource,
    Site as OldSite,
    DischargeModel as OldDischargeModel,
    VirtualSiteAssociation as OldVirtualSiteAssociation,
    DataValue,
    Variable,
    CensorCodeCV,
    QualityControlLevel,
    Unit,
    VariableNameCV,
    SampleMediumCV,
    ValueTypeCV,
    DataTypeCV,
    GeneralCategoryCV,
    SpeciationCV,
)
from sapphire_backend.imomo.data_structs.standard_data import Variables

fake = Faker("ru_RU")


class OldDBFactory:
    @staticmethod
    def create_session():
        engine = create_engine('sqlite:///:memory:')

        # Create all necessary tables for testing
        metadata = MetaData()
        for table in [
            OldSource.__table__,
            OldSite.__table__,
            OldDischargeModel.__table__,
            Variable.__table__,
            DataValue.__table__,
            CensorCodeCV.__table__,
            QualityControlLevel.__table__,
            OldVirtualSiteAssociation.__table__,
            VariableNameCV.__table__,
            Unit.__table__,
            SampleMediumCV.__table__,
            ValueTypeCV.__table__,
            DataTypeCV.__table__,
            GeneralCategoryCV.__table__,
            SpeciationCV.__table__,
        ]:
            table.metadata = metadata
            table.create(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        # Create default CV entries
        censor_code = CensorCodeCV(term='nc', definition='not censored')
        session.add(censor_code)

        quality_control = QualityControlLevel(
            quality_control_level_code=1,
            definition='Raw data',
            explanation='Raw data from source'
        )
        session.add(quality_control)

        # Add ALL required variable-related entries
        variable_name = VariableNameCV(
            term="Water Level",
            definition="Height of water surface above reference point"
        )
        session.add(variable_name)

        speciation = SpeciationCV(
            term="Not Applicable",
            definition="No speciation"
        )
        session.add(speciation)

        unit = Unit(
            unit_name="centimeter",
            unit_type="Length",
            unit_abbv="cm"
        )
        session.add(unit)

        time_unit = Unit(
            unit_name="hour",
            unit_type="Time",
            unit_abbv="hr"
        )
        session.add(time_unit)

        sample_medium = SampleMediumCV(
            term="Surface Water",
            definition="Surface water measurement"
        )
        session.add(sample_medium)

        value_type = ValueTypeCV(
            term="Field Observation",
            definition="Value obtained from field observation"
        )
        session.add(value_type)

        data_type = DataTypeCV(
            term="Continuous",
            definition="Continuous measurement"
        )
        session.add(data_type)

        general_category = GeneralCategoryCV(
            term="Hydrology",
            definition="Hydrological measurement"
        )
        session.add(general_category)

        session.commit()

        return session


class OldSourceFactory:
    @staticmethod
    def create(session, **kwargs):
        defaults = {
            "organization": "КыргызГидроМет",
            "year_type": "hydro_year",
            "language": "ru",
            "country": "Kyrgyzstan",
            "city": "Bishkek",
            "address": "Test Address",
            "zip_code": "720000",
            "email": "test@example.com",
            "contact_name": "Test Contact",
            "phone": "123456789",
            "citation": "Test Citation",
            "iso_metadata_id": 0,
        }

        defaults.update(kwargs)
        source = OldSource(**defaults)
        session.add(source)
        session.commit()
        return source


class OldSiteFactory:
    @staticmethod
    def create(session, source=None, **kwargs):
        if not source:
            source = OldSourceFactory.create(session)

        defaults = {
            "site_code": "1234",
            "site_name": "Test Station",
            "source_id": source.id,
            "latitude": 42.8746,
            "longitude": 74.5698,
            "lat_long_datum_id": 1,
            "country": source.country,
            "basin": "Нарын",
            "region": "ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ",
        }

        defaults.update(kwargs)
        site = OldSite(**defaults)
        session.add(site)
        session.commit()
        return site


class OldDischargeModelFactory:
    @staticmethod
    def create(session, site=None, **kwargs):
        if not site:
            site = OldSiteFactory.create(session)

        defaults = {
            "site": site,
            "model_name": "Test Model",
            "param_a": 1.0,
            "param_b": 2.0,
            "param_c": 3.0,
            "param_delta_level": 0.0,
            "valid_from": None,
        }

        defaults.update(kwargs)
        model = OldDischargeModel(**defaults)
        session.add(model)
        session.commit()
        return model


class DataValueFactory:
    """Factory for creating DataValue instances in old DB"""
    @staticmethod
    def create(session, site, data_value=None, local_date_time=None,
               variable__variable_code=None, ice_phenomena_string=None):
        """Create a DataValue instance"""
        if local_date_time is None:
            local_date_time = datetime(2023, 1, 1, 8, 0)  # naive datetime

        # Get or create variable with ALL required relationships
        variable = session.query(Variable).filter_by(
            variable_code=variable__variable_code or Variables.gauge_height_observation.value
        ).first()

        if variable is None:
            # Get all required related objects
            variable_name = session.query(VariableNameCV).first()
            speciation = session.query(SpeciationCV).first()
            variable_unit = session.query(Unit).filter_by(unit_type="Length").first()
            time_unit = session.query(Unit).filter_by(unit_type="Time").first()
            sample_medium = session.query(SampleMediumCV).first()
            value_type = session.query(ValueTypeCV).first()
            data_type = session.query(DataTypeCV).first()
            general_category = session.query(GeneralCategoryCV).first()

            variable = Variable(
                variable_code=variable__variable_code or Variables.gauge_height_observation.value,
                variable_name_id=variable_name.id,
                speciation_id=speciation.id,
                variable_unit_id=variable_unit.id,
                sample_medium_id=sample_medium.id,
                value_type_id=value_type.id,
                is_regular=False,
                time_support=0,
                time_unit_id=time_unit.id,
                data_type_id=data_type.id,
                general_category_id=general_category.id,
                no_data_value=-9999
            )
            session.add(variable)
            session.flush()

        # Get default censor code and quality control level
        censor_code = session.query(CensorCodeCV).first()
        quality_control = session.query(QualityControlLevel).first()

        # Create data value using IDs instead of objects
        data_value_obj = DataValue(
            data_value=data_value if data_value is not None else 123.45,
            local_date_time=local_date_time,  # naive datetime
            utc_offset=6.0,
            date_time_utc=local_date_time.replace(tzinfo=timezone.utc),  # UTC aware datetime
            ice_phenomena_string=ice_phenomena_string,
            site=site,
            variable=variable,
            method_id=1,
            source_id=site.source_id,
            censor_code_id=censor_code.id,
            quality_control_level_id=quality_control.id
        )

        session.add(data_value_obj)
        session.commit()

        return data_value_obj
