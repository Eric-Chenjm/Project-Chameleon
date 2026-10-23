# -*- coding: utf-8 -*-
import hashlib
import json
import os
import unittest
import smart_patch

ROOT = os.path.dirname(os.path.abspath(__file__))


class TestChameleonSafety(unittest.TestCase):
    def test_unknown_version_fallback_to_core(self):
        """未知版本必须触发防白屏熔断，回退至 customScheme.core.js。"""
        selected = smart_patch.select_custom_scheme("99.99.99", ROOT)
        self.assertTrue(selected.endswith("customScheme.core.js"), f"Expected core.js, got {selected}")

    def test_supported_2250_enables_ai_ui(self):
        """受支持的 Antigravity 2.25.0 必须成功启用 customScheme.ai-ui.js。"""
        selected = smart_patch.select_custom_scheme("2.25.0", ROOT)
        self.assertTrue(selected.endswith("customScheme.ai-ui.js"), f"Expected ai-ui.js, got {selected}")

    def test_compat_json_integrity(self):
        """校验 ai-ui-compat.json 结构与 2.25.0 签名完整性。"""
        compat_path = os.path.join(ROOT, "patches", "ai-ui-compat.json")
        with open(compat_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        bundles = data.get("supportedBundles", [])
        v2250 = [b for b in bundles if b.get("antigravityVersion") == "2.25.0"]
        self.assertEqual(len(v2250), 1, "2.25.0 must exist in supportedBundles")
        self.assertEqual(
            v2250[0].get("sourceSha256"),
            "91C2D259D53A16B0CB9AFE87E5D9F173BA613A46A076032A179AC5ECA5101463",
        )


if __name__ == "__main__":
    unittest.main()
