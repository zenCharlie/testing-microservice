from pydantic import BaseModel, Field
from typing import Optional, List, Any


class LinkBase(BaseModel):
    link_id: str
    road_name: Optional[str]
    length: Optional[float]


class SpeedRecordBase(BaseModel):
    timestamp: str  # ISO format
    speed: float
    day_of_week: str
    time_period: str
    link_id: int


class AggregatedSpeed(BaseModel):
    link_id: str
    road_name: Optional[str]
    length: Optional[float]
    average_speed: float


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


class SpatialFilterRequest(BaseModel):
    day: str
    period: str
    bbox: List[float] = Field(..., min_items=4, max_items=4)

