"""Unit tests for TerribleHostGroup resource."""

from unittest.mock import MagicMock

from tf.iface import CreateContext, DeleteContext, ImportContext, ReadContext, UpdateContext
from tf.utils import Diagnostics

from terrible_provider.host_group import TerribleHostGroup


def _ctx(klass):
    return klass(Diagnostics(), "terrible_host_group")


def _provider(state=None):
    prov = MagicMock()
    prov._state = state or {}
    prov._save_state = MagicMock()
    return prov


class TestTerribleHostGroup:
    def test_get_name(self):
        assert TerribleHostGroup.get_name() == "host_group"

    def test_schema_attrs(self):
        names = {a.name for a in TerribleHostGroup.get_schema().attributes}
        assert names == {"id", "host_ids"}

    def test_create_assigns_id(self):
        prov = _provider()
        inst = TerribleHostGroup(prov)
        state = inst.create(_ctx(CreateContext), {"host_ids": ["h1", "h2"]})
        assert len(state["id"]) == 32
        assert state["host_ids"] == ["h1", "h2"]

    def test_create_saves_state(self):
        prov = _provider()
        inst = TerribleHostGroup(prov)
        state = inst.create(_ctx(CreateContext), {"host_ids": ["h1"]})
        assert state["id"] in prov._state
        prov._save_state.assert_called_once()

    def test_read_returns_stored(self):
        prov = _provider({"g1": {"id": "g1", "host_ids": ["h1"]}})
        inst = TerribleHostGroup(prov)
        assert inst.read(_ctx(ReadContext), {"id": "g1"}) == {"id": "g1", "host_ids": ["h1"]}

    def test_read_missing_returns_none(self):
        prov = _provider()
        inst = TerribleHostGroup(prov)
        assert inst.read(_ctx(ReadContext), {"id": "nope"}) is None

    def test_update_replaces_host_ids(self):
        prov = _provider({"g1": {"id": "g1", "host_ids": ["h1"]}})
        inst = TerribleHostGroup(prov)
        result = inst.update(_ctx(UpdateContext), {"id": "g1"}, {"host_ids": ["h1", "h2"]})
        assert result["host_ids"] == ["h1", "h2"]
        assert result["id"] == "g1"
        prov._save_state.assert_called_once()

    def test_delete_removes_from_state(self):
        prov = _provider({"g1": {"id": "g1", "host_ids": []}})
        inst = TerribleHostGroup(prov)
        inst.delete(_ctx(DeleteContext), {"id": "g1"})
        assert "g1" not in prov._state
        prov._save_state.assert_called_once()

    def test_delete_missing_is_safe(self):
        prov = _provider()
        inst = TerribleHostGroup(prov)
        inst.delete(_ctx(DeleteContext), {"id": None})  # no crash

    def test_import_returns_state(self):
        prov = _provider({"g1": {"id": "g1", "host_ids": ["h1"]}})
        inst = TerribleHostGroup(prov)
        assert inst.import_(_ctx(ImportContext), "g1") == {"id": "g1", "host_ids": ["h1"]}

    def test_import_missing_returns_none(self):
        prov = _provider()
        inst = TerribleHostGroup(prov)
        assert inst.import_(_ctx(ImportContext), "gone") is None
