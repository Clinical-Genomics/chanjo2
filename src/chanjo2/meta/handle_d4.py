import logging
import subprocess
import tempfile
from statistics import mean
from typing import Dict, List, Optional, Tuple, Union

from pyd4 import D4File
from sqlalchemy.orm import Session

from chanjo2.crud.intervals import get_gene_intervals
from chanjo2.meta.handle_tasks import coverage_completeness_multitasker
from chanjo2.models import SQLExon, SQLGene, SQLTranscript
from chanjo2.models.pydantic_models import (
    GeneCoverage,
    IntervalCoverage,
    IntervalType,
    Sex,
    TranscriptTag,
)

LOG = logging.getLogger("uvicorn.access")
CHROM_INDEX = 0
START_INDEX = 1
STOP_INDEX = 2
STATS_MEAN_COVERAGE_INDEX = 3


def set_interval(
    chrom: str, start: Optional[int] = None, end: Optional[int] = None
) -> Tuple[str, Optional[int], Optional[int]]:
    """Create the interval tuple used by the pyd4 utility."""
    return (chrom, start, end) if start and end else chrom


def get_d4_file(coverage_file_path: str) -> D4File:
    """Create a D4 file from a file path/URL."""
    return D4File(coverage_file_path)


def get_intervals_coords_list(
    intervals: List[Union[SQLGene, SQLTranscript, SQLExon]]
) -> List[Tuple[str, int, int]]:
    """Return the coordinates of a list of intervals as a list of tuples."""
    interval_coords: List[Tuple[str, int, int]] = []
    for interval in intervals:
        interval_coords.append((interval.chromosome, interval.start, interval.stop))
    return interval_coords


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


def get_intervals_mean_coverage(
    d4_file: D4File, intervals: List[Tuple[str, int, int]]
) -> List[float]:
    """Return the mean value over a list of intervals of a d4 file."""
    return d4_file.mean(intervals)


def intervals_coverage(
    d4_file: D4File,
    intervals: List[Tuple[str, int, int]],
    completeness_thresholds: Optional[List[int]],
) -> List[IntervalCoverage]:
    """Return coverage over a list of intervals."""
    intervals_cov: List[IntervalCoverage] = []
    for interval in intervals:
        intervals_cov.append(
            IntervalCoverage(
                chromosome=interval[0],
                start=interval[1],
                end=interval[2],
                mean_coverage=d4_file.mean(interval),
                completeness=get_intervals_completeness(
                    d4_file=d4_file,
                    intervals=[interval],
                    completeness_thresholds=completeness_thresholds,
                ),
            )
        )
    return intervals_cov


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


def get_intervals_completeness(
    d4_file: D4File,
    intervals: List[Tuple[str, int, int]],
    completeness_thresholds: Optional[List[int]],
) -> Optional[Dict[int, float]]:
    """Compute coverage completeness over threshold values for a list of intervals."""

    if not completeness_thresholds:
        return None

    total_region_length: int = 0
    nr_complete_bases_by_threshold: List[int] = [0 for _ in completeness_thresholds]

    for interval in intervals:
        chrom: str = interval[0]
        start: int = interval[1]
        stop: int = interval[2]

        total_region_length += stop - start

        for _, _, d4_tracks_base_coverage in d4_file.enumerate_values(
            chrom, start, stop
        ):  # _ and _ -> interval chromosome and start position
            for index, threshold in enumerate(completeness_thresholds):
                if (
                    d4_tracks_base_coverage[0] >= threshold
                ):  # d4_tracks_base_coverage[0] is the coverage depth for the first track in the d4 file (float)
                    nr_complete_bases_by_threshold[index] += 1

    completeness_values: Dict[int, float] = {}

    for index, threshold in enumerate(completeness_thresholds):
        completeness_values[threshold] = (
            float(nr_complete_bases_by_threshold[index] / total_region_length)
            if nr_complete_bases_by_threshold[index]
            else 0
        )

    return completeness_values


