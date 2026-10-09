import json
import re
from pathlib import Path


_PACKAGE = Path(__file__).resolve().parent.parent / "custom_components" / "vmc_ubbink"
_CONFIG_FLOW = _PACKAGE / "config_flow.py"
_OPTIONS_FLOW = _PACKAGE / "options_flow.py"
_STRINGS = (_PACKAGE / "strings.json", _PACKAGE / "translations" / "en.json")


def test_new_server_setup_does_not_prefill_credentials():
    source = _CONFIG_FLOW.read_text()
    assert "default=DEFAULT_USERNAME" not in source
    assert "default=DEFAULT_PASSWORD" not in source
    assert "vol.Required(CONF_USERNAME): str" in source
    assert "vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR" in source


def test_model_is_asked_in_every_setup_and_options_step():
    # One field per connection mode (direct + server), in both flows, so a
    # W600 owner can pick the model whichever way the VMC is connected.
    for path in (_CONFIG_FLOW, _OPTIONS_FLOW):
        fields = re.findall(r"vol\.Required\(\s*CONF_MODEL\b", path.read_text())
        assert len(fields) == 2, path.name


def test_model_field_is_labelled_in_every_step():
    for path in _STRINGS:
        strings = json.loads(path.read_text())
        for section in ("config", "options"):
            for step in ("direct", "server"):
                data = strings[section]["step"][step]["data"]
                assert data.get("model") == "Model", (path.name, section, step)
