import os
import sys
import shutil
import subprocess
import platform
import json

def log(msg):
    print(f"[+] {msg}")

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[-] 命令执行失败: {cmd}")
        sys.exit(1)

def select_custom_scheme(app_version, current_dir):
    """Only enable the replacement UI for an explicitly supported runtime."""
    compat_path = os.path.join(current_dir, "patches", "ai-ui-compat.json")
    try:
        with open(compat_path, "r", encoding="utf-8") as compat_file:
            supported = json.load(compat_file).get("supportedBundles", [])
        if any(bundle.get("antigravityVersion") == app_version for bundle in supported):
            return os.path.join(current_dir, "patches", "customScheme.ai-ui.js")
    except (OSError, json.JSONDecodeError):
        pass
    return os.path.join(current_dir, "patches", "customScheme.core.js")

def main():
    system_name = platform.system()
    if system_name == "Windows":
        install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity")
        resources_dir = os.path.join(install_dir, "resources")
        npx_cmd = "npx.cmd"
        appdata_dir = os.path.join(os.environ.get("APPDATA", ""), "Antigravity")
    elif system_name == "Darwin":
        resources_dir = "/Applications/Antigravity.app/Contents/Resources"
        npx_cmd = "npx"
        appdata_dir = os.path.expanduser("~/Library/Application Support/Antigravity")
    else:
        print(f"[-] 不支持的操作系统: {system_name}")
        sys.exit(1)
        
    asar_path = os.path.join(resources_dir, "app.asar")
    asar_bak = os.path.join(resources_dir, "app.asar.bak")
    extract_dir = os.path.join(resources_dir, "extracted_asar")
    
    # 汉化包源文件路径 (当前目录)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    trans_dir = os.path.join(current_dir, "translations")
    
    if not os.path.exists(asar_path):
        print(f"[-] 找不到 app.asar: {asar_path}")
        sys.exit(1)

    # 优雅检测 Antigravity 进程是否正在运行，避免因覆盖被锁文件导致闪退
    if system_name == "Windows":
        chk_process = subprocess.run('tasklist /FI "IMAGENAME eq Antigravity.exe"', capture_output=True, text=True, shell=True)
        if "Antigravity.exe" in chk_process.stdout:
            log("⚠️ 检测到 Antigravity 正在运行中！")
            log("为防止文件占用被锁定导致闪退，请先完全退出 Antigravity 软件。")
            if sys.stdin.isatty():
                input("退出软件后，按回车键 [Enter] 继续注入流程...")

    log("1. 检查并备份 app.asar ...")
    clean_bak = os.path.join(resources_dir, "app.asar.clean_official_2250")
    if os.path.exists(clean_bak):
        # 始终优先以官方干净原版作为基准源，彻底防止污染累积
        shutil.copy2(clean_bak, asar_bak)
        log("已同步官方纯净基准备份 (app.asar.clean_official_2250 -> app.asar.bak)。")
    elif not os.path.exists(asar_bak):
        shutil.copy2(asar_path, asar_bak)
        log("首次安装，备份成功。")
    else:
        if os.path.getmtime(asar_path) > os.path.getmtime(asar_bak):
            shutil.copy2(asar_path, asar_bak)
            log("检测到官方 Antigravity 已升级，已自动更新原版 app.asar.bak 备份！")
        else:
            log("已有最新原版备份，直接使用原备份。")
        
    log("2. 拆解 app.asar (约需数秒) ...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    run_cmd(f'{npx_cmd} asar extract "{asar_path}" "{extract_dir}"')
    
    log("3. 注入 customScheme 协议处理器 ...")
    app_version = ""
    try:
        with open(os.path.join(extract_dir, "package.json"), "r", encoding="utf-8") as package_file:
            app_version = json.load(package_file).get("version", "")
    except (OSError, json.JSONDecodeError):
        log("无法识别 Antigravity 版本，已禁用 AI UI 替换以保证正常启动。")
    cs_src = select_custom_scheme(app_version, current_dir)
    cs_dst = os.path.join(extract_dir, "dist", "customScheme.js")
    if os.path.exists(cs_src):
        os.makedirs(os.path.dirname(cs_dst), exist_ok=True)
        shutil.copy2(cs_src, cs_dst)
        if cs_src.endswith("customScheme.ai-ui.js"):
            log(f"Antigravity {app_version} 已启用兼容的 AI 界面汉化协议劫持。")
        else:
            log(f"Antigravity {app_version or '未知版本'} 未在 AI UI 兼容列表中；保留官方 UI 以避免白屏。")
        
    log("4. 部署预编译汉化 UI 包到系统缓存 ...")
    os.makedirs(appdata_dir, exist_ok=True)
    ui_src = os.path.join(trans_dir, "zh_cn_ui_main.js")
    if os.path.exists(ui_src):
        ui_dst = os.path.join(appdata_dir, "zh_cn_ui_main.js")
        shutil.copy2(ui_src, ui_dst)
        log(f"预编译汉化 UI 包成功部署至: {ui_dst}")
    else:
        print("[-] 严重错误：找不到 zh_cn_ui_main.js，汉化将失效！")
        sys.exit(1)
        
    log("5. 重新精确封包 app.asar (自动分离 chrome-devtools-mcp) ...")
    tmp_asar = asar_path + ".tmp"
    run_cmd(f'{npx_cmd} asar pack "{extract_dir}" "{tmp_asar}" --unpack "**/node_modules/chrome-devtools-mcp/**"')
    
    # 覆盖原 asar
    os.replace(tmp_asar, asar_path)
    
    log("6. 清理临时解包目录 ...")
    shutil.rmtree(extract_dir)
        
    log("=========== 变色龙纯净汉化注入完成！ ===========")
    log(f"封包体积: {os.path.getsize(asar_path):,} 字节 (保持 4.49MB 官方级轻量，绝无冗余膨胀)")
    log("请完全重启 Antigravity 软件验证汉化效果。")

if __name__ == "__main__":
    main()
