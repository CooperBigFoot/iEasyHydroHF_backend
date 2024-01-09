

if __name__ == '__main__':
    import os
    import gettext
    import datetime

    locales = os.environ.get('LOCALES_PATH', 'locales')
    t = gettext.translation('messages', locales, languages=['ru'])
    t.install()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from imomo import secrets
    from imomo.managers.reports import ReportGenerator
    from imomo.models import Site

    engine = create_engine(
        'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}'.format(
            user=secrets.DB_USER,
            password=secrets.DB_PASSWORD,
            host=secrets.DB_HOST,
            port=secrets.DB_PORT,
            db_name=secrets.DB_NAME,
        ), echo=secrets.DB_ECHO)

    session_maker = sessionmaker(bind=engine)
    session_ = session_maker()

    base_dir = 'var'

    report_generator = ReportGenerator(
        'daily_bulletin',
        base_dir + '/template_example.xlsx',
    )

    sites_ = session_.query(Site).filter(Site.source_id == 1).filter(
        Site.is_not_meteo_(),
    ).all()

    #sites_ = [session_.query(Site).filter_by(id=107).one()]
    report_generator.validate()
    report_generator.generate_report(base_dir + '/report.xlsx', session_, sites_, date=datetime.datetime(2019, 2, 10))
