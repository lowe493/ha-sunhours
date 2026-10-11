"""SunHours sensors."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_CAPACITY, DEFAULT_CAPACITY


SENSORS = [
    ("peak_sun_hours", "Peak sun hours today", "h", None, SensorStateClass.MEASUREMENT),
    ("irradiation_kwh_m2", "Solar irradiation today", "kWh/m2", None, SensorStateClass.MEASUREMENT),
    ("estimated_generation_kwh", "Estimated solar generation today", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SunHoursSensor(coordinator, entry, key, name, unit, device_class, state_class)
                for key, name, unit, device_class, state_class in SENSORS]
    entities += [SunHoursTimeSensor(coordinator, entry, "sunrise", "Sunrise"),
                 SunHoursTimeSensor(coordinator, entry, "sunset", "Sunset")]
    # Existing generation daily forecast (starts from today/offset 0)
    entities += [DailyForecastSensor(coordinator, entry, offset) for offset in range(1, 7)]
    # NEW: Future sun hours forecast excluding today (+1 to +6 days ahead)
    entities += [FutureSunHoursSensor(coordinator, entry, offset) for offset in range(1, 7)]
    entities += [WeeklyForecastSensor(coordinator, entry)]
    async_add_entities(entities)


class SunHoursBase(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator)
        self.key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SunHours Solar Forecast",
            "manufacturer": "Open-Meteo / SunHours community integration",
            "model": "Solar irradiation forecast",
        }

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "location": data.get("location"),
            "postcode": data.get("postcode"),
            "capacity_kw": data.get("capacity_kw"),
            "hourly_forecast": data.get("hourly"),
            "attribution": data.get("attribution"),
        }


class SunHoursSensor(SunHoursBase):
    def __init__(self, coordinator, entry, key, name, unit, device_class, state_class):
        super().__init__(coordinator, entry, key, name)
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key) if self.coordinator.data else None


class SunHoursTimeSensor(SunHoursBase):
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator, entry, key, name)

    @property
    def native_value(self):
        from datetime import datetime
        value = self.coordinator.data.get(self.key) if self.coordinator.data else None
        if not value:
            return None
        return datetime.fromisoformat(value).astimezone()


class DailyForecastSensor(SunHoursBase):
    """Estimated PV generation for one of the next six days."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, offset):
        super().__init__(coordinator, entry, f"generation_day_{offset}", f"Solar generation forecast +{offset} day")
        self.offset = offset

    def _forecast_day(self):
        data = self.coordinator.data or {}
        forecast = data.get("daily_forecast", [])
        return forecast[self.offset] if len(forecast) > self.offset else None

    @property
    def native_value(self):
        day = self._forecast_day()
        return day.get("estimated_generation_kwh") if day else None

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        day = self._forecast_day()
        attrs["forecast_date"] = day.get("date") if day else None
        attrs["peak_sun_hours"] = day.get("peak_sun_hours") if day else None
        attrs["irradiation_kwh_m2"] = day.get("irradiation_kwh_m2") if day else None
        attrs["sunrise"] = day.get("sunrise") if day else None
        attrs["sunset"] = day.get("sunset") if day else None
        return attrs

class FutureSunHoursSensor(SunHoursBase):
    """Estimated sun hours for one of the next six days"""

    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, offset):
        super().__init__(coordinator, entry, f"sun_hours_day_{offset}", f"Sun hours forecast +{offset} day")
        self.offset = offset

    def _forecast_day(self):
        data = self.coordinator.data or {}
        forecast = data.get("daily_forecast", [])
        return forecast[self.offset] if len(forecast) > self.offset else None

    @property
    def native_value(self):
        day = self._forecast_day()
        return day.get("peak_sun_hours") if day else None

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        day = self._forecast_day()
        attrs["forecast_date"] = day.get("date") if day else None
        attrs["estimated_generation_kwh"] = day.get("estimated_generation_kwh") if day else None
        attrs["irradiation_kwh_m2"] = day.get("irradiation_kwh_m2") if day else None
        attrs["sunrise"] = day.get("sunrise") if day else None
        attrs["sunset"] = day.get("sunset") if day else None
        return attrs

class WeeklyForecastSensor(SunHoursBase):
    """Sum of the estimated generation for the seven forecast days."""

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "weekly_generation", "Estimated solar generation next 7 days")

    @property
    def native_value(self):
        return self.coordinator.data.get("weekly_estimated_generation_kwh") if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        attrs = super().extra_state_attributes
        attrs["daily_forecast"] = (self.coordinator.data or {}).get("daily_forecast", [])
        return attrs