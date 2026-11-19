# -*- coding: utf-8 -*-
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import smart_patch

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import verify_bundle


SHA256_2282 = "C3C5C9BB6D418E8D919CB94AA7DE4DF9BA449056B7D6122C32279CE72E2D2BAD"
SHA256_2322 = "4C0A1FF5659E7DD92E6AD249A386C0DBCE2C8E94B88522A2F366FF20B397081E"


class TestChameleonSafety(unittest.TestCase):
    def test_unknown_version_fallback_to_core(self):
        """未知版本必须触发防白屏熔断，回退至 customScheme.core.js。"""
        selected = smart_patch.select_custom_scheme("99.99.99", ROOT)
        self.assertTrue(selected.endswith("customScheme.core.js"), f"Expected core.js, got {selected}")

    def test_supported_versions_enable_ai_ui(self):
        """受支持的 Antigravity 2.28.2 与 2.32.2 必须成功启用 customScheme.ai-ui.js。"""
        for ver in ("2.28.2", "2.32.2"):
            with self.subTest(version=ver):
                selected = smart_patch.select_custom_scheme(ver, ROOT)
                self.assertTrue(selected.endswith("customScheme.ai-ui.js"), f"Expected ai-ui.js for {ver}, got {selected}")

    def test_compat_json_integrity(self):
        """校验 ai-ui-compat.json 结构、2.28.2 与 2.32.2 签名完整性。"""
        compat_path = os.path.join(ROOT, "patches", "ai-ui-compat.json")
        with open(compat_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        bundles = data.get("supportedBundles", [])
        self.assertGreater(len(bundles), 0, "supportedBundles must not be empty")
        for entry in bundles:
            ver = entry.get("antigravityVersion", "")
            sha = entry.get("sourceSha256", "")
            self.assertTrue(isinstance(ver, str) and len(ver) > 0, f"Invalid antigravityVersion: {entry}")
            self.assertRegex(sha, r"^[0-9A-F]{64}$", f"Invalid sourceSha256 for {ver}: {sha}")

        v2282 = [b for b in bundles if b.get("antigravityVersion") == "2.28.2"]
        self.assertEqual(len(v2282), 1, "2.28.2 must appear uniquely in supportedBundles")
        self.assertEqual(v2282[0].get("sourceSha256"), SHA256_2282)

        v2322 = [b for b in bundles if b.get("antigravityVersion") == "2.32.2"]
        self.assertEqual(len(v2322), 1, "2.32.2 must appear uniquely in supportedBundles")
        self.assertEqual(v2322[0].get("sourceSha256"), SHA256_2322)

    def test_chm_no_inject_preserves_high_risk_literals_and_arrays(self):
        """CHM_NO_INJECT=1 模式下必须 100% 保留高危代码字面量、数组与键位映射，并正常翻译纯 UI 属性。"""
        fixture_parts = [
            'var qu = { setActiveScreen: function(s) {} };',
            'var mu = qu.setActiveScreen; mu("Project General");',
            'a.activeScreen = "Project General";',
            'var keyObj = { Del: "Delete", 46: "Delete" };',
            'var entries = Object.entries({ 1: "Default", 2: "Network" });',
            'var revEnum = { 1: "Default", 2: "Network" };',
            'function zf(msg, fld) { return msg[fld]; } zf(b, "ReusedSubagentId"); zf(b, "Task");',
            'var fbUrl = encodeURIComponent("Provide Feedback");',
            'var m = new Set(["Customizations"]); m.delete("Customizations");',
            'var attrs = { "data-screen": "Developer" };',
            'var themeName = a === "light" ? "Default Light" : "Default Dark";',
            'var g = []; g.push("subagents");',
            'var tabs = ["Code Search", "Conversations", "Commands"];',
            'var convoState = { type: "subagent" };',
            'switch (st) { case "IDLE": case "RUNNING": case "BROWSER_SUBAGENT_TRAJECTORY": break; }',
            'if (S.key === "Delete" || a.key === "Tab") {}',
            'function yL(ev, k, fn) { return ev.key === k; } yL(a, "Backspace", 1); yL(a, "Delete", 2);',
            'const H6b = { light: ["", "Default", "Default Light"], dark: ["", "Default", "Default Dark"] };',
            'var Di = ["Projects", "Agents", "Environments"];',
            'var gEb = "General Appearance Shortcuts Notifications Models Customizations Browser Developer Running".split(" ");',
            'const Bt = ["needsAttention", "running", "done", "killed"];',
            'const YOb = ["PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"];',
            'var ucat = ["Cn", "Lu", "Ll", "No", null, "Po"];',
            'const kmap = new Map([["Delete", { key: "Delete", code: "Delete", vk: 46 }], ["Pause", { key: "Pause", code: "Pause", vk: 19 }]]);',
            'var kpairs = new Map([["Delete", "Delete"], ["Meta", "Meta"], ["Command", "Meta"], ["Pause", "Pause"]]);',
            'var qs = new URLSearchParams([["Email", "a@b.c"], ["continue", "/"]]);',
            'const rPb = ["Account"];',
            'function NMb({ hideBreakdownForGroups: f = ["System Prompt"] }) { return f; }',
            'telemetry("SETTING_CHANGED", { extra: { setting: "Project 4K", value: p === 2 ? "Project 4K" : "Default" } });',
            'var t5a = { draft: "Draft", open: "Open", merged: "Merged", closed: "Closed" };',
            'const PR = { allow: "Allow", ask: "Ask", deny: "Deny" };',
            'const xZc = { google3: "google3", none: "None" };',
            'var ui1 = { label:"New Conversation", title:"Account", "aria-label":"Message input" };',
        ]
        fixture_code = "\n".join(fixture_parts) + "\n"

        with tempfile.TemporaryDirectory() as td:
            in_path = os.path.join(td, "fixture_main.js")
            out_path = os.path.join(td, "fixture_out.js")
            with open(in_path, "w", encoding="utf-8") as f:
                f.write(fixture_code)

            env = os.environ.copy()
            env["APPDATA"] = td
            env["CHM_NO_INJECT"] = "1"
            proc = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "translate_ui.py"), "--input", in_path, "--output", out_path],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(proc.returncode, 0, f"translate_ui.py failed:\n{proc.stdout}\n{proc.stderr}")

            with open(out_path, "r", encoding="utf-8") as f:
                out = f.read()

            self.assertNotIn("\u0000", out, "Unrestored CHMPROTECT placeholder token found")
            self.assertNotIn("const dynamicDict", out)
            self.assertNotIn("translateDynamicRegex", out)

            preserved_snippets = [
                'mu("Project General")',
                'a.activeScreen = "Project General"',
                'Del: "Delete"',
                '46: "Delete"',
                '1: "Default", 2: "Network"',
                'zf(b, "Task")',
                'encodeURIComponent("Provide Feedback")',
                'm.delete("Customizations")',
                '"data-screen": "Developer"',
                'a === "light" ? "Default Light" : "Default Dark"',
                'g.push("subagents")',
                '["Code Search", "Conversations", "Commands"]',
                'type: "subagent"',
                'case "IDLE":',
                'case "RUNNING":',
                'case "BROWSER_SUBAGENT_TRAJECTORY":',
                'S.key === "Delete"',
                'a.key === "Tab"',
                'yL(a, "Delete", 2)',
                'const H6b = { light: ["", "Default", "Default Light"], dark: ["", "Default", "Default Dark"] }',
                'var Di = ["Projects", "Agents", "Environments"]',
                '"General Appearance Shortcuts Notifications Models Customizations Browser Developer Running".split(" ")',
                'const Bt = ["needsAttention", "running", "done", "killed"]',
                'const YOb = ["PreToolUse", "PostToolUse", "PreInvocation", "PostInvocation", "Stop"]',
                '["Cn", "Lu", "Ll", "No", null, "Po"]',
                '["Delete", { key: "Delete", code: "Delete", vk: 46 }]',
                '["Delete", "Delete"]',
                '["Command", "Meta"]',
                'new URLSearchParams([["Email", "a@b.c"], ["continue", "/"]])',
                'const rPb = ["Account"]',
                'hideBreakdownForGroups: f = ["System Prompt"]',
                'setting: "Project 4K"',
                'var t5a = { draft: "Draft", open: "Open", merged: "Merged", closed: "Closed" }',
                'const PR = { allow: "Allow", ask: "Ask", deny: "Deny" }',
                'const xZc = { google3: "google3", none: "None" }',
            ]
            for snippet in preserved_snippets:
                self.assertIn(snippet, out, f"Protected code literal mutated: {snippet}")

            # 确认纯 UI 文案与 aria-label 仍被正常汉化
            self.assertIn('label:"新建会话"', out)
            self.assertIn('title:"账户"', out)
            self.assertIn('"aria-label":"消息输入框"', out)

            _, total_bad = verify_bundle.scan_bundle(out)
            self.assertEqual(total_bad, 0, "CHM_NO_INJECT output failed verify_bundle.scan_bundle")

            # 可选外部真实 bundle 校验钩子（若显式设置 CHM_TEST_2322_MAIN_JS 环境变量）
            ext_2322 = os.environ.get("CHM_TEST_2322_MAIN_JS", "")
            if ext_2322 and os.path.isfile(ext_2322):
                ext_out = os.path.join(td, "ext_2322_noinj.js")
                p2 = subprocess.run(
                    [sys.executable, os.path.join(SCRIPTS_DIR, "translate_ui.py"), "--input", ext_2322, "--output", ext_out],
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(p2.returncode, 0, p2.stderr)
                with open(ext_out, "r", encoding="utf-8") as f:
                    ext_txt = f.read()
                _, ext_bad = verify_bundle.scan_bundle(ext_txt)
                self.assertEqual(ext_bad, 0)

    def test_dom_translator_non_tdz_and_regex_execution(self):
        """验证 dom_translator_js 语法有效，且 translateDynamicRegex/translateText 无 TDZ 错误并正确执行。"""
        node = shutil.which("node") or shutil.which("node.exe")
        if not node:
            self.skipTest("Node.js not found in PATH")

        translate_path = os.path.join(SCRIPTS_DIR, "translate_ui.py")
        with open(translate_path, "r", encoding="utf-8") as f:
            py_src = f.read()

        m = re.search(r'dom_translator_js\s*=\s*r"""(.*?)"""', py_src, re.S)
        self.assertIsNotNone(m, "Could not locate dom_translator_js in scripts/translate_ui.py")
        dom_js = m.group(1)

        with tempfile.TemporaryDirectory() as td:
            js_file = os.path.join(td, "dom_translator.js")
            with open(js_file, "w", encoding="utf-8") as f:
                f.write(dom_js)
            chk = subprocess.run([node, "--check", js_file], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(chk.returncode, 0, f"node --check failed:\n{chk.stderr}")

        start_idx = dom_js.index("const dynamicDict = {")
        end_idx = dom_js.index("const translatedNodes = new WeakSet();")
        engine_js = dom_js[start_idx:end_idx]

        harness = engine_js + "\n" + """
const assert = require('assert');
assert.strictEqual(translateDynamicRegex('Thought for 5s'), '已深度思考 5 秒');
assert.strictEqual(translateDynamicRegex(' Thought for 5s '), ' 已深度思考 5 秒 ');
assert.strictEqual(translateDynamicRegex(null), null);
assert.strictEqual(translateDynamicRegex(''), '');
assert.strictEqual(translateText('Thought for 5s'), '已深度思考 5 秒');
assert.strictEqual(translateText('Thinking for 3s'), '思考中 (3 秒)');
assert.strictEqual(translateText('Thinking (4s)…'), '思考中 (4 秒)…');
assert.strictEqual(translateText('Working · 8s'), '运行中 · 8 秒');
assert.strictEqual(translateText('Agent finished: Build OK'), '智能体已完成：Build OK');
assert.strictEqual(translateText('Terminal process t1 exited with non-zero code 2'), '终端进程 t1 已退出，非零退出代码：2');
assert.strictEqual(translateText('Step 2 of 5'), '第 2 步（共 5 步）');
assert.strictEqual(translateText('Go to turn 1 of 3'), '跳转到第 1 轮（共 3 轮）');
assert.strictEqual(translateText('Hey Alice, what should we build today?'), '你好 Alice，今天我们构建些什么？');
assert.strictEqual(translateText('Enter to Send'), '按 Enter 发送');
assert.strictEqual(translateText('Cancel'), '取消');
assert.strictEqual(translateText('Running command'), '正在运行命令');
assert.strictEqual(translateText('Unmapped_Sentinel_123'), 'Unmapped_Sentinel_123');
console.log('DOM_ENGINE_OK');
"""
        run_node = subprocess.run(
            [node, "-"],
            input=harness,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(run_node.returncode, 0, f"Node execution failed:\n{run_node.stdout}\n{run_node.stderr}")
        self.assertIn("DOM_ENGINE_OK", run_node.stdout)

    def test_verify_bundle_clean_and_cjk_leak_detection(self):
        """验证 verify_bundle 对洁净产物放行，并能拦截双引号与单引号下的四类中文代码泄露。"""
        clean_js = (
            'const a = { label: "新建会话", title: \'账户设置\', text: "系统设置", '
            'description: "查看详情", placeholder: "输入名称...", tooltip: "提示信息", '
            '"aria-label": "关闭", type: "subagent", screen: "Models" };\n'
            'switch (s) { case \'IDLE\': break; }\n'
            'if (a.key === \'Delete\') {}\n'
        )
        res_clean, bad_clean = verify_bundle.scan_bundle(clean_js)
        self.assertEqual(bad_clean, 0, f"Unexpected hits in clean JS: {res_clean}")

        leaks_double = (
            'if (a.key === "删除") {}\n'
            'switch (s) { case "待命": break; }\n'
            'const x = { type: "子智能体", screen: "模型", "模型": 1 };\n'
        )
        res_double, bad_double = verify_bundle.scan_bundle(leaks_double)
        self.assertGreaterEqual(bad_double, 5)
        for label, hits in res_double:
            self.assertGreater(sum(hits.values()), 0, f"Double-quote leak missed category: {label}")

        leaks_single = (
            "if ('删除' !== a.key) {}\n"
            "switch (s) { case '待命': break; }\n"
            "const x = { type: '子智能体', screen: '模型', '模型': 1 };\n"
        )
        res_single, bad_single = verify_bundle.scan_bundle(leaks_single)
        self.assertGreaterEqual(bad_single, 5)
        for label, hits in res_single:
            self.assertGreater(sum(hits.values()), 0, f"Single-quote leak missed category: {label}")

        with tempfile.TemporaryDirectory() as td:
            clean_file = os.path.join(td, "clean.js")
            leak_file = os.path.join(td, "leak.js")
            with open(clean_file, "w", encoding="utf-8") as f:
                f.write(clean_js)
            with open(leak_file, "w", encoding="utf-8") as f:
                f.write(leaks_single)

            cli_clean = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "verify_bundle.py"), clean_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(cli_clean.returncode, 0, cli_clean.stdout)

            cli_leak = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "verify_bundle.py"), leak_file],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(cli_leak.returncode, 2, cli_leak.stdout)


if __name__ == "__main__":
    unittest.main()
