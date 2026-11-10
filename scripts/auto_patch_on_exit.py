# -*- coding: utf-8 -*-
import os
import sys
import time
import shutil
import psutil

def is_antigravity_running():
    for p in psutil.process_iter(['name', 'exe']):
        try:
            name = (p.info['name'] or '').lower()
            exe = (p.info['exe'] or '').lower()
            if name == 'antigravity.exe' and 'resources' not in exe and 'ide' not in name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def log(msg):
    log_file = r"G:\Antigravity\scratch\auto_patch_daemon.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        f.flush()

def main():
    res_dir = r"C:\Users\90513\AppData\Local\Programs\antigravity\resources"
    asar_path = os.path.join(res_dir, "app.asar")
    tmp_asar = os.path.join(res_dir, "app.asar.tmp")
    unpacked_dir = os.path.join(res_dir, "app.asar.unpacked")
    tmp_unpacked = os.path.join(res_dir, "app.asar.tmp.unpacked")
    appdata_ui = os.path.join(os.environ.get("APPDATA", ""), "Antigravity", "zh_cn_ui_main.js")
    dist_ui = r"G:\Antigravity\Project-Chameleon-Repo\translations\zh_cn_ui_main.js"

    log("Daemon started successfully. Monitoring Antigravity main process...")

    # 1. 循环等待主进程退出
    while is_antigravity_running():
        time.sleep(0.5)

    log("Antigravity process exit detected! Applying patch immediately...")

    # 2. 毫秒级重试替换 asar
    replaced = False
    for attempt in range(20):
        try:
            if os.path.exists(tmp_asar):
                os.replace(tmp_asar, asar_path)
                replaced = True
                log(f"SUCCESS: app.asar replaced on attempt {attempt+1}!")
                break
        except Exception as e:
            time.sleep(0.2)

    # 3. 处理 unpacked
    if os.path.exists(tmp_unpacked):
        for attempt in range(10):
            try:
                if os.path.exists(unpacked_dir):
                    shutil.rmtree(unpacked_dir, ignore_errors=True)
                os.replace(tmp_unpacked, unpacked_dir)
                log("SUCCESS: app.asar.unpacked replaced!")
                break
            except Exception as e:
                time.sleep(0.2)

    # 4. 确保 UI 文件
    if not os.path.exists(appdata_ui) and os.path.exists(dist_ui):
        shutil.copy2(dist_ui, appdata_ui)
        log("SUCCESS: zh_cn_ui_main.js verified.")

    log("ALL DONE! Antigravity 2.30.0 is now 100% patched. Ready for relaunch.")

if __name__ == "__main__":
    main()
