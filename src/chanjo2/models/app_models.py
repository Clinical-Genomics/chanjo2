from pydantic import BaseModel


class CoverageInterval(BaseModel):
    chromosome: str
    start: int
    end: int
    individual_id: str
    interval_id: str
    mean_coverage: float
