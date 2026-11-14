from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user,roles
from ..constants.roles import Role
from ..schemas.correction import CorrectionBatch
from ..services.correction_service import submit_correction,list_corrections
router=APIRouter(prefix="/followups/corrections",tags=["corrections"])
@router.get("")
def index(db:Session=Depends(get_db),user=Depends(current_user)):return list_corrections(db)
@router.post("",status_code=201)
def submit(data:CorrectionBatch,db:Session=Depends(get_db),user=Depends(roles(Role.ADMIN,Role.ANALYST))):return submit_correction(db,data,user)
