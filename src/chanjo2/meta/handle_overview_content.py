from typing import Dict

from sqlmodel import Session

from chanjo2.models.pydantic_models import GeneralReportQuery


def get_overview_data(query: GeneralReportQuery, session: Session) -> Dict:
    """Return the information that will be displayed in the coverage overview page."""

    data: Dict = {
        "extras": {
            "interval_type": query.interval_type.value,
            "samples": [
                {"name": sample.name, "coverage_file_path": sample.coverage_file_path}
                for sample in query.samples
            ],
        },
    }
    return data
