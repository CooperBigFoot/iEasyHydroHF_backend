from decimal import Decimal

from sapphire_backend.estimations.models import HydrologicalNormVirtual
from sapphire_backend.metrics.choices import NormType
from sapphire_backend.utils.rounding import custom_round, hydrological_round


class TestVirtualStationHydrologicalNorm:
    def test_discharge_norm_decadal_two_virtual_associations(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        decadal_discharge_norm_manual_hydro_station_kyrgyz,
        decadal_discharge_norm_manual_second_hydro_station_kyrgyz,
    ):
        virtual_norm_expected = hydrological_round(
            virtual_station_association_one.weight
            / Decimal(100)
            * decadal_discharge_norm_manual_hydro_station_kyrgyz.value
            + virtual_station_association_two.weight
            / Decimal(100)
            * decadal_discharge_norm_manual_second_hydro_station_kyrgyz.value
        )

        virtual_norm_estimated = HydrologicalNormVirtual.objects.get(
            ordinal_number=decadal_discharge_norm_manual_hydro_station_kyrgyz.ordinal_number,
            norm_type=NormType.DECADAL,
            station_id=virtual_station.uuid,
        ).value

        assert custom_round(virtual_norm_estimated, 6) == custom_round(virtual_norm_expected, 6)

    def test_discharge_norm_decadal_three_virtual_associations(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        virtual_station_association_three,
        decadal_discharge_norm_manual_hydro_station_kyrgyz,
        decadal_discharge_norm_manual_second_hydro_station_kyrgyz,
        decadal_discharge_norm_manual_third_hydro_station_kyrgyz,
    ):
        virtual_norm_expected = hydrological_round(
            virtual_station_association_one.weight
            / Decimal(100)
            * decadal_discharge_norm_manual_hydro_station_kyrgyz.value
            + virtual_station_association_two.weight
            / Decimal(100)
            * decadal_discharge_norm_manual_second_hydro_station_kyrgyz.value
            + virtual_station_association_three.weight
            / Decimal(100)
            * decadal_discharge_norm_manual_third_hydro_station_kyrgyz.value
        )

        virtual_norm_estimated = HydrologicalNormVirtual.objects.get(
            ordinal_number=decadal_discharge_norm_manual_hydro_station_kyrgyz.ordinal_number,
            norm_type=NormType.DECADAL,
            station_id=virtual_station.uuid,
        ).value

        assert custom_round(virtual_norm_estimated, 6) == custom_round(virtual_norm_expected, 6)

    def test_discharge_norm_monthly(
        self,
        organization,
        virtual_station,
        virtual_station_association_one,
        virtual_station_association_two,
        monthly_discharge_norm_manual_hydro_station_kyrgyz,
        monthly_discharge_norm_manual_second_hydro_station_kyrgyz,
    ):
        virtual_norm_expected = hydrological_round(
            virtual_station_association_one.weight
            / Decimal("100")
            * monthly_discharge_norm_manual_hydro_station_kyrgyz.value
            + virtual_station_association_two.weight
            / Decimal("100")
            * monthly_discharge_norm_manual_second_hydro_station_kyrgyz.value
        )

        virtual_norm_estimated = HydrologicalNormVirtual.objects.get(
            ordinal_number=monthly_discharge_norm_manual_hydro_station_kyrgyz.ordinal_number,
            norm_type=NormType.MONTHLY,
            station_id=virtual_station.uuid,
        ).value

        assert custom_round(virtual_norm_estimated, 6) == custom_round(virtual_norm_expected, 6)
