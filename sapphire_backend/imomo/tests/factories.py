from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sapphire_backend.imomo.old_models import Source as OldSource, Site as OldSite, DischargeModel as OldDischargeModel

fake = Faker("ru_RU")

class OldDBFactory:
    @staticmethod
    def create_session():
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker(bind=engine)
        return Session()

class OldSourceFactory:
    @staticmethod
    def create(session, **kwargs):
        source = OldSource(
            organization="КыргызГидроМет",
            year_type="hydro_year",
            language="ru",
            country="Kyrgyzstan",
            city="Bishkek",
            **kwargs
        )
        session.add(source)
        session.commit()
        return source

class OldSiteFactory:
    @staticmethod
    def create(session, source=None, **kwargs):
        if not source:
            source = OldSourceFactory.create(session)

        site = OldSite(
            site_code="1234",
            site_name="Test Station",
            site_type="discharge",
            source=source,
            basin="Нарын",
            region="ЖАЛАЛ-АБАДСКАЯ ОБЛАСТЬ",
            **kwargs
        )
        session.add(site)
        session.commit()
        return site
