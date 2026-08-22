from datetime import date

from app.services.context import uk_season


def test_uk_season():
    assert uk_season(date(2026, 8, 22)) == "summer"
    assert uk_season(date(2026, 10, 1)) == "autumn"
