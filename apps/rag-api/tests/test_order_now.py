import sys
import json
import runpy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from moto import mock_aws

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.order_now_service import DEFAULT_ORDER_NOW_URL, DEFAULT_ORDER_NOW_RULES, OrderNowStorage


class OrderNowTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "order_now.json"
        self.storage = OrderNowStorage(self.path)

    def test_defaults_edits_disabling_and_delete_all_survive_restart(self):
        initial = self.storage.get_config()
        self.assertEqual(initial["default_url"], DEFAULT_ORDER_NOW_URL)
        self.assertEqual({rule["id"] for rule in initial["rules"]}, set(DEFAULT_ORDER_NOW_RULES))
        self.assertEqual(len(initial["rules"]), 13)
        self.assertEqual(len({rule["label"] for rule in initial["rules"]}), 10)
        navi = next(rule for rule in initial["rules"] if rule["id"] == "navi")
        updated, created = self.storage.save_rule({**navi, "enabled": False, "label": "Custom Navi"})
        self.assertFalse(created)
        self.assertEqual(len(self.storage.get_config()["rules"]), 12)
        restarted = OrderNowStorage(self.path)
        self.assertIn(updated, restarted.get_config(include_disabled=True)["rules"])
        for rule in restarted.get_config(include_disabled=True)["rules"]:
            self.assertEqual(restarted.delete_rule(rule["id"]), rule)
        self.assertIsNone(restarted.delete_rule("missing"))
        self.assertEqual(OrderNowStorage(self.path).get_config()["rules"], [])

    def test_normalization_duplicate_detection_and_target_preserves_query(self):
        payload = {"label": "Test", "pattern": "https://EXAMPLE.com/product/?campaign=x#info", "target_url": "https://shop.ff.com/products/test?variant=1#buy"}
        rule, created = self.storage.save_rule(payload)
        self.assertTrue(created)
        self.assertEqual(rule["pattern"], "https://example.com/product")
        self.assertEqual(rule["target_url"], payload["target_url"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.storage.save_rule({**payload, "pattern": "https://example.com/product"})
        prefix, _ = self.storage.save_rule({**payload, "pattern": "https://example.com/product/*"})
        self.assertEqual(prefix["pattern"], "https://example.com/product/*")

    def test_reject_invalid_sources_and_targets(self):
        payload = {"label": "Test", "pattern": "https://example.com/page", "target_url": "https://shop.ff.com/"}
        for field in ("pattern", "target_url"):
            for value in ("", "/relative", "javascript:alert(1)", "ftp://example.com/", "https://user:pass@example.com/", "https://example.com:99999/", "https://bad host/", "https://example.com/a\\b"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.storage.save_rule({**payload, field: value})
        with self.assertRaisesRegex(ValueError, "name"):
            self.storage.save_rule({**payload, "label": " "})
        with self.assertRaisesRegex(ValueError, "wildcard"):
            self.storage.save_rule({**payload, "pattern": "https://*.example.com/"})
        for button_label in (" ", "X" * 41):
            with self.assertRaisesRegex(ValueError, "Button text"):
                self.storage.save_rule({**payload, "button_label": button_label})

    def test_legacy_config_defaults_button_text_and_preserves_special_links(self):
        legacy = {"id": "legacy", "label": "Legacy", "pattern": "https://example.com/page", "target_url": DEFAULT_ORDER_NOW_URL, "enabled": True}
        self.path.write_text(json.dumps({"rules": {"legacy": legacy}}), encoding="utf-8")
        self.assertEqual(self.storage.get_config()["rules"][0]["button_label"], "Order Now")
        rule, created = self.storage.save_rule({**legacy, "button_label": "Contact Sales", "target_url": "https://www.ff.com/#eai-robotics-contact-us"})
        self.assertFalse(created)
        self.assertEqual(OrderNowStorage(self.path).get_config()["rules"], [rule])

    def test_catalog_sync_only_adds_missing_rules_and_preserves_admin_changes(self):
        script = Path(__file__).resolve().parents[3] / "scripts/sync_order_now_rules.py"
        missing_rules = runpy.run_path(str(script))["missing_rules"]
        defaults = list(DEFAULT_ORDER_NOW_RULES.values())
        existing = [
            {**DEFAULT_ORDER_NOW_RULES["futurist"], "pattern": "https://custom.example/futurist", "enabled": False},
            {**DEFAULT_ORDER_NOW_RULES["navi"], "id": "custom-navi", "pattern": "https://www.ff.com/us/navi"},
        ]
        additions = missing_rules(defaults, existing)
        self.assertEqual(len(additions), 11)
        self.assertNotIn("futurist", {rule["id"] for rule in additions})
        self.assertNotIn("navi", {rule["id"] for rule in additions})
        self.assertEqual(missing_rules(defaults, existing + additions), [])

    @mock_aws
    def test_dynamodb_persists_edits_and_deletions_in_an_independent_record(self):
        import boto3

        resource = boto3.resource("dynamodb", region_name="us-west-2")
        table = resource.create_table(
            TableName="homepage-test",
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": name, "AttributeType": "S"} for name in ("pk", "sk")],
            BillingMode="PAY_PER_REQUEST",
        )
        homepage = {"pk": "HOMEPAGE_PAGE", "sk": "fallback", "label": "Keep homepage"}
        table.put_item(Item=homepage)
        options = {"backend": "dynamodb", "dynamodb_table": table.name, "aws_region": "us-west-2"}
        storage = OrderNowStorage(self.path, **options)
        initial = storage.get_config()["rules"]
        self.assertEqual(len(initial), 13)
        navi = next(rule for rule in initial if rule["id"] == "navi")
        updated, created = storage.save_rule({**navi, "label": "Edited Navi", "enabled": False})
        self.assertFalse(created)
        restarted = OrderNowStorage(self.path, **options)
        self.assertIn(updated, restarted.get_config(include_disabled=True)["rules"])
        self.assertEqual(len(restarted.get_config()["rules"]), 12)
        for rule in restarted.get_config(include_disabled=True)["rules"]:
            self.assertEqual(restarted.delete_rule(rule["id"]), rule)
        self.assertIsNone(restarted.delete_rule("missing"))
        self.assertEqual(OrderNowStorage(self.path, **options).get_config()["rules"], [])
        self.assertEqual(table.get_item(Key={"pk": "HOMEPAGE_PAGE", "sk": "fallback"})["Item"], homepage)


if __name__ == "__main__":
    unittest.main()
