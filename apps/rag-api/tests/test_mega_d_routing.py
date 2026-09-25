import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chatkit_handler as handler


class MegaDRoutingTests(unittest.TestCase):
    def plan(self, *products):
        return handler.PlanOutput(
            input_lang="cn", query_text="charging",
            loop_plan=[handler.LoopPlanItem(agent="product", product_key=p) for p in products],
        )

    def test_comparison_uses_separate_product_stores(self):
        with patch.dict(handler._SUPPORT_AGENT_CONFIGS["aegis-mega-d"], vector_store_id="vs_mega"), patch.dict(
            handler._SUPPORT_AGENT_CONFIGS["aegis-max"], vector_store_id="vs_max"
        ):
            passes = handler._build_loop_passes_from_plan(self.plan("aegis-mega-d", "aegis-max").loop_plan)
        self.assertEqual([(p.product_key, p.vector_store_ids) for p in passes], [
            ("aegis-mega-d", ["vs_mega"]), ("aegis-max", ["vs_max"]),
        ])

    def test_ambiguous_question_uses_mega_d_page(self):
        plan = self.plan("aegis")
        handler._apply_page_product_context(plan, user_text="怎么充电？", page_url="https://example.com/aegis-mega-d/charging")
        self.assertEqual(plan.loop_plan[0].product_key, "aegis-mega-d")

    def test_explicit_mega_d_is_not_overridden_by_other_page(self):
        for name in ("Mega D", "mega-d", "AEGIS_MEGA_D", "FX Aegis Mega D"):
            with self.subTest(name=name):
                plan = self.plan("aegis-mega-d")
                handler._apply_page_product_context(plan, user_text=f"{name}怎么充电？", page_url="https://example.com/aegis-max/charging")
                self.assertEqual(plan.loop_plan[0].product_key, "aegis-mega-d")

    def test_explicit_mega_d_corrects_generic_aegis_plan(self):
        plan = self.plan("aegis")
        handler._apply_page_product_context(
            plan,
            user_text="FX Aegis Mega D 怎么充电？",
            page_url="https://example.com/aegis/charging",
        )
        self.assertEqual(plan.loop_plan[0].product_key, "aegis-mega-d")

    def test_compound_model_names_correct_generic_single_product_plans(self):
        cases = (
            ("Aegis Ultra 怎么充电？", "aegis", "aegis-ultra"),
            ("FX Aegis Mega A 怎么充电？", "aegis", "aegis-max"),
            ("Aegis Max 怎么充电？", "aegis", "aegis-max"),
            ("FX Aegis Hyper 怎么充电？", "aegis", "aegis-hyper"),
            ("Futurist Ultra 怎么充电？", "futurist", "futurist-ultra"),
            ("Master Ultra 怎么充电？", "master-mini", "master"),
            ("FF 91 如何充电？", "futurist", "ff91"),
            ("NAVI 怎么连接？", "aegis", "navi"),
        )
        for question, planned, expected in cases:
            with self.subTest(question=question):
                plan = self.plan(planned)
                handler._apply_page_product_context(
                    plan,
                    user_text=question,
                    page_url="https://example.com/",
                )
                self.assertEqual(plan.loop_plan[0].product_key, expected)

    def test_multiple_explicit_models_do_not_force_single_product_correction(self):
        plan = self.plan("aegis")
        handler._apply_page_product_context(
            plan,
            user_text="比较 Aegis Mega A 和 Aegis Ultra",
            page_url="https://example.com/aegis/",
        )
        self.assertEqual(plan.loop_plan[0].product_key, "aegis")

    def test_comparison_is_not_overridden_by_page(self):
        plan = self.plan("aegis-mega-d", "aegis-max")
        handler._apply_page_product_context(plan, user_text="比较两款的载荷", page_url="https://example.com/aegis/charging")
        self.assertEqual([p.product_key for p in plan.loop_plan], ["aegis-mega-d", "aegis-max"])

    def test_missing_store_retains_product_to_report_unavailability(self):
        with patch.dict(handler._SUPPORT_AGENT_CONFIGS["aegis-mega-d"], vector_store_id=""):
            passes = handler._build_loop_passes_from_plan(self.plan("aegis-mega-d").loop_plan)
        self.assertEqual([(p.domain, p.vector_store_ids) for p in passes], [("product", [])])


if __name__ == "__main__":
    unittest.main()
