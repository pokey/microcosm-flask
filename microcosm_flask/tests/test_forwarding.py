"""
Forwarding tests.

"""
from flask import url_for
from hamcrest import (
    assert_that,
    equal_to,
    is_,
)
from microcosm.api import create_object_graph


def test_forwarding():
    graph = create_object_graph("test", testing=True)
    graph.use(
        "flask",
        "port_forwarding",
    )

    @graph.app.route("/", endpoint="test")
    def endpoint():
        return url_for("test", _external=True)

    client = graph.app.test_client()
    response = client.get(
        "/",
        headers={
            "X-Forwarded-Port": "8080",
        },
    )

    assert_that(response.status_code, is_(equal_to(200)))
    assert_that(response.data, is_(equal_to("http://localhost:8080/")))
