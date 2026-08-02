import importlib.util
import sys
import types
import uuid
from pathlib import Path


_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent / "custom_components" / "vmc_ubbink"
)
_INIT_PATH = _PACKAGE_DIR / "__init__.py"


def _load_component(monkeypatch):
    package_name = f"vmc_ubbink_compat_{uuid.uuid4().hex}"

    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    core = types.ModuleType("homeassistant.core")
    exceptions = types.ModuleType("homeassistant.exceptions")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    core.HomeAssistant = type("HomeAssistant", (), {})
    exceptions.ConfigEntryNotReady = type("ConfigEntryNotReady", (Exception,), {})
    monkeypatch.setitem(sys.modules, "homeassistant", homeassistant)
    monkeypatch.setitem(sys.modules, "homeassistant.config_entries", config_entries)
    monkeypatch.setitem(sys.modules, "homeassistant.core", core)
    monkeypatch.setitem(sys.modules, "homeassistant.exceptions", exceptions)

    class FakeAPI:
        def __init__(self, host, port, username, password):
            self.args = (host, port, username, password)

    api = types.ModuleType(f"{package_name}.api")
    api.VMCUbifluxAPI = FakeAPI
    monkeypatch.setitem(sys.modules, f"{package_name}.api", api)

    class FakeDirectClient:
        def __init__(self, host, port, slave):
            self.args = (host, port, slave)

    direct = types.ModuleType(f"{package_name}.direct")
    direct.DirectClient = FakeDirectClient
    monkeypatch.setitem(sys.modules, f"{package_name}.direct", direct)

    spec = importlib.util.spec_from_file_location(
        package_name,
        _INIT_PATH,
        submodule_search_locations=[str(_PACKAGE_DIR)],
    )
    component = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, package_name, component)
    spec.loader.exec_module(component)
    return component


def _entry(data, options=None):
    return types.SimpleNamespace(data=data, options=options or {})


def test_legacy_server_entry_keeps_existing_fallback(monkeypatch):
    component = _load_component(monkeypatch)
    client = component.build_client(_entry({"host": "server.local", "port": 8085}))
    assert client.args == ("server.local", 8085, "admin", "secret")


def test_existing_server_entry_keeps_saved_credentials(monkeypatch):
    component = _load_component(monkeypatch)
    client = component.build_client(
        _entry(
            {
                "mode": "server",
                "host": "server.local",
                "port": 8085,
                "username": "saved-user",
                "password": "saved-password",
            }
        )
    )
    assert client.args == (
        "server.local",
        8085,
        "saved-user",
        "saved-password",
    )


def test_existing_direct_entry_still_needs_no_credentials(monkeypatch):
    component = _load_component(monkeypatch)
    client = component.build_client(
        _entry(
            {
                "mode": "direct",
                "host": "gateway.local",
                "port": 502,
                "slave_id": 20,
            }
        )
    )
    assert client.args == ("gateway.local", 502, 20)
