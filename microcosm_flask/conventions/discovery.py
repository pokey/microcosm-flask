"""
A discovery endpoint provides links to other endpoints.

"""
from flask import jsonify

from microcosm.api import defaults
from microcosm_flask.linking import Link, Links
from microcosm_flask.naming import name_for, singleton_path_for
from microcosm_flask.paging import Page
from microcosm_flask.operations import Operation


def iter_search_operations(graph, operations):
    for rule in graph.flask.url_map.iter_rules():
        if "." in rule.endpoint:
            operation, obj = Operation.parse(rule.endpoint)
            if operation in operations:
                yield operation, obj


@defaults(
    name="all",
    operations=[
        "search",
    ],
)
def configure_discovery(graph):
    """
    Build a singleton endpoint that provides a link to other endpoints.

    """
    name = graph.config.discovery.name
    operations = [
        Operation.from_name(operation_name.lower())
        for operation_name in graph.config.discovery.operations
    ]

    @graph.route(singleton_path_for(name), Operation.Discover, name)
    def discover():
        # accept pagination limit from request
        page = Page.from_request()
        page.offset = 0

        return jsonify(
            _links=Links({
                "self": Link.for_(Operation.Discover, name, qs=page.to_dict()),
                "search": [
                    Link.for_(
                        operation=operation,
                        obj=obj,
                        type=name_for(obj),
                        qs=page.to_dict(),
                    )
                    for operation, obj in iter_search_operations(graph, operations)
                ]
            }).to_dict()
        )

    return name
