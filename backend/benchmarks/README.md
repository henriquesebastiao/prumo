# Benchmarks

Performance benchmarks for the backend, run with [pytest-codspeed](https://codspeed.io/docs/reference/pytest-codspeed)
and tracked continuously by [CodSpeed](https://app.codspeed.io/henriquesebastiao/prumo).

They cover CPU-bound code that needs no database: the pure rules of each module (`rules.py`) and
the OpenAPI contract generation.

```sh
cd backend
uv run pytest benchmarks --codspeed
```

The `tests/` suite is not affected: `testpaths` only points at `tests`.
