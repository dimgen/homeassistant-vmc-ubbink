from pathlib import Path


_CONFIG_FLOW = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "vmc_ubbink"
    / "config_flow.py"
)


def test_new_server_setup_does_not_prefill_credentials():
    source = _CONFIG_FLOW.read_text()
    assert "default=DEFAULT_USERNAME" not in source
    assert "default=DEFAULT_PASSWORD" not in source
    assert "vol.Required(CONF_USERNAME): str" in source
    assert "vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR" in source
