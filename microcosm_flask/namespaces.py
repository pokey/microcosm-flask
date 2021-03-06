"""
Defines namespaces for operations that follow various API conventions.

In conjunction with the `Operation` enum, defines a naming convention for HTTP endpoints,
which in turn provides a discovery mechanism API routes.

"""
from re import match

from flask import request, url_for
from six.moves.urllib.parse import urlencode, urljoin
from werkzeug.exceptions import InternalServerError

from microcosm_flask.naming import (
    collection_path_for,
    instance_path_for,
    name_for,
    relation_path_for,
    singleton_path_for,
)
from microcosm_flask.operations import Operation


class Namespace(object):
    """
    Encapsulates the namespace for one or more operations.

    Each fully qualified operation can be viewed as a subject, verb, and optional object.

    The `Operation` enum defines the legal verbs (according to various conventions); this
    object encapsulates the rest.

    """

    def __init__(
        self,
        subject,
        object_=None,
        path=None,
        controller=None,
        version=None,
        enable_basic_auth=False
    ):
        """
        :param subject: the target resource (or resource name) of this namespace
        :param object_: the subject resource (or resource name) of this namespace (e.g. for relations)
        :param path: the path prefix for this namespace
        :param controller: the object responsible for implementations associated with this namespace.
        :param version: the version of this namespace
        :param enable_basic_auth: enable basic auth for this namespace if it's not enabled globally
        """
        self.subject = subject
        self.object_ = object_
        self.prefix = path or ""
        self.controller = controller
        self.version = version
        self.enable_basic_auth = enable_basic_auth

    @property
    def path(self):
        if self.version:
            return self.prefix + "/" + self.version
        else:
            return self.prefix

    @property
    def object_ns(self):
        """
        Create a new namespace for the current namespace's object value.

        """
        return Namespace(
            path=self.path,
            subject=self.object_,
            object_=None,
            version=self.version,
        )

    @property
    def subject_name(self):
        return name_for(self.subject)

    @property
    def object_name(self):
        return name_for(self.object_)

    @property
    def collection_path(self):
        return self.path + collection_path_for(self.subject)

    @property
    def instance_path(self):
        return self.path + instance_path_for(self.subject)

    @property
    def relation_path(self):
        return self.path + relation_path_for(self.subject, self.object_)

    @property
    def singleton_path(self):
        return self.path + singleton_path_for(self.subject)

    def endpoint_for(self, operation):
        """
        Create a (unique) endpoint name from an operation and a namespace.

        This naming convention matches how Flask blueprints routes are resolved
        (assuming that the blueprint and resources share the same name).

        Examples: `foo.search`, `bar.search_for.baz`

        """
        return operation.value.pattern.format(
            subject=self.subject_name,
            operation=operation.value.name,
            object_=self.object_name if self.object_ else None,
            version=self.version or "v1",
        )

    @staticmethod
    def parse_endpoint(endpoint):
        """
        Convert an endpoint name into an (operation, ns) tuple.

        """
        # compute the operation
        parts = endpoint.split(".")
        operation = Operation.from_name(parts[1])

        # extract its parts
        matcher = match(operation.endpoint_pattern, endpoint)
        if not matcher:
            raise InternalServerError("Malformed operation endpoint: {}".format(endpoint))
        kwargs = matcher.groupdict()
        del kwargs["operation"]
        return operation, Namespace(**kwargs)

    def url_for(self, operation, _external=True, **kwargs):
        """
        Construct a URL for an operation against a resource.

        :param kwargs: additional arguments for URL path expansion,
            which are passed to flask.url_for.
            In particular, _external=True produces absolute url.
        """
        return url_for(self.endpoint_for(operation), _external=_external, **kwargs)

    def href_for(self, operation, qs=None, **kwargs):
        """
        Construct an full href for an operation against a resource.

        :parm qs: the query string dictionary, if any
        :param kwargs: additional arguments for path expansion
        """
        url = urljoin(request.url_root, self.url_for(operation, **kwargs))
        qs_character = "?" if url.find("?") == -1 else "&"

        return "{}{}".format(
            url,
            "{}{}".format(qs_character, urlencode(qs)) if qs else "",
        )

    @classmethod
    def make(cls, value, path=None):
        """
        Create a Namespace from a value.

        Used to transition older APIs that relied on strings/objects/tuples/lists
        to pass subject and object information instead of Namespace instances.

        """
        if isinstance(value, Namespace):
            return value
        elif isinstance(value, (tuple, list)):
            return cls(
                subject=value[0],
                object_=value[1],
                path=path,
            )
        else:
            return cls(
                subject=value,
                path=path,
            )
