# -*- coding: utf-8 -*-
"""
一键重建并部署 Antigravity AI 界面汉化包 (zh_cn_ui_main.js)

流程:
    1. 抓取原版 UI bundle (或直接使用指定的本地文件)
    2. 安全翻译 (自动保护枚举 / 持久化标识 / 键盘事件等代码位置)
    3. 安全校验 + JS 语法校验
    4. 备份并部署到用户数据目录

用法:
    python rebuild_ui.py                          # 从运行中的 Antigravity 自动抓取 main.js
    python rebuild_ui.py --input main_2240.js     # 使用指定的原版 bundle
    python rebuild_ui.py --no-deploy              # 只生成，不覆盖线上文件
    python rebuild_ui.py --skip-translate         # 只做校验 (需配合 --bundle)

注意: 自动抓取需要 Antigravity 正在运行。
"""
import argparse
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def log(msg):
    print(f"[+] {msg}", flush=True)


def fail(msg):
    print(f"[-] {msg}")
    sys.exit(1)


def appdata_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", "")
        if not base:
            fail("未找到 APPDATA 环境变量。")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        fail(f"不支持的操作系统: {sys.platform}")
    return os.path.join(base, "Antigravity")


def same_target(src, dst):
    """判断两个路径是否指向同一目标文件（兼容 Windows 盘符/目录大小写与相对路径）。"""
    if os.path.exists(dst):
        try:
            return os.path.samefile(src, dst)
        except OSError:
            pass
    return os.path.normcase(os.path.realpath(src)) == os.path.normcase(os.path.realpath(dst))


def _discover_loopback_ports(return_groups=False):
    """扫描本机 127.0.0.1 监听端口（优先 language_server 进程所属端口）。"""
    ls_ports = []
    other_ports = []
    seen = set()

    if sys.platform == "win32":
        ls_pids = set()
        try:
            ps_out = subprocess.check_output(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name like 'language_server%'\" | Select-Object -ExpandProperty ProcessId",
                ],
                text=True,
                errors="replace",
                timeout=5,
            )
            for line in ps_out.splitlines():
                tok = line.strip()
                if tok.isdigit():
                    ls_pids.add(tok)
        except Exception:
            pass

        try:
            net_out = subprocess.check_output(
                ["netstat", "-ano", "-p", "TCP"],
                text=True,
                errors="replace",
                timeout=5,
            )
            for line in net_out.splitlines():
                m = re.search(r"127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING\s+(\d+)", line)
                if not m:
                    continue
                port_s, pid_s = m.group(1), m.group(2)
                if port_s in seen:
                    continue
                seen.add(port_s)
                if pid_s in ls_pids:
                    ls_ports.append(port_s)
                else:
                    other_ports.append(port_s)
        except Exception:
            pass
    else:
        try:
            lsof_out = subprocess.check_output(
                ["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"],
                text=True,
                errors="replace",
                timeout=5,
            )
            for line in lsof_out.splitlines():
                m = re.search(r"127\.0\.0\.1:(\d+)\s+\(LISTEN\)", line)
                if not m:
                    continue
                port_s = m.group(1)
                if port_s in seen:
                    continue
                seen.add(port_s)
                if "language_server" in line.lower():
                    ls_ports.append(port_s)
                else:
                    other_ports.append(port_s)
        except Exception:
            pass

    if return_groups:
        return ls_ports, other_ports
    return ls_ports + other_ports


