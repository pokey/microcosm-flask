"""
Factories to configure Flask.

"""
from flask import Flask


def configure_flask(graph):
    """
    Create the Flask application.

    """
    return Flask(graph.metadata.name)
