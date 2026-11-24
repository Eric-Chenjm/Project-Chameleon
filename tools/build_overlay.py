# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 — 统一 Overlay 构建与语法验证器
将模块化词典 src/dict/*.json + 运行时规则 src/runtime/rules.js + 核心引擎 src/runtime/engine.js
编译生成轻量化独立运行脚本 dist/chameleon-overlay.js。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_DIR = os.path.join(ROOT, "src", "dict")
RULES_PATH = os.path.join(ROOT, "src", "runtime", "rules.js")
ENGINE_PATH = os.path.join(ROOT, "src", "runtime", "engine.js")
DIST_DIR = os.path.join(ROOT, "dist")


def load_merged_dictionary():
    """加载所有 UI 词典分组并校验跨文件唯一性（native-electron 作为主进程和菜单备用也并入）。"""
    merged = {}
    duplicates = []
    if not os.path.isdir(DICT_DIR):
        raise FileNotFoundError(f"词典目录不存在: {DICT_DIR}")

    for fn in sorted(os.listdir(DICT_DIR)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(DICT_DIR, fn)
        data = json.load(open(path, "r", encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{fn} 必须是 JSON 对象")
        for k, v in data.items():
            if not k or not isinstance(v, str) or not v.strip():
                raise ValueError(f"{fn} 包含空键或空值: {k!r}")
            if k in merged and merged[k] != v:
                duplicates.append((k, fn))
            merged[k] = v

    # 按键长降序排序保证输出稳定与哈希一致
    ordered = dict(sorted(merged.items(), key=lambda x: (-len(x[0]), x[0])))
    return ordered, duplicates


def strip_cjs_exports(js_text):
    """移除 rules.js 末尾仅供 Node.js 测试使用的 module.exports 导出块。"""
    return re.sub(
        r"\nif\s*\(\s*typeof module\s*!==\s*'undefined'\s*&&\s*module\.exports\s*\)\s*\{[\s\S]*?\}\s*$",
        "\n",
        js_text,
    ).strip()


def build_bundle_source():
    dictionary, duplicates = load_merged_dictionary()
    rules_src = strip_cjs_exports(open(RULES_PATH, "r", encoding="utf-8").read())
    engine_tpl = open(ENGINE_PATH, "r", encoding="utf-8").read()

    for placeholder in ("/* __CHAMELEON_DICTIONARY__ */ {}", "/* __CHAMELEON_RULES__ */", "/* __CHAMELEON_FINGERPRINT__ */"):
        if placeholder not in engine_tpl:
            raise RuntimeError(f"engine.js 缺少必需占位符: {placeholder}")

    dict_json = json.dumps(dictionary, ensure_ascii=False, separators=(",", ":"))
    # 基于规则与词典内容确定性计算构建指纹
    digest = hashlib.sha256((dict_json + "\n" + rules_src).encode("utf-8")).hexdigest()[:12]
    fingerprint = f"chm-v3-{digest}"

    # 使用 lambda 避免 replace 误解析内容中的转义序列
    out_js = (
        engine_tpl
        .replace("/* __CHAMELEON_FINGERPRINT__ */", fingerprint)
        .replace("/* __CHAMELEON_DICTIONARY__ */ {}", dict_json, 1)
        .replace("/* __CHAMELEON_RULES__ */", rules_src, 1)
    )
    return out_js, fingerprint, len(dictionary), duplicates


def verify_js_syntax(js_path):
    node_cmd = "node"
    res = subprocess.run([node_cmd, "--check", js_path], capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        raise SyntaxError(f"Node 语法校验失败 ({js_path}):\n{res.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Project Chameleon v3.0 Overlay 构建器")
    parser.add_argument("--check", action="store_true", help="仅执行编译检查与语法验证，不覆盖产物")
    args = parser.parse_args()

    out_js, fingerprint, count, duplicates = build_bundle_source()
    if duplicates:
        print(f"[!] 提示: 检测到 {len(duplicates)} 个跨模块同名键（已按字母后加载覆盖）:")
        for k, fn in duplicates[:10]:
            print(f"    - {k!r} ({fn})")

    os.makedirs(DIST_DIR, exist_ok=True)
    target = os.path.join(DIST_DIR, "chameleon-overlay.js")

    if args.check:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tf:
            tf.write(out_js)
            tmp_path = tf.name
        try:
            verify_js_syntax(tmp_path)
            print(f"[PASS] Overlay 构建校验通过! 词条数: {count}, 体积: {len(out_js.encode('utf-8')):,} bytes, 指纹: {fingerprint}")
        finally:
            os.remove(tmp_path)
        return 0

    with open(target, "w", encoding="utf-8") as f:
        f.write(out_js)
    verify_js_syntax(target)
    size = os.path.getsize(target)
    print(f"[OK] 成功构建 dist/chameleon-overlay.js")
    print(f"     词条总数: {count} | 物理体积: {size:,} bytes ({size/1024:.1f} KB) | 指纹: {fingerprint}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
