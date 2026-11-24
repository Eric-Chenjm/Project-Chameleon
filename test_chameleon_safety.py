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
SHA256_2330 = "F066A497C9C61198394CB3218E42FF61D85B03910D81282589C3EF066905F347"
SHA256_2340 = "D52CE739C15044C02A32E1B9DF62BFE39DD8164C70A2AB783540E6ED5E070251"


class TestChameleonSafety(unittest.TestCase):
    def test_unknown_version_fallback_to_core(self):
        """未知版本必须触发防白屏熔断，回退至 customScheme.core.js。"""
        selected = smart_patch.select_custom_scheme("99.99.99", ROOT)
        self.assertTrue(selected.endswith("customScheme.core.js"), f"Expected core.js, got {selected}")

    def test_supported_versions_enable_ai_ui(self):
        """受支持的 Antigravity 2.28.2、2.32.2、2.33.0 与 2.34.0 必须成功启用 customScheme.ai-ui.js。"""
        for ver in ("2.28.2", "2.32.2", "2.33.0", "2.34.0"):
            with self.subTest(version=ver):
                selected = smart_patch.select_custom_scheme(ver, ROOT)
                self.assertTrue(selected.endswith("customScheme.ai-ui.js"), f"Expected ai-ui.js for {ver}, got {selected}")

    def test_compat_json_integrity(self):
        """校验 ai-ui-compat.json 结构、2.28.2、2.32.2、2.33.0 与 2.34.0 签名完整性。"""
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

        v2330 = [b for b in bundles if b.get("antigravityVersion") == "2.33.0"]
        self.assertEqual(len(v2330), 1, "2.33.0 must appear uniquely in supportedBundles")
        self.assertEqual(v2330[0].get("sourceSha256"), SHA256_2330)

        v2340 = [b for b in bundles if b.get("antigravityVersion") == "2.34.0"]
        self.assertEqual(len(v2340), 1, "2.34.0 must appear uniquely in supportedBundles")
        self.assertEqual(v2340[0].get("sourceSha256"), SHA256_2340)

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
            'function Xpb(){var a=(f,g,h)=>({key:f,modifiers:g,onMatch:(k,l)=>{RL(l,h,k)}}),b=(f,g,h,k)=>({key:f,modifiers:g,onMatch:(l,m)=>{l.preventDefault();RL(m,h,k)}});return[a("ArrowRight",cN,Fnb),a("Delete",{},RK),b("Backspace",Fpb,EK,!0),b("Delete",Fpb,EK,!1),a("Tab",cN,SK)]}',
            'function pQa(a){if(a.startsWith("Side question (conversation ")){a=a.slice(28);}}',
            'var agScreen = { screen: "Agents", label: "Agents" };',
            'var modal233 = { modalType: "BROWSER_SUBAGENT_TRAJECTORY", stepIndex: 1 };',
            'switch (st2) { case "audio_transcription_clip": case "setupRequired": case "permission_denied": break; }',
            'var payload233 = { type: "SSH_HOST", kind: "NEW_PROJECT" };',
            'const ENa = {"/files":"Files","/checks":"Checks","/commits":"Commits"};',
            'G("org.eclipse.elk.alg.common","Tree",225);',
            'var rwd=[["stage","Stage"],["desktop","Desktop"],["grid","Grid"]];',
            'var ui1 = { label:"New Conversation", title:"Account", "aria-label":"Message input" };',
            'var ui233 = { label:"Browsing Data", title:"Keybinding Scheme", "aria-label":"Toggle Virtual Machine", sub:{ label:"Enable Browser Agent", iconLabel:{label:"Code"}, treeIcon:{label:"Tree"} } };',
            'const XQb=[{value:"vscode",label:"VS Code Default",recommended:!0,description:a=>`Honors standard VS Code shortcuts without collisions (e.g. ${a?"\\u2318L Focus Input, \\u2318\\u21e7L New Conversation, \\u2318\\u21e7A Picker, \\u2318\\u21e7, Settings":"Ctrl+L Focus Input, Ctrl+Shift+L New Conversation, Ctrl+Shift+A Picker, Ctrl+Shift+, Settings"}).`},{value:"agy",label:"Antigravity (AGY) Style",description:a=>`Uses standalone Antigravity chords (e.g. ${a?"\\u2318I Focus Input, \\u2318\\u21e7O New Conversation, \\u2318K Picker in chat, \\u2318, Settings, \\u2318[/] History). Replaces Go to Symbol (\\u2318\\u21e7O) and Trigger Suggest (\\u2318I), and rebinds VS Code Settings to \\u2318\\u2325,.":\n"Ctrl+I Focus Input, Ctrl+Shift+O New Conversation, Ctrl+K Picker in chat, Ctrl+, Settings, Ctrl+[/] History). Replaces Go to Symbol (Ctrl+Shift+O) and Trigger Suggest (Ctrl+I), and rebinds VS Code Settings to Ctrl+Alt+,."}`}];',
            'var cmt233 = ({placeholder:h="Leave a comment",submitLabel:k="Add Comment"}) => [h, k];',
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
                'function Xpb(){var a=(f,g,h)=>({key:f,modifiers:g,onMatch:(k,l)=>{RL(l,h,k)}}),b=(f,g,h,k)=>({key:f,modifiers:g,onMatch:(l,m)=>{l.preventDefault();RL(m,h,k)}});return[a("ArrowRight",cN,Fnb),a("Delete",{},RK),b("Backspace",Fpb,EK,!0),b("Delete",Fpb,EK,!1),a("Tab",cN,SK)]}',
                'if(a.startsWith("Side question (conversation "))',
                'screen: "Agents"',
                'modalType: "BROWSER_SUBAGENT_TRAJECTORY"',
                'case "audio_transcription_clip": case "setupRequired": case "permission_denied":',
                'type: "SSH_HOST", kind: "NEW_PROJECT"',
                'const ENa = {"/files":"Files","/checks":"Checks","/commits":"Commits"}',
                'G("org.eclipse.elk.alg.common","Tree",225)',
            ]
            for snippet in preserved_snippets:
                self.assertIn(snippet, out, f"Protected code literal mutated: {snippet}")

            # 确认纯 UI 文案与 aria-label 仍被正常汉化
            self.assertIn('label:"新建会话"', out)
            self.assertIn('title:"账户"', out)
            self.assertIn('"aria-label":"消息输入框"', out)
            self.assertIn('label:"浏览数据"', out)
            self.assertIn('title:"快捷键方案"', out)
            self.assertIn('"aria-label":"切换虚拟机"', out)
            self.assertIn('label:"启用浏览器智能体"', out)
            self.assertIn('label:"代码块"', out)
            self.assertIn('label:"树形图"', out)
            self.assertIn('[["stage","舞台视图"],["desktop","桌面视图"],["grid","网格视图"]]', out)
            self.assertNotIn('Honors standard VS Code shortcuts', out)
            self.assertNotIn('Uses standalone Antigravity chords', out)
            self.assertIn('`遵循标准 VS Code 快捷键且无冲突（例如 ${a?"⌘L 聚焦输入框', out)
            self.assertIn('}）。`', out)
            self.assertIn('`使用独立的 Antigravity 组合键（例如 ${a?"⌘I 聚焦输入框', out)
            self.assertIn('placeholder:h="留下批注",submitLabel:k="添加批注"', out)
            self.assertNotIn('submitLabel:k="Add Comment"', out)

            _, total_bad = verify_bundle.scan_bundle(out)
            self.assertEqual(total_bad, 0, "CHM_NO_INJECT output failed verify_bundle.scan_bundle")

            # 可选外部真实 bundle 校验钩子（若显式设置 CHM_TEST_2322_MAIN_JS / CHM_TEST_2330_MAIN_JS 环境变量）
            for env_key in ("CHM_TEST_2322_MAIN_JS", "CHM_TEST_2330_MAIN_JS"):
                ext_path = os.environ.get(env_key, "")
                if ext_path and os.path.isfile(ext_path):
                    ext_out = os.path.join(td, f"{env_key.lower()}_noinj.js")
                    p2 = subprocess.run(
                        [sys.executable, os.path.join(SCRIPTS_DIR, "translate_ui.py"), "--input", ext_path, "--output", ext_out],
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

    def test_detect_key_checker_2330_declarative_factory(self):
        """验证 2.33.0 声明式 onMatch 快捷键工厂场景下 detect_key_checker 返回 None（不误匹配局部短名或回退 LG）。"""
        import translate_ui
        sample_2330 = (
            'function Epb(){var a=(f,g,h)=>({key:f,modifiers:g,onMatch:(k,l)=>{RL(l,h,k)}}),'
            'b=(f,g,h,k)=>({key:f,modifiers:g,onMatch:(l,m)=>{l.preventDefault();RL(m,h,k)}});'
            'return[a("ArrowRight",cN,Fnb),a("Delete",{},RK),b("Backspace",Fpb,EK,!0),a("Tab",cN,SK)]}\n'
            'function LG(x,y,z){return x+y+z;} LG(x,"Delete",1);\n'
        )
        protected, placeholders, stats = translate_ui.protect_code_positions(sample_2330)
        restored = translate_ui.restore_protected(protected, placeholders)
        self.assertEqual(restored, sample_2330)
        self.assertIn("Lexical快捷键工厂", stats)
        self.assertIsNone(translate_ui.detect_key_checker(sample_2330))

        # 若同时存在旧式全局 3 参判定函数 yL(a,"Backspace",1)，仍可正确识别
        sample_legacy = 'function yL(ev,k,fn){return ev.key===k} yL(a,"Backspace",1);'
        self.assertEqual(translate_ui.detect_key_checker(sample_legacy), "yL")

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
assert.strictEqual(translateText('Deleted cookies for example.com'), '已清除 example.com 的 Cookie');
assert.strictEqual(translateText('Delete cookies for example.com'), '清除 example.com 的 Cookie');
assert.strictEqual(translateText('3 cookies'), '3 个 Cookie');
assert.strictEqual(translateText('1 cookie'), '1 个 Cookie');
assert.strictEqual(translateText('Failed to update agent: timeout'), '更新智能体失败：timeout');
assert.strictEqual(translateText('Retrying transcription (attempt 2)…'), '正在重试转录（第 2 次尝试）…');
assert.strictEqual(translateText('SSH Config (~/.ssh/config)'), 'SSH 配置 (~/.ssh/config)');
assert.strictEqual(translateText('Add bundle my-bundle'), '添加插件包 my-bundle');
assert.strictEqual(translateText('Adding plugins from my-bundle'), '正在从 my-bundle 添加插件');
assert.strictEqual(translateText('No server is listening on port 3000 inside the remote workspace. Start it, or ask the agent to, then retry.'), '远程工作区内的端口 3000 上没有正在监听的服务。请启动服务（或让智能体启动）后重试。');
assert.strictEqual(translateText('The agent is paused in Chrome; its view keeps playing here. Resume to let it continue.'), '该智能体已在 Chrome 中暂停；画面仍在此处持续播放，恢复后可继续运行。');
assert.strictEqual(translateText('BrowserAgent is paused in Chrome; its view keeps playing here. Resume to let it continue.'), 'BrowserAgent 已在 Chrome 中暂停；画面仍在此处持续播放，恢复后可继续运行。');
assert.strictEqual(translateText('Honors standard VS Code shortcuts without collisions (e.g. Ctrl+L Focus Input).'), '遵循标准 VS Code 快捷键且无冲突（例如 Ctrl+L 聚焦输入框）。');
assert.strictEqual(translateText('Uses standalone Antigravity chords (e.g. Ctrl+I Focus Input). Replaces Go to Symbol (Ctrl+Shift+O) and Trigger Suggest (Ctrl+I), and rebinds VS Code Settings to Ctrl+Alt+,.'), '使用独立的 Antigravity 组合键（例如 Ctrl+I 聚焦输入框）。将替换转到符号 (Ctrl+Shift+O) 和触发建议 (Ctrl+I)，并将 VS Code 设置重新绑定为 Ctrl+Alt+,。');
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

    def test_rebuild_ui_probe_filters_sidecar_and_wrong_product(self):
        """验证 rebuild_ui._probe_main_js_url_from_ports 必须校验 productName=\"antigravity\" 且 /main.js > 1 MB，排除小型 sidecar。"""
        import ssl
        from unittest.mock import patch
        import rebuild_ui

        class FakeResp:
            def __init__(self, status, body=b"", headers=None):
                self.status = status
                self._body = body
                self.headers = headers or {}

            def read(self, n=-1):
                return self._body if n < 0 else self._body[:n]

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(req, context=None, timeout=1.5):
            url = req.full_url
            method = getattr(req, "method", "GET")
            # Port 56286: has __APP_CONFIG__ & /main.js but wrong productName
            if url == "https://127.0.0.1:56286/":
                return FakeResp(200, b'__APP_CONFIG__={"productName":"sidecar"}<script src="/main.js"></script>')
            # Port 56287: antigravity productName but 183 KB sidecar main.js
            if url == "https://127.0.0.1:56287/":
                return FakeResp(200, b'__APP_CONFIG__={"productName":"antigravity","appVersion":"2.33.0"}<script src="/main.js"></script>')
            if url == "https://127.0.0.1:56287/main.js" and method == "HEAD":
                return FakeResp(200, headers={"Content-Length": "187392"})
            # Port 45428: valid antigravity Hub UI (> 1 MB main.js)
            if url == "https://127.0.0.1:45428/":
                return FakeResp(200, b'__APP_CONFIG__={"productName":"antigravity","appVersion":"2.33.0"}<script src="/main.js"></script>')
            if url == "https://127.0.0.1:45428/main.js" and method == "HEAD":
                return FakeResp(200, headers={"Content-Length": "12353230"})
            raise OSError("unexpected request")

        ctx = ssl._create_unverified_context()
        with patch.object(rebuild_ui.urllib.request, "urlopen", side_effect=fake_urlopen):
            hit = rebuild_ui._probe_main_js_url_from_ports(["56286", "56287", "45428"], ctx)
        self.assertEqual(hit, "https://127.0.0.1:45428/main.js")

    def test_batch_scripts_crlf_encoding_and_no_taskkill(self):
        """校验仓库内全部 *.bat 均采用 Windows CRLF 行尾、编码与 chcp 一致且严禁包含 taskkill。"""
        import codecs
        import glob

        expected_bats = {
            "一键激活汉化_2300.bat",
            "一键激活汉化_2310.bat",
            "一键激活汉化_2312.bat",
            "一键激活汉化_2330.bat",
        }
        bat_paths = sorted(glob.glob(os.path.join(ROOT, "*.bat")))
        found_names = {os.path.basename(p) for p in bat_paths}
        self.assertTrue(expected_bats.issubset(found_names), f"Missing expected bat scripts: {expected_bats - found_names}")

        for path in bat_paths:
            name = os.path.basename(path)
            with self.subTest(bat=name):
                with open(path, "rb") as f:
                    raw = f.read()

                self.assertFalse(raw.startswith(codecs.BOM_UTF8), f"{name} must not contain UTF-8 BOM")
                crlf_count = raw.count(b"\r\n")
                lf_only_count = raw.count(b"\n") - crlf_count
                self.assertGreater(crlf_count, 0, f"{name} must use CRLF line endings")
                self.assertEqual(lf_only_count, 0, f"{name} contains {lf_only_count} LF-only lines")
                self.assertNotIn(b"taskkill", raw.lower(), f"{name} must not contain taskkill")

                has_chcp_65001 = b"chcp 65001" in raw.lower()
                if has_chcp_65001:
                    text = raw.decode("utf-8")
                    self.assertIn("变色龙", text)
                else:
                    text = raw.decode("gbk")
                    self.assertIn("变色龙", text)


if __name__ == "__main__":
    unittest.main()
