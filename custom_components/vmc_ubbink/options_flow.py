import voluptuous as vol

from homeassistant import config_entries

from .const import (
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


class VMCUbifluxOptionsFlowHandler(config_entries.OptionsFlow):
    # HA sets self.config_entry itself (read-only property); do NOT override __init__.

    def _current(self, key, default):
        opts = self.config_entry.options
        data = self.config_entry.data
        if key in opts:
            return opts[key]
        return data.get(key, default)

    async def async_step_init(self, user_input=None):
        # Mode selection menu; default = current mode (legacy entries without CONF_MODE => server).
        return self.async_show_menu(
            step_id="init",
            menu_options=["direct", "server"],
        )

    async def async_step_server(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data={CONF_MODE: MODE_SERVER, **user_input}
            )

        return self.async_show_form(
            step_id="server",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._current(CONF_HOST, DEFAULT_HOST)): str,
                    vol.Required(CONF_PORT, default=self._current(CONF_PORT, DEFAULT_PORT)): int,
                    vol.Required(CONF_USERNAME, default=self._current(CONF_USERNAME, DEFAULT_USERNAME)): str,
                    vol.Required(CONF_PASSWORD, default=self._current(CONF_PASSWORD, DEFAULT_PASSWORD)): str,
                }
            ),
        )

    async def async_step_direct(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data={CONF_MODE: MODE_DIRECT, **user_input}
            )

        return self.async_show_form(
            step_id="direct",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._current(CONF_HOST, DEFAULT_HOST)): str,
                    vol.Required(CONF_PORT, default=self._current(CONF_PORT, DEFAULT_TCP_PORT)): int,
                    vol.Required(CONF_SLAVE, default=self._current(CONF_SLAVE, DEFAULT_SLAVE)): int,
                }
            ),
        )
