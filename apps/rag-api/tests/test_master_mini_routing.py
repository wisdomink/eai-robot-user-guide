import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chatkit_handler as handler


class MasterMiniRoutingTests(unittest.TestCase):
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

    def test_master_mini_uses_dedicated_store(self):
        with patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["master-mini"],
            vector_store_id="vs_master_mini",
        ):
            passes = handler._build_loop_passes_from_plan(
                self.plan("master-mini").loop_plan
            )

        self.assertEqual(
            [(item.product_key, item.vector_store_ids) for item in passes],
            [("master-mini", ["vs_master_mini"])],
        )

    def test_master_mini_page_supplies_ambiguous_product_context(self):
        plan = self.plan("master")

        handler._apply_page_product_context(
            plan,
            user_text="怎么充电？",
            page_url="https://example.com/master-mini/charging",
        )

        self.assertEqual(plan.loop_plan[0].product_key, "master-mini")

    def test_explicit_master_mini_corrects_generic_master_plan(self):
        for name in ("FF Master Mini", "Master Mini", "master-mini", "master_mini"):
            with self.subTest(name=name):
                plan = self.plan("master")
                handler._apply_page_product_context(
                    plan,
                    user_text=f"{name} 怎么充电？",
                    page_url="https://example.com/master/charging",
                )
                self.assertEqual(plan.loop_plan[0].product_key, "master-mini")

    def test_comparison_uses_separate_master_stores(self):
        with patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["master"],
            vector_store_id="vs_master",
        ), patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["master-mini"],
            vector_store_id="vs_master_mini",
        ):
            passes = handler._build_loop_passes_from_plan(
                self.plan("master", "master-mini").loop_plan
            )

        self.assertEqual(
            [(item.product_key, item.vector_store_ids) for item in passes],
            [
                ("master", ["vs_master"]),
                ("master-mini", ["vs_master_mini"]),
            ],
        )

    def test_missing_store_retains_product_to_report_unavailability(self):
        with patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["master-mini"],
            vector_store_id="",
        ):
            passes = handler._build_loop_passes_from_plan(
                self.plan("master-mini").loop_plan
            )

        self.assertEqual(
            [(item.domain, item.product_key, item.vector_store_ids) for item in passes],
            [("product", "master-mini", [])],
        )


if __name__ == "__main__":
    unittest.main()
