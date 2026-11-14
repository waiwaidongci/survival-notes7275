import json
from redis import Redis
from ..config.settings import REDIS_URL
from ..models import SurvivalRun,FollowupCorrection
from ..constants.status import RunStatus
queue=Redis.from_url(REDIS_URL,decode_responses=True)
JOB_KEY="survival:jobs"
def current_data_revision(db):
    """全局数据修订号：最近一条已生效更正批次的id；无更正时为0。"""
    row=db.query(FollowupCorrection.id).filter_by(status="applied").order_by(FollowupCorrection.id.desc()).first()
    return int(row[0]) if row else 0
def job_payload(run):
    return json.dumps({"run_id":run.id,"target_revision":run.target_revision},ensure_ascii=False)
def enqueue_run(run):
    queue.rpush(JOB_KEY,job_payload(run))
def parse_job(raw):
    """兼容早期纯run_id消息与带修订号的JSON消息。"""
    try:
        payload=json.loads(raw)
        return int(payload["run_id"]),int(payload.get("target_revision"))
    except (ValueError,TypeError,KeyError):
        return int(raw),None
def recover_jobs(db):
    """进程中断后恢复：所有未完成（含running中断）研究按当前目标修订号重新入队。"""
    pending=db.query(SurvivalRun).filter(SurvivalRun.status.in_((RunStatus.QUEUED,RunStatus.RUNNING))).all()
    for run in pending:
        run.status=RunStatus.QUEUED;run.error=""
        try:enqueue_run(run)
        except Exception:pass
    if pending:db.commit()
    return len(pending)
