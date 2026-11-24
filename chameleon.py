# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 (变色龙计划) — 统一双模汉化 CLI 入口
特性：
  1. 零侵入 CDP 动态汉化模式 (--cdp): 绝对不修改 resources/app.asar，官方升级免疫崩溃。
  2. 安全增量 ASAR 无损模式 (--patch): 仅增量注入 preload/menu/tray 与 plugin:// 子帧，100% 保留官方 customScheme 协议。
  3. 一键构建 (--build)、状态检测 (--status)、官方还原 (--restore)。
  4. 严格恪守【零强杀进程安全规范】。
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tools.build_overlay import build_bundle_source, verify_js_syntax
from src.patcher.asar_patcher import (
    apply_incremental_patch,
    inspect_asar_status,
    restore_official_asar,
)
from src.patcher.cdp_injector import DEFAULT_CDP_PORT, run_cdp_watch_loop


def ensure_built_overlay():
    dist_path = os.path.join(ROOT, "dist", "chameleon-overlay.js")
    out_js, fingerprint, count, _ = build_bundle_source()
    os.makedirs(os.path.dirname(dist_path), exist_ok=True)
    # 若已存在且指纹一致则复用，否则更新
    need_write = True
    if os.path.exists(dist_path):
        cur = open(dist_path, "r", encoding="utf-8", errors="replace").read()
        if fingerprint in cur:
            need_write = False
    if need_write:
        with open(dist_path, "w", encoding="utf-8") as f:
            f.write(out_js)
        verify_js_syntax(dist_path)
    return out_js, fingerprint, count


def load_native_map():
    native_p = os.path.join(ROOT, "src", "native-menu.json")
    if os.path.exists(native_p):
        return json.load(open(native_p, "r", encoding="utf-8"))
    return {}


def cmd_status():
    st = inspect_asar_status()
    print("=== Project Chameleon v3.0 环境诊断 ===")
    print(f"安装资源目录  : {st['resources_dir']}")
    print(f"app.asar 存在 : {st['exists']} ({st['size']:,} bytes)")
    print(f"检测版本号    : {st['version'] or '未知'}")
    print(f"当前补丁状态  : {st['mode']}")
    print(f"官方协议完整  : {st['custom_scheme_intact']} (False 代表曾被旧版 v2 整文件覆盖过)")
    return 0


def interactive_menu():
    print("============================================================")
    print("       Project Chameleon v3.0 (变色龙汉化控制台)          ")
    print("============================================================")
    print("  [1] 零改包 CDP 动态汉化启动（推荐：不改 app.asar，免疫版本更新）")
    print("  [2] 增量无损 ASAR 补丁模式（免开调试端口，连系统托盘/原生菜单一并汉化）")
    print("  [3] 查看当前 Antigravity 安装版本与协议状态")
    print("  [4] 一键还原官方纯净英文原版 (app.asar)")
    print("  [5] 重新编译词库并执行体检")
    print("  [0] 退出")
    print("============================================================")
    choice = input("请选择操作编号 [1-5/0]: ").strip()
    if choice == "1":
        js, fp, cnt = ensure_built_overlay()
        print(f"[+] 已加载最新词库 ({cnt} 条, {fp})，正在启动 CDP 模式...")
        return run_cdp_watch_loop(js, fingerprint=fp, port=DEFAULT_CDP_PORT)
    if choice == "2":
        js, _, cnt = ensure_built_overlay()
        print(f"[+] 已准备最新引擎 ({cnt} 条)，开始增量注入...")
        ok = apply_incremental_patch(js, load_native_map())
        return 0 if ok else 1
    if choice == "3":
        return cmd_status()
    if choice == "4":
        ok = restore_official_asar()
        return 0 if ok else 1
    if choice == "5":
        js, fp, cnt = ensure_built_overlay()
        print(f"[OK] 构建与语法检验完成: {cnt} 条词条, 指纹 {fp}")
        from tools.dict_cli import cmd_lint
        return cmd_lint(None)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Project Chameleon v3.0 变色龙统一控制台")
    parser.add_argument("--cdp", action="store_true", help="零改包 CDP 动态汉化启动（推荐，不改 app.asar）")
    parser.add_argument("--attach-only", action="store_true", help="仅附加连接已有调试端口注入，不主动启动新窗口")
    parser.add_argument("--port", type=int, default=DEFAULT_CDP_PORT, help=f"CDP 调试端口 (默认 {DEFAULT_CDP_PORT})")
    parser.add_argument("--patch", action="store_true", help="增量无损修改 app.asar（preload/menu/tray，保留官方 customScheme.js）")
    parser.add_argument("--restore", action="store_true", help="从官方备份还原 app.asar")
    parser.add_argument("--status", action="store_true", help="检查当前客户端版本与补丁状态")
    parser.add_argument("--build", action="store_true", help="仅重新编译 dist/chameleon-overlay.js 并做语法检验")
    parser.add_argument("--dry-run", action="store_true", help="搭配 --patch 仅执行只读预检，不修改磁盘文件")
    args = parser.parse_args()

    if args.status:
        return cmd_status()
    if args.build:
        js, fp, cnt = ensure_built_overlay()
        print(f"[OK] 已构建 dist/chameleon-overlay.js ({cnt} 条, 指纹 {fp})")
        return 0
    if args.restore:
        return 0 if restore_official_asar() else 1
    if args.patch:
        js, _, _ = ensure_built_overlay()
        return 0 if apply_incremental_patch(js, load_native_map(), dry_run=args.dry_run) else 1
    if args.cdp or args.attach_only:
        js, fp, cnt = ensure_built_overlay()
        print(f"[+] 已加载 Chameleon v3.0 引擎 ({cnt} 条, {fp})")
        return run_cdp_watch_loop(js, fingerprint=fp, port=args.port, attach_only=args.attach_only)

    return interactive_menu()


if __name__ == "__main__":
    sys.exit(main())
