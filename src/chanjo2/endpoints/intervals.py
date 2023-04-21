from typing import List, Optional, Tuple, Union

from chanjo2.constants import (
    WRONG_BED_FILE_MSG,
    WRONG_COVERAGE_FILE_MSG,
    MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
)
from chanjo2.crud.intervals import get_exons, get_genes, get_transcripts
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.meta.handle_d4 import (
    interval_coverage,
    intervals_coverage,
    set_d4_file,
    set_interval,
)
from chanjo2.meta.handle_load_intervals import (
    update_exons,
    update_genes,
    update_transcripts,
)
from chanjo2.models.pydantic_models import (
    Builds,
    CoverageInterval,
    Exon,
    Gene,
    Transcript,
    GeneQuery,
    TranscriptQuery,
)
from fastapi import APIRouter, Depends, File, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pyd4 import D4File
from sqlmodel import Session

router = APIRouter()


def count_nr_filters(filters: List[str]) -> int:
    """Count the items in a query list that aren't null."""
    return sum(param is not None for param in params)


@router.get("/intervals/coverage/d4/interval/", response_model=CoverageInterval)
def d4_interval_coverage(
    coverage_file_path: str,
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    session: Session = Depends(get_session),
):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    interval: Tuple[str, Optional[int], Optional[int]] = set_interval(
        chrom=chromosome, start=start, end=end
    )
    try:
        d4_file: D4File = set_d4_file(coverage_file_path)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        interval=interval,
        mean_coverage=interval_coverage(d4_file, interval),
    )


@router.post(
    "/intervals/coverage/d4/interval_file/", response_model=List[CoverageInterval]
)
def d4_intervals_coverage(coverage_file_path: str, bed_file: bytes = File(...)):
    """Return coverage on the given intervals for a D4 resource located on the disk or on a remote server."""

    try:
        d4_file: D4File = set_d4_file(coverage_file_path=coverage_file_path)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    try:
        intervals: List[Tuple[str, Optional[int], Optional[int]]] = parse_bed(
            bed_file=bed_file
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=WRONG_BED_FILE_MSG,
        )

    return intervals_coverage(d4_file=d4_file, intervals=intervals)


@router.post("/intervals/load/genes/{build}")
async def load_genes(
    build: Builds, session: Session = Depends(get_session)
) -> Union[Response, HTTPException]:
    """Load genes in the given genome build."""

    try:
        nr_loaded_genes: int = await update_genes(build=build, session=session)
        return JSONResponse(
            content={"detail": f"{nr_loaded_genes} genes loaded into the database"}
        )

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ex.args,
        )


@router.post("/intervals/genes")
async def genes(
    query: GeneQuery, session: Session = Depends(get_session)
) -> List[Gene]:
    """Return genes according to query parameters."""
    nr_filters = count_nr_filters(
       filters=[query.ensembl_ids, query.hgnc_ids, query.hgnc_symbols]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )

    return get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        limit=query.limit if nr_filters == 0 else None,
    )


@router.post("/intervals/load/transcripts/{build}")
async def load_transcripts(
    build: Builds, session: Session = Depends(get_session)
) -> Union[Response, HTTPException]:
    """Load transcripts in the given genome build."""

    try:
        nr_loaded_transcripts: int = await update_transcripts(
            build=build, session=session
        )
        return JSONResponse(
            content={
                "detail": f"{nr_loaded_transcripts} transcripts loaded into the database"
            }
        )

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ex.args,
        )


@router.post("/intervals/transcripts")
async def transcripts(
    query: TranscriptQuery, session: Session = Depends(get_session)
) -> List[Transcript]:
    """Return transcripts according to query parameters."""
    nr_filters = count_nr_filters(
        [query.ensembl_ids, query.hgnc_ids, query.hgnc_symbols, query.ensembl_gene_ids]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )
    return get_transcripts(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        ensembl_gene_ids=query.ensembl_gene_ids,
        limit=query.limit if nr_filters == 0 else None,
    )


@router.post("/intervals/load/exons/{build}")
async def load_exons(
    build: Builds, session: Session = Depends(get_session)
) -> Union[Response, HTTPException]:
    """Load exons in the given genome build."""

    try:
        nr_loaded_exons: int = await update_exons(build=build, session=session)
        return JSONResponse(
            content={"detail": f"{nr_loaded_exons} exons loaded into the database"}
        )

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ex.args,
        )


@router.get("/intervals/exons/{build}")
async def exons(
    build: Builds, session: Session = Depends(get_session), limit: int = 100
) -> List[Exon]:
    """Return exons in the given genome build."""
    return get_exons(db=session, build=build, limit=limit)
