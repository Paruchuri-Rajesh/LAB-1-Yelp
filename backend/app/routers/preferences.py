from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserPreference
from app.schemas.preferences import PreferencesRead, PreferencesUpdate

router = APIRouter()


def _get_or_create_prefs(db: Session, user: User) -> UserPreference:
    if not user.preferences:
        prefs = UserPreference(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        db.refresh(user)
    return user.preferences


@router.get("/me/preferences", response_model=PreferencesRead)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_create_prefs(db, current_user)


@router.put("/me/preferences", response_model=PreferencesRead)
def update_preferences(
    data: PreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = _get_or_create_prefs(db, current_user)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs
