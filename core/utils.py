def _filter_dict(data, include=None, exclude=None):
    if not isinstance(data, dict):
        return data
    if include:
        data = {k: v for k, v in data.items() if k in include}
    if exclude:
        for key in exclude:
            data.pop(key, None)
    return data


def apply_field_selection(data, include=None, exclude=None):
    if not include and not exclude:
        return data

    if isinstance(data, list):
        return [apply_field_selection(item, include, exclude) for item in data]

    if isinstance(data, dict):
        return _filter_dict(data.copy(), include, exclude)

    return data
