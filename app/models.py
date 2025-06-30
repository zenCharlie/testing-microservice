from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from .database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(String, unique=True, index=True)
    road_name = Column(String)
    length = Column(Float)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326))  # WGS84

    speed_records = relationship("SpeedRecord", back_populates="link")


class SpeedRecord(Base):
    __tablename__ = "speed_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    speed = Column(Float)
    day_of_week = Column(String)  # e.g., "Monday", "Tuesday", etc.
    time_period = Column(String)  # e.g., "AM Peak", "PM Peak"
    
    link_id = Column(Integer, ForeignKey("links.id"))
    link = relationship("Link", back_populates="speed_records")
