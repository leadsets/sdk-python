# Contributing

Thanks for helping improve the Leadsets Python SDK.

## Development

The project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/leadsets/sdk-python.git
cd sdk-python
uv sync                    # creates .venv with the dev tools
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy                # type check (strict)
uv run pytest              # tests
uv build                   # wheel and sdist in dist/
```

Tests mock HTTP with [respx](https://lundberg.github.io/respx/). They never call the live API and
need no key.

## Pull requests

- Open an issue first for anything larger than a small fix, so we can agree on the approach.
- Keep each pull request to one change, with tests for both the sync and async clients.
- Keep `httpx` the only required runtime dependency.
- Update `CHANGELOG.md` under an "Unreleased" heading.
- Never commit API keys or `.env` files.

## Releases

Maintainers release by bumping `__version__` in `src/leadsets/_version.py`, updating the
changelog, and pushing a `vX.Y.Z` tag. The release workflow publishes to PyPI.

## Code of conduct

Be kind and constructive. We may remove comments or contributions that aren't.
