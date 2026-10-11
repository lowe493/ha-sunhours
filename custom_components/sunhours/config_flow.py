"""Config flow for SunHours."""
import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, CONF_POSTCODE, CONF_CAPACITY, DEFAULT_CAPACITY


class SunHoursConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure SunHours."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            postcode = re.sub(r"\s+", "", user_input[CONF_POSTCODE]).upper()
            if not re.match(r"^[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2}$", postcode):
                errors[CONF_POSTCODE] = "invalid_postcode"
            elif user_input[CONF_CAPACITY] <= 0 or user_input[CONF_CAPACITY] > 100:
                errors[CONF_CAPACITY] = "invalid_capacity"
            else:
                await self.async_set_unique_id(postcode)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SunHours ({postcode})",
                    data={CONF_POSTCODE: postcode, CONF_CAPACITY: float(user_input[CONF_CAPACITY])},
                )

        schema = vol.Schema({
            vol.Required(CONF_POSTCODE): str,
            vol.Required(CONF_CAPACITY, default=DEFAULT_CAPACITY): vol.Coerce(float),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
