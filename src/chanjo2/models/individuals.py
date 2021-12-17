from typing import Optional

from sqlmodel import Field, SQLModel


class IndividualBase(SQLModel):
    individual_id: str
    coverage_file_path: str


class Individual(IndividualBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IndividualCreate(IndividualBase):
    pass


class IndividualRead(IndividualBase):
    id: int
