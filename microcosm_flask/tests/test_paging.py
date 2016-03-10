"""
Paging tests.

"""
from hamcrest import (
    assert_that,
    equal_to,
    is_,
)

from microcosm.api import create_object_graph
from microcosm_flask.operations import Operation
from microcosm_flask.paging import Page, PaginatedList


def test_page_from_request():
    graph = create_object_graph(name="example", testing=True)

    with graph.flask.test_request_context():
        page = Page.from_request(default_limit=100)
        assert_that(page.offset, is_(equal_to(0)))
        assert_that(page.limit, is_(equal_to(100)))


def test_page_to_dict():
    page = Page(0, 10)
    assert_that(page.to_dict(), is_(equal_to({
        "offset": 0,
        "limit": 10
    })))


def test_page_next():
    page = Page(0, 10).next()
    assert_that(page.offset, is_(equal_to(10)))
    assert_that(page.limit, is_(equal_to(10)))


def test_page_prev():
    page = Page(20, 10).prev()
    assert_that(page.offset, is_(equal_to(10)))
    assert_that(page.limit, is_(equal_to(10)))


def test_paginated_list_to_dict():
    graph = create_object_graph(name="example", testing=True)

    @graph.route("/path", Operation.Search, "foo")
    def search_foo():
        pass

    paginated_list = PaginatedList("foo", Page(2, 2), ["1", "2"], 10)

    with graph.flask.test_request_context():
        assert_that(paginated_list.to_dict(), is_(equal_to({
            "count": 10,
            "items": [
                "1",
                "2",
            ],
            "offset": 2,
            "limit": 2,
            "_links": {
                "self": {
                    "href": "http://localhost/api/path?offset=2&limit=2",
                },
                "next": {
                    "href": "http://localhost/api/path?offset=4&limit=2",
                },
                "prev": {
                    "href": "http://localhost/api/path?offset=0&limit=2",
                },
            }
        })))
