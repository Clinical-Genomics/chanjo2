from importlib_resources import files

BASE_PATH: str = "chanjo2.resources"

CHR_X_Y_EXONS_BUILD_37 = "chrXY_exons_GRCh37.bed"
CHR_X_Y_EXONS_BUILD_38 = "chrXY_exons_GRCh38.bed"
CHR_X_Y_TRANSCRIPTS_BUILD_37 = "chrXY_transcripts_GRCh37.bed"
CHR_X_Y_TRANSCRIPTS_BUILD_38 = "chrXY_transcripts_GRCh38.bed"

CHR_X_Y_EXONS_BUILD_37_PATH = str(files(BASE_PATH).joinpath(CHR_X_Y_EXONS_BUILD_37))
CHR_X_Y_EXONS_BUILD_38_PATH = str(files(BASE_PATH).joinpath(CHR_X_Y_EXONS_BUILD_38))
CHR_X_Y_TRANSCRIPTS_BUILD_37_PATH = str(
    files(BASE_PATH).joinpath(CHR_X_Y_TRANSCRIPTS_BUILD_37)
)
CHR_X_Y_TRANSCRIPTS_BUILD_38_PATH = str(
    files(BASE_PATH).joinpath(CHR_X_Y_TRANSCRIPTS_BUILD_38)
)
