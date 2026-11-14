import math
from fastapi import HTTPException
from ..models import (Specimen,FollowupEvent,FollowupRevision,FollowupCorrection,
                      SurvivalRun,MaintenanceNote)
from ..constants.status import NoteStatus,CorrectionStatus,RunStatus
from ..utils.serialize import record
from ..utils.clock import now
from .audit_service import log
from . import job_service

def list_corrections(db):
    rows=db.query(FollowupCorrection).order_by(FollowupCorrection.id.desc()).limit(100).all()
    return [record(x) for x in rows]

def _merge_items(items):
    """按试件编号合并重复条目；同号异值或同号重复都返回拒绝说明。"""
    grouped={}
    order=[]
    conflicts=[]
    for item in items:
        code=item.specimen_code
        key=(item.expected_revision,item.duration_hours,item.event_observed)
        if code not in grouped:
            grouped[code]=key;order.append(code)
        elif grouped[code]!=key:
            conflicts.append(f"试件 {code} 在本批中出现相互冲突的更正值（同号异值）")
        else:
            conflicts.append(f"试件 {code} 在本批中重复出现，一个试件每批只能有一条下一号修订")
    return order,grouped,conflicts

def _validate_value(code,duration,event):
    if duration is None and event is None:
        return f"试件 {code} 未提供任何更正字段（时长或失效状态至少一项）"
    if duration is not None and (not math.isfinite(duration) or duration<=0 or duration>1e6):
        return f"试件 {code} 的随访时长必须是(0,1000000]内的有限小时数"
    if event is not None and not isinstance(event,bool):
        return f"试件 {code} 的失效状态必须是布尔值"
    return ""

def submit_correction(db,data,user):
    codes,merged,errors=_merge_items(data.items)
    specimens={s.code:s for s in db.query(Specimen).filter(Specimen.code.in_(codes)).all()}
    # 行级锁串行化并发更正，避免两个批次基于同一当前修订号同时生效（MySQL InnoDB；SQLite忽略FOR UPDATE）
    followups={}
    if codes:
        rows=(db.query(FollowupEvent).join(Specimen)
              .filter(Specimen.code.in_(codes)).with_for_update().all())
        for row in rows:
            followups[row.specimen_id]=row
    planned=[]
    for code in codes:
        expected_revision,duration,event=merged[code]
        bad=_validate_value(code,duration,event)
        if bad:errors.append(bad);continue
        specimen=specimens.get(code)
        if not specimen:
            errors.append(f"试件编号 {code} 不存在");continue
        followup=followups.get(specimen.id)
        if not followup:
            errors.append(f"试件 {code} 缺少终态随访，无法更正");continue
        if expected_revision!=followup.revision_no:
            errors.append(f"试件 {code} 的修订号应为当前值 {followup.revision_no}，收到 {expected_revision}，整批未生效")
            continue
        new_duration=followup.duration_hours if duration is None else duration
        new_event=followup.event_observed if event is None else event
        if new_duration==followup.duration_hours and new_event==followup.event_observed:
            errors.append(f"试件 {code} 的更正内容与当前终态完全相同（无实质变化），整批未生效")
            continue
        planned.append((specimen,followup,new_duration,new_event))
    if errors:
        batch=FollowupCorrection(reason=data.reason,status=CorrectionStatus.REJECTED,
                                 items=[i.model_dump() for i in data.items],
                                 affected_run_ids=[],applied_revision=None,
                                 reject_reason="；".join(errors[:20]),owner=user.email)
        db.add(batch);db.flush()
        log(db,user.email,"followup.correction.rejected",batch.id)
        db.commit()
        raise HTTPException(422,"整批更正被拒绝："+"；".join(errors[:10]))
    affected_cohort_ids={s.cohort_id for s,_,_,_ in planned}
    affected_runs=db.query(SurvivalRun).filter(
        (SurvivalRun.cohort_a_id.in_(affected_cohort_ids))|
        (SurvivalRun.cohort_b_id.in_(affected_cohort_ids))).all()
    batch=FollowupCorrection(reason=data.reason,status=CorrectionStatus.APPLIED,
                             items=[i.model_dump() for i in data.items],
                             affected_run_ids=[r.id for r in affected_runs],
                             applied_revision=None,owner=user.email)
    db.add(batch);db.flush()
    new_revision=batch.id
    for specimen,followup,new_duration,new_event in planned:
        followup.duration_hours=new_duration
        followup.event_observed=new_event
        followup.revision_no=new_revision
        db.add(FollowupRevision(specimen_id=specimen.id,revision_no=new_revision,
                                duration_hours=new_duration,event_observed=new_event,
                                note=followup.note,source="correction",
                                correction_id=batch.id,owner=user.email))
    for run in affected_runs:
        run.target_revision=new_revision
        run.status=RunStatus.QUEUED;run.error=""
        for note in db.query(MaintenanceNote).filter_by(run_id=run.id).all():
            if note.status in (NoteStatus.SUBMITTED,NoteStatus.APPROVED):
                note.status=NoteStatus.SUPERSEDED
                note.superseded_at=now()
                note.supersede_reason=f"随访更正批次#{new_revision}改变了输入数据，旧结论失效，需按重算结果重新确认。"
        log(db,user.email,"survival.invalidate",f"{run.id}@rev{new_revision}")
    batch.applied_revision=new_revision
    log(db,user.email,"followup.correction.applied",new_revision)
    db.commit()
    for run in affected_runs:
        try:job_service.enqueue_run(run)
        except Exception:pass
    db.refresh(batch)
    return record(batch)
