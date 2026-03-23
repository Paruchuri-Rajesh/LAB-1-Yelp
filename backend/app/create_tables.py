from app.database import engine, Base
from app.models import *  # noqa: F401,F403

# Create all tables according to models and constraints.
Base.metadata.create_all(bind=engine)

print("All tables created successfully.")
