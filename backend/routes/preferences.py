from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.user_preferences import UserPreferences
from schemas.user_preferences import PreferencesUpdate, PreferencesOut
from auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["User Preferences"])


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.put("/preferences", response_model=PreferencesOut)
def update_preferences(
    updates: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prefs, key, value)
    db.commit()
    db.refresh(prefs)
    return prefs
