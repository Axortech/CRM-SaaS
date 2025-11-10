from django.core.exceptions import FieldError
from django.db.models import Q
from rest_framework.filters import BaseFilterBackend


class AdvancedQueryFilterBackend(BaseFilterBackend):
    RESERVED_PARAMS = {
        "search",
        "ordering",
        "page",
        "per_page",
        "cursor",
        "fields",
        "exclude",
        "expand",
    }

    def filter_queryset(self, request, queryset, view):
        params = request.query_params
        filtered_queryset = queryset

        for key, value in params.items():
            if key in self.RESERVED_PARAMS or not value:
                continue

            if "," in value:
                values = [item.strip() for item in value.split(",") if item.strip()]
                if not values:
                    continue
                lookup = {f"{key}__in": values}
                filtered_queryset = self._safe_filter(filtered_queryset, lookup)
                continue

            if key.endswith("_after") or key.endswith("_before"):
                base_field, lookup_suffix = self._parse_range_filter(key)
                if base_field:
                    lookup = {f"{base_field}{lookup_suffix}": value}
                    filtered_queryset = self._safe_filter(filtered_queryset, lookup)

        return filtered_queryset

    def _parse_range_filter(self, param_name):
        if param_name.endswith("_after"):
            base = param_name[: -len("_after")]
            return base, "__gte"
        if param_name.endswith("_before"):
            base = param_name[: -len("_before")]
            return base, "__lte"
        return None, None

    def _safe_filter(self, queryset, lookup):
        try:
            return queryset.filter(**lookup)
        except FieldError:
            return queryset
