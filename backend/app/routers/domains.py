from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.db.models import Domain, Role, UserAccount
from app.db.session import get_db
from app.schemas import DomainIn, DomainOut

router = APIRouter(prefix="/domains", tags=["domains"])


@router.get("", response_model=list[DomainOut])
def list_domains(db: Session = Depends(get_db), _user: UserAccount = Depends(get_current_user)):
    return db.query(Domain).order_by(Domain.name).all()


@router.post("", response_model=DomainOut)
def create_domain(payload: DomainIn, db: Session = Depends(get_db), _user: UserAccount = Depends(require_role(Role.admin))):
    if db.query(Domain).filter_by(name=payload.name).first():
        raise HTTPException(409, "Domain already exists")
    domain = Domain(name=payload.name)
    db.add(domain)
    db.commit()
    return domain
