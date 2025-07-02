import pandas as pd
import sys
import os
from shapely.geometry import MultiLineString, LineString
from shapely import wkt
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import models, utils
from tqdm import tqdm
import json
from shapely.geometry import shape
from app.utils import load_speed_data

# Load DB connection from env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/trafficdb")
engine = create_engine(DATABASE_URL)

# Create tables (if not already created)
models.Base.metadata.create_all(engine)


def normalize_geometry(geom):
    if isinstance(geom, MultiLineString):
        # Just take the first LineString component
        return geom.geoms[0] if geom.geoms else None
    elif isinstance(geom, LineString):
        return geom
    return None


def load_link_info(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    print("📊 Columns in Link File:", df.columns.tolist())
    df["length"] = df["_length"]
    if "geo_json" in df.columns:
        # Parse GeoJSON into shapely geometry
        df["geometry"] = df["geo_json"].apply(lambda g: shape(json.loads(g)))
    elif "geometry" in df.columns:
        df["geometry"] = df["geometry"].apply(wkt.loads)
    elif "coordinates" in df.columns:
        df["geometry"] = df["coordinates"].apply(lambda coords: LineString(coords))
    else:
        raise ValueError("Expected 'geo_json', 'coordinates', or 'geometry' column in link_info.parquet.gz")
    return df


def insert_data(link_df: pd.DataFrame, speed_df: pd.DataFrame, batch_size=500):
    session = Session(bind=engine)

    # Create map for fast ID resolution
    link_id_map = {}

    print("Inserting links...")
    for row in tqdm(link_df.itertuples(), total=len(link_df)):
        geom = normalize_geometry(row.geometry)
        if geom is not None:
            geometry = from_shape(geom, srid=4326)
        geom = from_shape(row.geometry, srid=4326)
        link = models.Link(
            link_id=row.link_id,
            road_name=row.road_name,
            geometry=geom,
            length=row.length

        )
        session.add(link)
        session.flush()
        link_id_map[row.link_id] = link.id

    session.commit()

    print("Inserting speed records...")
    buffer = []
    for row in tqdm(speed_df.itertuples(), total=len(speed_df)):
        if row.link_id not in link_id_map:
            continue  # Skip records with no matching link

        record = models.SpeedRecord(
            timestamp=row.timestamp,
            average_speed=row.average_speed,
            day_of_week=row.day_of_week,
            time_period=row.time_period,
            link_id=link_id_map[row.link_id]
        )
        buffer.append(record)

        if len(buffer) >= batch_size:
            session.bulk_save_objects(buffer)
            session.commit()
            buffer = []

    if buffer:
        session.bulk_save_objects(buffer)
        session.commit()

    session.close()
    print("✅ ETL complete.")


if __name__ == "__main__":
    link_path = "data/link_info.parquet.gz"
    speed_path = "data/duval_jan1_2024.parquet.gz"

    print("🚛 Loading Parquet files...")
    link_df = load_link_info(link_path)
    speed_df = load_speed_data(speed_path)

    print("📥 Starting data ingestion...")
    insert_data(link_df, speed_df)