def _verify_main_js_size(main_js_url, ssl_ctx, min_bytes=1048576):
    """校验 /main.js 响应体积大于 min_bytes（默认 1 MB），排除 183KB 等小型 sidecar 服务。"""
    try:
        head_req = urllib.request.Request(
            main_js_url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(head_req, context=ssl_ctx, timeout=1.5) as resp:
            if resp.status == 200:
                cl = resp.headers.get("Content-Length")
                if cl and cl.strip().isdigit():
                    return int(cl.strip()) > min_bytes
    except Exception:
        pass

    try:
        get_req = urllib.request.Request(
            main_js_url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(get_req, context=ssl_ctx, timeout=3.0) as resp:
            if resp.status != 200:
                return False
            cl = resp.headers.get("Content-Length")
            if cl and cl.strip().isdigit():
                return int(cl.strip()) > min_bytes
            chunk = resp.read(min_bytes + 1)
            return len(chunk) > min_bytes
    except Exception:
        return False


def _probe_main_js_url_from_ports(ports, ssl_ctx, min_main_js_bytes=1048576):
    """通过请求 index.html 校验 __APP_CONFIG__、productName 与 /main.js 体积定位主 Hub UI 端口。"""
    for port in ports:
        index_url = f"https://127.0.0.1:{port}/"
        try:
            req = urllib.request.Request(index_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=1.5) as resp:
                if resp.status != 200:
                    continue
                html = resp.read(262144).decode("utf-8", errors="ignore")
            if "__APP_CONFIG__" not in html or "/main.js" not in html:
                continue
            if not re.search(r'"productName"\s*:\s*"antigravity"', html, re.IGNORECASE):
                continue
            candidate_url = f"https://127.0.0.1:{port}/main.js"
            if not _verify_main_js_size(candidate_url, ssl_ctx, min_bytes=min_main_js_bytes):
                continue
            ver_m = re.search(r'"appVersion"\s*:\s*"([^"]+)"', html)
            detected_ver = ver_m.group(1) if ver_m else "unknown"
            log(f"命中 Antigravity 主 UI 服务: https://127.0.0.1:{port}/ (appVersion={detected_ver})")
            return candidate_url
        except Exception:
            continue
    return None


def fetch_bundle(dest):
    """从运行中的 Antigravity 抓取原版 main.js（优先 DevToolsActivePort，缺失时扫描本地 UI 端口）。"""
    ssl_ctx = ssl._create_unverified_context()
    port_file = os.path.join(appdata_dir(), "DevToolsActivePort")
    main_js_url = None

    if os.path.exists(port_file):
        with open(port_file, "r", encoding="utf-8") as f:
            devtools_port = f.readline().strip()
        if devtools_port and devtools_port.isdigit():
            url = f"http://127.0.0.1:{devtools_port}/json"
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    data = json.loads(resp.read())
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("type") == "page":
                            m = re.match(r"^https://127\.0\.0\.1:(\d+)/", item.get("url", ""))
                            if m:
                                main_js_url = f"https://127.0.0.1:{m.group(1)}/main.js"
                                break
                    if not main_js_url:
                        for item in data:
                            if isinstance(item, dict):
                                m = re.match(r"^https://127\.0\.0\.1:(\d+)/", item.get("url", ""))
                                if m:
                                    main_js_url = f"https://127.0.0.1:{m.group(1)}/main.js"
                                    break
            except Exception as exc:
                log(f"访问 DevTools ({url}) 失败 ({exc})，尝试本地端口兜底探测...")

    if not main_js_url:
        log("未检测到可用的 DevToolsActivePort（2.33.0+ 默认清理），正在优先扫描本机 language_server UI 端口...")
        ls_ports, other_ports = _discover_loopback_ports(return_groups=True)
        if ls_ports:
            main_js_url = _probe_main_js_url_from_ports(ls_ports, ssl_ctx)
        if not main_js_url and other_ports:
            main_js_url = _probe_main_js_url_from_ports(other_ports, ssl_ctx)

    if not main_js_url:
        fail(
            "未能自动探测到运行中的 Antigravity 主 UI 服务。\n"
            "请确认 Antigravity 正在运行，或使用 --input <原版main.js路径> 手动指定源 bundle。"
        )

    log(f"下载原版 bundle: {main_js_url}")
    try:
        with urllib.request.urlopen(main_js_url, context=ssl_ctx, timeout=60) as resp:
            content = resp.read()
    except Exception as exc:
        fail(f"下载原版 bundle 失败 ({main_js_url}): {exc}")

    dest_dir = os.path.dirname(os.path.abspath(dest))
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(content)
    log(f"已保存 {len(content)} 字节 -> {dest}")
    return dest


def verify(bundle_path, allow_no_node=False):
    """安全校验 + JS 语法校验。"""
    verify_script = os.path.join(HERE, "verify_bundle.py")
    if not os.path.exists(verify_script):
        fail(f"找不到安全校验脚本: {verify_script}")

    rc = subprocess.call([sys.executable, verify_script, bundle_path])
    if rc != 0:
        fail("安全校验未通过，已中止部署。")

    node = shutil.which("node") or shutil.which("node.exe")
    if node:
        rc = subprocess.call([node, "--check", bundle_path])
        if rc != 0:
            fail("JS 语法校验未通过，已中止部署。")
        log("JS 语法校验通过")
    elif allow_no_node:
        print("[!] 未找到 node，已按 --allow-no-node 显式跳过语法校验")
    else:
        fail("未找到 node，无法执行 JS 语法校验（可通过 --allow-no-node 显式跳过）。")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="", help="原版 UI bundle 路径 (不填则自动抓取)")
    parser.add_argument("--bundle", default="", help="已翻译好的 bundle (配合 --skip-translate 只做校验)")
    parser.add_argument("--output", default="", help="翻译产物路径")
    parser.add_argument("--skip-translate", action="store_true", help="跳过翻译，只校验/部署")
    parser.add_argument("--no-deploy", action="store_true", help="只生成，不覆盖线上文件")
    parser.add_argument("--allow-no-node", action="store_true", help="当系统缺少 node 时显式跳过语法校验")
    args = parser.parse_args()

    if args.bundle and args.input:
        fail("--bundle 与 --input 不能同时指定。")
    if args.skip_translate and not args.bundle:
        fail("--skip-translate 必须配合 --bundle 指定待校验文件。")

    bundle = args.bundle
    if bundle:
        # 指定了已翻译好的产物，就只做校验 / 部署
        args.skip_translate = True

    build_tmp_dir = None
    if not args.skip_translate and (not args.input or not args.output):
        build_tmp_dir = os.path.join(tempfile.gettempdir(), "project_chameleon_build")
        os.makedirs(build_tmp_dir, exist_ok=True)

    if not args.skip_translate:
        source = args.input
        if not source:
            source = fetch_bundle(os.path.join(build_tmp_dir, f"main_{time.strftime('%Y%m%d_%H%M%S')}.js"))
        if not os.path.exists(source):
            fail(f"找不到源 bundle: {source}")

        bundle = args.output or os.path.join(build_tmp_dir, "zh_cn_ui_main_new.js")
        bundle_dir = os.path.dirname(os.path.abspath(bundle))
        if bundle_dir:
            os.makedirs(bundle_dir, exist_ok=True)

        log("开始翻译 (约需数分钟)…")
        rc = subprocess.call([
            sys.executable, os.path.join(HERE, "translate_ui.py"),
            "--input", source, "--output", bundle,
        ])
        if rc != 0:
            fail("翻译过程失败")

    if not bundle or not os.path.exists(bundle):
        fail(f"找不到汉化产物: {bundle}")

    verify(bundle, allow_no_node=args.allow_no_node)

    if args.no_deploy:
        log(f"已按要求跳过部署，产物位于: {bundle}")
        return

    target = os.path.join(appdata_dir(), "zh_cn_ui_main.js")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if not same_target(bundle, target):
        if os.path.exists(target):
            backup = target + ".bak_" + time.strftime("%Y%m%d_%H%M%S")
            shutil.copy2(target, backup)
            log(f"已备份原汉化包 -> {backup}")
        shutil.copy2(bundle, target)
        log(f"已部署: {target}")
    else:
        log(f"产物已位于目标缓存目录，跳过自复制: {target}")

    # 同步回项目，保证下次 smart_patch.py 注入的也是修复版
    repo_copy = os.path.join(ROOT, "translations", "zh_cn_ui_main.js")
    os.makedirs(os.path.dirname(repo_copy), exist_ok=True)
    if not same_target(bundle, repo_copy):
        shutil.copy2(bundle, repo_copy)
        log(f"已同步到项目: {repo_copy}")
    else:
        log(f"产物已在项目目录中，跳过自复制: {repo_copy}")

    log("完成！请完全重启 Antigravity (或 Ctrl+R 重载) 后验证。")


if __name__ == "__main__":
    main()
