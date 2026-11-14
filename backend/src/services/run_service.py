import csv,io
from fastapi import HTTPException
from ..models import SurvivalRun,TestCohort,MaintenanceNote
from ..constants.status import NoteStatus,RunStatus
from ..utils.serialize import record
from .audit_service import log
from . import job_service

def list_runs(db):return [record(x) for x in db.query(SurvivalRun).order_by(SurvivalRun.id.desc())]
def get_run(db,rid):
    row=db.get(SurvivalRun,rid)
    if not row:raise HTTPException(404,"耐久研究不存在")
    return row

def create_run(db,data,user):
    if data.cohort_a_id==data.cohort_b_id:raise HTTPException(422,"必须选择两批不同工艺")
    if not db.get(TestCohort,data.cohort_a_id) or not db.get(TestCohort,data.cohort_b_id):raise HTTPException(404,"工艺批次不存在")
    row=SurvivalRun(**data.model_dump(),owner=user.name,target_revision=job_service.current_data_revision(db))
    db.add(row);db.flush();log(db,user.email,"survival.enqueue",f"{row.id}@rev{row.target_revision}");db.commit()
    try:job_service.enqueue_run(row)
    except Exception:
        row.status=RunStatus.FAILED;row.error="队列不可用，可等待worker恢复自动重提";db.commit();raise HTTPException(503,"队列不可用，请稍后重试")
    return record(row)
def export_run(db,rid):
    row=get_run(db,rid)
    if row.status!="completed":raise HTTPException(409,"研究尚未完成")
    if row.result_revision!=row.target_revision:raise HTTPException(409,"研究结果落后于最新随访修订，重算确认前不能导出")
    note=db.query(MaintenanceNote).filter_by(run_id=rid,status=NoteStatus.APPROVED).first()
    if not note:raise HTTPException(403,"维护建议尚未经负责人确认，不能导出")
    if note.run_revision_no!=row.result_revision:raise HTTPException(409,"获批建议对应旧修订，重算后需重新确认才能导出")
    out=io.StringIO();w=csv.writer(out);w.writerow(['cohort','time_hours','at_risk','events','censored','survival','lower','upper','data_revision','input_hash'])
    for group in row.result['groups']:
        for p in group['curve']:w.writerow([group['cohort']['code']]+[p[k] for k in ['time','at_risk','events','censored','survival','lower','upper']]+[row.result_revision,row.result['input_hash']])
    return out.getvalue()
