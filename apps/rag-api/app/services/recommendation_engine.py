"""
Recommendation engine for dynamic product recommendations.

- Reads recommendation catalog items from recommendations.json
- Builds a compact prompt snippet for the triage agent
- Resolves the post-answer product card from triage output
- Keeps existing lead-capture helpers intact
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.services.recommendation_catalog_service import RecommendationCatalogStorage

logger = logging.getLogger(__name__)

RECOMMENDATIONS_PATH = Path(__file__).parent / "recommendations.json"


@dataclass
class Recommendation:
    id: str
    reco_type: Literal["product_reco", "lead_capture"]
    title: str
    description: str
    target_product: str | None = None
    target_slug: str | None = None


@dataclass
class RecommendationCatalogItem:
    id: str
    enabled: bool
    product_name: str
    trigger_scene: str
    recommendation_content_cn: str
    recommendation_content_en: str


class RecommendationEngine:
    """Evaluate post-answer product recommendations from catalog rules."""

    def __init__(self, storage: RecommendationCatalogStorage | None = None) -> None:
        self._storage = storage or RecommendationCatalogStorage.from_config()
        self._shown: dict[str, list[str]] = defaultdict(list)

    # ── config ────────────────────────────────────────────────────────────

    @staticmethod
    def _load_config() -> dict:
        with open(RECOMMENDATIONS_PATH, encoding="utf-8") as f:
            return json.load(f)

    def _get_config(self) -> dict:
        return self._storage.get_full_config()

    @staticmethod
    def _normalize_catalog_item(item: dict) -> RecommendationCatalogItem | None:
        if not isinstance(item, dict):
            return None

        rule_id = str(item.get("id", "")).strip()
        product_name = str(item.get("product_name", "")).strip()
        trigger_scene = str(item.get("trigger_scene", "")).strip()
        if not rule_id or not product_name or not trigger_scene:
            return None

        return RecommendationCatalogItem(
            id=rule_id,
            enabled=bool(item.get("enabled", True)),
            product_name=product_name,
            trigger_scene=trigger_scene,
            recommendation_content_cn=str(item.get("recommendation_content_cn", "")).strip(),
            recommendation_content_en=str(item.get("recommendation_content_en", "")).strip(),
        )

    # ── public API ────────────────────────────────────────────────────────

    def list_active_catalog_items(self) -> list[RecommendationCatalogItem]:
        config = self._get_config()
        raw_items = config.get("catalog_items", [])
        if not isinstance(raw_items, list):
            logger.warning("catalog_items is not a list in %s", RECOMMENDATIONS_PATH)
            return []

        items: list[RecommendationCatalogItem] = []
        for raw in raw_items:
            item = self._normalize_catalog_item(raw)
            if item and item.enabled:
                items.append(item)
        return items

    def build_triage_rules_prompt(self) -> str:
        """Return a compact prompt block for dynamic recommendation matching."""
        items = self.list_active_catalog_items()
        if not items:
            return (
                "当前没有启用的推荐规则。\n"
                "你必须输出 `recommendation_hit = \"no\"`，"
                "`recommendation_rule_id = \"\"`。"
            )

        lines = [
            "当前启用的推荐规则如下。仅当用户问题与某条规则的触发场景明显匹配时，"
            "才输出对应的 `recommendation_rule_id`。如果不明显匹配，则不要触发推荐。",
        ]
        for item in items:
            lines.append(
                f'- rule_id: "{item.id}" | product_name: "{item.product_name}" | '
                f'trigger_scene: "{item.trigger_scene}"'
            )
        lines.append(
            "你只能从以上 rule_id 中选择一个；如果没有明确匹配，"
            '输出 `recommendation_hit = "no"` 且 `recommendation_rule_id = ""`。'
        )
        return "\n".join(lines)

    def build_purchase_intent_prompt(self) -> str:
        """Build Step 5 body for triage: baseline rules + ops keywords / trigger notes from JSON."""
        cfg = self._get_config()
        lead = cfg.get("lead_capture")
        if not isinstance(lead, dict):
            lead = {}

        kw_root = cfg.get("purchase_intent_keywords")
        if not isinstance(kw_root, dict):
            kw_root = {}
        cn_kw = kw_root.get("cn")
        en_kw = kw_root.get("en")
        if not isinstance(cn_kw, list):
            cn_kw = []
        if not isinstance(en_kw, list):
            en_kw = []

        trigger_cn = str(lead.get("trigger_conditions_cn", "")).strip()
        trigger_en = str(lead.get("trigger_conditions_en", "")).strip()

        lines: list[str] = [
            "### 基础判定原则（必须遵守）",
            '输出 `purchase_intent`，只能是 `"yes"` 或 `"no"`。',
            "",
            '### `purchase_intent = "yes"` 的典型情况',
            "用户有明确或强烈潜在购买/商务接洽意图，包括但不限于：",
            "- 询价、报价、多少钱、价格方案",
            "- 购买、下单、订购、预订、哪里买、渠道/经销/代理咨询",
            "- 试用、Demo、采购、商务联系、销售对接",
            "",
            '### `purchase_intent = "no"` 的典型情况',
            "用户主要在咨询产品信息、功能、参数、使用说明、故障排查、售后等，不包含明确购买诉求。",
        ]

        if cn_kw or en_kw:
            lines.extend([
                "",
                "### 运营配置的关键词参考（结合用户语义综合判断，不要仅做字面匹配）",
            ])
            if cn_kw:
                lines.append("**中文关键词参考：**")
                for k in cn_kw:
                    s = str(k).strip()
                    if s:
                        lines.append(f"- {s}")
            if en_kw:
                lines.append("**English keyword hints:**")
                for k in en_kw:
                    s = str(k).strip()
                    if s:
                        lines.append(f"- {s}")

        if trigger_cn or trigger_en:
            lines.extend(["", "### 运营补充的触发条件说明"])
            if trigger_cn:
                lines.extend(["**中文：**", trigger_cn])
            if trigger_en:
                lines.extend(["**English:**", trigger_en])

        return "\n".join(lines)

    def evaluate_post_answer(
        self,
        input_lang: str,
        thread_id: str,
        recommendation_rule_id: str | None = None,
        purchase_intent: str = "no",
    ) -> Recommendation | None:
        """Return at most one recommendation or lead-capture card per turn.

        Priority: catalog rule match > purchase-intent lead capture.
        Each type is shown at most once per thread.
        """

        rule_id = (recommendation_rule_id or "").strip()
        if rule_id and rule_id not in self._shown[thread_id]:
            item = self._find_catalog_item(rule_id)
            if item:
                self._shown[thread_id].append(rule_id)
                return self._make_catalog_recommendation(item, input_lang)
            logger.warning("Recommendation rule not found: %s", rule_id)

        if purchase_intent == "yes" and "lead_capture" not in self._shown[thread_id]:
            self._shown[thread_id].append("lead_capture")
            return self._make_lead_capture(input_lang)

        return None

    def record_shown(self, thread_id: str, reco_id: str) -> None:
        if reco_id not in self._shown[thread_id]:
            self._shown[thread_id].append(reco_id)

    def clear_thread(self, thread_id: str) -> None:
        self._shown.pop(thread_id, None)

    # ── builders ──────────────────────────────────────────────────────────

    def _pick_lang(self, cfg: dict, key: str, lang: str) -> str:
        return cfg.get(f"{key}_cn" if lang == "cn" else f"{key}_en", "")

    def _pick_catalog_description(self, item: RecommendationCatalogItem, lang: str) -> str:
        if lang == "cn":
            return item.recommendation_content_cn or item.recommendation_content_en
        return item.recommendation_content_en or item.recommendation_content_cn

    def _find_catalog_item(self, rule_id: str) -> RecommendationCatalogItem | None:
        for item in self.list_active_catalog_items():
            if item.id == rule_id:
                return item
        return None

    def _product_label(self, product_name: str) -> str:
        config = self._get_config()
        for item in config.get("products", []):
            if isinstance(item, dict) and item.get("value") == product_name:
                return str(item.get("label") or product_name)
        return product_name

    def _target_slug(self, product_name: str) -> str:
        return f"/{product_name}" if product_name else "/"

    def _make_lead_capture(self, lang: str) -> Recommendation:
        cfg = self._get_config()["lead_capture"]
        return Recommendation(
            id="lead_capture",
            reco_type="lead_capture",
            title=self._pick_lang(cfg, "title", lang),
            description=self._pick_lang(cfg, "description", lang),
        )

    def _make_catalog_recommendation(
        self, item: RecommendationCatalogItem, lang: str
    ) -> Recommendation:
        label = self._product_label(item.product_name)
        title = f"推荐产品：{label}" if lang == "cn" else f"Recommended Product: {label}"
        return Recommendation(
            id=item.id,
            reco_type="product_reco",
            title=title,
            description=self._pick_catalog_description(item, lang),
            target_product=item.product_name,
            target_slug=self._target_slug(item.product_name),
        )

    # ── lead capture helpers ──────────────────────────────────────────────

    @property
    def product_options(self) -> list[dict]:
        return self._get_config().get("products", [])

    def lead_success_text(self, lang: str) -> tuple[str, str]:
        """Return (title, body) for the post-submit success card."""
        cfg = self._get_config()["lead_capture"]
        return (
            self._pick_lang(cfg, "success_title", lang),
            self._pick_lang(cfg, "success_text", lang),
        )
