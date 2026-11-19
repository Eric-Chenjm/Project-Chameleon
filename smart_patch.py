import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile


def log(msg):
    print(f"[+] {msg}")


def resolve_npx_cmd(system_name):
    """查找并返回当前平台的 npx 可执行命令路径。"""
    if system_name == "Windows":
        return shutil.which("npx.cmd") or shutil.which("npx") or "npx.cmd"
    return shutil.which("npx") or "npx"


def run_cmd(cmd):
    """执行外部命令（优先使用列表参数与 shell=False）。"""
    use_shell = isinstance(cmd, str)
    result = subprocess.run(cmd, shell=use_shell)
    if result.returncode != 0:
        print(f"[-] 命令执行失败 (rc={result.returncode}): {cmd}")
        sys.exit(1)


def select_custom_scheme(app_version, current_dir):
    """仅对白名单中显式支持的版本启用汉化 UI 拦截，其余版本回退核心协议。"""
    compat_path = os.path.join(current_dir, "patches", "ai-ui-compat.json")
    try:
        with open(compat_path, "r", encoding="utf-8") as compat_file:
            data = json.load(compat_file)
        if not isinstance(data, dict):
            return os.path.join(current_dir, "patches", "customScheme.core.js")
        supported = data.get("supportedBundles", [])
        if not isinstance(supported, list):
            return os.path.join(current_dir, "patches", "customScheme.core.js")
        if isinstance(app_version, str) and app_version and any(
            isinstance(bundle, dict) and bundle.get("antigravityVersion") == app_version
            for bundle in supported
        ):
            return os.path.join(current_dir, "patches", "customScheme.ai-ui.js")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
        pass
    return os.path.join(current_dir, "patches", "customScheme.core.js")


def build_version_tag(app_version):
    """将版本号规范化为文件后缀标签（例如 2.32.2 -> 2322）。"""
    if not isinstance(app_version, str):
        return ""
    return re.sub(r"[^0-9A-Za-z]+", "", app_version)


def is_already_patched_scheme(extract_dir):
    """判断解包目录中的 dist/customScheme.js 是否已包含变色龙汉化注入。"""
    cs_path = os.path.join(extract_dir, "dist", "customScheme.js")
    if not os.path.exists(cs_path):
        return False
    try:
        with open(cs_path, "r", encoding="utf-8", errors="replace") as scheme_file:
            content = scheme_file.read()
        return ("agy-ui" in content) or ("Serving translated AI UI bundle" in content)
    except OSError:
        return False


def check_antigravity_process(system_name):
    """温和检测 Antigravity 进程是否仍在运行，绝不执行强杀操作。"""
    if system_name != "Windows":
        return
    try:
        chk_process = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Antigravity.exe"],
            capture_output=True,
            text=True,
            errors="replace",
        )
    except OSError:
        return
    if "Antigravity.exe" in (chk_process.stdout or ""):
        log("⚠️ 检测到 Antigravity 正在运行中！")
        log("为防止文件占用被锁定导致闪退，请先完全退出 Antigravity 软件。")
        if sys.stdin.isatty():
            input("退出软件后，按回车键 [Enter] 继续注入流程...")


