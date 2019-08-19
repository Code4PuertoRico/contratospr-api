from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class PageNumberPagination(pagination.PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    (
                        "links",
                        {
                            "next": self.get_next_link(),
                            "previous": self.get_previous_link(),
                        },
                    ),
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("page", self.page.number),
                    ("results", data),
                ]
            )
        )
