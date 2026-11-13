"""Building the application and its OpenAPI contract (what `prumo openapi` exports)."""

from pytest_codspeed import BenchmarkFixture

from prumo.main import create_app
from prumo.openapi import build_schema, render_schema


def test_create_app(benchmark: BenchmarkFixture) -> None:
    benchmark(create_app)


def test_build_openapi_schema(benchmark: BenchmarkFixture) -> None:
    benchmark(build_schema)


def test_render_openapi_schema(benchmark: BenchmarkFixture) -> None:
    schema = build_schema()
    benchmark(render_schema, schema)
