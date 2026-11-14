import time,json,traceback,os
from pathlib import Path
from .config.database import Base,engine,SessionLocal
from .models import SurvivalRun,TestCohort
from .constants.status import RunStatus
from .services import job_service
from .services.job_service import queue,JOB_KEY
from .services.specimen_service import specimen_rows
from .services.survival_algorithm import analyze_survival
from .services.audit_service import log
ARTIFACTS=Path(os.environ.get("ARTIFACT_DIR","/artifacts"))
def archive(run):
    """归档文件与研究曲线同一修订：文件名与内容都带数据修订号。"""
    payload={"run_id":run.id,"run_name":run.name,"target_revision":run.target_revision,
             "result_revision":run.result_revision,"input_hash":run.result.get("input_hash"),
             "result":run.result}
    path=ARTIFACTS/f"run-{run.id}-rev{run.result_revision}.json"
    path.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False))
    latest=ARTIFACTS/f"run-{run.id}.json"
    latest.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False))

def process_job(raw):
    run_id,job_revision=job_service.parse_job(raw)
    with SessionLocal() as db:
        run=db.get(SurvivalRun,run_id)
        if not run:return
        if run.status not in (RunStatus.QUEUED,RunStatus.RUNNING):return
        # 消息里的修订号落后于研究当前目标：旧计算已被更新的更正取代，直接丢弃
        if job_revision is not None and job_revision!=run.target_revision:
            log(db,"worker","survival.job_stale",f"{run.id}:job{job_revision}<{run.target_revision}");db.commit();return
        run.status=RunStatus.RUNNING;db.commit()
        try:
            a,b=db.get(TestCohort,run.cohort_a_id),db.get(TestCohort,run.cohort_b_id)
            result=analyze_survival(a,b,specimen_rows(db,a.id),specimen_rows(db,b.id),run.confidence,run.target_revision)
            # 计算期间又来了更正：晚到的旧结论不能覆盖新目标
            if run.target_revision!=result["data_revision"] or run.status!=RunStatus.RUNNING:
                log(db,"worker","survival.result_stale",f"{run.id}:drop{result['data_revision']}keep{run.target_revision}");db.commit();return
            run.result=result;run.result_revision=run.target_revision;run.status=RunStatus.COMPLETED;run.error=""
            archive(run)
            log(db,"worker","survival.completed",f"{run.id}@rev{run.result_revision}")
        except Exception as e:
            # 目标修订未变才落失败态；若期间已有新更正，保持排队等待新计算
            if run.status==RunStatus.RUNNING and (job_revision is None or job_revision==run.target_revision):
                run.status=RunStatus.FAILED;run.error=str(e)
            traceback.print_exc()
        db.commit()

def main():
    Base.metadata.create_all(engine);ARTIFACTS.mkdir(exist_ok=True)
    with SessionLocal() as db:
        recovered=job_service.recover_jobs(db)
        if recovered:print(f"[worker] recovered {recovered} interrupted runs")
    while True:
        ARTIFACTS.joinpath("heartbeat").write_text(str(time.time()))
        job=queue.blpop(JOB_KEY,timeout=2)
        if not job:continue
        process_job(job[1])

if __name__=="__main__":
    main()
