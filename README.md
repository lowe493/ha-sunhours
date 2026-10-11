![logo](https://github.com/lowe493/ha-sunhours/blob/fcc8003f00590578a855b0fc0f847e6fdde2a115/img/logoSmall.png)

# SunHours Solar Forecast for Home Assistant

A small custom integration inspired by the SunHours.app calculator. It looks up a UK postcode with postcodes.io, requests hourly solar radiation and a 7-day daily solar forecast from Open-Meteo, and creates Home Assistant sensors.

## Sensors

- `sensor.sunhours_solar_forecast_peak_sun_hours_today` — peak sun hours estimate
- `sensor.sunhours_solar_forecast_solar_irradiation_today` — daily solar irradiation estimate in kWh/m²
- `sensor.sunhours_solar_forecast_estimated_solar_generation_today` — rough generation estimate using your configured system capacity
- Sunrise and sunset timestamp sensors
- Six additional daily generation sensors for tomorrow through day +6, each with forecast date, peak sun hours, irradiation, sunrise and sunset attributes
- A 7-day estimated generation total sensor with the full daily forecast in its attributes

Entity IDs can vary depending on your existing entities and Home Assistant's naming rules.

## Install manually

1. Copy `custom_components/sunhours` into your Home Assistant configuration directory, under `/config/custom_components/`.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**.
4. Search for **SunHours Solar Forecast**.
5. Enter your UK postcode and system capacity in kW (for example, `1.6`).

## Install via HACS (custom repository)

This ZIP is a starter project, not a published HACS repository. To install via HACS, place the files in a public GitHub repository, replace the placeholder repository URLs in `manifest.json`, run Home Assistant/HACS validation, and add it in HACS using **Custom repositories** → type **Integration**. HACS requires a GitHub repository; a local ZIP alone is not a HACS listing.

## How the estimate works

For today, the integration sums hourly Open-Meteo `shortwave_radiation` values and divides by 1,000 to estimate irradiation in kWh/m². For the next six days, it uses Open-Meteo `daily.shortwave_radiation_sum` (MJ/m²) converted to kWh/m² by dividing by 3.6. It then calculates:

`estimated_generation_kwh = system_capacity_kw × irradiation_kwh_m2`

This is a simplified estimate, not a full photovoltaic model. It does not model roof pitch, orientation, shading, temperature, inverter efficiency, panel degradation, or system losses. Use it as a rough forecast indicator, not a guarantee. If you have a real inverter generation sensor, compare this estimate against actual daily generation before relying on it for automations.

## Data sources and privacy

- Postcode coordinates: [postcodes.io](https://postcodes.io/)
- Forecast data: [Open-Meteo](https://open-meteo.com/)

Your postcode is sent to postcodes.io for lookup. The resulting coordinates are sent to Open-Meteo. No API key is required for this basic implementation.
