from rest_framework.renderers import JSONRenderer

from core.utils import apply_field_selection


class StandardJSONRenderer(JSONRenderer):
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get("response")
        request = renderer_context.get("request")

        if response is not None and not getattr(response, "exception", False):
            include = exclude = None
            if request:
                fields_param = request.query_params.get("fields")
                exclude_param = request.query_params.get("exclude")
                include = {field.strip() for field in fields_param.split(",") if field.strip()} if fields_param else None
                exclude = {field.strip() for field in exclude_param.split(",") if field.strip()} if exclude_param else None

            meta = None
            message = None

            if isinstance(data, dict):
                meta = data.pop("_meta", None)
                message = data.pop("_message", None)
                if "results" in data and len(data) == 1:
                    data = data["results"]

            filtered_data = apply_field_selection(data, include, exclude)
            payload = {
                "success": True,
                "data": filtered_data,
                "message": message or "Operation successful",
            }
            if meta:
                payload["meta"] = meta
            data = payload

        return super().render(data, accepted_media_type, renderer_context)
