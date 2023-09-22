import logging
from typing import Dict, List, Union

from pyd4 import D4File
from sqlmodel import Session

from chanjo2.crud.intervals import get_genes
from chanjo2.meta.handle_d4 import GeneCoverage
from chanjo2.meta.handle_d4 import get_sample_interval_coverage
from chanjo2.meta.handle_report_contents import get_ordered_levels, set_samples_coverage_files, INTERVAL_TYPE_SQL_TYPE
from chanjo2.models.pydantic_models import GeneralReportQuery, IntervalType

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
            completeness_thresholds=[query.default_level],
        )
        for sample, d4_file in samples_d4_files
    }

    return {
        "extras": {
            "default_level": query.default_level,
            "interval_type": query.interval_type.value,
            "samples": [
                {"name": sample.name, "coverage_file_path": sample.coverage_file_path}
                for sample in query.samples
            ],
        },
        "levels": get_ordered_levels(query.completeness_thresholds),
        "incomplete_coverage_rows": get_genes_overview_incomplete_coverage_rows(
            samples_coverage_stats=samples_coverage_stats, interval_type=query.interval_type.value,
            cov_level=query.default_level)
    }


def get_genes_overview_incomplete_coverage_rows(samples_coverage_stats: Dict[str, List[GeneCoverage]],
                                                interval_type: IntervalType, cov_level: int) -> List[str]:
    """Return the rows that populate a gene overview report."""

    LOG.error(samples_coverage_stats)

    def _is_interval_partially_covered(interval_completeness: Union[float, int]) -> bool:
        return interval_completeness < 1

    genes_overview_rows: List[str] = []

    for sample_name, genes_cov_stats_list in samples_coverage_stats.items():
        for gene_cov_stats in genes_cov_stats_list:
            if interval_type == IntervalType.GENES:
                completeness_at_level: float = gene_cov_stats.completeness.get(cov_level)
                if _is_interval_partially_covered(completeness_at_level):
                    genes_overview_rows.append(
                        [gene_cov_stats.hgnc_symbol, gene_cov_stats.hgnc_id, sample_name, completeness_at_level])
            else:
                for inner_interval_stats in gene_cov_stats.inner_intervals:
                    LOG.warning(inner_interval_stats)
                    completeness_at_level: float = inner_interval_stats.completeness.get(cov_level)
                    if _is_interval_partially_covered(completeness_at_level):
                        genes_overview_rows.append(
                            [gene_cov_stats.hgnc_symbol, inner_interval_stats.interval_id, sample_name,
                             completeness_at_level])

    return genes_overview_rows
