import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("sync_product_rag", Path(__file__).parents[1] / "sync_product_rag.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.pages = {"aegis-max/spec.md": {"name": "spec.md", "payload": b"new", "sha256": "new"}}

    def remote(self, sha="old", path="aegis-max/spec.md", product="aegis-max", status="completed", id="old"):
        return {"id": id, "name": "spec.md", "status": status, "attributes": {
            "managed_by": sync.MANAGER, "product_id": product, "source_path": path, "sha256": sha}}

    def test_unchanged_is_noop(self):
        plan = sync.plan_sync(self.pages, [self.remote(sha="new")], "aegis-max")
        self.assertEqual(plan["upload"], [])
        self.assertEqual(plan["detach"], [])

    def state(self):
        return {"owned": {}, "pending_cleanup": [], "retained_legacy": {}}

    def test_other_product_blocks_replacement(self):
        with self.assertRaises(ValueError):
            sync.plan_sync(self.pages, [self.remote(product="navi")], "aegis-max")

    def test_legacy_and_deleted_pages_removed_by_default(self):
        row = self.remote()
        row["attributes"] = {}
        row["name"] = "old-manual.pdf"
        plan = sync.plan_sync(self.pages, [row, self.remote(path="deleted.md", id="deleted")], "aegis-max")
        self.assertEqual(plan["detach"], ["old", "deleted"])

    def test_failed_index_preserves_old(self):
        client = Mock()
        client.files.create.return_value = SimpleNamespace(id="new")
        client.vector_stores.files.create.return_value = SimpleNamespace(status="failed")
        remote = [self.remote()]
        state = self.state()
        with self.assertRaises(RuntimeError):
            sync.apply_plan(client, "store", "aegis-max", self.pages, remote,
                            sync.plan_sync(self.pages, remote, "aegis-max"), state, {}, Mock())
        client.vector_stores.files.delete.assert_not_called()
        client.files.delete.assert_not_called()
        self.assertIn("new", state["owned"])

    def test_retry_reuses_new_and_detaches_legacy(self):
        remote = [self.remote(), self.remote(sha="new", id="new")]
        client = Mock()
        state = self.state()
        report = {}
        with patch.object(sync, "inventory", side_effect=[remote, [remote[1]]]):
            sync.apply_plan(client, "store", "aegis-max", self.pages, remote,
                            sync.plan_sync(self.pages, remote, "aegis-max"), state, report, Mock())
        client.files.create.assert_not_called()
        client.vector_stores.files.delete.assert_called_once_with(file_id="old", vector_store_id="store")
        client.files.delete.assert_not_called()
        self.assertIn("old", state["retained_legacy"])
        self.assertEqual(report["status"], "verified")

    def test_concurrent_change_blocks_deletion(self):
        remote = [self.remote(sha="new")]
        with patch.object(sync, "inventory", return_value=remote + [self.remote(id="unexpected")]):
            client = Mock()
            with self.assertRaises(RuntimeError):
                sync.apply_plan(client, "store", "aegis-max", self.pages, remote,
                                sync.plan_sync(self.pages, remote, "aegis-max"), self.state(), {}, Mock())
            client.vector_stores.files.delete.assert_not_called()

    def test_owned_unreferenced_deleted_shared_retained_unknown_never_deleted(self):
        state = self.state()
        state.update(owned={"old": {}, "shared": {}}, pending_cleanup=["old", "shared", "legacy"])
        client, report = Mock(), {}
        with patch.object(sync, "scan_references", return_value={"old": [], "shared": ["other-store"]}):
            sync.clean_files(client, state, report, Mock())
        client.files.delete.assert_called_once_with("old")
        self.assertEqual(state["pending_cleanup"], ["shared"])
        self.assertIn("legacy", state["retained_legacy"])

    def test_scan_failure_blocks_every_global_delete(self):
        state = self.state()
        state.update(owned={"old": {}}, pending_cleanup=["old"])
        client = Mock()
        with patch.object(sync, "scan_references", side_effect=RuntimeError("forbidden")):
            sync.clean_files(client, state, {}, Mock())
        client.files.delete.assert_not_called()
        self.assertEqual(state["pending_cleanup"], ["old"])

    def test_delete_failure_retains_retry_record(self):
        state = self.state()
        state.update(owned={"old": {}}, pending_cleanup=["old"])
        client = Mock()
        client.files.delete.side_effect = RuntimeError("network")
        with patch.object(sync, "scan_references", return_value={"old": []}):
            sync.clean_files(client, state, {}, Mock())
        self.assertEqual(state["pending_cleanup"], ["old"])
        self.assertIn("old", state["owned"])

    def test_verification_retries_stale_list_without_writes(self):
        client, report = Mock(), {}
        new = self.remote(sha="new", id="new")
        with patch.object(sync, "inventory", side_effect=[[self.remote(), new], [new]]), patch.object(sync.time, "sleep"):
            sync.verify_store(client, "store", "aegis-max", self.pages, report, Mock())
        self.assertEqual(len(report["verification"]), 2)
        self.assertEqual(report["verification"][0]["remaining"]["detach"], ["old"])
        client.files.delete.assert_not_called()
        client.vector_stores.files.delete.assert_not_called()

    def test_verification_persistent_mismatch_fails_with_evidence(self):
        report, save = {}, Mock()
        with patch.object(sync, "inventory", return_value=[]), patch.object(sync.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "missing_or_changed"):
                sync.verify_store(Mock(), "store", "aegis-max", self.pages, report, save, attempts=3)
        self.assertEqual(len(report["verification"]), 3)
        self.assertEqual(save.call_count, 3)
        self.assertEqual(report["verification"][-1]["remaining"]["upload"], list(self.pages))

    def test_create_existing_store_stops_without_post(self):
        client, report = Mock(), {}
        client.vector_stores.list.return_value = [SimpleNamespace(name="aegis-mega-d manuals", id="existing")]
        with self.assertRaisesRegex(ValueError, "Existing store"):
            sync.create_product_store(client, "aegis-mega-d", report, Mock())
        client.with_options.assert_not_called()
        self.assertEqual(report["existing_store_candidates"], ["existing"])

    def test_create_timeout_records_stage_and_disables_retries(self):
        client, report = Mock(), {}
        client.vector_stores.list.return_value = []
        client.with_options.return_value.vector_stores.create.side_effect = TimeoutError("timeout")
        with self.assertRaises(TimeoutError):
            sync.create_product_store(client, "aegis-mega-d", report, Mock())
        client.with_options.assert_called_once_with(max_retries=0)
        self.assertEqual(report["stage"], "creating_store")
        self.assertNotIn("store_id", report)

    def test_local_real_products(self):
        for product in ("aegis", "aegis-ultra", "aegis-max", "navi", "aegis-mega-d"):
            with self.subTest(product=product):
                pages = sync.load_pages(sync.ROOT / "apps/web/src/content", product)
                self.assertTrue(pages)
                self.assertTrue(all(len(p["sha256"]) == 64 for p in pages.values()))
        with self.assertRaises(ValueError):
            sync.load_pages(sync.ROOT / "apps/web/src/content", "missing")


if __name__ == "__main__":
    unittest.main()
