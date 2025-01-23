from faker import Faker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from sapphire_backend.imomo.old_models import (
    Source as OldSource,
    Site as OldSite,
    DischargeModel as OldDischargeModel,
    VirtualSiteAssociation as OldVirtualSiteAssociation,
    DataValue,
    Variable,
)
from sapphire_backend.imomo.data_structs.standard_data import Variables

fake = Faker("ru_RU")


class OldDBFactory:
    @staticmethod
    def create_session():
        engine = create_engine('sqlite:///:memory:')

        # Create only the tables we need for testing
        metadata = MetaData()
        for table in [
            OldSource.__table__,
            OldSite.__table__,
            OldDischargeModel.__table__,
            OldVirtualSiteAssociation.__table__,
            DataValue.__table__,
        ]:
            table.metadata = metadata
            table.create(engine)

        Session = sessionmaker(bind=engine)
        return Session()


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
        """Create a DataValue instance

        Args:
            session: SQLAlchemy session
            site: OldSite instance
            data_value: Optional float value
            local_date_time: Optional datetime
            variable__variable_code: Optional variable code from Variables enum
            ice_phenomena_string: Optional ice phenomena string (e.g. "1:50|2:75")
        """
        if local_date_time is None:
            local_date_time = datetime(2023, 1, 1, 8, 0)

        # Create variable
        variable = Variable(
            variable_code=variable__variable_code or Variables.gauge_height_observation.value,
            variable_name="Test Variable",
            variable_unit_id=1  # Assuming unit exists
        )
        session.add(variable)

        # Create data value
        data_value_obj = DataValue(
            data_value=data_value if data_value is not None else 123.45,
            local_date_time=local_date_time,
            utc_offset=6.0,  # Example offset
            date_time_utc=local_date_time,  # Simplified for testing
            ice_phenomena_string=ice_phenomena_string,
            site=site,
            variable=variable,
            method_id=1,  # Default method
            source_id=site.source_id,
            censor_code_id=1,  # Will be set by set_default_censor_code_id
            quality_control_level_id=1  # Will be set by set_default_quality_control_level_id
        )

        # Set default values using the model's methods
        data_value_obj.set_default_censor_code_id(session)
        data_value_obj.set_default_quality_control_level_id(session)

        session.add(data_value_obj)
        session.commit()

        return data_value_obj