def patch_install(
    resources_dir=None,
    appdata_dir=None,
    base_dir=None,
    dry_run=False,
    skip_process_check=False,
):
    """执行 Antigravity app.asar 解包、版本感知备份、注入与重新封包。"""
    system_name = platform.system()
    if resources_dir is None:
        if system_name == "Windows":
            install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity")
            resources_dir = os.path.join(install_dir, "resources")
        elif system_name == "Darwin":
            resources_dir = "/Applications/Antigravity.app/Contents/Resources"
        else:
            print(f"[-] 不支持的操作系统: {system_name}")
            sys.exit(1)

    if appdata_dir is None:
        if system_name == "Windows":
            appdata_root = os.environ.get("APPDATA", "")
            if not appdata_root:
                print("[-] 未找到 APPDATA 环境变量。")
                sys.exit(1)
            appdata_dir = os.path.join(appdata_root, "Antigravity")
        elif system_name == "Darwin":
            appdata_dir = os.path.expanduser("~/Library/Application Support/Antigravity")
        else:
            print(f"[-] 不支持的操作系统: {system_name}")
            sys.exit(1)

    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    npx_cmd = resolve_npx_cmd(system_name)
    asar_path = os.path.join(resources_dir, "app.asar")
    asar_bak = os.path.join(resources_dir, "app.asar.bak")
    extract_dir = os.path.join(resources_dir, "extracted_asar")
    trans_dir = os.path.join(base_dir, "translations")

    if not os.path.exists(asar_path):
        print(f"[-] 找不到 app.asar: {asar_path}")
        sys.exit(1)

    if dry_run:
        log("[Dry-Run] 仅执行只读检查与注入计划分析，不修改任何文件...")
        with tempfile.TemporaryDirectory(prefix="chameleon_dryrun_") as dry_extract:
            run_cmd([npx_cmd, "asar", "extract", asar_path, dry_extract])
            app_version = ""
            try:
                with open(os.path.join(dry_extract, "package.json"), "r", encoding="utf-8") as package_file:
                    pkg_data = json.load(package_file)
                if isinstance(pkg_data, dict):
                    raw_ver = pkg_data.get("version", "")
                    app_version = raw_ver if isinstance(raw_ver, str) else ""
            except (OSError, json.JSONDecodeError):
                pass
            ver_tag = build_version_tag(app_version)
            patched = is_already_patched_scheme(dry_extract)
            cs_src = select_custom_scheme(app_version, base_dir)
            ui_src = os.path.join(trans_dir, "zh_cn_ui_main.js")
            log(f"[Dry-Run] 检测到版本: {app_version or '未知版本'} (tag={ver_tag or 'none'}), 已注入={patched}")
            log(f"[Dry-Run] 目标协议文件: {cs_src}")
            log(f"[Dry-Run] 汉化 UI 包存在: {os.path.exists(ui_src)} ({ui_src})")
        return

    if not skip_process_check:
        check_antigravity_process(system_name)

    log("1. 拆解 app.asar (约需数秒) ...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    run_cmd([npx_cmd, "asar", "extract", asar_path, extract_dir])

    log("2. 识别版本并检查官方纯净基准备份 ...")
    app_version = ""
    try:
        with open(os.path.join(extract_dir, "package.json"), "r", encoding="utf-8") as package_file:
            pkg_data = json.load(package_file)
        if isinstance(pkg_data, dict):
            raw_ver = pkg_data.get("version", "")
            app_version = raw_ver if isinstance(raw_ver, str) else ""
    except (OSError, json.JSONDecodeError):
        log("无法识别 Antigravity 版本，已禁用 AI UI 替换以保证正常启动。")

    ver_tag = build_version_tag(app_version)
    if ver_tag:
        clean_bak = os.path.join(resources_dir, f"app.asar.clean_official_{ver_tag}")
        if os.path.exists(clean_bak):
            # 始终优先以当前版本官方干净原版作为基准源，彻底防止污染累积
            shutil.copy2(clean_bak, asar_bak)
            log(f"已同步官方纯净基准备份 (app.asar.clean_official_{ver_tag} -> app.asar.bak)。")
        elif not is_already_patched_scheme(extract_dir):
            # 仅在确认当前 app.asar 未含注入时建立该版本的官方纯净备份
            shutil.copy2(asar_path, clean_bak)
            shutil.copy2(clean_bak, asar_bak)
            log(f"已自动建立官方纯净基准备份 (app.asar.clean_official_{ver_tag})！")
        else:
            log(f"⚠️ 当前 app.asar 已含注入且缺少 app.asar.clean_official_{ver_tag}，跳过建立纯净备份。")
            if not os.path.exists(asar_bak):
                shutil.copy2(asar_path, asar_bak)
                log("已补充创建回退备份 app.asar.bak。")
    else:
        if not os.path.exists(asar_bak):
            shutil.copy2(asar_path, asar_bak)
            log("首次安装，备份成功。")
        elif os.path.getmtime(asar_path) > os.path.getmtime(asar_bak):
            shutil.copy2(asar_path, asar_bak)
            log("检测到官方 Antigravity 已升级，已自动更新原版 app.asar.bak 备份！")
        else:
            log("已有最新原版备份，直接使用原备份。")

    log("3. 注入 customScheme 协议处理器 ...")
    cs_src = select_custom_scheme(app_version, base_dir)
    cs_dst = os.path.join(extract_dir, "dist", "customScheme.js")
    if os.path.exists(cs_src):
        os.makedirs(os.path.dirname(cs_dst), exist_ok=True)
        shutil.copy2(cs_src, cs_dst)
        if cs_src.endswith("customScheme.ai-ui.js"):
            log(f"Antigravity {app_version} 已启用兼容的 AI 界面汉化协议劫持。")
        else:
            log(f"Antigravity {app_version or '未知版本'} 未在 AI UI 兼容列表中；保留官方 UI 以避免白屏。")
    else:
        shutil.rmtree(extract_dir, ignore_errors=True)
        print(f"[-] 找不到目标协议文件: {cs_src}")
        sys.exit(1)

    log("4. 部署预编译汉化 UI 包到系统缓存 ...")
    ui_src = os.path.join(trans_dir, "zh_cn_ui_main.js")
    if os.path.exists(ui_src):
        os.makedirs(appdata_dir, exist_ok=True)
        ui_dst = os.path.join(appdata_dir, "zh_cn_ui_main.js")
        shutil.copy2(ui_src, ui_dst)
        log(f"预编译汉化 UI 包成功部署至: {ui_dst}")
    else:
        shutil.rmtree(extract_dir, ignore_errors=True)
        print("[-] 严重错误：找不到 zh_cn_ui_main.js，汉化将失效！")
        sys.exit(1)

    log("5. 重新精确封包 app.asar (自动分离 chrome-devtools-mcp) ...")
    tmp_asar = asar_path + ".tmp"
    tmp_unpacked = tmp_asar + ".unpacked"
    unpacked_dir = asar_path + ".unpacked"
    unpacked_backup = asar_path + ".unpacked.swap_bak"
    asar_swap_bak = asar_path + ".swap_bak"
    if os.path.exists(tmp_asar):
        os.remove(tmp_asar)
    if os.path.exists(tmp_unpacked):
        shutil.rmtree(tmp_unpacked)
    if os.path.exists(unpacked_backup):
        shutil.rmtree(unpacked_backup)
    if os.path.exists(asar_swap_bak):
        os.remove(asar_swap_bak)

    run_cmd([
        npx_cmd,
        "asar",
        "pack",
        extract_dir,
        tmp_asar,
        "--unpack",
        "**/node_modules/chrome-devtools-mcp/**",
    ])

    asar_replaced = False
    unpacked_moved = False
    try:
        # 先移走旧的 app.asar.unpacked 备份，确保无文件占用后再替换 app.asar
        if os.path.exists(tmp_unpacked) and os.path.exists(unpacked_dir):
            os.replace(unpacked_dir, unpacked_backup)
            unpacked_moved = True
        if os.path.exists(asar_path):
            shutil.copy2(asar_path, asar_swap_bak)
        os.replace(tmp_asar, asar_path)
        asar_replaced = True
        if os.path.exists(tmp_unpacked):
            os.replace(tmp_unpacked, unpacked_dir)
    except PermissionError as exc:
        print(f"[-] 覆盖失败，文件可能正被 Antigravity 占用 ({exc})。")
        print("[-] 请先手动完全退出 Antigravity 软件后再重新运行本脚本。")
        # 若中断发生于部分替换阶段，优先回滚 app.asar 与 app.asar.unpacked 至替换前状态
        if asar_replaced and os.path.exists(asar_swap_bak):
            try:
                os.replace(asar_swap_bak, asar_path)
            except OSError:
                pass
        if unpacked_moved and os.path.exists(unpacked_backup) and not os.path.exists(unpacked_dir):
            try:
                os.replace(unpacked_backup, unpacked_dir)
            except OSError:
                pass
        for leftover in (tmp_asar, tmp_unpacked, unpacked_backup, asar_swap_bak, extract_dir):
            if os.path.isdir(leftover):
                shutil.rmtree(leftover, ignore_errors=True)
            elif os.path.exists(leftover):
                try:
                    os.remove(leftover)
                except OSError:
                    pass
        sys.exit(1)

    # 替换全部成功后，安全清理临时交换备份
    if os.path.exists(unpacked_backup):
        shutil.rmtree(unpacked_backup, ignore_errors=True)
    if os.path.exists(asar_swap_bak):
        try:
            os.remove(asar_swap_bak)
        except OSError:
            pass

    log("6. 清理临时解包目录 ...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)

    asar_size = os.path.getsize(asar_path)
    log("=========== 变色龙纯净汉化注入完成！ ===========")
    log(f"封包体积: {asar_size:,} 字节 ({asar_size / (1024 * 1024):.2f} MB，保持官方级轻量，绝无冗余膨胀)")
    log("请完全重启 Antigravity 软件验证汉化效果。")


def main():
    parser = argparse.ArgumentParser(description="Project Chameleon 纯净汉化注入器")
    parser.add_argument("--resources-dir", default=None, help="覆盖 Antigravity resources 目录路径")
    parser.add_argument("--appdata-dir", default=None, help="覆盖 Antigravity 用户数据目录路径")
    parser.add_argument("--base-dir", default=None, help="覆盖补丁与翻译包根目录路径")
    parser.add_argument("--dry-run", action="store_true", help="仅执行只读检查与方案预览，不修改文件")
    parser.add_argument("--skip-process-check", action="store_true", help="跳过 Antigravity 运行进程检测")
    args = parser.parse_args()

    patch_install(
        resources_dir=args.resources_dir,
        appdata_dir=args.appdata_dir,
        base_dir=args.base_dir,
        dry_run=args.dry_run,
        skip_process_check=args.skip_process_check,
    )


if __name__ == "__main__":
    main()
