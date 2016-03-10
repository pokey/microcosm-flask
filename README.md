# microcosm-flask

Opinionated Flask services.

[![Circle CI](https://circleci.com/gh/globality-corp/microcosm-flask/tree/develop.svg?style=svg)](https://circleci.com/gh/globality-corp/microcosm-logging/tree/develop)


## Conventions

 - Every Flask service has a health check endpoint at `/api/health`


## Configuration

 - The object graph's `debug` and `testing` flags are propagated to the Flask application.
