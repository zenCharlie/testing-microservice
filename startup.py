from app.database import Base, engine
import app.models

# Automatically create tables when app starts (dev only)
Base.metadata.create_all(bind=engine)