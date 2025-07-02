from datetime import datetime, time
import pandas as pd
from shapely import wkt
from shapely.geometry import LineString
from geoalchemy2.shape import from_shape
import pytz

# Time period definitions (24-hr)
TIME_PERIODS = [
    ("Overnight", time(0, 0), time(3, 59)),
    ("Early Morning", time(4, 0), time(6, 59)),
    ("AM Peak", time(7, 0), time(9, 59)),
    ("Midday", time(10, 0), time(12, 59)),
    ("Early Afternoon", time(13, 0), time(15, 59)),
    ("PM Peak", time(16, 0), time(18, 59)),
    ("Evening", time(19, 0), time(23, 59)),
]


def classify_time_period(dt: datetime) -> str:
    t = dt.time()
    for name, start, end in TIME_PERIODS:
        if start <= t <= end:
            return name
    return "Unknown"


def load_speed_data(path: str) -> pd.DataFrame:
    print("🚛 Loading speed data...")
    df = pd.read_parquet(path)
    print("📊 Columns in Speed File:", df.columns.tolist())
    process_speed_data(df)
    # Optional: process timestamp → datetime, extract time period
    return df


def get_day_of_week(dt: datetime) -> str:
    return dt.strftime("%A")


def process_speed_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds day_of_week and time_period columns to speed dataframe
    """
    df["timestamp"] = pd.to_datetime(df["date_time"])
    df["day_of_week"] = df["timestamp"].dt.day_name()
    df["time_period"] = df["timestamp"].apply(classify_time_period)
    return df


def parse_geometry_wkt(wkt_str: str):
    """
    Converts WKT to GeoAlchemy2-compatible geometry object
    """
    geom = wkt.loads(wkt_str)
    return from_shape(geom, srid=4326)


def linestring_from_coords(coords: list) -> LineString:
    """
    Given a list of coordinates, return a Shapely LineString
    """
    return LineString(coords)
