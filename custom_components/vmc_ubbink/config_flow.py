import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_MODE,
    MODE_SERVER,
    MODE_DIRECT,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SLAVE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    DEFAULT_TCP_PORT,
    DEFAULT_SLAVE,
)
from .options_flow import VMCUbifluxOptionsFlowHandler


class VMCUbifluxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        # Connection mode selection step.
        return self.async_show_menu(
            step_id="user",
            menu_options=["direct", "server"],
        )

    async def async_step_server(self, user_input=None):
        if user_input is not None:
            data = {CONF_MODE: MODE_SERVER, **user_input}
            return self.async_create_entry(title="VMC Ubiflux", data=data)

        return self.async_show_form(
            step_id="server",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
                    vol.Required(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
                }
            ),
        )

    async def async_step_direct(self, user_input=None):
        errors = {}
        if user_input is not None:
            ok = await self.hass.async_add_executor_job(
                _can_connect,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_SLAVE],
            )
            if ok:
                data = {CONF_MODE: MODE_DIRECT, **user_input}
                return self.async_create_entry(title="VMC Ubiflux", data=data)
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="direct",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_TCP_PORT): int,
                    vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return VMCUbifluxOptionsFlowHandler()


def _can_connect(host, port, slave):
    """Probe by reading serial_number (4010). Runs in the executor."""
    from .direct import DirectClient

    client = DirectClient(host, port, slave)
    try:
        client._ensure_connected()
        serial = client._device.get_serial_number()
        return bool(serial)
    except Exception:  # noqa: BLE001
        return False
    finally:
        client.close()
