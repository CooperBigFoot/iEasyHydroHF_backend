def mask_sensitive_data(in_data):
    SENSITIVE_KEYS = [
        "password",
        "oldPassword",
        "newPassword1",
        "newPassword2",
    ]

    if isinstance(in_data, dict):
        out_data = {}
        for key, value in in_data.iteritems():
            if isinstance(value, dict) or isinstance(value, list):
                out_data[key] = mask_sensitive_data(value)
            elif isinstance(value, basestring) and key in SENSITIVE_KEYS:
                out_data[key] = "***"
            else:
                out_data[key] = value
    elif isinstance(in_data, list):
        out_data = [mask_sensitive_data(value) for value in in_data]
    else:
        out_data = in_data

    return out_data