def get_d4tools_sample_genes_coverage(
    d4_file_path: str,
    genes: List[SQLGene],
    completeness_thresholds: List[Optional[int]],
):
    """Return coverage and coverage completeness over entire genes."""
    # Compute genes coverage
    genes_coords: List[str] = [
        f"{gene.chromosome}\t{gene.start}\t{gene.stop}" for gene in genes
    ]
    genes_coverage: List[float] = get_d4tools_intervals_mean_coverage(
        d4_file_path=d4_file_path, intervals=genes_coords
    )
    # Compute genes coverage completeness
    genes_ids_coords: List[Tuple[str, Tuple[str, int, int]]] = [
        (gene.ensembl_id, (gene.chromosome, gene.start, gene.stop)) for gene in genes
    ]
    genes_coverage_completeness: Dict[str, dict] = coverage_completeness_multitasker(
        d4_file_path=d4_file_path,
        thresholds=completeness_thresholds,
        interval_ids_coords=genes_ids_coords,
    )
    # Save stats in coverage objects
    genes_coverage_stats: List[GeneCoverage] = []
    for nr_gene, gene in enumerate(genes):
        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "mean_coverage": genes_coverage[nr_gene],
                "completeness": genes_coverage_completeness[gene.ensembl_id],
                "inner_intervals": [],
            }
        )
        genes_coverage_stats.append(gene_coverage)
    return genes_coverage_stats


def get_d4tools_sample_interval_coverage(
    db: Session,
    d4_file_path: str,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[GeneCoverage]:
    """Return coverage and coverage completeness over genes transcripts or exons."""

    if not genes:
        return []

    # Compute intervals coverage
    sql_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
        db=db,
        build=genes[0].build,
        interval_type=interval_type,
        ensembl_ids=None,
        hgnc_ids=None,
        hgnc_symbols=None,
        ensembl_gene_ids=[gene.ensembl_id for gene in genes],
        limit=None,
        transcript_tags=transcript_tags,
    )
    intervals_coords: List[str] = [
        f"{interval.chromosome}\t{interval.start}\t{interval.stop}"
        for interval in sql_intervals
    ]
    intervals_coverage: List[float] = get_d4tools_intervals_mean_coverage(
        d4_file_path=d4_file_path, intervals=intervals_coords
    )
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
    # Save stats in coverage objects
    genes_coverage_stats: List[GeneCoverage] = []
    thresholds_dict = {threshold: [] for threshold in completeness_thresholds}
    genes_stats: Dict[str, dict] = {
        gene.ensembl_id: {
            "mean_coverage": [],
            "completeness": thresholds_dict,
            "inner_intervals": [],
        }
        for gene in genes
    }

    inner_intervals_ensembl_ids = set()
    for interval_nr, interval in enumerate(sql_intervals):

        interval_ensembl_id: str = interval.ensembl_id
        if interval_ensembl_id in inner_intervals_ensembl_ids:
            continue

        interval_ensembl_gene: str = interval.ensembl_gene_id

        genes_stats[interval_ensembl_gene]["mean_coverage"].append(
            intervals_coverage[interval_nr]
        )
        for threshold in completeness_thresholds:
            genes_stats[interval_ensembl_gene]["completeness"][threshold].append(
                intervals_coverage_completeness[interval_ensembl_id][threshold]
            )

        genes_stats[interval_ensembl_gene]["inner_intervals"].append(
            IntervalCoverage(
                **{
                    "interval_type": interval_type.__tablename__,
                    "interval_id": interval.ensembl_id,
                    "mean_coverage": intervals_coverage[interval_nr],
                    "completeness": intervals_coverage_completeness[
                        interval_ensembl_id
                    ],
                }
            )
        )
        inner_intervals_ensembl_ids.add(interval_ensembl_id)

    for gene in genes:

        gene_mean_coverage = mean(genes_stats[gene.ensembl_id]["mean_coverage"])
        gene_cov_completenes = {}
        for threshold in completeness_thresholds:
            gene_cov_completenes[threshold] = mean(
                genes_stats[gene.ensembl_id]["completeness"][threshold]
            )

        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "mean_coverage": gene_mean_coverage,
                "completeness": gene_cov_completenes,
                "inner_intervals": genes_stats[gene.ensembl_id]["inner_intervals"],
            }
        )
        genes_coverage_stats.append(gene_coverage)

    return genes_coverage_stats


