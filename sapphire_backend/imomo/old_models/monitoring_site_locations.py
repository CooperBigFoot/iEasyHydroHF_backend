from sqlalchemy import DECIMAL, Boolean, Column, Float, ForeignKey, Integer, Sequence, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .data_sources import Source
from .orm import CVMixin, ImomoBase, session_required


class SpatialReference(ImomoBase):
    """Table for the reference systems for spatial data.


    This table collects the reference systems that can be used to express
    physical locations.

    Attributes:
        srs_id: Integer identifier for the Spatial Reference system
        srs_name: Name of the Spatial Reference System.
        is_geographic: Indicates whether the spatial reference system uses
                       geographical coordinates.
        notes: Additional descriptive information about the Spatial Reference
               System.
    """

    srs_id = Column(Integer)
    srs_name = Column(String(255), nullable=False, index=True)
    is_geographic = Column(Boolean)
    notes = Column(Text)


class VerticalDatumCV(ImomoBase, CVMixin):
    """Table for the controlled vocabulary of the vertical datum.

    The attributes are as defined in the CVMixin class.
    """

    pass


class VirtualSiteAssociation(ImomoBase):
    id = Column(Integer, Sequence("virtualsiteassociation_id_seq"), primary_key=True)
    aggregation_id = Column(Integer, ForeignKey("site.id"), primary_key=True)
    virtual_site_id = Column(Integer, ForeignKey("site.id"), primary_key=True)
    weighting = Column(DECIMAL(5, 2), nullable=False)
    __table_args__ = (UniqueConstraint("aggregation_id", "virtual_site_id"),)

    virtual_site = relationship("Site", foreign_keys=virtual_site_id, lazy="joined")

    aggregation = relationship("Site", foreign_keys=aggregation_id, lazy="joined")

    def __repr__(self):
        return f"<VirtualSiteAssociation: {self.aggregation_id} -> {self.virtual_site_id} ({self.weighting} %)>"


