"""
Pagination support.

"""
from flask import request

from microcosm_flask.linking import Link, Links
from microcosm_flask.operations import Operation


class Page(object):
    def __init__(self, offset, limit):
        self.offset = offset
        self.limit = limit

    @classmethod
    def from_request(cls, default_limit=20):
        try:
            offset = int(request.args["offset"])
        except:
            offset = 0
        try:
            limit = int(request.args["limit"])
        except:
            limit = default_limit
        return cls(offset=offset, limit=limit)

    def next(self):
        return Page(
            offset=self.offset + self.limit,
            limit=self.limit,
        )

    def prev(self):
        return Page(
            offset=self.offset - self.limit,
            limit=self.limit,
        )

    def to_dict(self):
        return dict(
            offset=self.offset,
            limit=self.limit,
        )

    def to_tuples(self):
        """
        Convert to tuples for deterministic order when passed to urlencode.

        """
        return [
            ("offset", self.offset),
            ("limit", self.limit),
        ]


class PaginatedList(object):

    def __init__(self, obj, page, items, count, to_dict_func=None):
        self.obj = obj
        self.page = page
        self.items = items
        self.count = count
        self.to_dict_func = to_dict_func

    def to_dict(self):
        return dict(
            count=self.count,
            items=[
                self.to_dict_func(item) if self.to_dict_func else item
                for item in self.items
            ],
            _links=self.links.to_dict(),
            **self.page.to_dict()
        )

    @property
    def operation(self):
        return Operation.Search

    @property
    def links(self):
        links = Links()
        links["self"] = Link.for_(self.operation, self.obj, qs=self.page.to_tuples())
        if self.page.offset + self.page.limit < self.count:
            links["next"] = Link.for_(self.operation, self.obj, qs=self.page.next().to_tuples())
        if self.page.offset > 0:
            links["prev"] = Link.for_(self.operation, self.obj, qs=self.page.prev().to_tuples())
        return links
