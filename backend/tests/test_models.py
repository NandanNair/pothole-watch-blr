"""Tests for the schema itself: migrations, constraints and spatial behaviour."""

import pytest
from geoalchemy2 import Geometry
from sqlalchemy import cast, func, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.models import Report, User

# A point on MG Road, Bengaluru.
MG_ROAD = (12.9757, 77.6064)


def point(lat: float, lon: float) -> str:
    """Build a PostGIS point. Note the order: longitude first, then latitude."""
    return f"SRID=4326;POINT({lon} {lat})"


def offset_north(lat: float, metres: float) -> float:
    """Latitude `metres` north of `lat` (one degree of latitude is about 111,320 m)."""
    return lat + metres / 111_320


@pytest.fixture
def user(db) -> User:
    user = User(email="tester@example.com", hashed_password="not-a-real-hash")  # noqa: S106
    db.add(user)
    db.flush()
    return user


def test_migration_creates_tables_and_enables_postgis(db) -> None:
    tables = inspect(db.connection()).get_table_names()

    assert {"users", "reports"} <= set(tables)
    assert db.execute(text("SELECT postgis_version()")).scalar() is not None


def test_reports_location_has_a_gist_index(db) -> None:
    index_definition = db.execute(
        text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_reports_location'")
    ).scalar()

    assert index_definition is not None
    assert "USING gist" in index_definition


def test_email_must_be_unique(db, user) -> None:
    db.add(User(email=user.email, hashed_password="x"))  # noqa: S106

    with pytest.raises(IntegrityError):
        db.flush()


def test_report_requires_an_existing_user(db) -> None:
    db.add(Report(user_id=999_999, location=point(*MG_ROAD), image_path="a.jpg"))

    with pytest.raises(IntegrityError):
        db.flush()


def test_report_round_trips_its_coordinates(db, user) -> None:
    lat, lon = MG_ROAD
    report = Report(user_id=user.id, location=point(lat, lon), note="deep one", image_path="a.jpg")
    db.add(report)
    db.flush()

    as_geometry = cast(Report.location, Geometry)
    stored_lat, stored_lon = db.execute(
        select(func.ST_Y(as_geometry), func.ST_X(as_geometry)).where(Report.id == report.id)
    ).one()

    assert stored_lat == pytest.approx(lat)
    assert stored_lon == pytest.approx(lon)
    assert report.created_at is not None


def test_st_dwithin_finds_only_reports_inside_the_radius(db, user) -> None:
    lat, lon = MG_ROAD
    near = Report(user_id=user.id, location=point(offset_north(lat, 5), lon), image_path="near.jpg")
    far = Report(user_id=user.id, location=point(offset_north(lat, 50), lon), image_path="far.jpg")
    db.add_all([near, far])
    db.flush()

    within_10_m = db.scalars(
        select(Report).where(func.ST_DWithin(Report.location, point(lat, lon), 10))
    ).all()

    assert [r.image_path for r in within_10_m] == ["near.jpg"]


def test_deleting_a_user_deletes_their_reports(db, user) -> None:
    db.add(Report(user_id=user.id, location=point(*MG_ROAD), image_path="a.jpg"))
    db.flush()

    db.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})

    assert db.scalar(select(func.count()).select_from(Report)) == 0
