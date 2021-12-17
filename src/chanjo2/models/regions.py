from typing import Optional

from sqlmodel import Field, SQLModel


class RegionBase(SQLModel):
    name: str
    file_path: str
    version: int = 1
    genome_build: str


class Region(RegionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class RegionCreate(RegionBase):
    pass


class RegionRead(RegionBase):
    id: int

