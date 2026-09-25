import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chatkit_handler as handler


class AegisHyperRoutingTests(unittest.TestCase):
    @staticmethod
    def plan(*products: str) -> handler.PlanOutput:
        return handler.PlanOutput(
            input_lang="cn",
            query_text="charging",
            loop_plan=[
                handler.LoopPlanItem(
                    agent="product",
                    product_key=product,
                    query_text=f"{product} charging",
                )
                for product in products
            ],
        )

    def test_aegis_hyper_uses_dedicated_store(self):
        with patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["aegis-hyper"],
            vector_store_id="vs_hyper",
        ):
            passes = handler._build_loop_passes_from_plan(
                self.plan("aegis-hyper").loop_plan
            )

        self.assertEqual(
            [(item.product_key, item.vector_store_ids) for item in passes],
            [("aegis-hyper", ["vs_hyper"])],
        )

    def test_aegis_hyper_page_supplies_ambiguous_product_context(self):
        plan = self.plan("aegis")
        handler._apply_page_product_context(
            plan,
            user_text="怎么充电？",
            page_url="https://example.com/aegis-hyper/operation",
        )
        self.assertEqual(plan.loop_plan[0].product_key, "aegis-hyper")

    def test_explicit_aegis_hyper_corrects_generic_aegis_plan(self):
        for name in (
            "FX Aegis Hyper",
            "FF Aegis Hyper",
            "Aegis Hyper",
            "aegis-hyper",
            "aegis_hyper",
        ):
            with self.subTest(name=name):
                plan = self.plan("aegis")
                handler._apply_page_product_context(
                    plan,
                    user_text=f"{name} 怎么充电？",
                    page_url="https://example.com/aegis/charging",
                )
                self.assertEqual(plan.loop_plan[0].product_key, "aegis-hyper")

    def test_unqualified_hyper_word_is_not_a_product_alias(self):
        plan = self.plan("aegis")
        handler._apply_page_product_context(
            plan,
            user_text="How do I open a hyperlink?",
            page_url="https://example.com/aegis/operation",
        )
        self.assertEqual(plan.loop_plan[0].product_key, "aegis")

    def test_missing_store_retains_product_to_report_unavailability(self):
        with patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["aegis-hyper"],
            vector_store_id="",
        ):
            passes = handler._build_loop_passes_from_plan(
                self.plan("aegis-hyper").loop_plan
            )

        self.assertEqual(
            [(item.domain, item.product_key, item.vector_store_ids) for item in passes],
            [("product", "aegis-hyper", [])],
        )


if __name__ == "__main__":
    unittest.main()
