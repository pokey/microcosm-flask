"""
Swagger (OpenAPI) convention.

Exposes swagger definitions for matching operations.

"""
from flask import jsonify, g

from microcosm.api import defaults
from microcosm_flask.conventions.base import Convention
from microcosm_flask.conventions.registry import iter_endpoints
from microcosm_flask.namespaces import Namespace
from microcosm_flask.operations import Operation
from microcosm_flask.swagger.definitions import build_swagger


class SwaggerConvention(Convention):

    def __init__(self, graph, path):
        super(SwaggerConvention, self).__init__(graph)
        self.path = path

    @property
    def matching_operations(self):
        return {
            Operation.from_name(operation_name)
            for operation_name in self.graph.config.swagger_convention.operations
        }

    @property
    def operations(self):
        """
        Compute current matching endpoints.

        Evaluated as a property to defer evaluation.

        """
        def match_func(operation, ns, rule):
            return (
                rule.rule.startswith(self.path) and
                operation in self.matching_operations
            )

        return list(iter_endpoints(self.graph, match_func))

    def configure_discover(self, ns, definition):
        """
        Register a swagger endpoint for a set of operations.

        """
        @self.graph.route(ns.singleton_path, Operation.Discover, ns)
        def discover():
            swagger = build_swagger(self.graph, ns.version, ns.path, self.operations)
            g.hide_body = True
            return jsonify(swagger)


@defaults(
    name="swagger",
    operations=[
        "create",
        "delete",
        "replace",
        "retrieve",
        "search",
        "search_for",
        "update",
    ],
    path_prefix="",
)
def configure_swagger(graph):
    """
    Build a singleton endpoint that provides swagger definitions for all operations.

    """
    name = graph.config.swagger_convention.name
    version = graph.config.swagger_convention.version

    base_path = graph.config.route.path_prefix
    path_prefix = graph.config.swagger_convention.path_prefix + "/" + version

    ns = Namespace(
        path=path_prefix,
        subject=name,
        version=version,
    )

    convention = SwaggerConvention(graph, base_path + path_prefix)
    convention.configure(ns, discover=tuple())
    return ns.subject
