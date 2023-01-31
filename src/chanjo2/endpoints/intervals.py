from typing import List

from chanjo2.dbutil import get_session
from chanjo2.models.pydantic_models import CoverageInterval
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlmodel import Session, select

router = APIRouter()


@router.get("/interval/{sample_id}/", response_model=CoverageInterval)
def read_interval(
    *,
    session: Session = Depends(get_session),
    sample_id: str,
    chromosome: str,
    start: int,
    end: int,
):
    sample = session.exec(select(Individual).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )
    coverage_file: D4File = D4File(sample.coverage_file_path)
    res: List[float] = coverage_file.mean([(chromosome, start, end)])
    interval_id: str = f"{chromosome}:{start}-{end}"
    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        sample_id=individual.individual_id,
        interval_id=interval_id,
        mean_coverage=res[0],
    )


@router.get("/{sample_id}/target_coverage", response_model=List[float])
def read_target_coverage(
    *,
    session: Session = Depends(get_session),
    sample_id: str,
):
    sample = session.exec(select(Individual).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )
    coverage_file: D4File = D4File(sample.coverage_file_path)
    with open(sample.region_file_path, "rb") as default_region_file:
        regions: List[tuple[str, int, int]] = parse_bed(
            bed_file=default_region_file.read()
        )
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results


@router.post("/interval_file/{sample_id}/", response_model=List[float])
def read_bed_intervals(
    *,
    session: Session = Depends(get_session),
    sample_id: str,
    interval_file: bytes = File(...),
):
    sample = session.exec(select(Sample).filter(sampple_id == sample_id)).first()
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )
    coverage_file: D4File = D4File(sample.coverage_file_path)
    regions: List[tuple[str, int, int]] = parse_bed(bed_file=interval_file)
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results
