import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.recommendation_catalog_service import RecommendationCatalogStorage


class RecommendationProductTests(unittest.TestCase):
    def test_legacy_product_list_is_completed_for_all_supported_products(self):
        products = RecommendationCatalogStorage._normalize_products([
            {"value": "master", "label": "Custom Master Label"},
            {"value": "aegis-max", "label": "Custom Max Label"},
        ])

        by_value = {item["value"]: item["label"] for item in products}
        self.assertEqual(
            set(by_value),
            {value for value, _ in RecommendationCatalogStorage._REQUIRED_LEAD_PRODUCTS},
        )
        self.assertEqual(by_value["master"], "Custom Master Label")
        self.assertEqual(by_value["aegis-max"], "Custom Max Label")
        self.assertEqual(by_value["master-mini"], "FF Master Mini")
        self.assertEqual(by_value["aegis-mega-d"], "FX Aegis Mega D")
        self.assertEqual(by_value["aegis-hyper"], "FX Aegis Hyper")
        self.assertEqual(by_value["navi"], "FF NAVI")


if __name__ == "__main__":
    unittest.main()
