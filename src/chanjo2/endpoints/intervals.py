from typing import Iterator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from chanjo2.constants import MULTIPLE_PARAMS_NOT_SUPPORTED_MSG
from chanjo2.crud.intervals import get_gene_intervals, get_genes
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import resource_lines
from chanjo2.meta.handle_load_intervals import (
    update_exons,
    update_genes,
    update_transcripts,
)
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    Builds,
    ExonBase,
    GeneBase,
    GeneIntervalQuery,
    GeneQuery,
    TranscriptBase,
)

router = APIRouter()


def count_nr_filters(filters: List[str]) -> int:
    """Count the items in a query list that aren't null."""
    return sum(filter is not None for filter in filters)


@router.post("/intervals/load/genes/{build}")
async def load_genes(
    build: Builds,
    file_path: Optional[str] = None,
    session: Session = Depends(get_session),
) -> Response:
    """Load genes in the given genome build."""

    try:
        if file_path:
            gene_lines: Iterator[str] = resource_lines(file_path=file_path)
            nr_loaded_genes: int = await update_genes(
                build=build, lines=gene_lines, session=session
            )
        else:
            nr_loaded_genes: int = await update_genes(build=build, session=session)
        return JSONResponse(
            content={"detail": f"{nr_loaded_genes} genes loaded into the database"}
        )

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ex.args,
        )


@router.post("/intervals/genes", response_model=List[GeneBase])
async def genes(query: GeneQuery, session: Session = Depends(get_session)):
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


@router.post("/intervals/load/transcripts/{build}", response_model=List[GeneBase])
async def load_transcripts(
    build: Builds,
    file_path: Optional[str] = None,
    session: Session = Depends(get_session),
) -> Response:
    """Load transcripts in the given genome build."""

    try:
        if file_path:
            transcripts_lines: Iterator[str] = resource_lines(file_path=file_path)
            nr_loaded_transcripts: int = await update_transcripts(
                build=build, lines=transcripts_lines, session=session
            )
        else:
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


@router.post("/intervals/transcripts", response_model=List[TranscriptBase])
async def transcripts(
    query: GeneIntervalQuery, session: Session = Depends(get_session)
):
    """Return transcripts according to query parameters."""
    nr_filters = count_nr_filters(
        filters=[
            query.ensembl_ids,
            query.hgnc_ids,
            query.hgnc_symbols,
            query.ensembl_gene_ids,
        ]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )
    return get_gene_intervals(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        ensembl_gene_ids=query.ensembl_gene_ids,
        limit=query.limit if nr_filters == 0 else None,
        interval_type=SQLTranscript,
    )


@router.post("/intervals/load/exons/{build}")
async def load_exons(
    build: Builds,
    file_path: Optional[str] = None,
    session: Session = Depends(get_session),
) -> Response:
    """Load exons in the given genome build."""

    try:
        if file_path:
            exons_lines: Iterator[str] = resource_lines(file_path=file_path)
            nr_loaded_exons: int = await update_exons(
                build=build, lines=exons_lines, session=session
            )
        else:
            nr_loaded_exons: int = await update_exons(build=build, session=session)
        return JSONResponse(
            content={"detail": f"{nr_loaded_exons} exons loaded into the database"}
        )

    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ex.args,
        )


@router.post("/intervals/exons", response_model=List[ExonBase])
async def exons(query: GeneIntervalQuery, session: Session = Depends(get_session)):
    """Return exons in the given genome build."""
    nr_filters = count_nr_filters(
        filters=[
            query.ensembl_ids,
            query.hgnc_ids,
            query.hgnc_symbols,
            query.ensembl_gene_ids,
        ]
    )
    if nr_filters > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MULTIPLE_PARAMS_NOT_SUPPORTED_MSG,
        )

    return get_gene_intervals(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_ids,
        hgnc_ids=query.hgnc_ids,
        hgnc_symbols=query.hgnc_symbols,
        ensembl_gene_ids=query.ensembl_gene_ids,
        limit=query.limit if nr_filters == 0 else None,
        interval_type=SQLExon,
    )
