from fastapi import HTTPException
from ..models import Specimen,FollowupRevision
from ..utils.serialize import record

def revision_history(db,code):
    specimen=db.query(Specimen).filter_by(code=code).first()
    if not specimen:raise HTTPException(404,"试件编号不存在")
    rows=db.query(FollowupRevision).filter_by(specimen_id=specimen.id).order_by(FollowupRevision.revision_no).all()
    return {"specimen_code":code,"specimen_id":specimen.id,"revisions":[record(x) for x in rows]}
