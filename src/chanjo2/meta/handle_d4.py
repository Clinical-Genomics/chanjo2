import logging
import subprocess
import tempfile
from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_gene_intervals, set_sql_intervals
from chanjo2.meta.handle_completeness_tasks import coverage_completeness_multitasker
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    Sex,
    TranscriptTag,
)

CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_MEAN_COVERAGE_INDEX = 3

LOG = logging.getLogger(__name__)


def get_d4tools_chromosome_mean_coverage(
    d4_file_path: str, chromosomes=List[str]
) -> List[Tuple[str, float]]:
    """Return mean coverage over entire chromosomes."""

    chromosomes_stats_mean_cmd: List[str] = subprocess.check_output(
        ["d4tools", "stat", "-s" "mean", d4_file_path],
        text=True,
    ).splitlines()
    chromosomes_coverage: List[Tuple[str, float]] = []
    for line in chromosomes_stats_mean_cmd:
        stats_data: List[str] = line.split("\t")
        if stats_data[CHROM_INDEX] in chromosomes:
            chromosomes_coverage.append(
                (stats_data[CHROM_INDEX], float(stats_data[STATS_MEAN_COVERAGE_INDEX]))
            )
    return chromosomes_coverage


def get_d4tools_intervals_mean_coverage(
    d4_file_path: str, intervals: List[str]
) -> List[float]:
    """Return the mean value over a list of intervals of a d4 file."""

    tmp_bed_file = tempfile.NamedTemporaryFile()
    with open(tmp_bed_file.name, "w") as bed_file:
        bed_file.write("\n".join(intervals))

    return get_d4tools_intervals_coverage(
        d4_file_path=d4_file_path, bed_file_path=tmp_bed_file.name
    )


def get_d4tools_intervals_coverage(
    d4_file_path: str, bed_file_path: str
) -> List[float]:
    """Return the coverage for intervals of a d4 file that are found in a bed file."""

    d4tools_stats_mean_cmd: str = subprocess.check_output(
        ["d4tools", "stat", "--region", bed_file_path, d4_file_path, "--stat", "mean"],
        text=True,
    )

    return [
        float(line.rstrip().split("\t")[3])
        for line in d4tools_stats_mean_cmd.splitlines()
    ]


def get_d4tools_intervals_completeness(
    d4_file_path: str, bed_file_path: str, completeness_thresholds: List[int]
) -> List[Dict]:
    """Return coverage completeness over all intervals of a bed file."""
    covered_threshold_stats = []
    d4tools_stats_perc_cov: str = subprocess.check_output(
        [
            "d4tools",
            "stat",
            "-s",
            f"perc_cov={','.join(str(threshold) for threshold in completeness_thresholds)}",
            "--region",
            bed_file_path,
            d4_file_path,
        ],
        text=True,
    )
    for line in d4tools_stats_perc_cov.splitlines():
        stats_dict: Dict = dict(
            (
                zip(
                    completeness_thresholds,
                    [float(stat) for stat in line.rstrip().split("\t")[3:]],
                )
            )
        )
        covered_threshold_stats.append(stats_dict)

    return covered_threshold_stats


def get_report_sample_interval_coverage(
    d4_file_path: str,
    sample_name: str,
    gene_ids_mapping: Dict[str, dict],
    bed_lines: List[str],
    completeness_thresholds: List[Optional[int]],
    default_threshold: int,
    report_data: dict,
) -> None:
    """Compute stats to populate a coverage report and coverage overview for one sample."""

    # Write bed lines to a temporary file
    with tempfile.NamedTemporaryFile(mode="w") as intervals_bed:
        intervals_bed.write("\n".join(bed_lines))
        intervals_bed.flush()

        # Compute intervals coverage
        intervals_coverage = get_d4tools_intervals_coverage(
            d4_file_path=d4_file_path, bed_file_path=intervals_bed.name
        )
        completeness_row_dict = {"mean_coverage": mean(intervals_coverage)}

        # Compute intervals completeness
        intervals_completeness = get_d4tools_intervals_completeness(
            d4_file_path=d4_file_path,
            bed_file_path=intervals_bed.name,
            completeness_thresholds=completeness_thresholds,
        )

    if len(bed_lines) != len(intervals_coverage) or len(bed_lines) != len(
        intervals_completeness
    ):
        LOG.error("Mismatch in the number of intervals for coverage and completeness")
        return

    # Initialize mappings for completeness and intervals coverage
    for gene_mapping in gene_ids_mapping.values():
        gene_mapping["completeness"] = {
            threshold: [] for threshold in completeness_thresholds
        }
        gene_mapping["intervals_covered_below_custom_threshold"] = []

    thresholds_dict = {threshold: [] for threshold in completeness_thresholds}

    # Populate completeness data for each gene
    for line_nr, line in enumerate(bed_lines):
        ensembl_gene = line.rstrip().split("\t")[3]
        for threshold in completeness_thresholds:
            interval_coverage = intervals_completeness[line_nr][threshold]
            thresholds_dict[threshold].append(interval_coverage)
            gene_ids_mapping[ensembl_gene]["completeness"][threshold].append(
                interval_coverage
            )

    # Calculate and store overall completeness data
    for threshold, values in thresholds_dict.items():
        completeness_row_dict[f"completeness_{threshold}"] = round(
            mean(values) * 100, 2
        )
    report_data["completeness_rows"].append((sample_name, completeness_row_dict))

    # Collect genes not completely covered at the default threshold
    incomplete_coverages_rows = []
    nr_intervals_under_threshold = 0
    genes_under_threshold = []

    for ensembl_gene, gene_mapping in gene_ids_mapping.items():
        mean_coverage = mean(gene_mapping["completeness"][default_threshold])
        if mean_coverage < 1:
            nr_intervals_under_threshold += 1
            incomplete_coverages_rows.append(
                (
                    gene_mapping["hgnc_symbol"],
                    gene_mapping["hgnc_id"],
                    ensembl_gene,
                    sample_name,
                    round(mean_coverage * 100, 2),
                )
            )
            genes_under_threshold.append(gene_mapping["hgnc_symbol"])

    report_data["incomplete_coverage_rows"] = incomplete_coverages_rows

    # Calculate percentage of fully covered intervals
    fully_covered_percent = round(
        100 * (len(bed_lines) - nr_intervals_under_threshold) / len(bed_lines), 2
    )

    report_data["default_level_completeness_rows"].append(
        (
            sample_name,
            fully_covered_percent,
            f"{nr_intervals_under_threshold}/{len(bed_lines)}",
            genes_under_threshold,
        )
    )


