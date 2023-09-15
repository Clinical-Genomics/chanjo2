from typing import Dict

from sqlmodel import Session

from chanjo2.meta.handle_report_contents import get_ordered_levels
from chanjo2.models.pydantic_models import GeneralReportQuery


def get_overview_data(query: GeneralReportQuery, session: Session) -> Dict:
    """Return the information that will be displayed in the coverage overview page."""

    data: Dict = {
        "levels": get_ordered_levels(threshold_levels=query.completeness_thresholds),
        "extras": {
            "default_level": query.default_level,
            "interval_type": query.interval_type.value,
            "samples": [
                {"name": sample.name, "coverage_file_path": sample.coverage_file_path}
                for sample in query.samples
            ],
        },
    }
    return data
