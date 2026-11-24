# -*- coding: utf-8 -*-
"""Project Chameleon v3.0 — 增量 ASAR 补丁与安全特性单元测试"""

import ast
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.patcher.asar_patcher import (
    PRELOAD_MARKER_END,
    PRELOAD_MARKER_START,
    build_menu_wrapper,
    build_preload_wrapper,
    build_subframe_wrapper,
    build_tray_wrapper,
    inject_marker_block,
    strip_marker_block,
)


class ChameleonV3PatcherTest(unittest.TestCase):
    def test_marker_injection_is_idempotent_and_reversible(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "preload.js")
            original = '"use strict";\nconsole.log("official preload");\n'
            with open(p, "w", encoding="utf-8") as f:
                f.write(original)

            inject_marker_block(p, PRELOAD_MARKER_START, PRELOAD_MARKER_END, build_preload_wrapper("console.log('v1');"))
            with open(p, "r", encoding="utf-8") as f:
                first = f.read()
            self.assertIn("official preload", first)
            self.assertIn("console.log('v1');", first)

            inject_marker_block(p, PRELOAD_MARKER_START, PRELOAD_MARKER_END, build_preload_wrapper("console.log('v2');"))
            with open(p, "r", encoding="utf-8") as f:
                second = f.read()
            self.assertNotIn("console.log('v1');", second)
            self.assertIn("console.log('v2');", second)
            self.assertEqual(second.count(PRELOAD_MARKER_START), 1)

            restored = strip_marker_block(second, PRELOAD_MARKER_START, PRELOAD_MARKER_END)
            self.assertEqual(restored.strip(), original.strip())

    def test_generated_wrappers_pass_node_syntax_check(self):
        with tempfile.TemporaryDirectory() as td:
            wrappers = {
                "preload.js": build_preload_wrapper("(() => { return 1; })();"),
                "menu.js": build_menu_wrapper({"File": "文件", "Check for Updates": "检查更新"}),
                "tray.js": build_tray_wrapper(),
                "main.js": build_subframe_wrapper(),
            }
            for name, code in wrappers.items():
                path = os.path.join(td, name)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                res = subprocess.run(["node", "--check", path], capture_output=True, text=True)
                self.assertEqual(res.returncode, 0, f"{name} 语法校验失败: {res.stderr}")

    def test_no_taskkill_call_in_v3_modules_and_batches(self):
        """遵守零强杀进程铁律：v3 核心脚本代码逻辑与批处理命令严禁包含 taskkill 调用。"""
        py_paths = [
            os.path.join(ROOT, "chameleon.py"),
            os.path.join(ROOT, "src", "patcher", "asar_patcher.py"),
            os.path.join(ROOT, "src", "patcher", "cdp_injector.py"),
            os.path.join(ROOT, "tools", "build_overlay.py"),
        ]
        for path in py_paths:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=path)
            doc_nodes = set()
            for container in ast.walk(tree):
                if isinstance(container, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if (
                        container.body
                        and isinstance(container.body[0], ast.Expr)
                        and isinstance(container.body[0].value, ast.Constant)
                    ):
                        doc_nodes.add(id(container.body[0].value))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in doc_nodes:
                    self.assertNotIn("taskkill", node.value.lower(), f"{path} 代码字符串常量包含强杀命令")

        for bat_name in ("一键启动_CDP零改包汉化.bat", "一键安装_增量无损补丁.bat", "一键还原_官方原版.bat"):
            bat_path = os.path.join(ROOT, bat_name)
            self.assertTrue(os.path.exists(bat_path), f"缺少批处理文件: {bat_name}")
            with open(bat_path, "r", encoding="utf-8", errors="replace") as f:
                self.assertNotIn("taskkill", f.read().lower(), f"{bat_name} 不得调用强杀命令")


if __name__ == "__main__":
    unittest.main()
