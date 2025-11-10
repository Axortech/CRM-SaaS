from collections import OrderedDict
from urllib.parse import urlparse, parse_qs

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response


class CursorResultsPagination(CursorPagination):
    page_size = 20
    max_page_size = 100
    ordering = "-created_at"

    def get_paginated_response(self, data):
        next_link = self.get_next_link()
        previous_link = self.get_previous_link()

        meta = {
            "cursor_next": self._extract_cursor(next_link),
            "cursor_previous": self._extract_cursor(previous_link),
            "per_page": self.get_page_size(self.request),
        }
        return Response({"results": data, "_meta": meta})

    def _extract_cursor(self, link):
        if not link:
            return None
        query = urlparse(link).query
        params = parse_qs(query)
        cursor = params.get(self.cursor_query_param)
        if cursor:
            return cursor[0]
        return None


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 100
    page_size_query_param = "per_page"
    cursor_param = "cursor"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cursor_pagination = CursorResultsPagination()
        self.use_cursor = False

    def paginate_queryset(self, queryset, request, view=None):
        if self.cursor_param in request.query_params:
            self.use_cursor = True
            self.cursor_pagination.request = request
            self.cursor_pagination.cursor_query_param = self.cursor_param
            self.cursor_pagination.page_size = self.get_page_size(request)
            self.cursor_pagination.max_page_size = self.max_page_size
            ordering = getattr(view, "ordering", None)
            if ordering:
                self.cursor_pagination.ordering = ordering
            return self.cursor_pagination.paginate_queryset(queryset, request, view)
        self.use_cursor = False
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self.use_cursor:
            return self.cursor_pagination.get_paginated_response(data)

        per_page = self.get_page_size(self.request)
        meta = OrderedDict(
            [
                ("page", self.page.number),
                ("per_page", per_page),
                ("total", self.page.paginator.count),
                ("total_pages", self.page.paginator.num_pages),
            ]
        )
        return Response({"results": data, "_meta": meta})
