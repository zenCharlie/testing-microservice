import pandas as pd
from shapely.geometry import LineString
from geoalchemy2.shape import from_shape
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app import models, utils
import os
from tqdm import tqdm


# Load DB connection from env
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://user:password@localhost:5432/trafficdb")
engine = create_engine(DATABASE_URL)

# Create tables (if not already created)
models.Base.metadata.create_all(engine)


def load_link_info(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["geometry"] = df["coordinates"].apply(lambda coords: LineString(coords))
    return df


def load_speed_data(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = utils.process_speed_data(df)
    return df


def insert_data(link_df: pd.DataFrame, speed_df: pd.DataFrame, batch_size=500):
    session = Session(bind=engine)

    # Create map for fast ID resolution
    link_id_map = {}

    print("Inserting links...")
    for row in tqdm(link_df.itertuples(), total=len(link_df)):
        geom = from_shape(row.geometry, srid=4326)
        link = models.Link(
            link_id=row.link_id,
            road_name=row.road_name,
            length=row.length,
            geometry=geom
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
            speed=row.speed,
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

