# -*- coding: utf-8 -*-
"""
Project Chameleon v3.0 — 安全增量 ASAR 无损补丁器
核心改进（对比旧版 v2）：
  1. 彻底废除整文件覆盖 dist/customScheme.js！100% 保留官方 agy-browser-stream、plugin:// 等全部最新协议。
  2. 彻底废除静态改写 12MB 混淆 main.js Bundle，彻底告别官方小更新即白屏/全英文的噩梦。
  3. 仅对以下位置执行幂等标志截断式增量注入（支持重复运行覆盖刷新、不污染原版）：
     - dist/preload.js（与 dist/ideInstall/wizardPreload.js）：注入高性能模块化 DOM 翻译引擎（含右下角中英切换球）。
     - dist/menu.js & dist/tray.js：注入无侵入 Menu.buildFromTemplate 全局包装器，零脆弱汉化原生顶部菜单与托盘菜单。
  4. 严格保留 --unpack "**/node_modules/chrome-devtools-mcp/**" 轻量打包规范与 SHA-256 去重纯净备份支持。
  5. 严格遵守【零强杀进程铁律】：绝不 taskkill，检测到文件占用时温和提示用户手动退出后继续或重试。
"""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys


PRELOAD_MARKER_START = "// === PROJECT_CHAMELEON_V3_PRELOAD_START ==="
PRELOAD_MARKER_END = "// === PROJECT_CHAMELEON_V3_PRELOAD_END ==="

MENU_MARKER_START = "// === PROJECT_CHAMELEON_V3_MENU_START ==="
MENU_MARKER_END = "// === PROJECT_CHAMELEON_V3_MENU_END ==="

TRAY_MARKER_START = "// === PROJECT_CHAMELEON_V3_TRAY_START ==="
TRAY_MARKER_END = "// === PROJECT_CHAMELEON_V3_TRAY_END ==="

SUBFRAME_MARKER_START = "// === PROJECT_CHAMELEON_V3_SUBFRAME_START ==="
SUBFRAME_MARKER_END = "// === PROJECT_CHAMELEON_V3_SUBFRAME_END ==="


def log(msg):
    print(f"[+] {msg}")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def get_default_paths():
    sys_name = platform.system()
    if sys_name == "Windows":
        res_candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\resources"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\resources"),
        ]
        res_dir = next((p for p in res_candidates if os.path.exists(p)), res_candidates[0])
        appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "Antigravity")
        npx_cmd = shutil.which("npx.cmd") or shutil.which("npx") or "npx.cmd"
    elif sys_name == "Darwin":
        res_dir = "/Applications/Antigravity.app/Contents/Resources"
        appdata_dir = os.path.expanduser("~/Library/Application Support/Antigravity")
        npx_cmd = shutil.which("npx") or "npx"
    else:
        res_dir = "/usr/share/antigravity/resources"
        appdata_dir = os.path.expanduser("~/.config/Antigravity")
        npx_cmd = shutil.which("npx") or "npx"
    return res_dir, appdata_dir, npx_cmd


def _run(cmd_list):
    res = subprocess.run(cmd_list, shell=False)
    if res.returncode != 0:
        raise RuntimeError(f"命令执行失败 (rc={res.returncode}): {' '.join(cmd_list)}")


def is_process_running():
    if platform.system() != "Windows":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Antigravity.exe"],
            capture_output=True, text=True, errors="replace"
        )
        return "Antigravity.exe" in (out.stdout or "")
    except OSError:
        return False


def strip_marker_block(text, start_marker, end_marker):
    """剥除旧的标志块，确保任何修改可幂等重复应用及 cleanly 恢复。"""
    while True:
        s_idx = text.find(start_marker)
        if s_idx == -1:
            break
        e_idx = text.find(end_marker, s_idx)
        if e_idx == -1:
            text = text[:s_idx].rstrip()
            break
        text = (text[:s_idx].rstrip() + "\n" + text[e_idx + len(end_marker):].lstrip()).strip() + "\n"
    return text


def inject_marker_block(file_path, start_marker, end_marker, payload):
    if not os.path.exists(file_path):
        return False
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()
    clean_raw = strip_marker_block(raw, start_marker, end_marker).rstrip()
    injected = f"{clean_raw}\n\n{start_marker}\n{payload.strip()}\n{end_marker}\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(injected)
    return True


def build_preload_wrapper(overlay_js):
    """在 Electron preload 上下文中安全加载 Chameleon DOM 引擎。"""
    return (
        "(function() {\n"
        "  try {\n"
        "    if (typeof window === 'undefined' || window.__chameleonPreloadBooted) return;\n"
        "    window.__chameleonPreloadBooted = true;\n"
        f"{overlay_js}\n"
        "  } catch (_chmErr) {}\n"
        "})();"
    )


