import logging

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_genes
from chanjo2.meta.handle_d4 import get_sample_interval_coverage
from chanjo2.meta.handle_report_contents import get_ordered_levels, set_samples_coverage_files, INTERVAL_TYPE_SQL_TYPE
from chanjo2.models.pydantic_models import GeneralReportQuery

LOG = logging.getLogger("uvicorn.access")


def get_overview_data(query: GeneralReportQuery, session: Session) -> dict:
    """Return the information that will be displayed in the coverage overview page."""

    set_samples_coverage_files(session=session, samples=query.samples)
    samples_d4_files: List[Tuple[str, D4File]] = [
        (sample.name, D4File(sample.coverage_file_path)) for sample in query.samples
    ]
    genes: List[SQLGene] = get_genes(
        db=session,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )
    samples_coverage_stats: Dict[str, List[GeneCoverage]] = {
        sample: get_sample_interval_coverage(
            db=session,
            d4_file=d4_file,
            genes=genes,
            interval_type=INTERVAL_TYPE_SQL_TYPE[query.interval_type],
            completeness_thresholds=query.completeness_thresholds,
        )
        for sample, d4_file in samples_d4_files
    }

    return {
        "extras": {
            "interval_type": query.interval_type.value,
            "samples": [
                {"name": sample.name, "coverage_file_path": sample.coverage_file_path}
                for sample in query.samples
            ],
        },
        "levels": get_ordered_levels(query.completeness_thresholds),
        "samples_coverage_stats": samples_coverage_stats
    }
