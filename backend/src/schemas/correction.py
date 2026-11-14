import math
from typing import Literal
from pydantic import BaseModel,Field,field_validator
class CorrectionItem(BaseModel):
    specimen_code:str=Field(min_length=1,max_length=80)
    expected_revision:int=Field(ge=1)
    duration_hours:float|None=Field(default=None,allow_inf_nan=True)
    event_observed:bool|None=None
    @field_validator("duration_hours")
    @classmethod
    def _check_duration(cls,v):
        if v is None:return v
        if not math.isfinite(v) or v<=0 or v>1e6:
            raise ValueError("随访时长必须是(0,1000000]内的有限小时数")
        return v
class CorrectionBatch(BaseModel):
    reason:str=Field(min_length=8,max_length=1000)
    items:list[CorrectionItem]=Field(min_length=1,max_length=500)
