import os
import sys
import shutil
import subprocess
import platform

def log(msg):
    print(f"[+] {msg}")

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"[-] 命令执行失败: {cmd}")
        sys.exit(1)

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
        
    log("1. 检查并备份 app.asar ...")
    if not os.path.exists(asar_bak):
        shutil.copy2(asar_path, asar_bak)
        log("首次安装，备份成功。")
    else:
        # 如果 app.asar 的修改时间比 app.asar.bak 更新，说明官方刚升级了版本
        if os.path.getmtime(asar_path) > os.path.getmtime(asar_bak):
            shutil.copy2(asar_path, asar_bak)
            log("检测到官方 Antigravity 已升级，已自动更新原版 app.asar.bak 备份！")
        else:
            log("已有最新备份，直接使用原备份。")
        
    log("2. 拆解 app.asar (这可能需要十几秒) ...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    run_cmd(f'{npx_cmd} @electron/asar extract "{asar_path}" "{extract_dir}"')
    
    log("3. 注入基础中文翻译资源 ...")
    # nls.messages.json
    out_dir = os.path.join(extract_dir, "out")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    nls_src = os.path.join(trans_dir, "nls.messages.zh-CN.json")
    nls_dst = os.path.join(out_dir, "nls.messages.json")
    if os.path.exists(nls_src):
        shutil.copy2(nls_src, nls_dst)
        log("注入 nls.messages.json 成功！")
        
    # product.json
    prod_src = os.path.join(trans_dir, "product.json")
    prod_dst = os.path.join(extract_dir, "product.json")
    if os.path.exists(prod_src):
        shutil.copy2(prod_src, prod_dst)
        log("注入 product.json 成功！")
        
    # AI 界面拦截器 customScheme.js
    cs_src = os.path.join(current_dir, "patches", "customScheme.ai-ui.js")
    cs_dst = os.path.join(extract_dir, "dist", "customScheme.js")
    if os.path.exists(cs_src):
        os.makedirs(os.path.dirname(cs_dst), exist_ok=True)
        shutil.copy2(cs_src, cs_dst)
        log("注入 customScheme 拦截器成功，AI 界面汉化已激活！")
        
    log("3.5 部署预编译汉化 UI 包到系统缓存 ...")
    os.makedirs(appdata_dir, exist_ok=True)
    # 部署预编译好的汉化包 zh_cn_ui_main.js
    ui_src = os.path.join(trans_dir, "zh_cn_ui_main.js")
    if os.path.exists(ui_src):
        ui_dst = os.path.join(appdata_dir, "zh_cn_ui_main.js")
        shutil.copy2(ui_src, ui_dst)
        log(f"预编译汉化 UI 包成功部署至: {ui_dst}")
    else:
        print("[-] 严重错误：找不到 zh_cn_ui_main.js，汉化将失效！")
        sys.exit(1)
        
    log("4. 重新封包 app.asar ...")
    tmp_asar = asar_path + ".tmp"
    run_cmd(f'{npx_cmd} @electron/asar pack "{extract_dir}" "{tmp_asar}"')
    
    # 覆盖原 asar
    os.replace(tmp_asar, asar_path)
    
    log("5. 清理临时解包目录 ...")
    shutil.rmtree(extract_dir)
    
    log("=========== 完美汉化注入完成！ ===========")
    log("请重启 Antigravity 或按 Ctrl+R (Windows) / Cmd+R (Mac) 重载界面。")

if __name__ == "__main__":
    main()
