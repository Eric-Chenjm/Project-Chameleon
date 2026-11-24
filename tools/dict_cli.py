# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 — 模块化词典 CLI 维护与体检工具
命令示例：
  python tools/dict_cli.py stats
  python tools/dict_cli.py lint
  python tools/dict_cli.py find "Thinking effort"
  python tools/dict_cli.py add settings "New Setting" "新设置"
  python tools/dict_cli.py remove common "BadKey"
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_DIR = os.path.join(ROOT, "src", "dict")

# 绝对不允许出现在通用 DOM 词典里的危险裸键
FORBIDDEN_BARE_KEYS = {
    "subagent", "subagents", "browsersubagent", "idle", "running", "done", "error",
    "default light", "default dark", "nord", "everforest",
    "antigravity", "gemini", "claude", "orchestrator", "swarm",
}


def load_all_groups():
    groups = {}
    for fn in sorted(os.listdir(DICT_DIR)):
        if not fn.endswith(".json"):
            continue
        name = fn[:-5]
        path = os.path.join(DICT_DIR, fn)
        groups[name] = json.load(open(path, "r", encoding="utf-8"))
    return groups


def save_group(name, data):
    path = os.path.join(DICT_DIR, f"{name}.json")
    ordered = dict(sorted(data.items(), key=lambda x: (-len(x[0]), x[0].lower())))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)


def cmd_stats(_args):
    groups = load_all_groups()
    total = 0
    seen = set()
    for name, data in groups.items():
        total += len(data)
        seen.update(data.keys())
        print(f"  {name:<18}: {len(data):>5} 条")
    print(f"  ------------------------------")
    print(f"  总计 / 去重唯一数  : {total} / {len(seen)} 条")
    return 0


def cmd_find(args):
    q = args.query.lower()
    groups = load_all_groups()
    hits = 0
    for name, data in groups.items():
        for k, v in data.items():
            if q in k.lower() or q in v.lower():
                print(f"[{name}] {k!r} -> {v!r}")
                hits += 1
    print(f"共匹配 {hits} 条记录。")
    return 0


def cmd_add(args):
    groups = load_all_groups()
    if args.group not in groups:
        print(f"[-] 未知分组 '{args.group}'，可选: {', '.join(groups.keys())}")
        return 1
    key = args.key.strip()
    val = args.value.strip()
    if not key or not val or key == val:
        print("[-] 键和译文不能为空且不能完全相同。")
        return 1
    if key.lower() in FORBIDDEN_BARE_KEYS:
        print(f"[-] 触发安全守卫：禁止收录高危标识 '{key}'。")
        return 1
    groups[args.group][key] = val
    save_group(args.group, groups[args.group])
    print(f"[OK] 已写入 {args.group}.json: {key!r} -> {val!r}")
    return 0


def cmd_remove(args):
    groups = load_all_groups()
    if args.group not in groups:
        print(f"[-] 未知分组 '{args.group}'")
        return 1
    if args.key not in groups[args.group]:
        print(f"[-] 未找到键: {args.key!r}")
        return 1
    del groups[args.group][args.key]
    save_group(args.group, groups[args.group])
    print(f"[OK] 已从 {args.group}.json 移除 {args.key!r}")
    return 0


def cmd_lint(_args):
    groups = load_all_groups()
    errors = []
    warnings = []
    global_seen = {}

    for name, data in groups.items():
        prev_len = None
        for k, v in data.items():
            if not isinstance(k, str) or not isinstance(v, str) or not k.strip() or not v.strip():
                errors.append(f"[{name}] 空键或空译文: {k!r}")
                continue
            if k == v:
                errors.append(f"[{name}] 原文与译文完全一致: {k!r}")
            if prev_len is not None and len(k) > prev_len:
                warnings.append(f"[{name}] 键长度未严格按非递增排序: {k!r}")
            prev_len = len(k)
            if k.lower() in FORBIDDEN_BARE_KEYS:
                errors.append(f"[{name}] 收录了高危禁译标识: {k!r}")
            if "\\" in k and "\\n" not in k:
                errors.append(f"[{name}] 包含可疑字面反斜杠: {k!r}")
            if k in global_seen:
                warnings.append(f"[{name}] 跨分组重复键: {k!r} (已在 {global_seen[k]} 中)")
            global_seen[k] = name

            # 权限语义反转审计
            kl = k.lower()
            if "allow" in kl and "deny" not in kl:
                if ("拒绝" in v or "禁止" in v) and "允许" not in v:
                    errors.append(f"[{name}] 疑似权限反转 (allow->禁止): {k!r} -> {v!r}")
            if ("deny" in kl or "block" in kl) and "allow" not in kl:
                if "允许" in v and "拒绝" not in v and "禁止" not in v and "拦截" not in v and "阻止" not in v:
                    errors.append(f"[{name}] 疑似权限反转 (deny->允许): {k!r} -> {v!r}")

    print(f"=== Chameleon 词典体检报告 ===")
    print(f"检查总词条: {len(global_seen)} 条 | 错误: {len(errors)} | 警告: {len(warnings)}")
    for e in errors[:20]:
        print(f"  [ERROR] {e}")
    for w in warnings[:15]:
        print(f"  [WARN]  {w}")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Project Chameleon 模块化词典 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stats", help="统计各分组词条数").set_defaults(func=cmd_stats)
    sub.add_parser("lint", help="运行词典安全与一致性体检").set_defaults(func=cmd_lint)

    p_find = sub.add_parser("find", help="查找词条")
    p_find.add_argument("query")
    p_find.set_defaults(func=cmd_find)

    p_add = sub.add_parser("add", help="添加或更新词条")
    p_add.add_argument("group")
    p_add.add_argument("key")
    p_add.add_argument("value")
    p_add.set_defaults(func=cmd_add)

    p_rm = sub.add_parser("remove", help="移除词条")
    p_rm.add_argument("group")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
