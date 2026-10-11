"""HTTP API client for postcode lookup and Open-Meteo."""
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.helpers.aiohttp_client import async_get_clientsession

POSTCODES_URL = "https://api.postcodes.io/postcodes/{postcode}"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class SunHoursApi:
    def __init__(self, hass, postcode: str, capacity_kw: float):
        self.session = async_get_clientsession(hass)
        self.postcode = postcode.strip().upper()
        self.capacity_kw = capacity_kw

    async def async_fetch(self):
        async with self.session.get(POSTCODES_URL.format(postcode=self.postcode), timeout=15) as resp:
            resp.raise_for_status()
            geo = await resp.json()
        if geo.get("status") != 200 or not geo.get("result"):
            raise ValueError("Postcode not found")
        place = geo["result"]
        lat, lon = place["latitude"], place["longitude"]

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "shortwave_radiation",
            "daily": "shortwave_radiation_sum,sunrise,sunset",
            "timezone": "auto",
            "forecast_days": 7,
        }
        async with self.session.get(FORECAST_URL, params=params, timeout=20) as resp:
            resp.raise_for_status()
            weather = await resp.json()

        hourly = weather["hourly"]
        radiation = hourly["shortwave_radiation"]
        times = hourly["time"]

        daily = weather["daily"]
        # Open-Meteo's daily shortwave_radiation_sum is in MJ/m²; convert to
        # kWh/m² by dividing by 3.6. Use the first daily value for today's
        # full-day forecast, rather than summing all 7 days of hourly data.
        today_irradiation = (daily["shortwave_radiation_sum"][0] or 0) / 3.6
        irradiation_kwh_m2 = today_irradiation
        peak_sun_hours = round(today_irradiation, 1)
        estimated_kwh = round(self.capacity_kw * today_irradiation, 2)

        daily_forecast = []
        for i, date in enumerate(daily["time"]):
            irradiation = (daily["shortwave_radiation_sum"][i] or 0) / 3.6
            daily_forecast.append({
                "date": date,
                "peak_sun_hours": round(irradiation, 1),
                "irradiation_kwh_m2": round(irradiation, 2),
                "estimated_generation_kwh": round(self.capacity_kw * irradiation, 2),
                "sunrise": daily["sunrise"][i],
                "sunset": daily["sunset"][i],
            })

        return {
            "postcode": self.postcode,
            "location": place.get("admin_ward") or place.get("admin_district") or self.postcode,
            "latitude": lat,
            "longitude": lon,
            "peak_sun_hours": peak_sun_hours,
            "irradiation_kwh_m2": round(irradiation_kwh_m2, 2),
            "estimated_generation_kwh": estimated_kwh,
            "capacity_kw": self.capacity_kw,
            "sunrise": daily["sunrise"][0],
            "sunset": daily["sunset"][0],
            "daily_forecast": daily_forecast,
            "weekly_estimated_generation_kwh": round(sum(day["estimated_generation_kwh"] for day in daily_forecast), 2),
            "hourly": [
                {"time": t, "shortwave_radiation_w_m2": v}
                for t, v in zip(times, radiation)
            ],
            "attribution": "Forecast from Open-Meteo; postcode coordinates from postcodes.io",
        }
