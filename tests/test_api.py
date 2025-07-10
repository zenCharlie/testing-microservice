import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_aggregates():
    response = client.get("/aggregates/?day=Monday&period=AM Peak")
    assert response.status_code == 200 or response.status_code == 404

def test_get_link():
    response = client.get("/aggregates/1?day=Monday&period=AM Peak")
    assert response.status_code in [200, 404]

def test_post_spatial_filter():
    response = client.post("/aggregates/spatial_filter/", json={
        "day": "Wednesday",
        "period": "AM Peak",
        "bbox": [-81.8, 30.1, -81.6, 30.3]
    })
    assert response.status_code in [200, 404]
