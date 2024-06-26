import os

from django.conf import settings
from ieasyreports.core.report_generator import DefaultReportGenerator


class IEasyHydroReportGenerator(DefaultReportGenerator):
    def _get_template_full_path(self) -> str:
        return self.template_filename

    def save_report(self, name: str, output_path: str):
        if output_path is None:
            output_path = os.path.join(settings.MEDIA_ROOT, "reports")

        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        if name is None:
            name = f"{self.template_filename.split('.xlsx')[0]}.xlsx"

        self.template.save(os.path.join(output_path, name))