def build_menu_wrapper(native_map):
    """零脆弱接管 Electron Menu.buildFromTemplate，不破坏官方任何新增菜单逻辑。"""
    map_json = json.dumps(native_map, ensure_ascii=False)
    return f"""(function() {{
  if (globalThis.__chameleonMenuPatched) return;
  globalThis.__chameleonMenuPatched = true;
  try {{
    const electron = require('electron');
    if (!electron || !electron.Menu || typeof electron.Menu.buildFromTemplate !== 'function') return;
    const origBuild = electron.Menu.buildFromTemplate.bind(electron.Menu);
    const dict = {map_json};
    const lowerDict = new Map();
    for (const [k, v] of Object.entries(dict)) lowerDict.set(k.toLowerCase(), v);
    const trLabel = (lbl) => {{
      if (typeof lbl !== 'string' || !lbl) return lbl;
      if (dict[lbl]) return dict[lbl];
      const noAmp = lbl.replace(/&/g, '');
      const hit = dict[noAmp] || lowerDict.get(noAmp.toLowerCase());
      if (hit) return hit;
      // 保留快捷键或动态前缀匹配，如 SSH / Check for Updates
      if (/^Check for Updates/i.test(noAmp)) return '检查更新...';
      return lbl;
    }};
    const trItems = (items) => {{
      if (!Array.isArray(items)) return items;
      return items.map((item) => {{
        if (!item || typeof item !== 'object') return item;
        const copy = Object.assign({{}}, item);
        if (typeof copy.label === 'string') copy.label = trLabel(copy.label);
        if (Array.isArray(copy.submenu)) copy.submenu = trItems(copy.submenu);
        return copy;
      }});
    }};
    electron.Menu.buildFromTemplate = function(template) {{
      return origBuild(trItems(template));
    }};
  }} catch (_e) {{}}
}})();"""


def build_subframe_wrapper():
    """安全监听 web-contents-created，从同目录 dist/chameleon-overlay.js 读取引擎并向 plugin:// 跨域子帧注入。"""
    return """(function() {
  if (globalThis.__chameleonSubframePatched) return;
  globalThis.__chameleonSubframePatched = true;
  try {
    const fs = require('fs');
    const path = require('path');
    const { app, webFrameMain } = require('electron');
    if (!app || !webFrameMain || typeof webFrameMain.fromId !== 'function') return;
    const overlayPath = path.join(__dirname, 'chameleon-overlay.js');
    if (!fs.existsSync(overlayPath)) return;
    const payload = fs.readFileSync(overlayPath, 'utf8');
    if (!payload) return;
    const isPluginSubframe = (rawUrl) => {
      if (typeof rawUrl !== 'string' || !rawUrl.startsWith('plugin://')) return false;
      try {
        const u = new URL(rawUrl);
        return u.protocol === 'plugin:' && /^[a-z0-9._-]+$/i.test(u.hostname);
      } catch (_) { return false; }
    };
    app.on('web-contents-created', (_ev, wc) => {
      const injectById = (_e, _isMain, pid, rid) => {
        try {
          const frame = webFrameMain.fromId(pid, rid);
          if (frame && !frame.isDestroyed?.() && isPluginSubframe(frame.url)) {
            Promise.resolve(frame.executeJavaScript(payload, false)).catch(() => {});
          }
        } catch (_) {}
      };
      wc.on('did-frame-finish-load', injectById);
      wc.on('did-navigate-in-page', (_e, _url, _isMain, pid, rid) => injectById(_e, _isMain, pid, rid));
    });
  } catch (_e) {}
})();"""


def build_tray_wrapper():
    """拦截托盘动态计数标签与上下文菜单更新。"""
    return """(function() {
  if (globalThis.__chameleonTrayPatched) return;
  globalThis.__chameleonTrayPatched = true;
  try {
    const electron = require('electron');
    if (!electron || !electron.Tray || !electron.Tray.prototype) return;
    const origSetCtx = electron.Tray.prototype.setContextMenu;
    if (typeof origSetCtx === 'function') {
      electron.Tray.prototype.setContextMenu = function(menu) {
        try {
          if (menu && Array.isArray(menu.items)) {
            for (const item of menu.items) {
              if (!item || typeof item.label !== 'string') continue;
              if (item.label === 'No agents running') item.label = '暂无智能体运行';
              else {
                const m = item.label.match(/^(\\d+)\\s+agents?\\s+running$/i);
                if (m) item.label = `${m[1]} 个智能体正在运行`;
              }
            }
          }
        } catch (_) {}
        return origSetCtx.call(this, menu);
      };
    }
  } catch (_e) {}
})();"""


