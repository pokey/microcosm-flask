from marshmallow import Schema, fields


class EmptySchema(Schema):
    """
    Dummy schema for making empty requests without swagger validation errors.
    """
    _ = fields.Boolean(required=True, dump_only=True)
