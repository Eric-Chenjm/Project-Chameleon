import os
import sys
import time
import json
import subprocess
import urllib.request
import ssl
import zipfile
import shutil
import platform
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def show_popup(title, message):
    if platform.system() == "Windows":
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x0)
    else:
        print(f"[{title}] {message}")

def get_installed_antigravity_info():
    system_name = platform.system()
    if system_name == "Windows":
        install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity")
        resources_dir = os.path.join(install_dir, "resources")
    elif system_name == "Darwin":
        resources_dir = "/Applications/Antigravity.app/Contents/Resources"
    else:
        return None, None
        
    asar_path = os.path.join(resources_dir, "app.asar")
    if not os.path.exists(asar_path):
        return None, None
        
    mtime = os.path.getmtime(asar_path)
    return asar_path, mtime

def fetch_and_rebuild():
    repo_dir = r"G:\Antigravity\Project-Chameleon-Repo"
    scratch_main = r"G:\Antigravity\scratch\main_auto.js"
    
    # 查找 Antigravity 的 127.0.0.1 端口并抓取 main.js
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    netstat = subprocess.check_output('netstat -ano', shell=True).decode('gbk', errors='ignore')
    import re
    ports = set(re.findall(r'127\.0\.0\.1:(\d+)\s+.*LISTENING', netstat))

    fetched = False
    for port in ports:
        url = f'https://127.0.0.1:{port}/main.js'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=0.8) as resp:
                if resp.status == 200:
                    data = resp.read()
                    os.makedirs(os.path.dirname(scratch_main), exist_ok=True)
                    with open(scratch_main, 'wb') as f:
                        f.write(data)
                    fetched = True
                    break
        except Exception:
            pass

    if fetched:
        print("[+] 成功抓取最新原生 UI main.js！")
        # 1. 重新编译
        py_translate = os.path.join(repo_dir, "scripts", "translate_ui.py")
        subprocess.run(f'python "{py_translate}" --input "{scratch_main}"', shell=True)
        
        # 2. 拷贝编译产物到 repo translations
        appdata_ui = os.path.expandvars(r"%APPDATA%\Antigravity\zh_cn_ui_main.js")
        repo_ui = os.path.join(repo_dir, "translations", "zh_cn_ui_main.js")
        if os.path.exists(appdata_ui):
            shutil.copy2(appdata_ui, repo_ui)
            
        # 3. 提交 Git 并 Push 到 GitHub
        subprocess.run('git add . && git commit -m "auto: 🤖 Chameleon watchdog auto-adapted new official update" && git push', cwd=repo_dir, shell=True)
        print("[+] 最新汉化包已自动编译并 Push 至 GitHub 仓库！")

    # 4. 下载 GitHub 最新 Zip 包并解压到 G:\Antigravity
    try:
        url = 'https://github.com/Eric-Chenjm/Project-Chameleon/archive/refs/heads/main.zip'
        zip_path = r'G:\Antigravity\Project-Chameleon-main.zip'
        extract_dir = r'G:\Antigravity'

        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_f:
            out_f.write(resp.read())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        print("[+] 最新安装包已成功自动下载并解压到 G:\\Antigravity！")
    except Exception as e:
        print(f"[-] 下载解压安装包失败: {e}")

def main():
    state_file = r"G:\Antigravity\scratch\watchdog_state.json"
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    asar_path, current_mtime = get_installed_antigravity_info()
    if not asar_path:
        print("[-] 未找到安装的 Antigravity 应用。")
        return
        
    last_mtime = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                last_mtime = data.get("last_mtime", 0)
        except:
            pass
            
    if current_mtime > last_mtime:
        print("[!] 检测到 Antigravity 官方应用更新！正在启动全自动追随汉化机制...")
        fetch_and_rebuild()
        
        # 更新状态记录
        with open(state_file, 'w') as f:
            json.dump({"last_mtime": current_mtime, "updated_at": time.time()}, f)
            
        show_popup(
            "🦎 变色龙自动汉化守护进程",
            "检测到官方 Antigravity 已完成版本更新！\n\n变色龙已为您在后台全自动完成：\n1. 抓取新代码并重新编译汉化包\n2. 自动同步更新提交至 GitHub\n3. 自动下载最新包并解压至 G:\\Antigravity\n\n【⚠️重要提示防闪退】：\n请先【手动完全退出】 Antigravity 软件！\n然后双击 G:\\Antigravity\\Project-Chameleon-main\\smart_patch.py 即可一键恢复 100% 汉化！"
        )
    else:
        print("[+] Antigravity 暂无版本更新，系统状态健康。")

if __name__ == "__main__":
    main()
