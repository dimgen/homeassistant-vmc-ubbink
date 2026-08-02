import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

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
    DEFAULT_TCP_PORT,
    DEFAULT_SLAVE,
)
from .mode_options import get_mode_value, merge_mode_options

MODE_FIELDS = {
    MODE_SERVER: (CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD),
    MODE_DIRECT: (CONF_HOST, CONF_PORT, CONF_SLAVE),
}

PASSWORD_SELECTOR = TextSelector(
    TextSelectorConfig(
        type=TextSelectorType.PASSWORD,
        autocomplete="current-password",
    )
)


class VMCUbifluxOptionsFlowHandler(config_entries.OptionsFlow):
    # HA sets self.config_entry itself (read-only property); do NOT override __init__.

    def _mode_value(self, mode, key, default=None):
        return get_mode_value(
            self.config_entry.data,
            self.config_entry.options,
            mode,
            key,
            default,
            MODE_SERVER,
        )

    def _required_with_suggested_value(self, mode, key):
        current = self._mode_value(mode, key)
        if current is None:
            return vol.Required(key)
        return vol.Required(key, description={"suggested_value": current})

    def _merged_options(self, mode, user_input):
        return merge_mode_options(
            self.config_entry.data,
            self.config_entry.options,
            mode,
            user_input,
            MODE_FIELDS,
            MODE_SERVER,
        )

    async def async_step_init(self, user_input=None):
        # Mode selection menu; default = current mode (legacy entries without CONF_MODE => server).
        return self.async_show_menu(
            step_id="init",
            menu_options=["direct", "server"],
        )

    async def async_step_server(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data=self._merged_options(MODE_SERVER, user_input)
            )

        return self.async_show_form(
            step_id="server",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self._mode_value(MODE_SERVER, CONF_HOST, DEFAULT_HOST),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=self._mode_value(MODE_SERVER, CONF_PORT, DEFAULT_PORT),
                    ): int,
                    self._required_with_suggested_value(
                        MODE_SERVER, CONF_USERNAME
                    ): str,
                    self._required_with_suggested_value(
                        MODE_SERVER, CONF_PASSWORD
                    ): PASSWORD_SELECTOR,
                }
            ),
        )

    async def async_step_direct(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="", data=self._merged_options(MODE_DIRECT, user_input)
            )

        return self.async_show_form(
            step_id="direct",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self._mode_value(MODE_DIRECT, CONF_HOST, DEFAULT_HOST),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=self._mode_value(
                            MODE_DIRECT, CONF_PORT, DEFAULT_TCP_PORT
                        ),
                    ): int,
                    vol.Required(
                        CONF_SLAVE,
                        default=self._mode_value(
                            MODE_DIRECT, CONF_SLAVE, DEFAULT_SLAVE
                        ),
                    ): int,
                }
            ),
        )
