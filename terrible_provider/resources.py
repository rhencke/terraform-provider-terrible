import json
import uuid
from typing import Optional

from tf.schema import Schema, Attribute
from tf.types import String
from tf.utils import Diagnostics
from tf.iface import Resource, CreateContext, ReadContext, UpdateContext, DeleteContext, ImportContext


class TerribleItem(Resource):
    @classmethod
    def get_name(cls) -> str:
        return "item"

    @classmethod
    def get_schema(cls) -> Schema:
        return Schema(
            attributes=[
                Attribute("id", String(), description="Unique id", computed=True),
                Attribute("name", String(), description="Name", required=True),
                Attribute("value", String(), description="Value", optional=True),
            ]
        )

    def __init__(self, provider):
        self._prov = provider

    def _persist(self):
        self._prov._save_state()

    def create(self, ctx: CreateContext, planned: dict) -> Optional[dict]:
        diags: Diagnostics = ctx.diagnostics
        # generate id
        new_id = uuid.uuid4().hex
        state = {**planned}
        state["id"] = new_id
        # store
        self._prov._state[new_id] = state
        self._persist()
        return state

    def read(self, ctx: ReadContext, current: dict) -> Optional[dict]:
        diags: Diagnostics = ctx.diagnostics
        rid = current.get("id")
        if rid is None:
            diags.add_error("Missing id for read", path=["id"])  # type: ignore[arg-type]
            return None

        return self._prov._state.get(rid)

    def update(self, ctx: UpdateContext, current: dict, planned: dict) -> Optional[dict]:
        diags: Diagnostics = ctx.diagnostics
        rid = current.get("id")
        if rid not in self._prov._state:
            diags.add_error(f"Resource {rid} not found for update", path=["id"])  # type: ignore[arg-type]
            return None

        new = {**self._prov._state[rid], **planned}
        new["id"] = rid
        self._prov._state[rid] = new
        self._persist()
        return new

    def delete(self, ctx: DeleteContext, current: dict):
        diags: Diagnostics = ctx.diagnostics
        rid = current.get("id")
        if rid in self._prov._state:
            del self._prov._state[rid]
            self._persist()
        return None

    def import_(self, ctx: ImportContext, id: str) -> Optional[dict]:
        # Import by id if exists
        return self._prov._state.get(id)
