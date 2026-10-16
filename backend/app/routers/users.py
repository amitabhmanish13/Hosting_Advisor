from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app.auth.deps import require_role
from app.db.models import Role, UserAccount, UserRole
from app.db.session import get_db
from app.schemas import UserOut, UserRoleIn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _user: UserAccount = Depends(require_role(Role.admin))):
    return db.query(UserAccount).options(selectinload(UserAccount.roles), selectinload(UserAccount.domain)).all()


@router.post("/{user_id}/roles", response_model=UserOut)
def add_role(
    user_id: int,
    payload: UserRoleIn,
    db: Session = Depends(get_db),
    _admin: UserAccount = Depends(require_role(Role.admin)),
):
    user = db.get(UserAccount, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    db.add(UserRole(user_id=user.id, role=Role(payload.role), domain_id=payload.domain_id))
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}/roles/{role_id}", response_model=UserOut)
def remove_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    _admin: UserAccount = Depends(require_role(Role.admin)),
):
    role = db.get(UserRole, role_id)
    if not role or role.user_id != user_id:
        raise HTTPException(404, "Role grant not found")
    db.delete(role)
    db.commit()
    user = db.get(UserAccount, user_id)
    db.refresh(user)
    return user
