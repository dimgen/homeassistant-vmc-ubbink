import voluptuous as vol
from homeassistant import config_entries
from .const import CONF_HOST, CONF_PORT, CONF_USERNAME, CONF_PASSWORD, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USERNAME, DEFAULT_PASSWORD

class VMCUbifluxOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST, default=self.config_entry.options.get(CONF_HOST, self.config_entry.data.get(CONF_HOST, DEFAULT_HOST))): str,
                vol.Required(CONF_PORT, default=self.config_entry.options.get(CONF_PORT, self.config_entry.data.get(CONF_PORT, DEFAULT_PORT))): int,
                vol.Required(CONF_USERNAME, default=self.config_entry.options.get(CONF_USERNAME, self.config_entry.data.get(CONF_USERNAME, DEFAULT_USERNAME))): str,
                vol.Required(CONF_PASSWORD, default=self.config_entry.options.get(CONF_PASSWORD, self.config_entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD))): str,
            }),
        )
