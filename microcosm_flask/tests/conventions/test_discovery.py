"""
Test the discovery endpoint.

"""
from json import loads

from hamcrest import (
    assert_that,
    equal_to,
    is_,
)

from microcosm.api import create_object_graph
from microcosm_flask.operations import Operation


def test_discovery():
    graph = create_object_graph(name="example", testing=True)
    # TODO: can we make this automatic?
    graph.use("discovery")

    @graph.route("/path", Operation.Search, "foo")
    def search_foo():
        pass

    client = graph.flask.test_client()

    response = client.get("/api/all")
    assert_that(response.status_code, is_(equal_to(200)))
    data = loads(response.get_data())
    assert_that(data, is_(equal_to({
        "_links": {
            "search": [{
                "href": "http://localhost/api/path?limit=20&offset=0",
                "type": "foo",
            }],
            "self": {
                "href": "http://localhost/api/all?limit=20&offset=0"
            },
        }
    })))
