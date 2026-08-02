from mode_options import get_mode_value, merge_mode_options


MODE_FIELDS = {
    "server": ("host", "port", "username", "password"),
    "direct": ("host", "port", "slave_id"),
}


def test_existing_server_entry_keeps_credentials_when_switching_modes():
    entry_data = {
        "mode": "server",
        "host": "server.local",
        "port": 8085,
        "username": "admin",
        "password": "secret",
    }

    direct_options = merge_mode_options(
        entry_data,
        {},
        "direct",
        {"host": "gateway.local", "port": 502, "slave_id": 20},
        MODE_FIELDS,
    )

    assert get_mode_value(entry_data, direct_options, "server", "host") == "server.local"
    assert get_mode_value(entry_data, direct_options, "server", "username") == "admin"
    assert get_mode_value(entry_data, direct_options, "server", "password") == "secret"

    server_input = {
        key: get_mode_value(entry_data, direct_options, "server", key)
        for key in MODE_FIELDS["server"]
    }
    server_options = merge_mode_options(
        entry_data,
        direct_options,
        "server",
        server_input,
        MODE_FIELDS,
    )

    assert server_options["host"] == "server.local"
    assert server_options["username"] == "admin"
    assert server_options["password"] == "secret"
    assert (
        get_mode_value(entry_data, server_options, "direct", "host")
        == "gateway.local"
    )
    assert get_mode_value(entry_data, server_options, "direct", "port") == 502


def test_new_direct_entry_has_no_server_credential_suggestions():
    entry_data = {
        "mode": "direct",
        "host": "gateway.local",
        "port": 502,
        "slave_id": 20,
    }
    assert get_mode_value(entry_data, {}, "server", "username") is None
    assert get_mode_value(entry_data, {}, "server", "password") is None


def test_merge_preserves_unrelated_options():
    merged = merge_mode_options(
        {"mode": "server"},
        {"unrelated": True},
        "direct",
        {"host": "gateway.local", "port": 502, "slave_id": 20},
        MODE_FIELDS,
    )
    assert merged["unrelated"] is True
