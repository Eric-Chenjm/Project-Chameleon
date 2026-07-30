import os
import sys
import time
import json
import subprocess
import platform

def get_installed_antigravity_exe():
    system_name = platform.system()
    if system_name == "Windows":
        exe_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe")
        asar_path = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Antigravity\resources\app.asar")
    elif system_name == "Darwin":
        exe_path = "/Applications/Antigravity.app/Contents/MacOS/Electron"
        asar_path = "/Applications/Antigravity.app/Contents/Resources/app.asar"
    else:
        return None, None
    return exe_path, asar_path

def main():
    exe_path, asar_path = get_installed_antigravity_exe()
    if not exe_path or not os.path.exists(exe_path):
        print(f"[-] 未找到 Antigravity 可执行文件: {exe_path}")
        input("按回车退出...")
        return

    # 1. 极速比对时间戳 (耗时 0.001s)
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    state_file = os.path.join(current_dir, "scratch", "watchdog_state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    current_mtime = os.path.getmtime(asar_path) if os.path.exists(asar_path) else 0
    last_mtime = 0
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                last_mtime = json.load(f).get("last_mtime", 0)
        except:
            pass

    # 2. 如果官方刚升级了 app.asar
    if current_mtime > last_mtime and last_mtime != 0:
        print("[!] 检测到 Antigravity 官方发布了新版本更新！")
        print("[+] 正在启动全自动适配与重编译流水线...")
        
        watchdog_script = os.path.join(current_dir, "scripts", "chameleon_auto_watchdog.py")
        subprocess.run(f'python "{watchdog_script}"', shell=True)
        
        print("\n[+] 编译与 GitHub 同步完成！准备为您一键应用最新汉化补丁...")
        smart_patch = os.path.join(current_dir, "smart_patch.py")
        subprocess.run(f'python "{smart_patch}"', shell=True)
        
        # 更新记录
        with open(state_file, 'w') as f:
            json.dump({"last_mtime": current_mtime, "updated_at": time.time()}, f)
            
        print("\n[🎉] 补丁升级成功！正在为您启动 Antigravity 中文版...")
        time.sleep(1)

    # 3. 拉起 Antigravity 软件
    subprocess.Popen([exe_path])

if __name__ == "__main__":
    main()
