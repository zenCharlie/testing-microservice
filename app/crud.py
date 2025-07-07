from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast
from geoalchemy2.shape import to_shape
from shapely.geometry import box
from app import models
from typing import List, Tuple


def create_link(db: Session, link_data: dict):
    db_link = models.Link(**link_data)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


def create_speed_record(db: Session, record_data: dict):
    db_record = models.SpeedRecord(**record_data)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_aggregated_speed(db: Session, day: str, period: str):
    """
    Returns aggregated average speed per link for a given day and period.
    """
    results = (
        db.query(
            models.Link.link_id,
            models.Link.road_name,
            models.Link.length,
            models.Link.geometry,
            func.avg(models.SpeedRecord.average_speed).label("average_speed"),
        )
        .join(models.SpeedRecord)
        .filter(
            models.SpeedRecord.day_of_week == day,
            models.SpeedRecord.time_period == period
        )
        .group_by(models.Link.id)
        .all()
    )
    return results


def get_link_aggregate(db: Session, link_id: str, day: str, period: str):
    return (
        db.query(
            models.Link.road_name,
            models.Link.length,
            models.Link.geometry,
            func.avg(models.SpeedRecord.average_speed).label("average_speed"),
        )
        .join(models.SpeedRecord)
        .filter(
            models.Link.link_id == link_id,
            models.SpeedRecord.day_of_week == day,
            models.SpeedRecord.time_period == period,
        )
        .group_by(models.Link.id)
        .first()
    )


def get_slow_links(db: Session, period: str, threshold: float, min_days: int):
    """
    Links with average speeds below threshold for at least `min_days` in a week.
    """
    subquery = (
        db.query(
            models.Link.link_id,
            models.SpeedRecord.day_of_week,
            func.avg(models.SpeedRecord.average_speed).label("avg_speed")
        )
        .join(models.SpeedRecord)
        .filter(models.SpeedRecord.time_period == period)
        .group_by(models.Link.link_id, models.SpeedRecord.day_of_week)
        .having(func.avg(models.SpeedRecord.average_speed) < threshold)
        .subquery()
    )

    results = (
        db.query(subquery.c.link_id, func.count().label("slow_days"))
        .group_by(subquery.c.link_id)
        .having(func.count() >= min_days)
        .all()
    )
    return results


def get_links_in_bbox(db: Session, day: str, period: str, bbox: List[float]):
    """
    Spatial filter by bounding box and time.
    """
    minx, miny, maxx, maxy = bbox
    bounding_box = box(minx, miny, maxx, maxy).wkt

    results = (
        db.query(
            models.Link.link_id,
            models.Link.road_name,
            models.Link.length,
            models.Link.geometry,
            func.avg(models.SpeedRecord.average_speed).label("average_speed")
        )
        .join(models.SpeedRecord)
        .filter(
            models.SpeedRecord.day_of_week == day,
            models.SpeedRecord.time_period == period,
            func.ST_Intersects(
                models.Link.geometry,
                func.ST_GeomFromText(bounding_box, 4326)
            )
        )
        .group_by(models.Link.id)
        .all()
    )
    return results
