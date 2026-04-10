def _extract_number(value):
    if value is None:
        return 0
    parts = str(value).split("_")
    if len(parts) < 2:
        try:
            return int(value)
        except ValueError:
            return 0
    try:
        return int(parts[-1])
    except ValueError:
        return 0


def next_prefixed_id(items, key, prefix, width=3):
    max_value = 0
    for item in items:
        max_value = max(max_value, _extract_number(item.get(key)))
    return f"{prefix}{str(max_value + 1).zfill(width)}"


def next_int_id(items, key="id"):
    max_value = 0
    for item in items:
        try:
            max_value = max(max_value, int(item.get(key)))
        except (TypeError, ValueError):
            continue
    return max_value + 1


def new_uuid():
    import uuid

    return str(uuid.uuid4())
