"""
Testing fixtures (e.g. for CRUD).

"""
from uuid import uuid4

from marshmallow import fields, Schema

from microcosm_flask.linking import Links, Link
from microcosm_flask.operations import Operation


class Person(object):
    def __init__(self, id, first_name, last_name):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name


class NewPersonSchema(Schema):
    firstName = fields.Str(attribute="first_name", required=True)
    lastName = fields.Str(attribute="last_name", required=True)


class NewPersonBatchSchema(Schema):
    items = fields.List(fields.Nested(NewPersonSchema))


class PersonSchema(NewPersonSchema):
    id = fields.UUID(required=True)
    _links = fields.Method("get_links", dump_only=True)

    def get_links(self, obj):
        links = Links()
        links["self"] = Link.for_(Operation.Retrieve, Person, person_id=obj.id)
        return links.to_dict()


class PersonBatchSchema(NewPersonSchema):
    items = fields.List(fields.Nested(PersonSchema))


PERSON_ID_1 = uuid4()
PERSON_ID_2 = uuid4()
PERSON_1 = Person(PERSON_ID_1, "Alice", "Smith")


def person_create(**kwargs):
    return Person(id=PERSON_ID_2, **kwargs)


def person_search(offset, limit):
    return [PERSON_1], 1


def person_update_batch(items):
    return dict(
        items=[
            person_create(**item)
            for item in items
        ]
    )


def person_retrieve(person_id):
    if person_id == PERSON_ID_1:
        return PERSON_1
    else:
        return None


def person_delete(person_id):
    return person_id == PERSON_ID_1


def person_replace(person_id, **kwargs):
    return Person(id=person_id, **kwargs)


def person_update(person_id, **kwargs):
    if person_id == PERSON_ID_1:
        for key, value in kwargs.items():
            setattr(PERSON_1, key, value)
        return PERSON_1
    else:
        return None
