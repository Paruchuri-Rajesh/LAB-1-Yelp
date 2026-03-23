from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from app.config import settings
from app.database import engine, Base
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.preferences import router as preferences_router
from app.routers.restaurants import router as restaurants_router
from app.routers.reviews import router as reviews_router
from app.routers.owner import router as owner_router
from app.routers.admin_photos import router as admin_photos_router


def create_app() -> FastAPI:
    app = FastAPI(title="Yelp Clone API", version="1.0.0")

    @app.on_event("startup")
    def init_db():
        # Ensure auxiliary tables required by the application exist.
        # import models to ensure all model modules are registered with SQLAlchemy metadata
        import app.models as _models  # noqa: F401
        Base.metadata.create_all(bind=engine)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ensure upload directories exist at startup
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(f"{settings.UPLOAD_DIR}/profile_pics").mkdir(exist_ok=True)

    # Serve uploaded files as static assets
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    prefix = "/api/v1"
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    app.include_router(preferences_router, prefix=f"{prefix}/users", tags=["preferences"])
    app.include_router(restaurants_router, prefix=f"{prefix}/restaurants", tags=["restaurants"])
    app.include_router(reviews_router, prefix=f"{prefix}/restaurants", tags=["reviews"])
    app.include_router(owner_router, prefix=f"{prefix}/owner", tags=["owner"])
    app.include_router(admin_photos_router, prefix=f"{prefix}/admin/photos", tags=["admin"]) 
    from app.routers.ai_assistant import router as ai_assistant_router
    app.include_router(ai_assistant_router, prefix=f"{prefix}/ai-assistant", tags=["ai-assistant"]) 

    return app


app = create_app()
