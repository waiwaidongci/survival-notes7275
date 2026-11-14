from sqlalchemy import ForeignKey,String,Text,Double,Integer,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class FollowupRevision(Base):
    """每个试件随访的不可变修订留痕：原始观察与每次更正各一行。"""
    __tablename__="followup_revisions"
    __table_args__=(UniqueConstraint("specimen_id","revision_no",name="uq_followup_revision"),)
    id:Mapped[int]=mapped_column(primary_key=True)
    specimen_id:Mapped[int]=mapped_column(ForeignKey("specimens.id"))
    revision_no:Mapped[int]
    duration_hours:Mapped[float]=mapped_column(Double)
    event_observed:Mapped[bool]
    note:Mapped[str]=mapped_column(Text)
    source:Mapped[str]=mapped_column(String(24),default="seed")
    correction_id:Mapped[int|None]=mapped_column(ForeignKey("followup_corrections.id"),nullable=True)
    owner:Mapped[str]=mapped_column(String(160),default="")
    created_at:Mapped[str]=mapped_column(String(64),default=now)
