import os
from typing import Any

from django.conf import settings
from ieasyreports.core.report_generator import DefaultReportGenerator


class IEasyHydroReportGenerator(DefaultReportGenerator):
    def _get_template_full_path(self) -> str:
        return self.template_filename

    def get_grouping_attribute(self) -> str | None:
        if self.header_tag_info["tag"] == "SITE_REGION":
            return "region"
        elif self.header_tag_info["tag"] == "SITE_BASIN":
            return "basin"
        else:
            return None

    def sort_stations(self, stations: list[Any]) -> list[Any]:
        grouping_attr = self.get_grouping_attribute()
        if not grouping_attr:
            return stations

        sorted_stations = sorted(
            stations,
            key=lambda s: (
                getattr(s.site, grouping_attr).bulletin_order,
                getattr(s.site, grouping_attr).name,
                s.bulletin_order,
                s.name,
            ),
        )

        return sorted_stations

    def prepare_list_objects(self, list_objects: list[Any]) -> list[Any]:
        return self.sort_stations(list_objects)

    def save_report(self, name: str, output_path: str):
        if output_path is None:
            output_path = os.path.join(settings.MEDIA_ROOT, "reports")

        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        if name is None:
            name = f"{self.template_filename.split('.xlsx')[0]}.xlsx"

        self.template.save(os.path.join(output_path, name))
