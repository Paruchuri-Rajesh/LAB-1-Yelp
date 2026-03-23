from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_owner
from app.schemas.owner import OwnerDashboardSummary, OwnerRestaurantDashboard
from app.schemas.restaurant import RestaurantDetail, RestaurantUpdate
from app.services.restaurant_service import (
    claim_restaurant,
    get_owner_dashboard_summary,
    get_owner_restaurant_dashboard,
    get_owner_restaurants,
    update_owned_restaurant,
    parse_address_components,
    geocode_address,
)
from app.services import file_service
from app.models.restaurant import Restaurant, RestaurantPhoto, RestaurantOwnership
from app.services.restaurant_service import get_restaurant_by_id
from app.services.file_service import delete_file
from app.models.restaurant import RestaurantHours
from pydantic import BaseModel
from typing import List
from datetime import time


class HoursIn(BaseModel):
    day_of_week: str
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False
router = APIRouter()


@router.post("/restaurants", response_model=RestaurantDetail, status_code=status.HTTP_201_CREATED)
async def create_my_restaurant(
    name: str = Form(...),
    address: str | None = Form(None),
    city: str | None = Form(None),
    state: str | None = Form(None),
    zip_code: str | None = Form(None),
    phone: str | None = Form(None),
    website: str | None = Form(None),
    cuisine_type: str | None = Form(None),
    price_range: str | None = Form(None),
    description: str | None = Form(None),
    photos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    # attempt to derive city/state/zip from the address if not explicitly provided
    if not city or not state:
        street, parsed_city, parsed_state, parsed_zip = parse_address_components(address)
        city = city or parsed_city
        state = state or parsed_state
        zip_code = zip_code or parsed_zip

    # try to geocode address to get lat/lon for map placement
    lat, lon = geocode_address(address or f"{city or ''} {state or ''}" )

    # create restaurant
    rest = Restaurant(
        name=name,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        phone=phone,
        website=website,
        cuisine_type=cuisine_type,
        price_range=price_range,
        description=description,
        source="local",
        latitude=lat,
        longitude=lon,
    )
    db.add(rest)
    db.commit()
    db.refresh(rest)

    # save photos if provided
    if photos:
        for idx, f in enumerate(photos):
            path = await file_service.save_upload(f, "restaurant_photos")
            photo = RestaurantPhoto(restaurant_id=rest.id, file_path=path, is_primary=(idx == 0))
            db.add(photo)
        db.commit()

    # create ownership
    claim = RestaurantOwnership(restaurant_id=rest.id, owner_id=current_owner.id, status="claimed")
    db.add(claim)
    db.commit()

    return get_restaurant_by_id(db, rest.id)


@router.post("/restaurants/{restaurant_id}/photos", status_code=status.HTTP_201_CREATED)
async def upload_restaurant_photos(
    restaurant_id: int,
    photos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    # ensure owner owns this restaurant
    ownership = (
        db.query(RestaurantOwnership)
        .filter(RestaurantOwnership.restaurant_id == restaurant_id, RestaurantOwnership.owner_id == current_owner.id)
        .first()
    )
    if not ownership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner does not own this restaurant")
    added = []
    if photos:
        for idx, f in enumerate(photos):
            path = await file_service.save_upload(f, "restaurant_photos")
            photo = RestaurantPhoto(restaurant_id=restaurant_id, file_path=path, is_primary=False)
            db.add(photo)
            added.append(photo)
        db.commit()
    return {"added": len(added)}



@router.delete("/restaurants/{restaurant_id}/photos/{photo_id}", status_code=200)
def delete_restaurant_photo(
    restaurant_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    # ensure owner owns this restaurant
    ownership = (
        db.query(RestaurantOwnership)
        .filter(RestaurantOwnership.restaurant_id == restaurant_id, RestaurantOwnership.owner_id == current_owner.id)
        .first()
    )
    if not ownership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner does not own this restaurant")

    photo = db.query(RestaurantPhoto).filter(RestaurantPhoto.id == photo_id, RestaurantPhoto.restaurant_id == restaurant_id).first()
    if not photo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    # delete file from disk
    delete_file(photo.file_path)
    db.delete(photo)
    db.commit()
    return {"deleted": photo_id}


@router.put("/restaurants/{restaurant_id}/hours", status_code=200)
def update_restaurant_hours(
    restaurant_id: int,
    hours: List[HoursIn],
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    # ensure owner owns this restaurant
    ownership = (
        db.query(RestaurantOwnership)
        .filter(RestaurantOwnership.restaurant_id == restaurant_id, RestaurantOwnership.owner_id == current_owner.id)
        .first()
    )
    if not ownership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner does not own this restaurant")

    # replace existing hours with incoming hours
    db.query(RestaurantHours).filter(RestaurantHours.restaurant_id == restaurant_id).delete(synchronize_session=False)
    for h in hours:
        rh = RestaurantHours(
            restaurant_id=restaurant_id,
            day_of_week=h.day_of_week,
            open_time=h.open_time,
            close_time=h.close_time,
            is_closed=h.is_closed,
        )
        db.add(rh)
    db.commit()
    return {"updated": len(hours)}
@router.post("/restaurants/{restaurant_id}/claim", status_code=status.HTTP_201_CREATED)
def claim_my_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    claim = claim_restaurant(db, restaurant_id, current_owner.id)
    return {"id": claim.id, "restaurant_id": claim.restaurant_id, "status": claim.status}


@router.get("/restaurants")
def list_owned_restaurants(
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    return get_owner_restaurants(db, current_owner.id)


@router.get("/dashboard", response_model=OwnerDashboardSummary)
def owner_dashboard(
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    return get_owner_dashboard_summary(db, current_owner.id)


@router.get("/restaurants/{restaurant_id}/dashboard", response_model=OwnerRestaurantDashboard)
def owner_restaurant_dashboard(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    return get_owner_restaurant_dashboard(db, current_owner.id, restaurant_id)


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantDetail)
def update_my_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner),
):
    return update_owned_restaurant(db, current_owner.id, restaurant_id, data.model_dump(exclude_unset=True))
