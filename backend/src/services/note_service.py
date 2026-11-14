from fastapi import HTTPException
from ..models import SurvivalRun,MaintenanceNote
from ..constants.status import NoteStatus
from ..utils.clock import now
from ..utils.serialize import record
from .audit_service import log

def list_notes(db):return [record(x) for x in db.query(MaintenanceNote).order_by(MaintenanceNote.id.desc()).all()]
def create_note(db,data,user):
    run=db.get(SurvivalRun,data.run_id)
    if not run or run.status!="completed":raise HTTPException(409,"只能为已完成研究提交维护建议")
    if run.result_revision!=run.target_revision:raise HTTPException(409,"研究正在按最新随访修订重算，请等待重算完成后再提交建议")
    row=MaintenanceNote(**data.model_dump(),owner=user.name,status=NoteStatus.SUBMITTED,run_revision_no=run.result_revision)
    db.add(row);db.flush();log(db,user.email,"maintenance.submit",f"{row.id}@rev{row.run_revision_no}");db.commit();return record(row)
def review_note(db,nid,data,user):
    row=db.get(MaintenanceNote,nid)
    if not row:raise HTTPException(404,"维护建议不存在")
    if row.status!=NoteStatus.SUBMITTED:raise HTTPException(409,"已复核或已失效的建议不可重复审批")
    run=db.get(SurvivalRun,row.run_id)
    if run and run.result_revision!=run.target_revision:raise HTTPException(409,"研究已进入新一轮重算，请按最新结果重新提交建议")
    row.status=data.status;row.review_note=data.review_note;row.reviewer=user.name;row.reviewed_at=now()
    log(db,user.email,"maintenance."+data.status,f"{row.id}@rev{row.run_revision_no}");db.commit();return record(row)
