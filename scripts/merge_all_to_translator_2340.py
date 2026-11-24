# -*- coding: utf-8 -*-
"""
merge_all_to_translator_2340.py
专用于 Antigravity 2.34.0 版本新增 UI 词条与属性前缀规则的自动化安全合并。
"""
import os
import re
import json

def main():
    repo_root = r"G:\Antigravity\Project-Chameleon-Repo"
    translate_ui_path = os.path.join(repo_root, "scripts", "translate_ui.py")
    
    with open(translate_ui_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 2.34.0 专项词典定义
    STATIC_TRANSLATIONS_2340 = {
        # 快捷键与导航命令
        "Toggle Voice Recording": "切换语音录制",
        "Toggle Environment Selector": "切换环境选择器",
        "Toggle Side Panel": "切换侧边面板",
        "Toggle Maximize Side Panel": "切换侧边面板最大化",
        "Open Conversation Picker": "打开会话选择器",
        "Open in Cider": "在 Cider 中打开",
        "Go Back": "后退",
        "Go Forward": "前进",
        "Select Next Conversation": "选择下一个会话",
        "Select Previous Conversation": "选择上一个会话",
        "Select Sidebar Item 1": "选择侧边栏项 1",
        "Select Sidebar Item 2": "选择侧边栏项 2",
        "Select Sidebar Item 3": "选择侧边栏项 3",
        "Select Sidebar Item 4": "选择侧边栏项 4",
        "Select Sidebar Item 5": "选择侧边栏项 5",
        "Select Sidebar Item 6": "选择侧边栏项 6",
        "Select Sidebar Item 7": "选择侧边栏项 7",
        "Select Sidebar Item 8": "选择侧边栏项 8",
        "Select Sidebar Item 9": "选择侧边栏项 9",
        "Toggle Sidebar": "切换侧边栏",
        "Submit Prompt (Alternate to Enter)": "提交提示词 (Enter 备选快捷键)",
        "Playback speed (< / >)": "播放速度 (< / >)",
        "Dev mode: Localhost server automatically detected": "开发者模式：已自动检测到本地服务器",
        "Link Settings": "链接设置",
        "Open In": "打开方式",
        "Enter a URL (e.g. http://localhost:8080)": "输入 URL (例如 http://localhost:8080)",
        "Remove from history (Shift+Delete)": "从历史记录中移除 (Shift+Delete)",
        "Show in folder": "在文件夹中显示",
        "Cancel download": "取消下载",
        "Remove from list": "从列表中移除",
        "Embedded web preview": "内嵌网页预览",
        "Chat Layout": "对话布局",
        "Input Box": "输入框",
        "Enter to send": "按 Enter 发送",
        
        # 设置与模型编排
        "Account connection was not completed.": "账户连接未完成。",
        "Change model": "更改模型",
        "Enable Notifications": "启用通知",
        "Error Loading Models": "加载模型出错",
        "Executor Model": "执行器模型 (Executor Model)",
        "No Models Available": "暂无可用模型",
        "Orchestrator Model": "编排器模型 (Orchestrator Model)",
        "Orchestrator Settings": "编排器设置",
        "Permission preset": "权限预设",
        "Select Model": "选择模型",
        "Telemetry is disabled in Settings": "遥测功能已在设置中禁用",
        "Themes": "主题与配色",
        
        # 智能体交互与任务生命周期
        "Custom Agent Error:": "自定义智能体错误：",
        "Please list the steps to reproduce the issue": "请列出重现该问题的步骤",
        "Resume this agent where it paused": "从暂停处恢复该智能体",
        "Stop this agent": "终止该智能体",
        "Tell the agent what to do instead...": "告知智能体改为什么操作...",
        "What should the agent do on each run?": "智能体每次运行应执行什么操作？",
        
        # 终端与代码环境
        "Copy debug info": "复制调试信息",
        "Default Cog branch / ref": "默认 Cog 分支 / 引用",
        "Enable terminal sandbox": "启用终端沙箱",
        "Prompt to run when triggered...": "触发时运行的提示词...",
        "Terminal command auto execution": "终端命令自动执行",
        "Terminal commands": "终端命令",
        "Terminal window": "终端窗口",
        "Uncommitted": "未提交更改",
        
        # 常用界面提示与时间区间
        "(Optional) Tell us more or type your reason...": "（可选）提供更多信息或输入原因...",
        "14 days": "14 天",
        "21 days": "21 天",
        "7 days": "7 天",
        "Accessibility": "无障碍访问",
        "Antigravity Interactive HTML": "Antigravity 交互式 HTML",
        "Any time": "任意时间",
        "Browser tools (browser_.*)": "浏览器工具 (browser_.*)",
        "Browsing History": "浏览历史记录",
        "Clear Search": "清空搜索",
        "Click to copy URL": "点击复制 URL",
        "Click to copy prompt": "点击复制提示词",
        "Click to view details": "点击查看详情",
        "Compact Mode": "紧凑模式",
        "Confirm Deletion": "确认删除",
        "Connected Accounts": "已连接账户",
        "Connection Lost": "连接断开",
        "Copy URL": "复制 URL",
        "Custom Prompt": "自定义提示词",
        "Delete Conversation": "删除会话",
        "Disable notifications": "禁用通知",
        "Download Complete": "下载完成",
        "Download Failed": "下载失败",
        "Download Starting...": "开始下载...",
        "Edit Configuration": "编辑配置",
        "Execution Error": "执行出错",
        "Export Conversation": "导出会话",
        "Failed to load image": "加载图片失败",
        "Generate Response": "生成回复",
        "Import Settings": "导入设置",
        "Keyboard Navigation": "键盘导航",
        "Learn Mode": "学习模式",
        "Manage Plugins": "管理插件",
        "Memory Usage": "内存占用",
        "Model Parameters": "模型参数",
        "More Options": "更多选项",
        "Network Error": "网络错误",
        "New Task": "新建任务",
        "No results found": "未找到结果",
        "Notification Preferences": "通知偏好",
        "Open Directory": "打开目录",
        "Open File Location": "打开文件所在位置",
        "Output Console": "输出控制台",
        "Performance Metrics": "性能指标",
        "Preview Mode": "预览模式",
        "Quick Switcher": "快速切换器",
        "Recent Searches": "最近搜索",
        "Refresh List": "刷新列表",
        "Reset to Default": "恢复默认值",
        "Save Changes": "保存更改",
        "Security Settings": "安全设置",
        "Select All": "全选",
        "Show Less": "收起",
        "Show More": "展开更多",
        "Sync Now": "立即同步",
        "System Requirements": "系统要求",
        "Task History": "任务历史",
        "User Feedback": "用户反馈",
        "View Details": "查看详情",
        "View Logs": "查看日志",
        "Voice Input": "语音输入",
        "Waiting for response...": "等待响应中...",
        "Workspace Root": "工作区根目录",

        # 属性前缀安全词条（彻底避免裸词污染）
        'label:"Fork"': 'label:"派生会话 (Fork)"',
        'label:"Plan"': 'label:"实施规划 (Plan)"',
        'title:"Plan"': 'title:"实施规划 (Plan)"',
        'label:"Branch"': 'label:"分支 (Branch)"',
        'label:"Comments"': 'label:"评论列表"',
        'label:"Comment"': 'label:"评论"',
        'label:"Members"': 'label:"成员列表"',
        'label:"Downloads"': 'label:"下载内容"',
        'title:"Downloads"': 'title:"下载内容"',
        'label:"Skills"': 'label:"技能池"',
        'title:"Skills"': 'title:"技能池"',
        'label:"Seek"': 'label:"进度跳转"',
        'label:"Volume"': 'label:"音量调节"',
        'label:"From"': 'label:"发送方"',
        'label:"Sent"': 'label:"已发送"',
        'label:"Owner"': 'label:"所有者"',
        'label:"Author"': 'label:"作者"',
        'label:"Forward"': 'label:"前进"',
        'title:"Forward"': 'title:"前进"',
        'label:"Quote"': 'label:"引用"',
        'label:"Extension"': 'label:"扩展"',
        'label:"External"': 'label:"外部"',
        'label:"Enterprise"': 'label:"企业版"',
        'label:"Sound"': 'label:"提示音"',
        'title:"Sound"': 'title:"声音设置"',
        'title:"Accessibility"': 'title:"无障碍设置"',
        'title:"Chat"': 'title:"对话面板"',
        'tooltip:"Critique"': 'tooltip:"方案评审与批判"',
        'tooltip:"Skills"': 'tooltip:"已启用的技能列表"',
    }

    DYNAMIC_DICT_2340 = {
        "Toggle Voice Recording": "切换语音录制",
        "Toggle Environment Selector": "切换环境选择器",
        "Toggle Side Panel": "切换侧边面板",
        "Toggle Maximize Side Panel": "切换侧边面板最大化",
        "Open Conversation Picker": "打开会话选择器",
        "Open in Cider": "在 Cider 中打开",
        "Go Back": "后退",
        "Go Forward": "前进",
        "Select Next Conversation": "选择下一个会话",
        "Select Previous Conversation": "选择上一个会话",
        "Select Sidebar Item 1": "选择侧边栏项 1",
        "Select Sidebar Item 2": "选择侧边栏项 2",
        "Select Sidebar Item 3": "选择侧边栏项 3",
        "Select Sidebar Item 4": "选择侧边栏项 4",
        "Select Sidebar Item 5": "选择侧边栏项 5",
        "Select Sidebar Item 6": "选择侧边栏项 6",
        "Select Sidebar Item 7": "选择侧边栏项 7",
        "Select Sidebar Item 8": "选择侧边栏项 8",
        "Select Sidebar Item 9": "选择侧边栏项 9",
        "Toggle Sidebar": "切换侧边栏",
        "Submit Prompt (Alternate to Enter)": "提交提示词 (Enter 备选快捷键)",
        "Playback speed (< / >)": "播放速度 (< / >)",
        "Dev mode: Localhost server automatically detected": "开发者模式：已自动检测到本地服务器",
        "Link Settings": "链接设置",
        "Open In": "打开方式",
        "Enter a URL (e.g. http://localhost:8080)": "输入 URL (例如 http://localhost:8080)",
        "Remove from history (Shift+Delete)": "从历史记录中移除 (Shift+Delete)",
        "Show in folder": "在文件夹中显示",
        "Cancel download": "取消下载",
        "Remove from list": "从列表中移除",
        "Embedded web preview": "内嵌网页预览",
        "Chat Layout": "对话布局",
        "Input Box": "输入框",
        "Enter to send": "按 Enter 发送",
        "Account connection was not completed.": "账户连接未完成。",
        "Change model": "更改模型",
        "Enable Notifications": "启用通知",
        "Error Loading Models": "加载模型出错",
        "Executor Model": "执行器模型 (Executor Model)",
        "No Models Available": "暂无可用模型",
        "Orchestrator Model": "编排器模型 (Orchestrator Model)",
        "Orchestrator Settings": "编排器设置",
        "Permission preset": "权限预设",
        "Select Model": "选择模型",
        "Telemetry is disabled in Settings": "遥测功能已在设置中禁用",
        "Themes": "主题与配色",
        "Custom Agent Error:": "自定义智能体错误：",
        "Please list the steps to reproduce the issue": "请列出重现该问题的步骤",
        "Resume this agent where it paused": "从暂停处恢复该智能体",
        "Stop this agent": "终止该智能体",
        "Tell the agent what to do instead...": "告知智能体改为什么操作...",
        "What should the agent do on each run?": "智能体每次运行应执行什么操作？",
        "Copy debug info": "复制调试信息",
        "Default Cog branch / ref": "默认 Cog 分支 / 引用",
        "Enable terminal sandbox": "启用终端沙箱",
        "Prompt to run when triggered...": "触发时运行的提示词...",
        "Terminal command auto execution": "终端命令自动执行",
        "Terminal commands": "终端命令",
        "Terminal window": "终端窗口",
        "Uncommitted": "未提交更改",
        "(Optional) Tell us more or type your reason...": "（可选）提供更多信息或输入原因...",
        "14 days": "14 天",
        "21 days": "21 天",
        "7 days": "7 天",
        "Accessibility": "无障碍访问",
        "Antigravity Interactive HTML": "Antigravity 交互式 HTML",
        "Any time": "任意时间",
        "Browser tools (browser_.*)": "浏览器工具 (browser_.*)",
        "Browsing History": "浏览历史记录",
        "Clear Search": "清空搜索",
        "Click to copy URL": "点击复制 URL",
        "Click to copy prompt": "点击复制提示词",
        "Click to view details": "点击查看详情",
        "Compact Mode": "紧凑模式",
        "Confirm Deletion": "确认删除",
        "Connected Accounts": "已连接账户",
        "Connection Lost": "连接断开",
        "Copy URL": "复制 URL",
        "Custom Prompt": "自定义提示词",
        "Delete Conversation": "删除会话",
        "Disable notifications": "禁用通知",
        "Download Complete": "下载完成",
        "Download Failed": "下载失败",
        "Download Starting...": "开始下载...",
        "Edit Configuration": "编辑配置",
        "Execution Error": "执行出错",
        "Export Conversation": "导出会话",
        "Failed to load image": "加载图片失败",
        "Generate Response": "生成回复",
        "Import Settings": "导入设置",
        "Keyboard Navigation": "键盘导航",
        "Learn Mode": "学习模式",
        "Manage Plugins": "管理插件",
        "Memory Usage": "内存占用",
        "Model Parameters": "模型参数",
        "More Options": "更多选项",
        "Network Error": "网络错误",
        "New Task": "新建任务",
        "No results found": "未找到结果",
        "Notification Preferences": "通知偏好",
        "Open Directory": "打开目录",
        "Open File Location": "打开文件所在位置",
        "Output Console": "输出控制台",
        "Performance Metrics": "性能指标",
        "Preview Mode": "预览模式",
        "Quick Switcher": "快速切换器",
        "Recent Searches": "最近搜索",
        "Refresh List": "刷新列表",
        "Reset to Default": "恢复默认值",
        "Save Changes": "保存更改",
        "Security Settings": "安全设置",
        "Select All": "全选",
        "Show Less": "收起",
        "Show More": "展开更多",
        "Sync Now": "立即同步",
        "System Requirements": "系统要求",
        "Task History": "任务历史",
        "User Feedback": "用户反馈",
        "View Details": "查看详情",
        "View Logs": "查看日志",
        "Voice Input": "语音输入",
        "Waiting for response...": "等待响应中...",
        "Workspace Root": "工作区根目录",
    }

    # 2. 合并入 translations 字典
    m_trans = re.search(r'translations\s*=\s*\{([\s\S]+?)\n\s*\}\n\s*print\("Applying translations\.\.\."\)', content)
    if not m_trans:
        raise RuntimeError("Could not locate translations dict in translate_ui.py")
    
    trans_body = m_trans.group(1)
    existing_trans_keys = set()
    for line in trans_body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        km = re.match(r'^(?:\"([^\"]+)\"|\'([^\']+)\'|([^:]+))\s*:', line)
        if km:
            k = km.group(1) or km.group(2) or km.group(3)
            if k:
                existing_trans_keys.add(k.strip())

    to_add_static = {}
    for k, v in STATIC_TRANSLATIONS_2340.items():
        if k not in existing_trans_keys:
            to_add_static[k] = v

    print(f"New static translations to add: {len(to_add_static)}")
    if to_add_static:
        addition_lines = ["\n        # --- 2.34.0 Audit Merged Entries ---"]
        for k, v in to_add_static.items():
            k_str = json.dumps(k, ensure_ascii=False)
            v_str = json.dumps(v, ensure_ascii=False)
            addition_lines.append(f'        {k_str}: {v_str},')
        new_trans_body = trans_body + "\n".join(addition_lines)
        content = content[:m_trans.start(1)] + new_trans_body + content[m_trans.end(1):]
        print("Successfully merged 2.34.0 entries into translations dict!")

    # 3. 合并入 dynamicDict 字典
    m_dyn = re.search(r'const dynamicDict\s*=\s*\{([\s\S]+?)\n\s*\};', content)
    if not m_dyn:
        raise RuntimeError("Could not locate dynamicDict in translate_ui.py")

    dyn_body = m_dyn.group(1)
    existing_dyn_keys = set()
    for line in dyn_body.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        km = re.match(r'^\"([^\"]+)\"\s*:', line)
        if km:
            existing_dyn_keys.add(km.group(1).strip())

    to_add_dyn = {}
    for k, v in DYNAMIC_DICT_2340.items():
        if k not in existing_dyn_keys:
            to_add_dyn[k] = v

    print(f"New dynamicDict entries to add: {len(to_add_dyn)}")
    if to_add_dyn:
        dyn_lines = ["\n    // --- 2.34.0 Dynamic Audit Entries ---"]
        for k, v in to_add_dyn.items():
            k_str = json.dumps(k, ensure_ascii=False)
            v_str = json.dumps(v, ensure_ascii=False)
            dyn_lines.append(f'    {k_str}: {v_str},')
        new_dyn_body = dyn_body + "\n".join(dyn_lines)
        content = content[:m_dyn.start(1)] + new_dyn_body + content[m_dyn.end(1):]
        print("Successfully merged 2.34.0 entries into dynamicDict!")

    # 4. 写回 translate_ui.py
    with open(translate_ui_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Finished merging 2.34.0 entries into translate_ui.py successfully!")

if __name__ == "__main__":
    main()
