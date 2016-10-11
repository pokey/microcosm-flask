"""
Support for request forwarding.

HATEOAS depends heavily on services being able to generate URIs back to their own resources.
Under some request forwarding scenarios (especially AWS ALBs), services may not be resolved
on a URI that is accessible to other services. This can be solved by configuring static
service URIs... or by resolving URIs using X-Forwarded headers.

"""
from flask import request, _request_ctx_stack

from microcosm_flask.session import register_session_factory


def use_forwarded_port(graph):
    """
    Inject the `X-Forwarded-Port` (if any) into the current URL adapter.

    The URL adapter is used by `url_for` to build a URLs.

    """
    forwarded_port = request.headers.get("X-Forwarded-Port")
    if not forwarded_port:
        return None

    if _request_ctx_stack is None:
        return None

    # There must be a better way!
    context = _request_ctx_stack.top
    context.url_adapter.server_name = "{}:{}".format(
        context.url_adapter.server_name.split(":", 1)[0],
        forwarded_port,
    )

    return forwarded_port


def configure_port_forwarding(graph):
    """
    Bind the SQLAlchemy session context to Flask.

    The current session is available at `g.db.session`.

    """
    return register_session_factory(graph, "forwarded_port", use_forwarded_port)