def inspect_asar_status(resources_dir=None, npx_cmd=None):
    if resources_dir is None or npx_cmd is None:
        d_res, _, d_npx = get_default_paths()
        resources_dir = resources_dir or d_res
        npx_cmd = npx_cmd or d_npx
    asar_path = os.path.join(resources_dir, "app.asar")
    info = {
        "exists": os.path.exists(asar_path),
        "asar_path": asar_path,
        "resources_dir": resources_dir,
        "version": None,
        "mode": "unknown",
        "custom_scheme_intact": None,
        "size": os.path.getsize(asar_path) if os.path.exists(asar_path) else 0,
    }
    if not info["exists"]:
        return info

    import tempfile
    with tempfile.TemporaryDirectory(prefix="chameleon_inspect_") as td:
        for rel in ("package.json", "dist/preload.js", "dist/customScheme.js"):
            subprocess.run([npx_cmd, "asar", "extract-file", asar_path, rel], cwd=td, capture_output=True)
        pkg_f = os.path.join(td, "package.json")
        if os.path.exists(pkg_f):
            with open(pkg_f, "r", encoding="utf-8") as f:
                info["version"] = json.load(f).get("version")
        pre_f = os.path.join(td, "preload.js")
        if os.path.exists(pre_f):
            with open(pre_f, "r", encoding="utf-8", errors="replace") as f:
                pre_txt = f.read()
        else:
            pre_txt = ""
        cs_f = os.path.join(td, "customScheme.js")
        if os.path.exists(cs_f):
            with open(cs_f, "r", encoding="utf-8", errors="replace") as f:
                cs_txt = f.read()
        else:
            cs_txt = ""

        if PRELOAD_MARKER_START in pre_txt:
            info["mode"] = "v3_incremental"
        elif "agy-ui" in cs_txt:
            info["mode"] = "legacy_v2_customScheme"
        else:
            info["mode"] = "official_clean"
        info["custom_scheme_intact"] = ("agy-ui" not in cs_txt)
    return info


