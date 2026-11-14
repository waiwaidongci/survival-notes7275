from sqlalchemy import ForeignKey,String,JSON,Text,Double,Integer
from sqlalchemy.orm import Mapped,mapped_column
from ..config.database import Base
from ..utils.clock import now
class SurvivalRun(Base):
    __tablename__="survival_runs"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(120))
    cohort_a_id:Mapped[int]=mapped_column(ForeignKey("test_cohorts.id"))
    cohort_b_id:Mapped[int]=mapped_column(ForeignKey("test_cohorts.id"))
    confidence:Mapped[float]=mapped_column(Double,default=.95)
    status:Mapped[str]=mapped_column(String(24),default="queued")
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(Text,default="")
    owner:Mapped[str]=mapped_column(String(100))
    created_at:Mapped[str]=mapped_column(String(64),default=now)
    # 入队/重算所针对的数据修订号，与已完成结果对应的数据修订号
    target_revision:Mapped[int]=mapped_column(Integer,default=0)
    result_revision:Mapped[int|None]=mapped_column(Integer,nullable=True)