class Site(ImomoBase):
    """Table for the sites of data collection.

    This table represent the sites where the data values are observed or
    collected. The sites are associated with a single data source, this
    represents ownership of the observation site in the same manner as
    the data values are owned by a single data source.

    Attributes:
        site_code: Unique local code used by the data source to identify
                   the site (50 char limit).
        site_name: Easily identifiable name (255 char limit).
        source: Owner data source.
        latitude: Latitude value.
        longitude: Longitude value.
        lat_long_datum_id: Foreign key to the coordinate reference
                           system used for the latitude, longitude.
        elevation_m: Elevation value for the site, in meters.
        vertical_datum_id: Foreign key to the reference for the elevation
                           value.
        local_x: X-coordinate for the local projection.
        local_y: Y-coordinate for the local projection.
        local_projection_id: Foreign key to the reference projection used
                             for the local coordinates, if any.
        pos_accuracy_m: Accuracy in meters of the site's location.
        country: Country where the site is located.
        basin: Basin where the site is located.
        region: Administrative region according to the data source.
        comments: Additional comments for the site.
    """

    METEO_SUFFIX = "m"

    id = Column(Integer, Sequence("site_id_seq"), primary_key=True)
    site_code = Column(String(50), nullable=False, index=True, unique=True)
    site_name = Column(String(255), nullable=False, index=True, unique=False)
    source_id = Column(ForeignKey(Source.id), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    lat_long_datum_id = Column(ForeignKey(SpatialReference.id), nullable=False)
    elevation_m = Column(Float, default=0.0)
    vertical_datum_id = Column(ForeignKey(VerticalDatumCV.id))
    local_x = Column(Float)
    local_y = Column(Float)
    local_projection_id = Column(ForeignKey(SpatialReference.id))
    pos_accuracy_m = Column(Float)
    country = Column(String(255), nullable=False)
    basin = Column(String(255), nullable=False)
    region = Column(String(255), nullable=False, default="Unknown")
    comments = Column(Text)

    catchment_area_id = Column(Integer)

    is_virtual = Column(Boolean, default=False, nullable=False)

    aggregation_site_associations = relationship(
        "VirtualSiteAssociation",
        primaryjoin=id == VirtualSiteAssociation.virtual_site_id,
        lazy="joined",
        order_by=VirtualSiteAssociation.id,
        cascade="all,delete",
    )

    virtual_site_associations = relationship(
        "VirtualSiteAssociation",
        primaryjoin=id == VirtualSiteAssociation.aggregation_id,
        lazy="joined",
        order_by=VirtualSiteAssociation.id,
        cascade="all,delete",
    )

    virtual_sites = relationship(
        "Site",
        secondary=VirtualSiteAssociation.__table__,
        primaryjoin=VirtualSiteAssociation.aggregation_id == id,
        secondaryjoin=VirtualSiteAssociation.virtual_site_id == id,
        order_by=VirtualSiteAssociation.id,
        lazy="joined",
    )

    aggregations = relationship(
        "Site",
        secondary=VirtualSiteAssociation.__table__,
        primaryjoin=VirtualSiteAssociation.virtual_site_id == id,
        secondaryjoin=VirtualSiteAssociation.aggregation_id == id,
        order_by=VirtualSiteAssociation.id,
        lazy="joined",
    )

    data_values = relationship("DataValue", cascade="all,delete")
    discharge_models = relationship(
        "DischargeModel",
        cascade="all,delete",
        lazy="dynamic",
    )
    discharge_curve_settings = relationship("DischargeCurveSettings", cascade="all,delete")
    forecast_models = relationship("ForecastModel", cascade="all,delete")
    forecast_results = relationship("ForecastResult", cascade="all,delete")

    @property
    def site_code_repr(self):
        if self.site_code.endswith(self.METEO_SUFFIX):
            return self.site_code[:-1]

        return self.site_code

    @classmethod
    def is_not_meteo_(cls):
        return cls.site_code.notilike(f"%{cls.METEO_SUFFIX}")

    @classmethod
    def is_meteo_(cls):
        return cls.site_code.like(f"%{cls.METEO_SUFFIX}")

    @property
    def site_type(self):
        if self.is_meteo_site:
            return "meteo"
        elif self.is_virtual:
            return "virtual-discharge"
        else:
            return "discharge"

    @property
    def is_meteo_site(self):
        return self.site_code.endswith(self.METEO_SUFFIX)

    @property
    def is_discharge_site(self):
        return not self.is_meteo_site

    @session_required
    def set_default_lat_long_datum_id(self, session):
        """Sets the lat_long_datum_id attribute to the default value.

        The value assigned is a sensible default for spatial reference systems,
        namely the entry corresponding to the WGS84 SRS.

        Args:
            session: The session object to use to query the database.
        """
        self.lat_long_datum_id = session.query(SpatialReference.id).filter(SpatialReference.srs_id == 4326).scalar()

    def to_jsonizable(self, exclude=None):
        jsonizable = super().to_jsonizable(exclude)

        if jsonizable["site_code"].endswith(self.METEO_SUFFIX):
            jsonizable["site_code"] = jsonizable["site_code"][:-1]

        jsonizable["site_type"] = self.site_type

        if self.is_virtual:
            jsonizable["aggregations"] = []
            for aggregation_ass in self.aggregation_site_associations:
                jsonizable["aggregations"].append(
                    {
                        "id": aggregation_ass.aggregation_id,
                        "weighting": float(aggregation_ass.weighting),
                        "site_code": aggregation_ass.aggregation.site_code,
                        "site_name": aggregation_ass.aggregation.site_name,
                    }
                )
        else:
            jsonizable["virtual_stations"] = []
            for virtual_sites_ass in self.virtual_site_associations:
                jsonizable["virtual_stations"].append(
                    {
                        "id": virtual_sites_ass.virtual_site_id,
                        "weighting": float(virtual_sites_ass.weighting),
                        "site_code": virtual_sites_ass.virtual_site.site_code,
                        "site_name": virtual_sites_ass.virtual_site.site_name,
                    }
                )
        return jsonizable

    def __str__(self):
        """User-friendly representation of the site instance."""
        return str(self.site_code)

    def __repr__(self):
        site_name = str(self.site_name.encode("utf-8"))
        return f"<Site ({self.site_type}): {site_name} (code: {self.site_code}, id: {self.id})>"
