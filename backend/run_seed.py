# backend/run_seed.py  (temporary helper)
from app.database import SessionLocal
from app.services.data_seeding_service import DataSeedingService

db = SessionLocal()
DataSeedingService.seed_all_data(db)
db.close()