def get_sample_interval_coverage(
    db: Session,
    d4_file: D4File,
    genes: List[SQLGene],
    interval_type: Union[SQLGene, SQLTranscript, SQLExon],
    completeness_thresholds: List[Optional[int]],
    transcript_tags: Optional[List[TranscriptTag]] = [],
) -> List[GeneCoverage]:
    genes_coverage_stats: List[GeneCoverage] = []
    for gene in genes:
        gene_coverage = GeneCoverage(
            **{
                "ensembl_gene_id": gene.ensembl_id,
                "hgnc_id": gene.hgnc_id,
                "hgnc_symbol": gene.hgnc_symbol,
                "interval_type": IntervalType.GENES,
                "mean_coverage": 0,
                "completeness": {},
                "inner_intervals": [],
            }
        )

        if interval_type == SQLGene:  # The interval requested is the genes itself
            gene_coordinates: Tuple[str, int, int] = (
                gene.chromosome,
                gene.start,
                gene.stop,
            )
            gene_coverage.mean_coverage = d4_file.mean(gene_coordinates)
            gene_coverage.completeness = get_intervals_completeness(
                d4_file=d4_file,
                intervals=[gene_coordinates],
                completeness_thresholds=completeness_thresholds,
            )

        else:  # Retrieve transcripts or exons for this gene
            sql_intervals: List[Union[SQLTranscript, SQLExon]] = get_gene_intervals(
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

            intervals_coords: List[Tuple[str, int, int]] = get_intervals_coords_list(
                intervals=sql_intervals
            )

            intervals_mean_covs: List[float] = get_intervals_mean_coverage(
                d4_file=d4_file, intervals=intervals_coords
            )
            gene_coverage.mean_coverage = (
                mean(intervals_mean_covs) if intervals_mean_covs else 0
            )

            gene_coverage.completeness = get_intervals_completeness(
                d4_file=d4_file,
                intervals=intervals_coords,
                completeness_thresholds=completeness_thresholds,
            )

            inner_intervals_ensembl_ids = set()

            for interval in sql_intervals:
                if interval.ensembl_id in inner_intervals_ensembl_ids:
                    continue

                interval_coordinates: Tuple[str, int, int] = (
                    interval.chromosome,
                    interval.start,
                    interval.stop,
                )

                interval_coverage = IntervalCoverage(
                    **{
                        "interval_type": interval_type.__tablename__,
                        "interval_id": _get_interval_id(sql_interval=interval),
                        "mean_coverage": d4_file.mean(interval_coordinates),
                        "completeness": get_intervals_completeness(
                            d4_file=d4_file,
                            intervals=[interval_coordinates],
                            completeness_thresholds=completeness_thresholds,
                        ),
                    }
                )

                gene_coverage.inner_intervals.append(interval_coverage)

                inner_intervals_ensembl_ids.add(interval.ensembl_id)

        genes_coverage_stats.append(gene_coverage)

    return genes_coverage_stats


def _get_interval_id(sql_interval: Union[SQLTranscript, SQLExon]) -> str:
    """Returns an Ensembl ID for an exon or several joined IDs (Ensembl, Mane or RefSeq) for a transcript."""

    interval_ids = []
    interval_as_dict = sql_interval.__dict__
    for field in [member.value for member in TranscriptTag]:
        transcript_tag = interval_as_dict.get(field)
        if transcript_tag:
            interval_ids.append(transcript_tag)

    return ", ".join(interval_ids) or sql_interval.ensembl_id


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
