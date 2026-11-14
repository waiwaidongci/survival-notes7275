from sqlalchemy import String,Text,JSON,Integer
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class FollowupCorrection(Base):
    """整批更正台账：申请的明细、校验结论与生效后的全局数据修订号都留痕。"""
    __tablename__="followup_corrections"
    id:Mapped[int]=mapped_column(primary_key=True)
    reason:Mapped[str]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(24),default="applied")
    items:Mapped[list]=mapped_column(JSON,default=list)
    affected_run_ids:Mapped[list]=mapped_column(JSON,default=list)
    applied_revision:Mapped[int|None]=mapped_column(Integer,nullable=True)
    reject_reason:Mapped[str]=mapped_column(Text,default="")
    owner:Mapped[str]=mapped_column(String(160))
    created_at:Mapped[str]=mapped_column(String(64),default=now)
