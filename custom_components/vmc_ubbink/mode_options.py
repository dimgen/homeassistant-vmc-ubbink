_MODE_KEY = "mode"
_CACHE_PREFIX = "_mode"


def _cache_key(mode, key):
    return f"{_CACHE_PREFIX}_{mode}_{key}"


def _active_mode(entry_data, current_options, default_mode):
    return current_options.get(
        _MODE_KEY,
        entry_data.get(_MODE_KEY, default_mode),
    )


def get_mode_value(
    entry_data,
    current_options,
    mode,
    key,
    default=None,
    default_mode="server",
):
    """Get a setting previously saved for one connection mode."""
    cached_key = _cache_key(mode, key)
    if cached_key in current_options:
        return current_options[cached_key]

    if _active_mode(entry_data, current_options, default_mode) == mode:
        if key in current_options:
            return current_options[key]
        return entry_data.get(key, default)

    if entry_data.get(_MODE_KEY, default_mode) == mode:
        return entry_data.get(key, default)

    return default


def merge_mode_options(
    entry_data,
    current_options,
    target_mode,
    user_input,
    mode_fields,
    default_mode="server",
):
    """Save active values while retaining settings for the other mode."""
    merged = dict(current_options)
    previous_mode = _active_mode(entry_data, current_options, default_mode)

    for key in mode_fields.get(previous_mode, ()):
        value = get_mode_value(
            entry_data,
            current_options,
            previous_mode,
            key,
            default_mode=default_mode,
        )
        if value is not None:
            merged[_cache_key(previous_mode, key)] = value

    merged.update(user_input)
    merged[_MODE_KEY] = target_mode
    for key in mode_fields[target_mode]:
        if key in user_input:
            merged[_cache_key(target_mode, key)] = user_input[key]

    return merged