def get_sample_interval_coverage(
    db: Session,
    d4_file_path: str,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[GeneCoverage]:

    if not genes:
        return []

    genes_coverage_stats: List[GeneCoverage] = []

    sql_intervals: List[Union[SQLGene, SQLTranscript, SQLExon]] = set_sql_intervals(
        db=db, interval_type=interval_type, genes=genes, transcript_tags=transcript_tags
    )
    interval_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = [
        (interval.ensembl_id, (interval.chromosome, interval.start, interval.stop))
        for interval in sql_intervals
    ]
    intervals_coverage_completeness: Dict[str, dict] = (
        coverage_completeness_multitasker(
            d4_file_path=d4_file_path,
            thresholds=completeness_thresholds,
            interval_ids_coords=interval_ids_coords,
        )
    )

    # Create GeneCoverage objects
    for gene in genes:
        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "interval_id": gene.ensembl_id,
                "mean_coverage": 0,
                "completeness": {},
                "inner_intervals": [],
            }
        )

        if interval_type == SQLGene:  # The interval requested is the genes itself
            gene_coverage.mean_coverage = mean(
                get_d4tools_intervals_mean_coverage(
                    d4_file_path=d4_file_path,
                    intervals=[f"{gene.chromosome}\t{gene.start}\t{gene.stop}"],
                )
            )
            gene_coverage.completeness = intervals_coverage_completeness.get(
                gene.ensembl_id, {}
            )

        else:  # Retrieve transcripts or exons for this gene

            gene_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
                db=db,
                build=gene.build,
                interval_type=interval_type,
                ensembl_ids=None,
                hgnc_ids=None,
                hgnc_symbols=None,
                ensembl_gene_ids=[gene.ensembl_id],
                limit=None,
                transcript_tags=transcript_tags,
            )

            inner_intervals_ensembl_ids = set()
            intervals_bed_coords: List[str] = []
            intervals_mean_completeness: Dict[int:List] = {
                threshold: [] for threshold in completeness_thresholds
            }

            for interval in gene_intervals:
                if interval.ensembl_id in inner_intervals_ensembl_ids:
                    continue

                intervals_bed_coords.append(
                    f"{interval.chromosome}\t{interval.start}\t{interval.stop}"
                )

                for threshold in completeness_thresholds:
                    intervals_mean_completeness[threshold].append(
                        intervals_coverage_completeness[interval.ensembl_id][threshold]
                    )

                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type.__tablename__,
                        "interval_id": interval.ensembl_id,
                        "mean_coverage": mean(
                            get_d4tools_intervals_mean_coverage(
                                d4_file_path=d4_file_path,
                                intervals=[
                                    f"{interval.chromosome}\t{interval.start}\t{interval.stop}"
                                ],
                            )
                        ),
                        "completeness": intervals_coverage_completeness[
                            interval.ensembl_id
                        ],
                    }
                )

                gene_coverage.inner_intervals.append(interval_coverage)
                inner_intervals_ensembl_ids.add(interval.ensembl_id)

            gene_intervals_mean_coverage: List[float] = (
                get_d4tools_intervals_mean_coverage(
                    d4_file_path=d4_file_path, intervals=intervals_bed_coords
                )
            )
            gene_coverage.mean_coverage = (
                mean(gene_intervals_mean_coverage)
                if gene_intervals_mean_coverage
                else 0
            )

            for threshold in completeness_thresholds:
                gene_coverage.completeness[threshold] = (
                    mean(intervals_mean_completeness[threshold])
                    if intervals_mean_completeness[threshold]
                    else 0
                )

        genes_coverage_stats.append(gene_coverage)

    return genes_coverage_stats


def predict_sex(x_cov: float, y_cov: float) -> str:
    """Return predict sex based on sex chromosomes coverage - this code is taken from the old chanjo."""
    if y_cov == 0:
        return Sex.FEMALE.value
    else:
        ratio: float = x_cov / y_cov
        if x_cov == 0 or (ratio > 12 and ratio < 100):
            return Sex.UNKNOWN.value
        elif ratio <= 12:
            # this is the entire prediction, it's usually very obvious
            return Sex.MALE.value
        else:
            # the few reads mapping to the Y chromosomes are artifacts
            return Sex.FEMALE.value


def get_samples_sex_metrics(d4_file_path: str) -> Dict:
    """Compute coverage over sex chromosomes and predicted sex."""

    sex_chroms_coverage: List[Tuple[str, float]] = get_d4tools_chromosome_mean_coverage(
        d4_file_path=d4_file_path, chromosomes=["X", "Y"]
    )

    return {
        "x_coverage": round(sex_chroms_coverage[0][1], 1),
        "y_coverage": round(sex_chroms_coverage[1][1], 1),
        "predicted_sex": predict_sex(
            x_cov=sex_chroms_coverage[0][1], y_cov=sex_chroms_coverage[1][1]
        ),
    }
