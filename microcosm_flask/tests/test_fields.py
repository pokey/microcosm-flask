"""
Test fields.

"""
from enum import Enum, IntEnum, unique

from hamcrest import (
    assert_that,
    contains,
    equal_to,
    is_,
)
from marshmallow import Schema
from marshmallow.fields import String
from werkzeug.datastructures import ImmutableMultiDict

from microcosm_flask.fields import (
    EnumField,
    QueryStringList,
    TimestampField,
)


TIMESTAMP = 1427702400.0
TIMESTAMP_EXTRA_PRECISION = 1427702400.1
ISOFORMAT_NAIVE = "2015-03-30T08:00:00"
ISOFORMAT_NAIVE_EXTRA_PRECISION = "2015-03-30T08:00:00.100000"
ISOFORMAT_NON_UTC = "2015-03-30T08:00:00+7:00"
ISOFORMAT_UTC = "2015-03-30T08:00:00Z"


@unique
class TestEnum(Enum):
    Foo = "foo"
    Bar = "bar"


@unique
class TestIntEnum(IntEnum):
    Foo = 1
    Bar = 2


class EnumSchema(Schema):
    name = EnumField(TestEnum, by_value=False)
    value = EnumField(TestEnum, by_value=True)
    int_name = EnumField(TestIntEnum, by_value=False)
    int_value = EnumField(TestIntEnum, by_value=True)


class TimestampSchema(Schema):
    unix = TimestampField()
    iso = TimestampField(use_isoformat=True)


class QueryStringListSchema(Schema):
    foo_ids = QueryStringList(String())


def test_load_enums():
    """
    Can deserialize enums.

    """
    schema = EnumSchema()
    result = schema.load({
        "name": TestEnum.Foo.name,
        "value": TestEnum.Bar.value,
        "int_name": TestIntEnum.Foo.name,
        "int_value": TestIntEnum.Bar.value,
    })

    assert_that(result.data["name"], is_(equal_to(TestEnum.Foo)))
    assert_that(result.data["value"], is_(equal_to(TestEnum.Bar)))
    assert_that(result.data["int_name"], is_(equal_to(TestIntEnum.Foo)))
    assert_that(result.data["int_value"], is_(equal_to(TestIntEnum.Bar)))


def test_dump_enums():
    """
    Can serialize enums.

    """
    schema = EnumSchema()
    result = schema.dump({
        "name": TestEnum.Foo,
        "value": TestEnum.Bar,
        "int_name": TestIntEnum.Foo,
        "int_value": TestIntEnum.Bar,
    })

    assert_that(result.data["name"], is_(equal_to(TestEnum.Foo.name)))
    assert_that(result.data["value"], is_(equal_to(TestEnum.Bar.value)))
    assert_that(result.data["int_name"], is_(equal_to(TestIntEnum.Foo.name)))
    assert_that(result.data["int_value"], is_(equal_to(TestIntEnum.Bar.value)))


def test_load_int_enum_as_string():
    """
    Can deserialize int enums from strings.

    """
    schema = EnumSchema()
    result = schema.load({
        "int_value": str(TestIntEnum.Bar.value),
    })

    assert_that(result.data["int_value"], is_(equal_to(TestIntEnum.Bar)))


def test_load_from_unix_timestamp_float():
    """
    Can deserialize float seconds.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": TIMESTAMP,
        "iso": TIMESTAMP,
    })

    assert_that(result.data["unix"], is_(equal_to(TIMESTAMP)))
    assert_that(result.data["iso"], is_(equal_to(TIMESTAMP)))


def test_load_from_unix_timestamp_int():
    """
    Can deserialize int seconds.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": int(TIMESTAMP),
        "iso": int(TIMESTAMP),
    })

    assert_that(result.data["unix"], is_(equal_to(int(TIMESTAMP))))
    assert_that(result.data["iso"], is_(equal_to(int(TIMESTAMP))))


def test_load_from_naive_isoformat():
    """
    Can deserialize naive isoformat.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": ISOFORMAT_NAIVE,
        "iso": ISOFORMAT_NAIVE,
    })

    assert_that(result.data["unix"], is_(equal_to(TIMESTAMP)))
    assert_that(result.data["iso"], is_(equal_to(TIMESTAMP)))


def test_load_from_naive_isoformat_extra_precision():
    """
    Can deserialize naive isoformat with sub-second precision.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": ISOFORMAT_NAIVE_EXTRA_PRECISION,
        "iso": ISOFORMAT_NAIVE_EXTRA_PRECISION,
    })

    assert_that(result.data["unix"], is_(equal_to(TIMESTAMP_EXTRA_PRECISION)))
    assert_that(result.data["iso"], is_(equal_to(TIMESTAMP_EXTRA_PRECISION)))


def test_load_from_utc_isoformat():
    """
    Can deserialize naive isoformat.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": ISOFORMAT_UTC,
        "iso": ISOFORMAT_UTC,
    })

    assert_that(result.data["unix"], is_(equal_to(TIMESTAMP)))
    assert_that(result.data["iso"], is_(equal_to(TIMESTAMP)))


def test_load_from_non_utc_isoformat():
    """
    Can deserialize naive isoformat.

    """
    schema = TimestampSchema()
    result = schema.load({
        "unix": ISOFORMAT_NON_UTC,
        "iso": ISOFORMAT_NON_UTC,
    })

    assert_that(result.errors["unix"], contains("Timestamps must be defined in UTC"))
    assert_that(result.errors["iso"], contains("Timestamps must be defined in UTC"))


def test_dump():
    """
    Can serialize to appropriate type.

    """
    schema = TimestampSchema()
    result = schema.dump({
        "unix": TIMESTAMP,
        "iso": TIMESTAMP,
    })

    assert_that(result.data["unix"], is_(equal_to(TIMESTAMP)))
    assert_that(result.data["iso"], is_(equal_to(ISOFORMAT_NAIVE)))


def test_query_list_load_with_comma_separated_single_keys():
    """
    tests for support of /foo?foo_ids=1,2
    """
    schema = QueryStringListSchema()
    result = schema.load(
        ImmutableMultiDict([("foo_ids", "a,b")]),
    )

    assert_that(result.data["foo_ids"], is_(equal_to(["a", "b"])))


def test_query_list_load_with_duplicate_keys():
    """
    tests for support of /foo?foo_ids[]=1&foo_ids[]=2
    """
    schema = QueryStringListSchema()
    result = schema.load(
        ImmutableMultiDict([("foo_ids", "a"), ("foo_ids", "b")]),
    )

    assert_that(result.data["foo_ids"], is_(equal_to(["a", "b"])))


def test_query_list_dump():
    schema = QueryStringListSchema()
    result = schema.dump({
        "foo_ids": ["a"],
    })

    assert_that(result.data["foo_ids"], is_(equal_to(["a"])))
