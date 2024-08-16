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
    sql_intervals: List[Union[SQLGene, SQLTranscript, SQLExon]],
    intervals_coords: List[str],
    completeness_thresholds: List[Optional[int]],
    default_threshold: int,
    report_data: dict,
) -> None:
    """Compute stats to populate a coverage report and coverage overview for one sample."""

    if not intervals_coords:
        return

    # Compute intervals coverage
    intervals_coverage: List[float] = get_d4tools_intervals_mean_coverage(
        d4_file_path=d4_file_path, intervals=intervals_coords
    )
    completeness_row_dict: dict = {"mean_coverage": mean(intervals_coverage)}

    # Compute intervals coverage completeness
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

    interval_ids = set()
    thresholds_dict = {threshold: [] for threshold in completeness_thresholds}
    incomplete_coverages_rows: List[Tuple[int, str, str, str, float]] = []
    nr_intervals_covered_under_custom_threshold: int = 0
    genes_covered_under_custom_threshold = set()

    for interval_nr, interval in enumerate(sql_intervals):
        if interval.ensembl_id in interval_ids:
            continue
        for threshold in completeness_thresholds:
            interval_coverage_at_threshold: float = intervals_coverage_completeness[
                interval.ensembl_id
            ][threshold]
            thresholds_dict[threshold].append(interval_coverage_at_threshold)

            # Collect intervals which are not completely covered at the custom threshold
            if threshold == default_threshold and interval_coverage_at_threshold < 1:
                nr_intervals_covered_under_custom_threshold += 1
                interval_ensembl_gene: str = (
                    interval.ensembl_id
                    if interval.ensembl_id.startswith("ENSG")
                    else interval.ensembl_gene_id
                )
                interval_hgnc_id: int = gene_ids_mapping[interval_ensembl_gene][
                    "hgnc_id"
                ]
                interval_hgnc_symbol: str = gene_ids_mapping[interval_ensembl_gene][
                    "hgnc_symbol"
                ]
                genes_covered_under_custom_threshold.add(interval_hgnc_symbol)
                incomplete_coverages_rows.append(
                    (
                        interval_hgnc_symbol,
                        interval_hgnc_id,
                        interval.ensembl_id,
                        sample_name,
                        round(interval_coverage_at_threshold * 100, 2),
                    )
                )

        interval_ids.add(interval.ensembl_id)

    for threshold in completeness_thresholds:
        completeness_row_dict[f"completeness_{threshold}"] = round(
            mean(thresholds_dict[threshold]) * 100, 2
        )

    report_data["completeness_rows"].append((sample_name, completeness_row_dict))
    report_data["incomplete_coverage_rows"] += incomplete_coverages_rows
    fully_covered_intervals_percent = round(
        100
        * (len(interval_ids) - nr_intervals_covered_under_custom_threshold)
        / len(interval_ids),
        2,
    )
    report_data["default_level_completeness_rows"].append(
        (
            sample_name,
            fully_covered_intervals_percent,
            f"{nr_intervals_covered_under_custom_threshold}/{len(interval_ids)}",
            genes_covered_under_custom_threshold,
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

    bed_lines: List[str] = [
        f"{interval.chromosome}\t{interval.start}\t{interval.stop}\t{interval.ensembl_gene_id or interval.ensembl_id}\t{interval.ensembl_id}"
        for interval in sql_intervals
    ]
    # Write bed lines to a temporary file
    with tempfile.NamedTemporaryFile(mode="w") as intervals_bed:
        intervals_bed.write("\n".join(bed_lines))
        intervals_bed.flush()

        # Compute intervals coverage
        intervals_coverage = get_d4tools_intervals_coverage(
            d4_file_path=d4_file_path, bed_file_path=intervals_bed.name
        )

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
            gene_coverage.mean_coverage: float = intervals_coverage[0]
            gene_coverage.completeness: Dict[int, float] = intervals_completeness[0]
        else:  # Transcript of exon
            inner_intervals_ensembl_ids = set()
            mean_intervals_coverage = []
            mean_intervals_completeness = {
                threshold: [] for threshold in completeness_thresholds
            }

            for line_nr, line in enumerate(bed_lines):
                ensembl_gene: str = line.rstrip().split("\t")[3]
                if ensembl_gene != gene.ensembl_id:
                    continue
                ensembl_id: str = line.rstrip().split("\t")[
                    4
                ]  # transcript or exon Ensembl ID
                if ensembl_id in inner_intervals_ensembl_ids:
                    continue
                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type.__tablename__,
                        "interval_id": ensembl_id,
                        "mean_coverage": intervals_coverage[line_nr],
                        "completeness": intervals_completeness[line_nr],
                    }
                )
                mean_intervals_coverage.append(intervals_coverage[line_nr])
                for threshold in completeness_thresholds:
                    mean_intervals_completeness[threshold].append(
                        intervals_completeness[line_nr][threshold]
                    )
                gene_coverage.inner_intervals.append(interval_coverage)
                inner_intervals_ensembl_ids.add(ensembl_id)

            gene_coverage.mean_coverage = mean(mean_intervals_coverage)
            for threshold in completeness_thresholds:
                mean_intervals_completeness[threshold] = mean(
                    mean_intervals_completeness[threshold]
                )
            gene_coverage.completeness = mean_intervals_completeness
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
