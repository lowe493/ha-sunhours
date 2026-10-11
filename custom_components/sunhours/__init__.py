"""SunHours forecast integration."""
from datetime import timedelta
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, CONF_POSTCODE, CONF_CAPACITY, DEFAULT_CAPACITY, SCAN_INTERVAL
from .api import SunHoursApi

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = SunHoursApi(
        hass,
        entry.data[CONF_POSTCODE],
        float(entry.options.get(CONF_CAPACITY, entry.data.get(CONF_CAPACITY, DEFAULT_CAPACITY))),
    )

    async def async_update_data():
        try:
            return await api.async_fetch()
        except (aiohttp.ClientError, TimeoutError, ValueError, KeyError) as err:
            raise UpdateFailed(f"Unable to fetch SunHours forecast: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(minutes=SCAN_INTERVAL),
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
