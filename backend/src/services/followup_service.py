from fastapi import HTTPException
from ..models import FollowupEvent
from ..utils.serialize import record
from .audit_service import log

def annotate_followup(db,eid,data,user):
    event=db.get(FollowupEvent,eid)
    if not event:raise HTTPException(404,"随访记录不存在")
    # 备注不改变终态时长/状态，不产生新修订号，也不触发研究重算
    event.note=data.note;log(db,user.email,"followup.annotate",event.id);db.commit();return record(event)