def apply_incremental_patch(overlay_js, native_map, resources_dir=None, dry_run=False, skip_process_check=False):
    default_res, _, npx_cmd = get_default_paths()
    resources_dir = resources_dir or default_res
    asar_path = os.path.join(resources_dir, "app.asar")
    if not os.path.exists(asar_path):
        raise FileNotFoundError(f"找不到 app.asar: {asar_path}")

    status = inspect_asar_status(resources_dir, npx_cmd)
    ver = status.get("version") or "unknown"
    ver_tag = "".join(c for c in ver if c.isalnum())
    clean_bak = os.path.join(resources_dir, f"app.asar.clean_official_{ver_tag}" if ver_tag else "app.asar.bak")

    log(f"检测到安装版本: {ver} | 当前模式: {status['mode']} | 原生协议完整: {status['custom_scheme_intact']}")

    # 如果当前是旧版 v2 覆盖过的 asar 且本地已有官方纯净备份，必须基于官方纯净备份恢复后再执行 v3 增量注入！
    source_asar = asar_path
    if status["mode"] == "legacy_v2_customScheme":
        if os.path.exists(clean_bak):
            log(f"⚠️ 检测到旧版 v2 替换过 customScheme.js，自动切换以纯净官方备份 ({os.path.basename(clean_bak)}) 作为重打包基准，彻底修复官方协议！")
            source_asar = clean_bak
        else:
            log("⚠️ 警告：当前 app.asar 为旧版 v2 补丁态且缺少纯净备份，建议先用官方安装包覆盖修复后再运行本工具。")
    elif status["mode"] == "official_clean":
        if not os.path.exists(clean_bak):
            shutil.copy2(asar_path, clean_bak)
            shutil.copy2(clean_bak, os.path.join(resources_dir, "app.asar.bak"))
            log(f"已建立官方纯净基准备份: {os.path.basename(clean_bak)}")

    if dry_run:
        log("[Dry-Run] 仅分析检查，不改写任何安装文件。")
        return True

    if not skip_process_check and is_process_running():
        log("⚠️ 检测到 Antigravity.exe 正在运行（含系统托盘或后台服务）。")
        log("根据【零强杀进程安全规范】，本工具绝不强杀软件进程。")
        if not sys.stdin.isatty():
            log("请先在右下角系统托盘右键退出 Antigravity（确认全部退出）后重试本命令。")
            return False
        while is_process_running():
            input("请完全退出 Antigravity（含托盘图标）后，按 [Enter] 继续...")

    extract_dir = os.path.join(resources_dir, "extracted_chameleon_v3")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir, ignore_errors=True)

    try:
        log(f"1/4 正在从基准解包 app.asar ({os.path.basename(source_asar)}) ...")
        # 若 source_asar 指向 clean_official_xxx 且磁盘上没有对应的 .unpacked，先关联当前 app.asar.unpacked 供 extract 读取
        temp_unpacked_link = None
        if source_asar != asar_path and os.path.exists(asar_path + ".unpacked") and not os.path.exists(source_asar + ".unpacked"):
            shutil.copytree(asar_path + ".unpacked", source_asar + ".unpacked")
            temp_unpacked_link = source_asar + ".unpacked"

        try:
            _run([npx_cmd, "asar", "extract", source_asar, extract_dir])
        finally:
            if temp_unpacked_link and os.path.exists(temp_unpacked_link):
                shutil.rmtree(temp_unpacked_link, ignore_errors=True)

        log("2/4 正在增量注入 Web UI 引擎 (dist/preload.js & wizardPreload.js)，绝不改动 customScheme.js ...")
        preload_payload = build_preload_wrapper(overlay_js)
        inject_marker_block(os.path.join(extract_dir, "dist", "preload.js"), PRELOAD_MARKER_START, PRELOAD_MARKER_END, preload_payload)
        wizard_preload = os.path.join(extract_dir, "dist", "ideInstall", "wizardPreload.js")
        if os.path.exists(wizard_preload):
            inject_marker_block(wizard_preload, PRELOAD_MARKER_START, PRELOAD_MARKER_END, preload_payload)

        log("3/4 正在增量注入原生菜单、托盘与跨域子帧拦截 (dist/menu.js, tray.js & main.js) ...")
        with open(os.path.join(extract_dir, "dist", "chameleon-overlay.js"), "w", encoding="utf-8") as ov_f:
            ov_f.write(overlay_js)
        inject_marker_block(os.path.join(extract_dir, "dist", "menu.js"), MENU_MARKER_START, MENU_MARKER_END, build_menu_wrapper(native_map))
        inject_marker_block(os.path.join(extract_dir, "dist", "tray.js"), TRAY_MARKER_START, TRAY_MARKER_END, build_tray_wrapper())
        inject_marker_block(os.path.join(extract_dir, "dist", "main.js"), SUBFRAME_MARKER_START, SUBFRAME_MARKER_END, build_subframe_wrapper())

        log("4/4 正在轻量级封包 app.asar (自动隔离 chrome-devtools-mcp) ...")
        tmp_asar = asar_path + ".v3tmp"
        if os.path.exists(tmp_asar):
            os.remove(tmp_asar)
        if os.path.exists(tmp_asar + ".unpacked"):
            shutil.rmtree(tmp_asar + ".unpacked", ignore_errors=True)

        _run([npx_cmd, "asar", "pack", extract_dir, tmp_asar, "--unpack", "**/node_modules/chrome-devtools-mcp/**"])

        # 原子替换主包及 unpacked 目录
        os.replace(tmp_asar, asar_path)
        if os.path.exists(tmp_asar + ".unpacked"):
            unpacked_dst = asar_path + ".unpacked"
            if os.path.exists(unpacked_dst):
                shutil.rmtree(unpacked_dst, ignore_errors=True)
            os.replace(tmp_asar + ".unpacked", unpacked_dst)

        log(f"=========== Chameleon v3.0 增量汉化注入成功！(体积: {os.path.getsize(asar_path):,} 字节) ===========")
        return True
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def restore_official_asar(resources_dir=None, skip_process_check=False):
    default_res, _, npx_cmd = get_default_paths()
    resources_dir = resources_dir or default_res
    asar_path = os.path.join(resources_dir, "app.asar")
    status = inspect_asar_status(resources_dir, npx_cmd)
    ver = status.get("version") or ""
    ver_tag = "".join(c for c in ver if c.isalnum())
    candidates = []
    if ver_tag:
        candidates.append(os.path.join(resources_dir, f"app.asar.clean_official_{ver_tag}"))
    candidates.append(os.path.join(resources_dir, "app.asar.bak"))

    backup = next((c for c in candidates if os.path.exists(c)), None)
    if not backup:
        print("[-] 未找到可还原的官方纯净备份文件。")
        return False

    if not skip_process_check and is_process_running():
        log("⚠️ 请先手动完全退出 Antigravity 后再执行还原操作。")
        return False

    shutil.copy2(backup, asar_path)
    log(f"已从 {os.path.basename(backup)} 成功还原官方原版 app.asar！")
    return True
