
"""
System Settings Module
Data-Driven Curriculum Optimizer

Manages configurable academic thresholds using a JSON file.
Does not modify app.py or the database.
"""

import json
from pathlib import Path
from typing import Any


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Settings are stored separately from Python source code
SETTINGS_FILE = PROJECT_ROOT / "data" / "system_settings.json"


# Default academic settings
DEFAULT_SETTINGS = {
    "attendance_threshold": 75.0,
    "performance_threshold": 50.0,
    "lo_attainment_target": 70.0,
    "risk_thresholds": {
        "low_risk_min": 70.0,
        "watchlist_min": 50.0,
    },
}


def validate_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """
    Validate settings before saving.

    Percentage values must be between 0 and 100.
    The low-risk boundary must be greater than the watchlist boundary.
    """
    if not isinstance(settings, dict):
        raise ValueError("Settings must be provided as a dictionary.")

    required_keys = (
        "attendance_threshold",
        "performance_threshold",
        "lo_attainment_target",
        "risk_thresholds",
    )

    for key in required_keys:
        if key not in settings:
            raise ValueError(f"Missing required setting: {key}")

    validated = dict(settings)

    percentage_keys = (
        "attendance_threshold",
        "performance_threshold",
        "lo_attainment_target",
    )

    for key in percentage_keys:
        value = validated[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a number.")

        if not 0 <= value <= 100:
            raise ValueError(f"{key} must be between 0 and 100.")

        validated[key] = float(value)

    risk = validated["risk_thresholds"]

    if not isinstance(risk, dict):
        raise ValueError("risk_thresholds must be a dictionary.")

    for key in ("low_risk_min", "watchlist_min"):
        if key not in risk:
            raise ValueError(f"Missing risk threshold: {key}")

        value = risk[key]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{key} must be a number.")

        if not 0 <= value <= 100:
            raise ValueError(f"{key} must be between 0 and 100.")

    if risk["low_risk_min"] <= risk["watchlist_min"]:
        raise ValueError(
            "low_risk_min must be greater than watchlist_min."
        )

    validated["risk_thresholds"] = {
        "low_risk_min": float(risk["low_risk_min"]),
        "watchlist_min": float(risk["watchlist_min"]),
    }

    return validated


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and save settings to the JSON configuration file."""
    validated = validate_settings(settings)

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = SETTINGS_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(validated, file, indent=4)

        temporary_file.replace(SETTINGS_FILE)

    finally:
        if temporary_file.exists():
            temporary_file.unlink()

    return validated


def load_settings() -> dict[str, Any]:
    """
    Load saved settings.

    If no settings file exists, create it using default settings.
    Invalid existing settings raise an error instead of silently
    replacing the user's configuration.
    """
    if not SETTINGS_FILE.exists():
        return save_settings(DEFAULT_SETTINGS)

    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as file:
            settings = json.load(file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Settings file contains invalid JSON: {SETTINGS_FILE}"
        ) from exc

    return validate_settings(settings)


def reset_settings() -> dict[str, Any]:
    """Restore and save the default settings."""
    return save_settings(DEFAULT_SETTINGS)


def update_setting(key: str, value: Any) -> dict[str, Any]:
    """Update one supported setting and save the result."""
    settings = load_settings()

    if key in (
        "attendance_threshold",
        "performance_threshold",
        "lo_attainment_target",
    ):
        settings[key] = value

    elif key in ("low_risk_min", "watchlist_min"):
        settings["risk_thresholds"][key] = value

    else:
        raise ValueError(f"Unsupported setting: {key}")

    return save_settings(settings)


def display_settings() -> None:
    """Display the currently configured settings."""
    settings = load_settings()

    print("\nDATA-DRIVEN CURRICULUM OPTIMIZER")
    print("SYSTEM SETTINGS")
    print("-" * 40)
    print(
        f"Attendance threshold: "
        f"{settings['attendance_threshold']}%"
    )
    print(
        f"Performance threshold: "
        f"{settings['performance_threshold']}%"
    )
    print(
        f"LO attainment target: "
        f"{settings['lo_attainment_target']}%"
    )
    print(
        f"Low-risk boundary: "
        f"{settings['risk_thresholds']['low_risk_min']}%"
    )
    print(
        f"Watchlist boundary: "
        f"{settings['risk_thresholds']['watchlist_min']}%"
    )
    print(f"\nSettings file: {SETTINGS_FILE}")


if __name__ == "__main__":
    display_settings()
    print("\nSystem settings module test completed.")
