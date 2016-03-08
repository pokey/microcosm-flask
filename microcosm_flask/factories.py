"""
Factories to configure Flask.

"""
from flask import Flask


def configure_flask(graph):
    """
    Create the Flask application.

    """
    flask = Flask(graph.metadata.name)
    flask.debug = graph.metadata.debug
    flask.testing = graph.metadata.testing

    # TODO: wire in the graph's configuration to Flask's

    return flask
