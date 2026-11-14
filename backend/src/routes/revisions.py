from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from ..config.database import get_db
from ..controllers.dependencies import current_user
from ..services.revision_service import revision_history
router=APIRouter(prefix="/specimens",tags=["revisions"])
@router.get("/{code}/revisions")
def history(code:str,db:Session=Depends(get_db),user=Depends(current_user)):return revision_history(db,code)
