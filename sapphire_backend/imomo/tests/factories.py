from faker import Faker
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from sapphire_backend.imomo.old_models import (
    Source as OldSource,
    Site as OldSite,
    DischargeModel as OldDischargeModel,
    VirtualSiteAssociation as OldVirtualSiteAssociation,
    DataValue,
)

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
