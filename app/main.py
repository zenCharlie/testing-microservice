from fastapi import FastAPI, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import database, crud, schemas
from geoalchemy2.shape import to_shape
from typing import List

app = FastAPI()


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/aggregates/", response_model=List[schemas.GeoJSONFeature])

def get_aggregated(day: str, period: str, db: Session = Depends(get_db)):
    rows = crud.get_aggregated_speed(db, day, period)
    features = []
    for row in rows:
        geom = to_shape(row.geometry)
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": {
                "link_id": row.link_id,
                "road_name": row.road_name,
                "length": row.length,
                "average_speed": row.average_speed,
            }
        })
    return JSONResponse(content=features)


@app.get("/aggregates/{link_id}", response_model=schemas.GeoJSONFeature)
def get_link_info(link_id: str, day: str, period: str, db: Session = Depends(get_db)):
    row = crud.get_link_aggregate(db, link_id, day, period)
    if not row:
        raise HTTPException(status_code=404, detail="Link not found")
    return {
        "type": "Feature",
        "geometry": to_shape(row.geometry).__geo_interface__,
        "properties": {
            "road_name": row.road_name,
            "length": row.length,
            "average_speed": row.average_speed
        }
    }


@app.get("/patterns/slow_links/")
def get_slow_links(period: str, threshold: float, min_days: int, db: Session = Depends(get_db)):
    return crud.get_slow_links(db, period, threshold, min_days)


@app.post("/aggregates/spatial_filter/", response_model=List[schemas.GeoJSONFeature])
def spatial_filter(req: schemas.SpatialFilterRequest, db: Session = Depends(get_db)):
    rows = crud.get_links_in_bbox(db, req.day, req.period, req.bbox)
    features = []
    for row in rows:
        geom = to_shape(row.geometry)
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": {
                "link_id": row.link_id,
                "road_name": row.road_name,
                "length": row.length,
                "average_speed": row.average_speed,
            }
        })
    return features


@app.get("/")
def root():
    return {"message": "Urban SDK FastAPI Microservice is running"}

