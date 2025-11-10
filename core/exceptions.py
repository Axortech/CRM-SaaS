from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response

    details = response.data
    if isinstance(details, list):
        details = {"detail": details}

    error_message = "An error occurred"
    if isinstance(details, dict):
        if "detail" in details:
            error_message = details.get("detail")
        elif details:
            first_key = next(iter(details))
            value = details[first_key]
            if isinstance(value, list):
                error_message = value[0]
            else:
                error_message = str(value)

    error_code = getattr(getattr(exc, "default_code", None), "upper", lambda: None)()
    if not error_code:
        error_code = response.status_text.replace(" ", "_").upper()

    response.data = {
        "success": False,
        "error": {
            "code": error_code or "ERROR",
            "message": error_message or "Error",
            "details": details,
        },
    }
    return response
