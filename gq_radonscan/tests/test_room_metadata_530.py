from radonscan3.storage import Storage


def test_room_storage_accepts_only_room_and_measurement_height(tmp_path):
    storage = Storage(tmp_path / "radon.sqlite3")
    saved = storage.save_location(
        {
            "room": "Keller",
            "measurement_height_m": 1.2,
            "building": "Home",
            # Legacy fields must not survive the simplified 5.3.0 model.
            "floor": "UG",
            "room_type": "Basement",
            "notes": "legacy note",
        }
    )

    assert saved["room"] == "Keller"
    assert saved["name"] == "Keller"
    assert saved["building"] == ""
    assert saved["measurement_height_m"] == 1.2
    assert saved["floor"] == ""
    assert saved["room_type"] == ""
    assert saved["notes"] == ""
    assert saved["map_id"] is None


def test_room_name_and_measurement_height_are_validated(tmp_path):
    storage = Storage(tmp_path / "radon.sqlite3")

    try:
        storage.save_location({"room": "", "measurement_height_m": 1.0})
    except Exception as exc:
        assert "room name" in str(exc).lower()
    else:
        raise AssertionError("empty room name was accepted")

    try:
        storage.save_location({"room": "Keller", "measurement_height_m": 11})
    except Exception as exc:
        assert "between 0 and 10" in str(exc)
    else:
        raise AssertionError("invalid measurement height was accepted")
