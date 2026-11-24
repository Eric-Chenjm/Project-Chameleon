# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 — 零侵入 CDP (Chrome DevTools Protocol) 动态热注入器
特点：
  1. 完全不修改、不解包普通版 resources/app.asar（彻底免疫官方覆盖更新、保留原版数字签名）。
  2. 只要官方前端通过浏览器/WebView 渲染，即可跨版本直接注入 95%+ 核心界面汉化并支持右下角实时中英切换。
  3. 严格遵守【零强杀进程铁律】：绝不调用 taskkill 强杀正在运行中的 Antigravity，仅发现或拉起调试端口并注入。
"""

import json
import os
import platform
import subprocess
import sys
import time
import urllib.request
import urllib.error


DEFAULT_CDP_PORT = 58321


def find_antigravity_exe():
    """查找本机 Antigravity 普通版可执行文件路径。"""
    sys_name = platform.system()
    if sys_name == "Windows":
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe"),
        ]
    elif sys_name == "Darwin":
        candidates = ["/Applications/Antigravity.app/Contents/MacOS/Electron"]
    else:
        candidates = [
            "/usr/bin/antigravity",
            "/opt/Antigravity/antigravity",
            os.path.expanduser("~/.local/bin/antigravity"),
        ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def fetch_cdp_targets(port=DEFAULT_CDP_PORT, timeout=2.0):
    """查询本机 127.0.0.1:<port>/json/list 中可注入的目标页面。"""
    url = f"http://127.0.0.1:{port}/json/list"
    req = urllib.request.Request(url, headers={"User-Agent": "Project-Chameleon/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            targets = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return []

    valid = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        t_type = t.get("type", "")
        ws_url = t.get("webSocketDebuggerUrl", "")
        target_url = t.get("url", "")
        if t_type not in ("page", "iframe", "webview"):
            continue
        # 严格校验回环主机，仅允许连接本地 CDP WebSocket
        if not ws_url.startswith(f"ws://127.0.0.1:{port}/") and not ws_url.startswith(f"ws://localhost:{port}/"):
            continue
        # 跳过纯 blank 过渡页或内部 devtools 页
        if target_url.startswith("devtools://") or target_url == "about:blank":
            continue
        valid.append(t)
    return valid


def _ws_evaluate_cdp(ws_url, payload_js, fingerprint="", is_swarm=False):
    """通过 websocket-client向目标页面发送 Page.addScriptToEvaluateOnNewDocument 与 Runtime.evaluate。"""
    try:
        import websocket
    except ImportError as exc:
        raise RuntimeError(
            "缺少 websocket-client 库，请在环境运行: pip install websocket-client"
        ) from exc

    ws = websocket.create_connection(ws_url, timeout=5, origin="http://127.0.0.1")
    try:
        msg_id = 1

        def call(method, params=None):
            nonlocal msg_id
            cur = msg_id
            msg_id += 1
            ws.send(json.dumps({"id": cur, "method": method, "params": params or {}}))
            deadline = time.time() + 4.0
            while time.time() < deadline:
                raw = ws.recv()
                if not raw:
                    continue
                data = json.loads(raw)
                if data.get("id") == cur:
                    return data
            return {}

        # 检查当前页面是否已经注入且指纹相同
        check_expr = (
            f"window.__chameleonInstalled === true && "
            f"window.__chameleonObservedDoc === document && "
            f"window.__chameleonFingerprint === {json.dumps(fingerprint)}"
        )
        res = call("Runtime.evaluate", {"expression": check_expr, "returnByValue": True})
        val = res.get("result", {}).get("result", {}).get("value")
        if val is True:
            return "already_injected"

        full_source = (
            f"window.__chameleonRequestedFingerprint = {json.dumps(fingerprint)};\n"
            + payload_js
        )
        if not is_swarm:
            call("Page.enable")
            call("Page.addScriptToEvaluateOnNewDocument", {"source": full_source})

        eval_res = call("Runtime.evaluate", {"expression": full_source, "awaitPromise": False})
        if "exceptionDetails" in eval_res.get("result", {}):
            desc = eval_res["result"]["exceptionDetails"].get("text", "Runtime exception")
            return f"error: {desc}"
        return "injected"
    finally:
        ws.close()


def launch_with_debug_port(port=DEFAULT_CDP_PORT):
    """过滤 ELECTRON_RUN_AS_NODE 后，以本地回环 CDP 端口启动 Antigravity。"""
    exe = find_antigravity_exe()
    if not os.path.exists(exe):
        raise FileNotFoundError(f"未找到 Antigravity 可执行文件: {exe}")

    env = {k: v for k, v in os.environ.items() if k.upper() != "ELECTRON_RUN_AS_NODE"}
    args = [
        exe,
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
    ]
    flags = 0
    if platform.system() == "Windows":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)

    subprocess.Popen(
        args,
        cwd=os.path.dirname(exe),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=flags,
    )
    return exe


def inject_once(overlay_js, swarm_overlay_js=None, fingerprint="", port=DEFAULT_CDP_PORT):
    """扫描当前调试端口下全部合格目标并执行幂等热注入。"""
    targets = fetch_cdp_targets(port=port)
    results = []
    for t in targets:
        ws_url = t.get("webSocketDebuggerUrl", "")
        url = t.get("url", "")
        is_swarm = url.startswith("plugin://swarm--")
        payload = swarm_overlay_js if (is_swarm and swarm_overlay_js) else overlay_js
        try:
            status = _ws_evaluate_cdp(ws_url, payload, fingerprint=fingerprint, is_swarm=is_swarm)
            results.append({"title": t.get("title", ""), "url": url, "status": status})
        except Exception as e:
            results.append({"title": t.get("title", ""), "url": url, "status": f"failed: {e}"})
    return results


def run_cdp_watch_loop(overlay_js, swarm_overlay_js=None, fingerprint="", port=DEFAULT_CDP_PORT, attach_only=False):
    """零改包 CDP 监听模式：附着现有调试端口（或温和拉起新实例）并持续为新开页面/Swarm 注入汉化。"""
    targets = fetch_cdp_targets(port=port)
    if not targets:
        if attach_only:
            print(f"[-] 端口 {port} 当前未开启 CDP 调试（若从普通快捷方式启动，请改用 `chameleon.py --cdp` 启动或携带 `--remote-debugging-port={port}`）。")
            return 1
        print(f"[+] 正在以零侵入调试模式启动 Antigravity (127.0.0.1:{port})...")
        launch_with_debug_port(port=port)
        # 等待最多 20 秒端口就绪
        deadline = time.time() + 20.0
        while time.time() < deadline:
            targets = fetch_cdp_targets(port=port)
            if targets:
                break
            time.sleep(0.5)

    if not targets:
        print(f"[!] 在 127.0.0.1:{port} 未检测到活跃页面目标（若 Antigravity 原先已在无调试端口状态下运行，请手动完全退出后重试）。")
        return 1

    print(f"[+] 已连接到调试端口 {port}，开始热注入与动态守护（按 Ctrl+C 退出守护，界面仍保持汉化）...")
    seen_statuses = {}
    try:
        while True:
            res = inject_once(overlay_js, swarm_overlay_js=swarm_overlay_js, fingerprint=fingerprint, port=port)
            if not res:
                # 所有调试页已关闭，守护自动结束
                print("[+] 目标窗口已关闭，CDP 汉化守护正常退出。")
                break
            for item in res:
                key = item["url"][:100]
                if seen_statuses.get(key) != item["status"]:
                    seen_statuses[key] = item["status"]
                    if item["status"] == "injected":
                        print(f"[OK] 已实时汉化页面: {item['title'] or key}")
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n[+] 已手动停止 CDP 守护监听。")
    return 0
