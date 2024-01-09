# -*- encoding: UTF-8 -*-
from sqlalchemy import Column, Float, String, ForeignKey, Index, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from .monitoring_site_locations import Site
from .orm import ImomoBase, UTCDateTime


class DischargeModel(ImomoBase):
    """Table for the discharge models, also known as rating curves.

    This table represents all discharge models registered and used in the
    system to calculate discharge from gage height measurements. The model
    is a simple power relationship, specifically Q = c(H + a)^b.

    Attributes:
        model_name: A descriptive identifier for the model.
        param_a: The offset parameter in the equation.
        param_b: The exponent in the equation.
        param_c: The gain in the equation.
        param_delta_level: An implicit parameter that represents uncertainty
                           about the current model, its effect is the same as
                           a.
        valid_from: The starting date when the model is valid.
        site_id: Foreign key to the site for which the model was created.
        site: ORM relationship to the site.
    """
    model_name = Column(String(255), nullable=False)
    param_a = Column(Float, nullable=False)
    param_b = Column(Float, nullable=False, default=2)
    param_c = Column(Float, nullable=False)
    param_delta_level = Column(Float, nullable=False, default=0)
    valid_from = Column(UTCDateTime, nullable=True)
    site_id = Column(ForeignKey(Site.id), nullable=False)

    site = relationship(Site)

    __table_args__ = (
        Index('ix_discharge_model_valid_from_desc', valid_from.desc()),
        Index('ix_discharge_model_site_id', site_id),
        UniqueConstraint('site_id', 'valid_from', name='discharge_model_site_id_valid_from_key'),
    )

    def calculate_discharge(self, water_level):
        return self.param_c * (water_level + self.param_a) ** self.param_b

    def __repr__(self):
        return '<DischargeModel ({id}): Q = {c} (H + {a} ) ^ {b} , valid from: {valid_from}>'.format(
            a=self.param_a,
            b=self.param_b,
            c=self.param_c,
            valid_from=self.valid_from,
            id=self.id,
        )


class DischargeCurveSettings(ImomoBase):
    """Table for the discharge curve x/y axis minmax settings

    This table represents chosen settings for displaying each discharge curve

    Attributes:
        min_water_level: minimum y-axis setting;
        max_water_level: maximum y-axis setting;
        min_discharge: minimum x-axis setting;
        max_discharge: maximum x-axis setting;
        fit_viewport_to_data: self-descriptive boolean;
        discharge_model_id: Foreign key to the discharge curve model this setting refers to
        discharge_model: ORM relationship to the discharge curve.
    """
    min_water_level = Column(Float, nullable=False)
    max_water_level = Column(Float, nullable=False)
    min_discharge = Column(Float, nullable=False)
    max_discharge = Column(Float, nullable=False)
    fit_viewport_to_data = Column(Boolean, default=False, nullable=False)
    site_id = Column(ForeignKey(Site.id), nullable=False)

    site = relationship(Site)
