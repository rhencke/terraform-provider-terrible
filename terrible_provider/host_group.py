import uuid
from typing import Optional

from tf.schema import Schema, Attribute
from tf.types import NormalizedJson, String
from tf.iface import Resource, CreateContext, ReadContext, UpdateContext, DeleteContext, ImportContext


class TerribleHostGroup(Resource):
    """A named group of terrible_host IDs for targeting tasks across multiple hosts."""

    @classmethod
    def get_name(cls) -> str:
        return "host_group"

    @classmethod
    def get_schema(cls) -> Schema:
        return Schema(
            attributes=[
                Attribute("id", String(), description="Unique host group ID", computed=True),
                Attribute(
                    "host_ids",
                    NormalizedJson(),
                    description="List of terrible_host IDs to include in this group.",
                    required=True,
                ),
            ]
        )

    def __init__(self, provider):
        self._prov = provider

    def create(self, ctx: CreateContext, planned: dict) -> Optional[dict]:
        new_id = uuid.uuid4().hex
        state = {**planned, "id": new_id}
        self._prov._state[new_id] = state
        self._prov._save_state()
        return state

    def read(self, ctx: ReadContext, current: dict) -> Optional[dict]:
        return self._prov._state.get(current.get("id"))

    def update(self, ctx: UpdateContext, current: dict, planned: dict) -> Optional[dict]:
        rid = current["id"]
        state = {**planned, "id": rid}
        self._prov._state[rid] = state
        self._prov._save_state()
        return state

    def delete(self, ctx: DeleteContext, current: dict):
        self._prov._state.pop(current.get("id"), None)
        self._prov._save_state()

    def import_(self, ctx: ImportContext, id: str) -> Optional[dict]:
        return self._prov._state.get(id)
