from __future__ import annotations

from radonscan3.homeassistant import HomeAssistantClient


def test_status_exposes_home_assistant_location_config(monkeypatch):
    client = HomeAssistantClient("test-token")
    monkeypatch.setattr(
        client,
        "_request",
        lambda method, path, payload=None: {
            "version": "2026.7.0",
            "location_name": "Home",
            "address": "Linnenkamp 22, 44536 Lünen",
            "latitude": 51.60176,
            "longitude": 7.45410,
            "elevation": 58,
            "country": "DE",
            "time_zone": "Europe/Berlin",
        },
    )

    status = client.status()

    assert status == {
        "available": True,
        "connected": True,
        "version": "2026.7.0",
        "location_name": "Home",
        "address": "Linnenkamp 22, 44536 Lünen",
        "latitude": 51.60176,
        "longitude": 7.45410,
        "elevation": 58,
        "country": "DE",
        "time_zone": "Europe/Berlin",
    }


def test_location_address_uses_only_fields_supplied_by_home_assistant():
    assert HomeAssistantClient._location_address(
        {
            "street": "Linnenkamp 22",
            "postal_code": "44536",
            "city": "Lünen",
        }
    ) == "Linnenkamp 22, 44536 Lünen"
    assert HomeAssistantClient._location_address(
        {
            "formatted_address": "Linnenkamp 22, 44536 Lünen",
            "street": "ignored",
        }
    ) == "Linnenkamp 22, 44536 Lünen"
    assert HomeAssistantClient._location_address(
        {
            "latitude": 51.60176,
            "longitude": 7.45410,
            "location_name": "Home",
        }
    ) is None
