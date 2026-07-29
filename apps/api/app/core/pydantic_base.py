"""
Base Pydantic schema for the vidashort API.

Per CLAUDE.md §3 the API contract (docs/contracts/00-overview.md, docs/api/00-overview.md)
is camelCase on the wire. All schemas inherit from `BaseSchema` so they
serialize with `to_camel` aliases automatically.

`populate_by_name=True` lets request schemas accept either the Python snake_case
field name OR the camelCase alias on input — so clients can send either form,
but the canonical Python attribute remains snake_case (matches SQLAlchemy models).
"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
