# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 — 只读 UI 增量英文巡检器 (Live UI Auditor)
结合 CDP 端口探测：仅读取当前运行界面中可见的非代码区英文文本，并与本地 src/dict 词库做差集比对，
5 秒精确定位 Antigravity 官方新版本多出的未汉化词条，彻底摆脱盲目扫 12MB 混淆源码。
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.patcher.cdp_injector import DEFAULT_CDP_PORT, fetch_cdp_targets

COLLECT_JS = """(() => {
  const out = new Set();
  const skipTags = new Set(['SCRIPT','STYLE','NOSCRIPT','CODE','PRE','SVG','PATH','INPUT','TEXTAREA']);
  const attrs = ['aria-label','placeholder','title','data-tooltip'];
  const skipNode = (el) => {
    let cur = el;
    while (cur && cur.nodeType === 1) {
      if (skipTags.has(cur.tagName) || cur.isContentEditable) return true;
      const c = typeof cur.className === 'string' ? cur.className : '';
      if (c.includes('monaco-editor') || c.includes('xterm') || c.includes('prose') || c.includes('user-input-step')) return true;
      if (cur.id === 'chameleon-toggle-root') return true;
      cur = cur.parentElement;
    }
    return false;
  };
  const walker = document.createTreeWalker(document.body || document.documentElement, 1 | 4);
  let n;
  while ((n = walker.nextNode())) {
    if (n.nodeType === 1) {
      if (skipNode(n)) continue;
      for (const a of attrs) {
        const v = (n.getAttribute(a) || '').trim();
        if (v && /[a-zA-Z]{2,}/.test(v) && !/[\\u4e00-\\u9fff]/.test(v) && v.length <= 160) out.add(v);
      }
    } else if (n.nodeType === 3) {
      if (skipNode(n.parentElement)) continue;
      const v = (n.nodeValue || '').trim();
      if (v && /[a-zA-Z]{2,}/.test(v) && !/[\\u4e00-\\u9fff]/.test(v) && v.length <= 160) out.add(v);
    }
  }
  return Array.from(out);
})()"""


def main():
    parser = argparse.ArgumentParser(description="Chameleon 只读 UI 英文漏翻巡检工具")
    parser.add_argument("--port", type=int, default=DEFAULT_CDP_PORT, help="CDP 调试端口 (默认 58321)")
    args = parser.parse_args()

    targets = fetch_cdp_targets(port=args.port)
    if not targets:
        print(f"[-] 端口 {args.port} 未发现运行中的调试页面。请先通过 `chameleon.py --cdp` 启动 Antigravity。")
        return 1

    import websocket
    collected = set()
    for t in targets:
        ws = websocket.create_connection(t["webSocketDebuggerUrl"], timeout=5, origin="http://127.0.0.1")
        try:
            ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": COLLECT_JS, "returnByValue": True}}))
            resp = json.loads(ws.recv())
            vals = resp.get("result", {}).get("result", {}).get("value", [])
            if isinstance(vals, list):
                collected.update(vals)
        finally:
            ws.close()

    # 比对现有词库
    known = set()
    dict_dir = os.path.join(ROOT, "src", "dict")
    for fn in os.listdir(dict_dir):
        if fn.endswith(".json"):
            d = json.load(open(os.path.join(dict_dir, fn), "r", encoding="utf-8"))
            known.update(k.lower() for k in d.keys())

    missing = sorted(s for s in collected if s.lower() not in known)
    print(f"扫描到可见英文候选共 {len(collected)} 条，不在静态词库中的共有 {len(missing)} 条:")
    for item in missing[:80]:
        print("  -", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
