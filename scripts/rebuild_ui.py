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


def fetch_bundle(dest):
    """从运行中的 Antigravity 的 DevTools 端口抓取原版 main.js。"""
    ssl_ctx = ssl._create_unverified_context()
    port_file = os.path.join(appdata_dir(), "DevToolsActivePort")
    if not os.path.exists(port_file):
        fail("找不到 DevToolsActivePort，请先启动 Antigravity 再重试。")

    with open(port_file, "r", encoding="utf-8") as f:
        devtools_port = f.readline().strip()
    if not devtools_port or not devtools_port.isdigit():
        fail(f"无效的 DevToolsActivePort 内容: {devtools_port!r}")

    url = f"http://127.0.0.1:{devtools_port}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        fail(f"无法访问 DevTools ({url}): {exc}")

    if not isinstance(data, list):
        fail("DevTools 返回的目标列表格式异常。")

    # 优先匹配 type == "page" 且锚定 URL 开头的本地 HTTPS 端口
    main_js_url = None
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
    if not main_js_url:
        fail("未能从 DevTools 目标中识别出 UI 端口。")

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
