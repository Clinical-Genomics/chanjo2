from chanjo2.models.pydantic_models import TagBase
from chanjo2.models.sql_models import Tag as SQLTag
from sqlmodel import Session


def create_db_tag(db: Session, tag: TagBase) -> SQLTag:
    """Create a tag."""
    db_tag = SQLTag(name=tag.name, type=tag.type, build=tag.build)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag
