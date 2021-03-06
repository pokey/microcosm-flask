"""
Conventions for canonical CRUD endpoints.

"""
from inflection import pluralize

from microcosm_flask.conventions.base import Convention
from microcosm_flask.conventions.encoding import (
    dump_response_data,
    load_query_string_data,
    load_request_data,
    merge_data,
    require_response_data,
)
from microcosm_flask.conventions.registry import qs, request, response
from microcosm_flask.namespaces import Namespace
from microcosm_flask.operations import Operation
from microcosm_flask.paging import Page, PaginatedList, make_paginated_list_schema


class CRUDConvention(Convention):

    @property
    def page_cls(self):
        return Page

    def configure_search(self, ns, definition):
        """
        Register a search endpoint.

        The definition's func should be a search function, which must:
        - accept kwargs for the query string (minimally for pagination)
        - return a tuple of (items, count) where count is the total number of items
          available (in the case of pagination)

        The definition's request_schema will be used to process query string arguments.

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        paginated_list_schema = make_paginated_list_schema(ns, definition.response_schema)()

        @self.graph.route(ns.collection_path, Operation.Search, ns)
        @qs(definition.request_schema)
        @response(paginated_list_schema)
        def search(**path_data):
            request_data = load_query_string_data(definition.request_schema)
            page = self.page_cls.from_query_string(request_data)
            return_value = definition.func(**merge_data(path_data, request_data))

            if len(return_value) == 3:
                items, count, context = return_value
            else:
                context = {}
                items, count = return_value

            response_data = PaginatedList(
                ns=ns,
                page=page,
                items=items,
                count=count,
                schema=definition.response_schema,
                operation=Operation.Search,
                **context
            )
            return dump_response_data(paginated_list_schema, response_data)

        search.__doc__ = "Search the collection of all {}".format(pluralize(ns.subject_name))

    def configure_create(self, ns, definition):
        """
        Register a create endpoint.

        The definition's func should be a create function, which must:
        - accept kwargs for the request and path data
        - return a new item

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        @self.graph.route(ns.collection_path, Operation.Create, ns)
        @request(definition.request_schema)
        @response(definition.response_schema)
        def create(**path_data):
            request_data = load_request_data(definition.request_schema)
            response_data = definition.func(**merge_data(path_data, request_data))
            return dump_response_data(definition.response_schema, response_data, Operation.Create.value.default_code)

        create.__doc__ = "Create a new {}".format(ns.subject_name)

    def configure_updatebatch(self, ns, definition):
        """
        Register an update batch endpoint.

        The definition's func should be an update function, which must:
        - accept kwargs for the request and path data
        - return a new item

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        operation = Operation.UpdateBatch

        @self.graph.route(ns.collection_path, operation, ns)
        @request(definition.request_schema)
        @response(definition.response_schema)
        def update_batch(**path_data):
            request_data = load_request_data(definition.request_schema)
            response_data = definition.func(**merge_data(path_data, request_data))
            return dump_response_data(definition.response_schema, response_data, operation.value.default_code)

        update_batch.__doc__ = "Update a batch of {}".format(ns.subject_name)

    def configure_retrieve(self, ns, definition):
        """
        Register a retrieve endpoint.

        The definition's func should be a retrieve function, which must:
        - accept kwargs for path data
        - return an item or falsey

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        @self.graph.route(ns.instance_path, Operation.Retrieve, ns)
        @response(definition.response_schema)
        def retrieve(**path_data):
            response_data = require_response_data(definition.func(**path_data))
            return dump_response_data(definition.response_schema, response_data)

        retrieve.__doc__ = "Retrieve a {} by id".format(ns.subject_name)

    def configure_delete(self, ns, definition):
        """
        Register a delete endpoint.

        The definition's func should be a delete function, which must:
        - accept kwargs for path data
        - return truthy/falsey

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        @self.graph.route(ns.instance_path, Operation.Delete, ns)
        def delete(**path_data):
            require_response_data(definition.func(**path_data))
            return "", Operation.Delete.value.default_code

        delete.__doc__ = "Delete a {} by id".format(ns.subject_name)

    def configure_replace(self, ns, definition):
        """
        Register a replace endpoint.

        The definition's func should be a replace function, which must:
        - accept kwargs for the request and path data
        - return the replaced item

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        @self.graph.route(ns.instance_path, Operation.Replace, ns)
        @request(definition.request_schema)
        @response(definition.response_schema)
        def replace(**path_data):
            request_data = load_request_data(definition.request_schema)
            # Replace/put should create a resource if not already present, but we do not
            # enforce these semantics at the HTTP layer. If `func` returns falsey, we
            # will raise a 404.
            response_data = require_response_data(definition.func(**merge_data(path_data, request_data)))
            return dump_response_data(definition.response_schema, response_data)

        replace.__doc__ = "Create or update a {} by id".format(ns.subject_name)

    def configure_update(self, ns, definition):
        """
        Register an update endpoint.

        The definition's func should be an update function, which must:
        - accept kwargs for the request and path data
        - return an updated item

        :param ns: the namespace
        :param definition: the endpoint definition

        """
        @self.graph.route(ns.instance_path, Operation.Update, ns)
        @request(definition.request_schema)
        @response(definition.response_schema)
        def update(**path_data):
            # NB: using partial here means that marshmallow will not validate required fields
            request_data = load_request_data(definition.request_schema, partial=True)
            response_data = require_response_data(definition.func(**merge_data(path_data, request_data)))
            return dump_response_data(definition.response_schema, response_data)

        update.__doc__ = "Update some or all of a {} by id".format(ns.subject_name)


def configure_crud(graph, ns, mappings, path_prefix=""):
    """
    Register CRUD endpoints for a resource object.

    :param mappings: a dictionary from operations to tuple, where each tuple contains
                     the target function and zero or more marshmallow schemas according
                     to the signature of the "register_<foo>_endpoint" functions

    Example mapping:

        {
            Operation.Create: (create_foo, NewFooSchema(), FooSchema()),
            Operation.Delete: (delete_foo,),
            Operation.Retrieve: (retrieve_foo, FooSchema()),
        }

    """
    ns = Namespace.make(ns, path=path_prefix)
    convention = CRUDConvention(graph)
    convention.configure(ns, mappings)
