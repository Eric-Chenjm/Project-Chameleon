import os
import sys
import re
import argparse
import platform
def to_single_quoted(value):
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def apply_safe_literal_replacement(content, original_literal, translated_literal):
    source_value = original_literal[1:-1]
    target_value = translated_literal[1:-1]

    before = content
    content = content.replace(repr(source_value).replace('"', "'"), to_single_quoted(target_value))
    content = content.replace(f'"{source_value}"', f'"{target_value}"')
    content = content.replace(to_single_quoted(source_value), to_single_quoted(target_value))
    content = content.replace('"' + source_value.replace("\\", "\\\\").replace('"', '\\"') + '"',
                              '"' + target_value.replace("\\", "\\\\").replace('"', '\\"') + '"')
    return content, content != before

def main():
    print("=== Antigravity 2.0 UI Translator ===")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=os.environ.get(
            "AGY_UI_MAIN_SOURCE",
            r"C:\Users\Administrator\.gemini\antigravity\brain\a12d81c7-05e0-4def-b7bc-6e8543fed692\scratch\ui_main.js",
        ),
        help="Path to the extracted Antigravity UI main bundle.",
    )
    args = parser.parse_args()
    
    # Paths
    input_file = args.input
    
    system_name = platform.system()
    if system_name == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            print("Error: APPDATA environment variable not found.")
            sys.exit(1)
        output_dir = os.path.join(appdata, "Antigravity")
    elif system_name == "Darwin":
        output_dir = os.path.expanduser("~/Library/Application Support/Antigravity")
    else:
        print(f"Error: Unsupported OS {system_name}")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "zh_cn_ui_main.js")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)
        
    print(f"Reading from: {input_file}")
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Define string translation mapping
    # Note: We must be very precise to match JSON property keys, arrays, or JSX definitions
    translations = {
        "Scheduled Tasks": "计划定时任务",
        "Open Commit Graph": "查看 Git 提交历史图谱",
        "Go Forward in Pane": "在面板中前进",
        "Go Back in Pane": "在面板中后退",
        "Reset Zoom": "重置缩放比例",
        "Zoom Out": "界面缩小",
        "Zoom In": "界面放大",
        "Reset overrides": "重置所有特性覆盖",
        "Search flags": "搜索特性开关",
        "Turn on a flag you don't have": "开启未全量灰度的实验性特性 Flag",
        "Custom Flags": "实验性功能特性开关 (Flags)",
        "These allowed domain rules are set by your organization's administrator and cannot be removed.": "此受信任域名白名单由所在组织 IT 管理员集中强制下发，本地无法修改或删除。",
        "Organization Allowed Domains (Read-Only)": "组织下发的受信任域名（只读）",
        "Must be a valid URL": "必须是格式合法的 URL 网址",
        "Enter avatar URL (optional)": "输入机器人头像 URL（可选）",
        "Avatar URL": "头像图片链接",
        "Enter bot name (optional)": "输入机器人显示名称（可选）",
        "Bot Name": "机器人名称",
        "Creating Sidecar": "正在启动 Sidecar 伴生进程",
        "Creating Cloud Project": "正在创建关联 Google Cloud 项目",
        "Creating Chat Bot": "正在创建对话机器人",
        "Installing Chat Bot": "正在安装对话机器人",
        "Setup may take over 5 minutes. Please keep this screen open during setup.": "安装与初始化可能需要 5 分钟以上，在此期间请保持当前页面开启。",
        "Connecting to language server...": "正在连接语言服务器 (LSP)...",
        "Browse and enable plugins from the Build With Google catalog.": "浏览并一键启用来自 Build With Google 生态目录的官方扩展插件。",
        "Plugins": "扩展插件市场",
        "Enter directory path...": "输入存放技能的目录路径...",
        "Skills Configuration Error:": "技能配置解析错误：",
        "Refresh skills paths": "重新加载技能路径",
        "Skill Custom Paths": "自定义技能搜索路径",
        "Hooks": "生命周期钩子",
        "Configure hooks that run on agent lifecycle events.": "配置在智能体生命周期事件（如会话启动、命令执行前后）触发的执行脚本。",
        "Manage Hooks": "管理生命周期钩子 (Hooks)",
        "No quota information available.": "暂无可用配额信息。",
        "Refresh quota and credits data": "刷新配额与额度数据",
        "Get More AI Credits": "充值 / 获取更多 AI 积分",
        "Manage your model quota and credits.": "管理你的大模型调用速率配额与 AI 积分额度 (Credits)。",
        "For Antigravity Business consumption options, see": "关于 Antigravity 商业版计费与用量方案，请参阅",
        "See Activity": "查看用量与活动记录",
        "App version": "客户端软件版本",
        "Not Signed In": "未登录账户",
        "Enter URL pattern...": "输入 URL 或域名通配规则（例如：https://api.github.com/*）...",
        "URLs the agent can read or open in this workspace.": "智能体在当前工作区内被允许发起 GET 请求或读取内容的 URL/域名。",
        "Read URLs": "网页读取 (URL)",
        "Commands the agent can run outside the sandbox in this workspace.": "在当前工作区内，允许智能体绕过沙箱隔离直接在宿主机执行的命令。",
        "Commands Outside Sandbox": "沙箱外命令执行",
        "Enter command (e.g., git, blaze)...": "输入允许执行的命令（例如：git、npm、mvn）...",
        "Enter file or directory path...": "输入文件或目录的绝对/相对路径...",
        "Paths the agent can modify inside this workspace.": "智能体在当前工作区内被允许创建、修改或删除的文件或目录路径。",
        "Paths the agent can read inside this workspace.": "智能体在当前工作区内被允许读取的文件或目录路径。",
        "A high-risk mode that disables all safety barriers. The agent operates with full system access, auto-executes all terminal commands, and reads or writes to all local files without review prompts.": "⚠️ 极高风险模式：解除全部安全限制。智能体拥有完整的操作系统访问权限，将全自动秒级执行所有终端命令并自由读写本地任意文件，全程无任何确认弹窗。",
        "Useful for tasks that require file access across your full machine. The agent has full read and write access to all local files, but all proposed terminal commands require manual review and approval before running.": "适用于需要跨多个项目或整机范围调阅/写入文件的复杂任务。智能体对所有本地文件拥有读写权限，但执行终端命令前仍必须通过人工审批。",
        "Useful for typical development with an emphasis on security. It prioritizes safety over speed by requiring manual approval for all terminal commands and files outside the project directory.": "适用于注重代码安全性的常规开发场景。通过对所有终端命令和项目目录外文件操作强制审批，确保安全优先于执行速度。",
        "Inherit from global settings.": "完全继承全局统一配置的安全策略。",
        "Inherit Global": "继承全局预设",
        "managed by your organization": "已由所在组织管理员集中托管配置",
        "Conversation History": "关联历史对话上下文",
        "Let the agent access its knowledge base to inform its responses.": "允许智能体检索并引用本地或项目知识库以生成更精准的回复。",
        "Knowledge": "智能体知识库检索",
        "Predict the location of your next edit and navigate you there with a tab.": "智能预测你接下来可能编辑的代码位置，按下 Tab 键直接瞬移光标。",
        "Tab to Jump": "Tab 智能光标跳转",
        "Automatically expand the Changes Overview toolbar when the agent makes edits.": "智能体完成文件编辑后，自动展开变更概览工具栏以便快速审查。",
        "Auto-Expand Changes Overview": "自动展开代码变更概览",
        "Show a floating notification card when background conversations need attention.": "当后台运行的对话需要人工操作或遇到异常时，显示浮动通知卡片。",
        "Show browser notifications when your action is needed or execution finishes.": "当需要人工介入审批或智能体执行完毕时，发送系统级桌面通知。",
        "Automatically prompt you to restart the app when a new update is ready.": "当检测到新版本并下载就绪时，自动提示重启应用生效。",
        "Queue": "排队等待空闲",
        "Send Immediately": "就绪后即刻发送",
        "Configure when follow-up messages are sent.": "配置在智能体繁忙时发送追问消息的处理时机。",
        "Updater": "软件更新",
        "Execution": "执行与投递",
        "The full developer experience.": "全功能开发体验，配备集成终端、差异对比与开发工具箱。",
        "Simplified interface without developer tooling.": "简化交互界面，隐藏底层终端与开发工具，专注协作。",
        "Non-technical": "协作极简模式",
        "Choose how technical the interface should be (go/agy-cowork).": "选择界面的专业技术深度（极简协作 vs 全能开发）。",
        "Product Skin": "工作界面技术风格",
        "Fill": "撑满 / 自适应宽度",
        "Configure the default width of tables.": "配置对话与文档中表格的呈现宽度。",
        "Table Width": "表格显示宽度",
        "Vesper": "夜昏 (Vesper)",
        "Solarized Dark": "Solarized 深色",
        "Tokyo Night": "东京之夜 (Tokyo Night)",
        "One Dark Pro": "One Dark Pro",
        "Monokai": "经典 Monokai",
        "Dracula": "吸血鬼 (Dracula)",
        "Default Dark": "默认深色 (Default Dark)",
        "Default Light": "默认浅色 (Default Light)",
        "Accent": "强调主色",
        "Foreground": "文本前景色",
        "Background": "背景颜色",
        "Reset to preset": "重置为预设颜色",
        "Preset": "主题预设",
        "Strong": "高对比度",
        "Contrast": "对比度增强",
        "Switch to Dark Mode": "切换至深色模式",
        "Switch to Light Mode": "切换至浅色模式",
        "Inherit Editor": "跟随编辑器主题",
        "Configure tab completion, suggestions, and navigation behavior.": "配置 Tab 代码补全、行内建议与光标智能跳转行为。",
        "Manage your notification preferences.": "管理你的桌面提醒与声音通知偏好。",
        "Configure editor-specific behaviors and shortcuts.": "配置编辑器专用行为、补全与快捷交互。",
        "Configure the agent's visual theme and display preferences.": "配置智能体的视觉主题与界面显示偏好。",
        "Go to General settings": "前往通用设置",
        "Labs settings have moved to the Advanced section of General settings.": "实验特性设置已迁移至“通用设置”的“高级”分区中。",
        "Labs settings have moved": "实验特性设置已迁移",
        "Browser settings have moved to the Browser section of General settings.": "浏览器设置已迁移至“通用设置”的“浏览器”分区中。",
        "Browser settings have moved": "浏览器设置已迁移",
        "Best of N settings have moved to the Advanced section of General settings.": "多候选探索 (Best of N) 设置已迁移至“通用设置”的“高级”分区中。",
        "Best of N settings have moved": "多候选探索设置已迁移",
        "Standalone Conversation": "独立对话（未关联项目）",
        "CitC Settings": "CitC 云端工作区设置",
        "Editor Settings": "编辑器设置",
        "Models & Usage": "模型与用量",
        "Best of N": "多候选探索 (Best of N)",
        "Labs": "实验特性",
        "Developer": "开发者选项",
        "Skin": "界面风格",
        "Redirect blocked: unsafe protocol": "重定向已拦截：不安全协议",
        "Blocked by organization policy": "已被组织安全策略拦截",
        "Blocked, needs input": "已拦截，等待用户授权",
        "BLOCKED": "已拦截",
        "Blocked": "已拦截",
        "Always run": "始终运行",
        "Allow Once": "仅允许一次",
        "Allow once": "仅允许一次",
        "Tool Permissions": "工具调用权限",
        "Permission Preset": "权限预设",
        "Network Permissions": "网络访问权限",
        "Site Allowlist": "网站允许列表",
        "Open allowlist": "打开允许列表",
        "Added to allowlist": "已添加到允许列表",
        "Add to allowlist": "添加到允许列表",
        "Network access is disabled in sandbox mode.": "在沙箱模式下网络访问已禁用。",
        "Sandbox Allow Network": "允许沙箱网络访问",
        "Proceed in Sandbox": "在沙箱中继续执行",
        "Run (unsandboxed)": "在沙箱外运行",
        "CHECKPOINT": "检查点",
        "Checkpoint": "检查点",
        "Revert to Snapshot": "回滚到快照",
        "Workspace > Restore to Snapshot": "工作区 > 还原至快照",
        "Restore to Snapshot": "还原至快照",
        "Deny List Terminal Commands": "终端命令拒绝列表 (黑名单)",
        "Allow List Terminal Commands": "终端命令允许列表 (白名单)",
        "Terminal Scrollback": "终端回滚行数",
        "Timed out": "执行超时",
        "Killed": "已强制终止",
        "INTERRUPTED": "已中断",
        "Terminated": "已终止",
        "Executing": "正在执行",
        "Terminals": "终端列表",
        "Terminal & Tooling Permissions": "终端与工具权限",
        "Standalone terminals": "独立终端",
        "Standalone Terminals": "独立终端",
        "Resize terminal panes": "调整终端分栏大小",
        "Failed to create terminal": "创建终端失败",
        "Creating terminal...": "正在创建终端...",
        "No active terminals. Click + to create one.": "暂无活动终端。点击 + 创建一个终端。",
        "No active terminals": "暂无活动终端",
        "Insert in terminal": "插入到终端",
        "Insert in Terminal": "插入到终端",
        "Open Terminal": "打开终端",
        "Clear Terminal": "清空终端",
        "Delete Terminal": "删除终端",
        "Split Terminal": "拆分终端",
        "Close Terminal Tab": "关闭终端标签页",
        "New Terminal Tab": "新建终端标签页",
        "Open Folder (Interactive)": "打开文件夹 (交互式)",
        "Open Folder": "打开文件夹",
        "Create fork in current workspace": "在当前工作区中创建分支副本",
        "Create fork in new workspace": "在新工作区中创建分支副本",
        "New Conversation in Workspace": "在工作区中新建对话",
        "Sidebar grouped by workspace": "侧边栏按工作区分组",
        "Group By Workspace": "按工作区分组",
        "Switch IDE Workspace": "切换 IDE 工作区",
        "Recent Remote Workspaces": "最近远程工作区",
        "Connect to Remote Workspace": "连接到远程工作区",
        "Search Recent Workspaces": "搜索最近工作区",
        "Search past workspaces...": "搜索历史工作区...",
        "Search workspaces...": "搜索工作区...",
        "All Workspaces": "所有工作区",
        "Current workspace": "当前工作区",
        "Current Workspace": "当前工作区",
        "No workspaces found": "未找到工作区",
        "Available workspaces": "可用工作区",
        "Select workspace...": "选择工作区...",
        "Select Workspace": "选择工作区",
        "Unmount workspace": "卸载工作区",
        "Copy workspace": "复制工作区",
        "Archive Workspace": "归档工作区",
        "Delete workspace": "删除工作区",
        "New Workspace": "新建工作区",
        "Open Workspace Selector": "打开工作区选择器",
        "Open Workspace": "打开工作区",
        "Close to the Left": "关闭左侧标签页",
        "Close to the Right": "关闭右侧标签页",
        "Close Tab": "关闭标签页",
        "Collapse All Folders": "折叠所有文件夹",
        "Expand All Folders": "展开所有文件夹",
        "Copy Config File Path": "复制配置文件路径",
        "Copy File Name": "复制文件名",
        "Delete Conversation": "删除对话",
        "Delete Folder": "删除文件夹",
        "Delete File": "删除文件",
        "Rename Group": "重命名分组",
        "New Folder": "新建文件夹",
        "New File": "新建文件",
        "Open to the Side": "在侧边分栏打开",
        "Reveal in Explorer": "在文件资源管理器中显示",
        "Reveal in Finder": "在访达中显示",
        "Show in File Manager": "在文件管理器中显示",
        "Show in File Explorer": "在文件资源管理器中显示",
        "Expand diff": "展开代码差异",
        "Collapse diff": "折叠代码差异",
        "Apply selection": "应用选区更改",
        "Accept selection": "接受选区更改",
        "Revert this change": "还原此更改",
        "Reject this change": "拒绝此更改",
        "Accept this change": "接受此更改",
        "Discard all changes": "放弃所有更改",
        "Reject all changes": "拒绝所有更改",
        "Accept all changes": "接受所有更改",
        "Changes Overview": "变更概览",
        "Pending Changes": "待处理的更改",
        "Previous Difference": "上一个差异",
        "Next Difference": "下一个差异",
        "Previous Change": "上一个更改",
        "Next Change": "下一个更改",
        "File Comments": "文件批注",
        "File Diff Comments": "代码差异批注",
        "Revert file changes": "还原文件更改",
        "Only staged changes are being committed.": "仅提交已暂存的更改。",
        "Both staged and unstaged changes are being committed.": "正在同时提交已暂存和未暂存的更改。",
        "Include unstaged changes": "包含未暂存更改",
        "Discard unstaged changes": "放弃未暂存更改",
        "Commit staged changes": "提交已暂存更改",
        "Untracked (Unstaged)": "未跟踪 (未暂存)",
        "Added (Staged)": "已添加 (已暂存)",
        "Staged": "已暂存",
        "Unstaged Changes": "未暂存的更改",
        "Staged Changes": "已暂存的更改",
        "Split Diff": "分栏代码差异",
        "Stacked Diff": "堆叠代码差异",
        "Unified Diff": "统一差异视图",
        "Inline Diff": "行内代码差异",
        "Open side-by-side view": "打开并排对比视图",
        "Side-by-side layout": "并排对比布局",
        "Side-by-Side": "并排对比",
        "Expand Diffs": "展开所有差异",
        "Collapse Diffs": "折叠所有差异",
        "Open Diff": "打开代码差异",
        "Let the agent access its knowledge base to inform its responses": "允许智能体访问其知识库以辅助回答",
        "Let the agent access past conversations to inform its responses": "允许智能体访问历史对话以辅助回答",
        "Show suggestions when typing in the editor": "在编辑器中输入时显示代码建议",
        "Use full Git clones for Best of N": "在 Best of N 模式中使用完整 Git 克隆",
        "Open Agent on Reload": "窗口重载时打开智能体面板",
        "Inline Actions": "行内操作",
        "Enable Browser Tools": "启用浏览器工具",
        "Enable Notifications for Agent": "启用智能体通知",
        "Queue Wait": "队列等待",
        "Streaming Generation": "流式生成",
        "Time to First Token (TTFT)": "首字生成延迟 (TTFT)",
        "Context Summarization": "上下文总结",
        "User Intent Generation": "生成用户意图",
        "• Thinking duration:": "• 思考耗时:",
        "Thinking...": "思考中...",
        "Copy thinking": "复制思考过程",
        "Thought Process": "思考过程",
        "Queue until after the current turn.": "排队等待，在当前轮次结束后发送。",
        "Interrupt the agent and send immediately.": "立即打断智能体并发送消息。",
        "Queued Messages": "排队中的消息",
        "Queued messages": "排队中的消息",
        "Continue Response": "继续生成回复",
        "Split Conversation Vertically": "垂直分栏对话",
        "Split Conversation Horizontally": "水平分栏对话",
        "Find in Conversation": "在对话中查找",
        "Conversation copied as Markdown to clipboard": "对话已作为 Markdown 复制到剪贴板",
        "Copy Conversation Markdown": "复制对话为 Markdown",
        "Edit Conversation Title": "编辑对话标题",
        "Rename This Conversation": "重命名此对话",
        "Restore Conversation": "恢复此对话",
        "Archive This Conversation": "归档此对话",
        "Pinned Conversations": "已固定的对话",
        "Unpin This Conversation": "取消固定此对话",
        "Pin This Conversation": "固定此对话",
        "Parent Conversation": "父级对话",
        "Creating worktree for the forked conversation...": "正在为派生对话创建工作树 (worktree)...",
        "Creating the forked conversation...": "正在创建派生对话...",
        "Forked conversation": "已派生的对话",
        "Fork Conversation": "派生对话 (Fork)",
        "The conversation was compacted while generating this response.": "在生成此回复时对话已被压缩。",
        "The conversation was compacted to fit within the context window.": "对话已压缩以适应上下文窗口。",
        "Compacting": "正在压缩上下文",
        "Quote Selection": "引用选中文本",
        "Comment on Selection": "对选区添加批注",
        "Open with External Browser": "在外部浏览器中打开",
        "Open in Preview Tab": "在预览标签页中打开",
        "Open in Preview Pane": "在预览面板中打开",
        "No artifacts generated": "未生成任何产物",
        "Select text in the artifact to add a comment": "在产物中选中文本以添加批注",
        "Configure the default width of markdown artifacts.": "配置 Markdown 产物的默认显示宽度。",
        "Markdown Artifact Width": "Markdown 产物显示宽度",
        "Export artifact": "导出产物",
        "Export Artifact": "导出产物",
        "Global Artifact Viewer": "全局产物查看器",
        "Artifact Viewer": "产物查看器",
        "Artifact Name": "产物名称",
        "Artifact Comments": "产物批注",
        "Manually Rejected": "已手动拒绝",
        "Approve?": "是否批准？",
        "Approve this action": "批准此操作",
        "Reject all": "全部拒绝",
        "Reject Step": "拒绝步骤",
        "Accept Step": "接受此步骤更改",
        "Auto-proceeded with": "已自动继续执行",
        "Proceeded with": "已继续执行",
        "Proceed Anyway": "仍然继续执行",
        "Proceed with implementation plan": "按实施规划继续执行",
        "Proceed with Plan": "按规划继续执行",
        "Refresh custom agents": "刷新自定义智能体",
        "Select Agent": "选择智能体",
        "Autonomous Mode": "自主模式",
        "Browser Subagent Viewer": "浏览器子智能体查看器",
        "Cannot send message to subagent.": "无法向子智能体发送消息。",
        "This subagent was killed and can no longer be messaged.": "该子智能体已被强制终止，无法再向其发送消息。",
        "No subagents": "暂无子智能体",
        "Invoked subagent": "已调用子智能体",
        "Stop all subagents": "停止所有子智能体",
        "Expand subagents": "展开子智能体",
        "Collapse subagents": "折叠子智能体",
        "Child Subagents (": "子级智能体 (",
        "Take Snapshot": "生成快照",
        "View Snapshot": "查看快照",
        "Restore Snapshot": "恢复快照",
        "Workspace Snapshot": "工作区快照",
        "A full copy of this workspace, uncommitted changes included.": "此工作区的完整副本，包含未提交的更改。",
        "A copy of the workspace snapshot recorded at this step.": "在此步骤记录的工作区快照副本。",
        "Agent response": "智能体响应",
        "Agent permissions preset selector": "智能体权限预设选择器",
        "Agent options": "智能体选项",
        "Agent needs permission to execute JavaScript": "智能体需要执行 JavaScript 的权限",
        "Agent is analyzing videos": "智能体正在分析视频",
        "Agent finished": "智能体执行完毕",
        "Agent execution failed.": "智能体执行失败。",
        "Agent encountered an internal error.": "智能体遇到内部错误。",
        "Agent data is not available": "智能体数据不可用",
        "Agent cannot modify files outside of the workspace in strict mode.": "在严格模式下，智能体无法修改工作区外部的文件。",
        "Agent always asks for review.": "智能体在执行前始终请求评审。",
        "Agent Team": "智能体团队",
        "Auto-Run Next Step": "自动运行下一步",
        "Auto-Approve Commands": "自动批准命令",
        "Always Deny for Project": "在此项目中始终拒绝",
        "Always Allow for Project": "在此项目中始终允许",
        "Allow in Project": "在当前项目中允许",
        "Allow in Current Session": "仅在当前会话中允许",
        "All Changes Saved": "所有更改已保存",
        "Agent is ready for input": "智能体已就绪，等待输入",
        "Agent is actively working": "智能体正在工作中",
        "Agent will generate diffs": "智能体将生成代码差异",
        "A license or project selection is required to use Antigravity.": "使用 Antigravity 需要授权许可证或选择关联项目。",
        "A Google Cloud project is required to use Antigravity.": "使用 Antigravity 需要关联 Google Cloud 项目。",
        "Agent Stopped": "智能体已停止",
        "Agent Settings (For Project)": "智能体设置 (针对当前项目)",
        "Agent Settings": "智能体设置",
        "Agent Security Settings": "智能体安全设置",
        "Agent Script Command Configuration": "智能体脚本命令配置",
        "Agent Script": "智能体脚本",
        "Agent Platform": "智能体平台",
        "Agent Non-Workspace File Access": "智能体非工作区文件访问权限",
        "Agent Host Address": "智能体主机地址",
        "Agent Hooks Configuration": "智能体钩子 (Hooks) 配置",
        "Agent Edits": "智能体代码修改",
        "Agent Auto-Fix Lints": "智能体自动修复代码检查 (Lints)",
        "Advanced File Access": "高级文件访问权限",
        "Advanced Command Access": "高级命令执行权限",
        "Add MCP server": "添加 MCP 服务器",
        "Add MCP Server": "添加 MCP 服务器",
        "Close Saved": "关闭已保存项",
        "Close Others": "关闭其他",
        "Close All": "全部关闭",
        "Split Down": "向下分栏",
        "Split Right": "向右分栏",
        "Open in New Window": "在新窗口中打开",
        "Open Containing Folder": "打开所在文件夹",
        "Open in Terminal": "在终端中打开",
        "Reveal in File Explorer": "在文件资源管理器中显示",
        "Copy Relative Path": "复制相对路径",
        "Copy Path": "复制路径",
        "Copy Link": "复制链接",
        "Save and Close": "保存并关闭",
        "Reset to Default": "重置为默认值",
        "Clear All": "全部清除",
        "Discard All": "全部放弃",
        "Apply All": "全部应用",
        "Apply Changes": "应用更改",
        "Discard Changes": "放弃更改",
        "Keep Changes": "保留更改",
        "Reject Changes": "拒绝更改",
        "Confirm Changes": "确认更改",
        "Cancel Execution": "取消执行",
        "Add recent remote workspace": "添加最近的远程工作区",
        "Add MCP Servers": "添加 MCP 服务器",
        "A snapshot was saved before running. To restore your previous output:": "运行前已保存快照。如需恢复之前的输出：",
        "A shell setup script run before every command the agent executes.": "在智能体执行每条命令前运行的 Shell 初始化脚本。",
        "Actuation Permissions": "智能体执行权限",
        "Access a file outside workspace": "访问工作区外部的文件",
        "Add inline comment": "添加行内注释",
        "Add to Chat/Quote": "添加到对话引用",
        "Add to Chat": "添加到对话",
        "Add Workspace": "新建工作区",
        "Add Terminal": "新建终端",
        "A Gemini-powered security agent decides if commands should be auto-approved.": "由 Gemini 驱动的安全智能体负责判定命令是否可自动批准。",
        "A project with this name already exists.": "已存在同名项目。",
        "A new version is available.": "有新版本可用。",
        "Added to the model's instructions.": "已添加到模型的系统指令中。",
        "Active token streaming duration from the language model.": "大语言模型的 Token 流式生成持续时间。",
        "AI Credits Used to Generate Response": "本次生成消耗的 AI 额度",
        "Active Context Start": "活动上下文起点",
        "Active Skills": "已启用的技能",
        "Add context": "添加上下文",
        "Add Context": "添加上下文",
        "Add Model": "添加模型",
        "Add Custom Model": "添加自定义模型",
        "Trigger multiple response variants from the same prompt.": "根据同一提示词生成多个响应候选变体。",
        "Unsupported file format": "不支持的文件格式",
        "Unfold code block": "展开代码块",
        "Workspace folder suggestions": "工作区文件夹推荐",
        "Workflow files": "工作流文件",
        "Thank you! Your feedback has been submitted successfully.": "谢谢！您的反馈已成功提交。",
        "Thanks for your feedback!": "感谢您的反馈！",
        "View archived conversations in history.": "在历史记录中查看已归档的对话。",
        "View MCP settings": "查看 MCP 设置",
        "Upload to Agent": "上传给智能体",
        "Tool Calls": "工具调用列表",
        "Tool Call Ready": "工具调用已就绪",
        "Tab to Import": "按 Tab 键导入",
        "Switch IDE workspace": "切换 IDE 工作区",
        "Suggestions in Editor": "编辑器内代码补全建议",
        "System Prompt": "系统提示词",
        "Step Preview": "步骤预览",
        "Task Logs": "任务日志",
        "Task Log": "任务日志",
        "Strict Mode": "严格模式",
        "Terminal commands the agent can execute in this workspace.": "智能体可以在此工作区执行的终端命令。",
        "Terminal commands the agent can execute.": "智能体可以执行的终端命令。",
        "Terminal: Add to Chat": "终端：添加到对话",
        "Terminal Commands": "终端命令",
        "Terminal Command Auto Execution": "终端命令自动执行",
        "The agent auto-executes commands matched by an allow list entry.": "智能体会自动执行白名单匹配的命令。",
        "The agent always asks for review.": "智能体在执行前始终请求评审。",
        "The agent has encountered an internal error.": "智能体遇到了内部错误。",
        "The agent has questions for you:": "智能体向您提出了问题：",
        "The agent has a question for you:": "智能体向您提出了一个问题：",
        "The agent is waiting for your input.": "智能体正在等待您的输入。",
        "Team of subagents to do long running work": "用于执行长时间运行任务的子智能体团队",
        "View child subagents": "查看子智能体",
        "Stop subagent": "停止子智能体",
        "Stop Subagent": "停止子智能体",
        "Stop All Subagents": "停止所有子智能体",
        "Web Search": "网络搜索",
        "Run Commands": "运行终端命令",
        "Read Files": "读取文件",
        "Write Files": "写入文件",
        "Yes, save rule in this workspace": "是的，在此工作区保存规则",
        "Yes, and always allow in this workspace": "是的，在此工作区中始终允许",
        "Yes, I agree to help improve": "是的，我同意协助改进",
        "The background color of unchanged code in the diff editor.": "差异编辑器中未修改代码的背景色。",
        "The selection background color of the terminal.": "终端选中内容时的背景色。",
        "The foreground color of the terminal.": "终端文本的前景色。",
        "The foreground color of the terminal cursor.": "终端光标的前景色。",
        "Title bar foreground when the window is inactive.": "窗口处于非活动状态时的标题栏前景色。",
        "Title bar foreground when the window is active.": "窗口处于活动状态时的标题栏前景色。",
        "Title bar background when the window is inactive.": "窗口处于非活动状态时的标题栏背景色。",
        "Title bar background when the window is active.": "窗口处于活动状态时的标题栏背景色。",
        "This plugin is disabled. Enable it above to see what it contributes.": "此插件已禁用。请在上方启用以查看其提供的功能。",
        "This plugin does not add any slash commands.": "此插件未添加任何斜杠指令。",
        "When enabled, sandboxed commands are allowed to make network requests.": "启用后，沙箱命令将被允许发起网络请求。",
        "This command ran in the sandbox.": "此命令已在隔离沙箱中运行。",
        "This skill is installed in your workspace": "此技能已安装在您的工作区中",
        "Unnamed skill": "未命名技能",
        "Unnamed agent": "未命名智能体",
        "Unnamed MCP server": "未命名 MCP 服务器",
        "Unnamed MCP Server": "未命名 MCP 服务器",
        "Unnamed Agent": "未命名智能体",
        "UI extensions": "UI 界面扩展",
        "UI Plugins": "UI 插件",
        "UI Extensions": "UI 界面扩展",
        "Workspaces are not available for this project": "此项目暂无可用工作区",
        "Workspace setup warning": "工作区配置警告",
        "Workspace name cannot be empty": "工作区名称不能为空",
        "Workspace icon": "工作区图标",
        "Workspace archived successfully": "工作区已成功归档",
        "Workspace Actions": "工作区操作",
        "Workspace File Access": "工作区文件读写权限",
        "Workspace Command Access": "工作区终端命令权限",
        "Workspace Web Access": "工作区网络访问权限",
        "Workspace File Explorer": "工作区文件浏览器",
        "Workspace Name": "工作区名称",
        "Workspace Settings": "工作区设置",
        "Updating will restart the server and apply the latest changes.": "更新将重启服务并应用最新更改。",
        "Update Anyway": "仍然更新",
        "Update Available": "有可用更新",
        "User cancelled agent execution.": "用户已取消智能体执行。",
        "Too many requests, please try again in a bit!": "请求过于频繁，请稍后再试！",
        "Your AI credits balance is too low to continue.": "您的 AI 额度余额过低，无法继续。",
        "Your quota for this model is running low.": "该模型的配额即将用尽。",
        "Search everywhere": "全局搜索",
        "Search files by name": "按文件名搜索",
        "Type to search...": "输入关键词进行搜索...",
        "Type to search for code across your workspace.": "输入以在当前工作区全局搜索代码。",
        "Toggle Terminal": "切换终端",
        "Toggle Project Selector": "切换项目选择器",
        "Toggle Model Selector": "切换模型选择器",
        "Toggle File Viewer": "切换文件查看器",
        "Toggle Editor": "切换编辑器",
        "Virtual File Viewer": "虚拟文件查看器",
        "Virtual File": "虚拟文件",
        "Web Preview": "网页预览",
        "View plans": "查看规划",
        "View network requests": "查看所有网络请求",
        "View network request": "查看网络请求",
        "View documentation": "查看文档",
        "View Debug": "查看调试信息",
        "View Page": "查看页面",
        "View Usage": "查看配额用量",
        "View Logs": "查看日志",
        "View File": "查看文件",
        "View Stacked Diff": "堆叠查看代码差异",
        "View Split Diff": "分栏查看代码差异",
        "Viewing Diff": "正在查看代码差异",
        "View Diff": "查看差异",
        "Fast research": "快速检索",
        "Thorough research": "深度研究",
        "Tools": "工具",
        "Tool Defs": "工具定义",
        "Tool arguments": "工具参数",
        "Tool Output": "工具输出",
        "Tool Execution": "工具执行",
        "Tool Call Generation": "工具调用生成",
        "Tool Call Gen": "生成工具调用",
        "Used MCP tool": "已使用 MCP 工具",
        "Used tool": "已使用工具",
        "This chat is archived.": "此对话已归档。",
        "Untitled chat": "未命名对话",
        "Thinking": "思考中",
        "Thinking for": "思考时间",
        # Navigation / Sidebars
        'label:"New Conversation"': 'label:"新建对话"',
        'label:"Create Project"': 'label:"创建项目"',
        'label:"Command Palette"': 'label:"命令面板"',
        'label:"Toggle Fullscreen"': 'label:"切换全屏"',
        'label:"Zoom In"': 'label:"放大"',
        'label:"Zoom Out"': 'label:"缩小"',
        'label:"Reset Zoom"': 'label:"重置缩放"',
        'label:"Toggle Developer Tools"': 'label:"开发者工具"',
        'label:"Minimize"': 'label:"最小化"',
        'label:"Maximize"': 'label:"最大化"',
        'label:"Close"': 'label:"关闭"',
        'label:"About"': 'label:"关于"',
        'label:"Check for Updates"': 'label:"检查更新"',
        
        'title:"File"': 'title:"文件"',
        'title:"View"': 'title:"视图"',
        'title:"Window"': 'title:"窗口"',
        
        # Sidebar section labels
        '"New Conversation"': '"新建对话"',
        '"Scheduled Tasks"': '"计划任务"',
        '"Conversation History"': '"历史对话"',
        '"Projects"': '"项目"',
        '"No conversations yet"': '"暂无历史对话"',
        '"Settings"': '"设置"',
        
        # Chat input placeholder
        '"Ask anything, @ to mention"': '"问任何问题，输入 @ 提及"',
        '", / for actions"': '"，输入 / 执行操作"',
        'aria-label:"Message input"': 'aria-label:"消息输入框"',
        
        # Settings Screens
        '"Project General"': '"项目常规"',
        '"Project Folders"': '"项目文件夹"',
        '"Project Agent"': '"项目智能体"',
        'title:"Account"': 'title:"账户"',
        'label:"Account"': 'label:"账户"',
        'title:"Google Drive"': 'title:"谷歌云端硬盘"',
        'label:"Google Drive"': 'label:"谷歌云端硬盘"',
        'title:"General"': 'title:"通用"',
        'label:"General"': 'label:"通用"',
        'title:"Appearance"': 'title:"外观"',
        'label:"Appearance"': 'label:"外观"',
        '"Chat Settings"': '"聊天设置"',
        '"Verbose agent chat"': '"详细智能体对话"',
        '"Display and preserve intermediate thinking steps"': '"显示并保留中间思考步骤"',
        '"Configure the agent\'s visual theme and display preferences."': '"配置智能体的视觉主题和显示偏好。"',
        '"Select light, dark, or inherit system settings."': '"选择浅色、深色或跟随系统设置。"',
        '"Light Theme"': '"浅色主题"',
        '"Dark Theme"': '"深色主题"',
        '"Preset"': '"预设"',
        '"Default Light"': '"默认浅色"',
        '"Default Dark"': '"默认深色"',
        '"Background"': '"背景"',
        '"Foreground"': '"前景"',
        '"Accent"': '"强调色"',
        'title:"Models"': 'title:"模型"',
        'label:"Models"': 'label:"模型"',
        'title:"Customizations"': 'title:"自定义"',
        'label:"Customizations"': 'label:"自定义"',
        'title:"Browser"': 'title:"浏览器"',
        'label:"Browser"': 'label:"浏览器"',
        'title:"App"': 'title:"应用"',
        'label:"App"': 'label:"应用"',
        'title:"Permissions"': 'title:"权限"',
        'label:"Permissions"': 'label:"权限"',
        'title:"Notifications"': 'title:"通知"',
        'label:"Notifications"': 'label:"通知"',
        'title:"Editor"': 'title:"编辑器"',
        'label:"Editor"': 'label:"编辑器"',
        'title:"Tab"': 'title:"Tab"',
        'label:"Tab"': 'label:"Tab"',
        '"Best of N"': '"Best of N"',
        '"Browser Settings"': '"浏览器设置"',
        '"App Settings"': '"应用设置"',
        '"Manage application settings."': '"管理应用设置。"',
        '"Configure settings for Best of N mode."': '"配置 Best of N 模式的相关设置。"',
        '"Best of N Settings"': '"Best of N 设置"',
        '"Shortcuts"': '"快捷键"',
        '"Provide Feedback"': '"提供反馈"',
        '"Notification Settings"': '"通知设置"',
        '"Open System Preferences"': '"打开系统设置"',
        '"Keyboard shortcuts for quick navigation and control."': '"用于快速导航和控制的键盘快捷键。"',
        '"RECOMMENDED"': '"推荐"',
        '"Open Conversation Picker"': '"打开对话选择器"',
        '"Open File Search"': '"打开文件搜索"',
        '"Focus Input"': '"聚焦输入框"',
        '"Go Back"': '"返回"',
        '"Go Forward"': '"前进"',
        '"File Picker"': '"文件选择器"',
        '"Select Previous Conversation"': '"选择上一个对话"',
        '"Select Next Conversation"': '"选择下一个对话"',
        '"CONVERSATION"': '"对话"',
        '"LAYOUT CONTROLS"': '"布局控制"',
        '"Toggle Model Selector"': '"切换模型选择器"',
        '"Toggle Voice Recording"': '"切换语音录制"',
        '"Find in Pane"': '"在面板中查找"',
        '"Toggle Sidebar"': '"切换侧边栏"',
        '"Toggle Auxiliary Pane"': '"切换辅助面板"',
        '"Enable Telemetry"': '"启用遥测"',
        '"Marketing Emails"': '"营销邮件"',
        '"Your Plan:"': '"当前套餐："',
        '"Upgrade"': '"升级"',
        '"Sign Out"': '"退出登录"',
        '"Email"': '"邮箱"',
        '"Terms of Service"': '"服务条款"',
        'title:"Projects"': 'title:"项目"',
        'label:"Projects"': 'label:"项目"',
        'title:"Conversations"': 'title:"对话"',
        'label:"Conversations"': 'label:"对话"',
        '"Not in Project"': '"未归属项目"',
        '"Workspaces"': '"工作区"',
        '"Show all"': '"显示全部"',
        '"Theme"': '"主题"',
        '"Keyboard Shortcuts"': '"快捷键"',
        '"Permissions"': '"权限"',
        '"No project selected or project management not available."': '"未选择项目，或项目管理不可用。"',
        '"Open Settings"': '"打开设置"',
        '"Open Keyboard Shortcuts"': '"打开快捷键列表"',
        '"No agents running"': '"当前没有运行中的智能体"',
        '"Folders"': '"文件夹"',
        '"Add Folder"': '"添加文件夹"',
        '"Agent Settings"': '"智能体设置"',
        '"Security Preset"': '"安全预设"',
        '"Unrestricted"': '"无限制"',
        '"Agent Behavior"': '"智能体行为"',
        '"Artifact Review Policy"': '"产物评审策略"',
        '"Local Permissions"': '"本地权限"',
        '"File Access Rules"': '"文件访问规则"',
        '"Network Access Rules"': '"网络访问规则"',
        '"MCP Tools"': '"MCP 工具"',
        '"Danger Zone"': '"危险区域"',
        '"Delete Project"': '"删除项目"',
        '"Open"': '"打开"',

        # --- 新增的 2.2.1 词条 (Conversations / Permissions / Models) ---
        '"Always Ask"': '"始终询问"',
        '"Require Review"': '"需要评审"',
        '"Custom"': '"自定义"',
        '"Allow"': '"允许"',
        '"Enable Sandbox Mode (Preview)"': '"启用沙箱模式（预览）"',
        '"Restrict agent tools to a secure, isolated local sandbox."': '"将智能体工具限制在安全、隔离的本地沙箱中。"',
        '"Specifies Agent\'s behavior when asking for review on artifacts, which are rich documents created by the agent to provide a better conversational experience."': '"指定智能体在请求评审产物时的行为。产物是它为提供更丰富对话体验而创建的文档。"',
        '"Enable AI Credit Overages"': '"启用 AI 额度超支"',
        '"When toggled on, Antigravity will use your AI credits to fulfill model requests once you\'re out of model quota. Antigravity will always use your model quota first before using AI credits."': '"开启后，当模型配额耗尽时，Antigravity 将使用您的 AI 额度处理模型请求。Antigravity 将始终优先使用模型配额。"',
        '"Model Quota"': '"模型配额"',
        '"Within each group, models share a weekly limit and a 5-hour limit. Quota is consumed proportionally to the cost of the tokens. Thus, limits will last longer with shorter tasks or using more cost-effective models. The 5-hour limit smooths out aggregate demand to fairly distribute global capacity across all users, while your weekly limit is tied directly to your individual tier."': '"在每个组中，模型共享周限额和 5 小时限额。配额消耗与 Token 成本成正比。因此，任务越短或使用更划算的模型，限额持续的时间就越长。5 小时限额有助于平滑总体需求以在所有用户之间公平分配容量，而您的周限额则直接与您的套餐等级挂钩。"',
        '"Gemini Models"': '"Gemini 模型"',
        '"Weekly Limit"': '"周限额"',
        '"Five Hour Limit"': '"5小时限额"',
        '"Claude and GPT models"': '"Claude 和 GPT 模型"',
        '"Agent settings and permissions for conversations outside of projects."': '"项目外对话的智能体设置和权限。"',
        '"Choose a predefined security preset for the agent. This controls terminal auto-execution policy, and file access policy."': '"为智能体选择预定义的安全预设。它会控制终端自动执行策略和文件访问策略。"',
        '"Outside of Folders File Access Policy"': '"外部文件夹文件访问策略"',
        '"Configures how the agent tries to access files outside of its working folders."': '"配置智能体尝试访问其工作文件夹以外文件的方式。"',
        '"Terminal Command Auto Execution"': '"终端命令自动执行"',
        '"Controls whether terminal commands require your approval before running."': '"控制终端命令在执行前是否需要你的批准。"',

        '"Learn more about Unrestricted"': '"了解更多关于“无限制”"',
        '"Learn more about "': '"了解更多关于 "',
        '"Rules"': '"规则"',
        '"Show 1 breakdown"': '"显示 1 项明细"',
        '"Terminal Commands"': '"终端命令"',
        '"Commands Outside Sandbox"': '"沙箱外命令"',
        '"Global"': '"全局"',
        '"File Reads"': '"文件读取"',
        '"File Writes"': '"文件写入"',
        '"Read URLs"': '"读取 URL"',
        '"Skills"': '"技能"',
        '"Custom"': '"自定义"',
        '"Hide breakdown"': '"隐藏明细"',
        '"No customizations found for this workspace."': '"当前工作区未找到任何自定义内容。"',
        '"Learn more about Unrestricted"': '"了解更多关于无限制"',
        '"user_global"': '"用户全局"',
        '"Suggestions"': '"建议"',
        '"Navigation"': '"导航"',
        '"Context"': '"上下文"',
        '"Advanced"': '"高级"',
        '"Quota"': '"配额"',
        '"Default Customizations"': '"默认自定义"',
        '"Customize Global Skills"': '"自定义全局技能"',
        '"Custom Agents"': '"自定义智能体"',
        '"MCP Servers"': '"MCP 服务器"',
        '"Actuation Permissions"': '"执行权限"',
        '"Browser Actuation Rules"': '"浏览器执行规则"',
        '"Configure allowed and denied URLs for browser actuation."': '"配置浏览器执行时允许和拒绝的 URL。"',
        '"Edit"': '"编辑"',
        '"Add"': '"添加"',
        '"Delete command"': '"删除命令"',
        '"Remove"': '"移除"',
        '"Cancel"': '"取消"',

        # Settings labels / descriptions
        '"Allow List Terminal Commands"': '"允许列表终端命令"',
        '"Deny List Terminal Commands"': '"拒绝列表终端命令"',
        '"Agent Auto-Fix Lints"': '"智能体自动修复 Lint"',
        '"Enable Workspace API"': '"启用 Workspace API"',
        '"Confirm Window Reload"': '"确认窗口重载"',
        '"Enable Demo Mode (Beta)"': '"启用演示模式（Beta）"',
        '"Explain and Fix in Current Conversation"': '"在当前对话中解释并修复"',
        '"Strict Mode"': '"严格模式"',
        '"Agent Non-Workspace File Access"': '"智能体访问工作区外文件"',
        '"Enable Terminal Sandbox"': '"启用终端沙箱"',
        '"Sandbox Allow Network"': '"沙箱允许网络"',
        '"Enable Shell Integration"': '"启用 Shell 集成"',
        '"Terminal Command Auto Execution"': '"终端命令自动执行"',
        '"Agent Host Address"': '"智能体主机地址"',
        '"Review Policy"': '"评审策略"',
        '"Enable Sounds for Agent"': '"为智能体启用提示音"',
        '"Auto-Expand Changes Overview"': '"自动展开变更概览"',
        '"Conversation History"': '"历史对话"',
        '"Knowledge"': '"知识库"',
        '"Auto-Open Edited Files"': '"自动打开已编辑文件"',
        '"Open Agent on Reload"': '"重载时打开智能体"',
        '"Suggestions in Editor"': '"编辑器内建议"',
        '"Tab to Jump"': '"Tab 跳转"',
        '"Tab to Import"': '"Tab 导入"',
        '"Tab Speed"': '"Tab 速度"',
        '"Highlight After Accept"': '"接受后高亮"',
        '"Tab Gitignore Access"': '"Tab 访问 .gitignore"',
        '"Browser Javascript Execution Policy"': '"浏览器 JavaScript 执行策略"',
        '"Chrome Binary Path"': '"Chrome 可执行文件路径"',
        '"Browser User Profile Path"': '"浏览器用户配置路径"',
        '"Browser CDP Port"': '"浏览器 CDP 端口"',
        '"Show Selection Actions"': '"显示选区操作"',
        '"Include Jetski Default Customizations"': '"包含 Jetski 默认自定义"',
        '"Prevent Sleep"': '"防止休眠"',
        '"Keep In Menu Bar"': '"保持在菜单栏中"',
        '"Enable Remote Control"': '"启用远程控制"',
        '"Disabled"': '"禁用"',
        '"Request Review"': '"请求评审"',
        '"Always Proceed"': '"始终继续"',
        '"Proceed in Sandbox"': '"在沙箱中继续"',
        '"Fast"': '"快速"',
        '"Slow"': '"慢速"',
        '"Terminal"': '"终端"',
        '"File Access"': '"文件访问"',
        '"Automation"': '"自动化"',
        '"History"': '"历史"',
        '"Sandboxed"': '"沙箱模式"',
        '"Strict"': '"严格模式"',
        '"Enabled"': '"已启用"',
        '"Value:"': '"值："',

        # Settings descriptions
        '"When enabled, Agent can interact with Google Workspace through the API to search and read documents."': '"启用后，智能体可以通过 API 与 Google Workspace 交互，搜索并读取文档。"',
        '"Toggle if a confirmation is shown when using the "Reload Window" button."': '"控制使用“重载窗口”按钮时是否显示确认提示。"',
        '"When enabled, "Explain and Fix" actions will continue in the current conversation instead of starting a new one."': '"启用后，“解释并修复”操作会在当前对话中继续，而不是新建对话。"',
        '"When enabled, terminal commands run with sandbox restrictions."': '"启用后，终端命令将在沙箱限制下运行。"',
        '"When enabled, sandboxed commands are allowed to make network requests."': '"启用后，沙箱中的命令可以发起网络请求。"',
        '"When enabled, Agent will use IDE\'s shell integration to detect and report terminal command execution. When disabled, the agent will use its own shell. Restart the application for this to take effect."': '"启用后，智能体会使用 IDE 的 Shell 集成来检测并报告终端命令执行情况。禁用后，智能体将使用自己的 Shell。重新启动应用后生效。"',
        '"When enabled, Agent will use IDE\'s shell integration to detect and report terminal command execution."': '"启用后，智能体会使用 IDE 的 Shell 集成来检测并报告终端命令执行情况。"',
        '"When enabled, Agent is given awareness of lint errors created by its edits and may fix them without explicit user prompting."': '"启用后，智能体会感知自身编辑产生的 Lint 错误，并可在无需明确提示的情况下修复。"',
        '"When enabled, the agent will be able to access past conversations to inform its responses."': '"启用后，智能体可以访问历史对话来辅助生成回复。"',
        '"Open files in the background if Agent creates or edits them"': '"当智能体创建或编辑文件时，在后台自动打开这些文件。"',
        '"To modify notification settings, open your operating system\'s system preferences."': '"若要修改通知设置，请打开操作系统的系统设置。"',
        '"Manage your plan, credentials, and general preferences."': '"管理你的套餐、凭据和通用偏好设置。"',
        '"When toggled on, Antigravity collects usage data to help Google enhance performance and features."': '"开启后，Antigravity 会收集使用数据，以帮助 Google 改进性能和功能。"',
        '"Receive product updates, tips, and promotions from Google Antigravity via email."': '"通过电子邮件接收来自 Google Antigravity 的产品更新、技巧和推广信息。"',
        '"You can upgrade to a Google AI Ultra plan to receive the highest rate limits."': '"你可以升级到 Google AI Ultra 套餐，以获得最高的速率限制。"',
        '"By using this app, you agree to its"': '"使用此应用即表示你同意其"',
        '"Open Agent panel on window reload"': '"窗口重载时打开智能体面板。"',
        '"Allows the agent to access files outside of your current workspace."': '"允许智能体访问当前工作区之外的文件。"',
        '"Agent cannot modify files outside of the workspace in strict mode."': '"在严格模式下，智能体无法修改工作区之外的文件。"',
        '"Agent will always ask to review in strict mode."': '"在严格模式下，智能体始终会请求评审。"',
        '"Show suggestions when typing in the editor."': '"在编辑器输入时显示建议。"',
        '"Quickly add and update imports with a tab keypress."': '"通过按下 Tab 键快速添加和更新导入。"',
        '"Set the speed of tab suggestions"': '"设置 Tab 建议的显示速度。"',
        '"Highlight newly inserted text after accepting a Tab completion."': '"接受 Tab 补全后高亮新插入的文本。"',
        '"Controls whether the agent can run custom JavaScript to automate complex browser actions."': '"控制智能体是否可以运行自定义 JavaScript 来自动化复杂的浏览器操作。"',
        '"Path to the Chrome/Chromium executable. Leave empty for auto-detection."': '"Chrome/Chromium 可执行文件路径。留空则自动检测。"',
        '"Custom path for the browser user profile directory. Leave empty for default (~/.gemini/antigravity-browser-profile)."': '"浏览器用户配置目录的自定义路径。留空则使用默认值（~/.gemini/antigravity-browser-profile）。"',
        '"Port number for Chrome DevTools Protocol remote debugging. Leave empty for default (9222)."': '"Chrome DevTools Protocol 远程调试端口。留空则使用默认值（9222）。"',
        '"Show "Edit" and "Chat" buttons when selecting text in the editor."': '"在编辑器中选中文本时显示“编辑”和“聊天”按钮。"',
        '"When enabled, the agent will include default customizations, including default skills."': '"启用后，智能体会包含默认自定义内容，包括默认技能。"',
        '"Prevent the computer from sleeping while the app is running."': '"在应用运行期间阻止计算机进入睡眠。"',
        '"The app will be accessible from the menu bar and will keep running in the background when all windows are closed."': '"应用可从菜单栏访问，并会在所有窗口关闭后继续在后台运行。"',
        '"If enabled, you can manage your conversations from the Antigravity website. Please reload the application to apply this setting."': '"启用后，你可以在 Antigravity 网站上管理对话。请重新加载应用以使设置生效。"',
        '"Configure the browser subagent. It requires"': '"配置浏览器子智能体。它需要"',
        '"to be installed. The browser subagent can be invoked by typing /browser in the conversation input box."': '"已安装。可在对话输入框中输入 /browser 来调用浏览器子智能体。"',
        '"No permissions configured."': '"尚未配置任何权限。"',
        '"Controls whether terminal commands require your approval before running."': '"控制终端命令在执行前是否需要你的批准。"',
        '"Restricts agent tools to a secure, isolated local sandbox."': '"将智能体工具限制在安全、隔离的本地沙箱中。"',
        '"Agents run in a secure sandbox that restricts access to external resources outside of your trusted folders."': '"智能体会在安全沙箱中运行，限制其访问受信任文件夹之外的外部资源。"',
        '"Terminal commands always require review and the agent cannot access files outside of its given workspaces."': '"终端命令始终需要评审，且智能体无法访问其指定工作区之外的文件。"',
        '"Execute URLs"': '"执行 URL"',
        '"Allow/deny agent browser actuation access to specific URLs."': '"允许或拒绝智能体对特定 URL 执行浏览器操作。"',
        '"Allow/deny agent read access to specific files or directories."': '"允许或拒绝智能体读取特定文件或目录。"',
        '"Allow/deny agent write access to specific files or directories."': '"允许或拒绝智能体写入特定文件或目录。"',
        '"Allow/deny agent read access to specific URLs or domains."': '"允许或拒绝智能体读取特定 URL 或域名。"',
        '"Allow/deny specific terminal commands."': '"允许或拒绝特定终端命令。"',
        '"Allow/deny agent command execution outside the sandbox."': '"允许或拒绝智能体在沙箱外执行命令。"',
        '"External tools the agent can call via Model Context Protocol."': '"智能体可通过 Model Context Protocol 调用的外部工具。"',
        '"e.g., /path/to/file"': '"例如：/path/to/file"',
        '"e.g., https://example.com"': '"例如：https://example.com"',
        '"e.g., npm test"': '"例如：npm test"',
        '"e.g., curl"': '"例如：curl"',
        '"Enter tool name or server..."': '"输入工具名称或服务器..."',
        '"Inherits from"': '"继承自"',
        '"global settings"': '"全局设置"',
        '". Local permissions have higher priority."': '"。本地权限具有更高优先级。"',
        '"Learn more about"': '"了解更多关于"',
        '"Manage project folders, agent settings, and permissions."': '"管理项目文件夹、智能体设置和权限。"',
        '"Choose a predefined security preset for the agent. This controls terminal auto-execution policy, and file access policy."': '"为智能体选择预定义的安全预设。它会控制终端自动执行策略和文件访问策略。"',
        '"Specifies Agent\'s behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience."': '"指定智能体在请求评审产物时的行为。产物是它为提供更丰富对话体验而创建的文档。"',
        '"Inherits from global settings. Local permissions have higher priority. Learn more."': '"继承全局设置。本地权限具有更高优先级。了解更多。"',
        '"Inherits from global settings. Local permissions have higher priority. "': '"继承全局设置。本地权限具有更高优先级。"',
        '"Learn more."': '"了解更多。"',
        '"Configure allowed and denied paths for file reads and writes."': '"配置文件读写时允许和拒绝的路径。"',
        '"Configure allowed and denied URLs for reading."': '"配置读取时允许和拒绝的 URL。"',
        '"Configure allowed terminal commands."': '"配置允许的终端命令。"',
        '"Configure allowed commands outside the sandbox."': '"配置沙箱外允许执行的命令。"',
        '"Configure external tools via Model Context Protocol."': '"通过 Model Context Protocol 配置外部工具。"',
        '"The breakdown below shows token usage from customizations like skills, rules, and MCP. If the budget is exceeded, large customizations will be truncated automatically."': '"下方明细显示技能、规则、MCP 等自定义内容的 token 使用情况。如果超出预算，较大的自定义内容会被自动截断。"',
        '"of the customization budget is available."': '"的自定义预算仍可用。"',
        '"The customization budget is available."': '"自定义预算仍可用。"',
        '"Permanently delete this project and all of its conversations."': '"永久删除该项目及其所有对话。"',

        # Project Initializer Dialog
        '"Getting started with a Project"': '"项目入门指南"',
        '"Now that you\'ve created a project, configure your project\'s agent settings or start a conversation."': '"项目创建成功！现在可以配置项目智能体设置，或者直接开始对话。"',
        '"Learn more"': '"了解更多"',
        '"Learn More"': '"了解更多"',
        
        # Buttons & Actions
        '"Submit"': '"提交"',
        '"Continue"': '"继续"',
        '"Cancel"': '"取消"',
        '"Quit"': '"退出"',
        '"Approve"': '"批准"',
        '"Reject"': '"拒绝"',
        '"Allow"': '"允许"',
        '"Deny"': '"拒绝"',
        
        # Agent execution statuses
        '"Completed"': '"已完成"',
        '"Task"': '"任务"',
        '"running"': '"运行中"',
        '"Running"': '"运行中"',
        '"completed"': '"已完成"',
        '"Approved"': '"已批准"',
        '"Requested change"': '"请求变更"',
        '"Denied"': '"已拒绝"',
        
        # Header / Status titles
        '"Action Required"': '"需要操作"',
        '"Completed Operations"': '"已完成操作"',
        '"Walkthrough"': '"任务演练"',
        '"Review"': '"评审"',
        '"Wait"': '"等待"',
        'Learn more about ': '了解更多关于 ',
        'Inherits from global settings. Local permissions have higher priority. ': '继承全局设置。本地权限具有更高优先级。',
        'of the customization budget is available.': '的自定义预算仍可用。',
        'Rules\n(1.6%)': '规则\n(1.6%)',
        'Show 1 breakdown': '显示 1 项明细',
        'Learn more about Unrestricted': '了解更多关于无限制',
        'Learn more about 无限制': '了解更多关于无限制',
        'Inherits from global settings. Local permissions have higher priority. 了解更多.': '继承全局设置。本地权限具有更高优先级。了解更多。',
        '"Agent settings and permissions for conversations outside of projects."': '"项目外对话的智能体设置和权限。"',
        '"Outside of Folders File Access Policy"': '"文件夹外部文件访问策略"',
        '"Configures how the agent tries to access files outside of its working folders."': '"配置智能体尝试访问其工作文件夹以外文件的方式。"',
        '"Agent security mode"': '"智能体安全模式"',
        '"Select one of the "': '"选择 "',
        '" options. Agent settings and permissions can be further customized below."': '" 个选项之一。智能体设置和权限可在下方进一步自定义。"',
    }
    
    print("Applying translations...")
    replaced_count = 0
    literal_pattern = re.compile(r"""^(["']).*\1$""")

    for original, translated in translations.items():
        replaced = False
        if literal_pattern.match(original) and literal_pattern.match(translated):
            content, replaced = apply_safe_literal_replacement(content, original, translated)
        else:
            if original in content:
                content = content.replace(original, translated)
                replaced = True
            else:
                alt_original = original.replace('"', "'")
                alt_translated = translated.replace('"', "'")
                if alt_original in content:
                    content = content.replace(alt_original, alt_translated)
                    replaced = True

        if replaced:
            replaced_count += 1
            
    print(f"Replaced {replaced_count} of {len(translations)} strings.")
    
    # ---------------- 注入全局动态 DOM 翻译拦截器 ----------------
    dom_translator_js = r"""
// 注入动态 DOM 汉化引擎 (针对 React 深度封装无法静态替换的长句与危险短词)
(function() {
  const dynamicDict = {
    "General": "通用",
    "Account": "账户",
    "Appearance": "外观",
    "Models": "模型",
    "Customizations": "自定义",
    "Browser": "浏览器",
    "App": "应用",
    "Conversations": "对话",
    "Always Ask": "始终询问",
    "Require Review": "需要评审",
    "Custom": "自定义",
    "Allow": "允许",
    "Turbo Mode": "急速模式",
    "Default": "默认",
    "Full machine": "完全访问",
    "Turbo mode": "急速模式",
    "Disables all safety barriers for maximal iteration velocity.": "禁用所有安全屏障以获得最快的迭代速度。",
    "All terminal commands require review. The agent can read or write to any file in the machine.": "所有终端命令都需要手动评审。智能体可读取或写入设备上的任何文件。",
    "Requires manual review for all terminal commands and file accesses outside of the working folders.": "对工作文件夹以外的所有终端命令和文件访问需要手动评审。",
    "Enable Sandbox Mode (Preview)": "启用沙箱模式（预览）",
    "Restrict agent tools to a secure, isolated local sandbox.": "将智能体工具限制在安全、隔离的本地沙箱中。",
    "Agent Behavior": "智能体行为",
    "Artifact Review Policy": "产物评审策略",
    "Specifies Agent's behavior when asking for review on artifacts, which are rich documents created by the agent to provide a better conversational experience.": "指定智能体在请求评审产物时的行为。产物是它为提供更丰富对话体验而创建的文档。",
    "Local Permissions": "本地权限",
    "Enable AI Credit Overages": "启用 AI 额度超支",
    "Model Quota": "模型配额",
    "Gemini Models": "Gemini 模型",
    "Weekly Limit": "周限额",
    "Five Hour Limit": "5小时限额",
    "Claude and GPT models": "Claude 和 GPT 模型",
    "Plan": "套餐",
    "Your Plan: Google AI Pro": "当前套餐: Google AI Pro",
    "You can upgrade to a Google AI Ultra plan to receive higher rate limits.": "您可以升级到 Google AI Ultra 套餐以获得更高的速率限制。",
    "Model Credits": "模型信用点",
    "Refresh": "刷新",
    "Token Usage": "Token 使用情况",
    "Manually customize individual settings.": "手动自定义各项设置。",
    "Installed MCP Servers": "已安装的 MCP 服务器",
    "Add MCP +": "添加 MCP +",
    "No MCP Servers": "暂无 MCP 服务器",
    "You currently don't have any MCP Servers installed. Add an MCP server above": "您当前未安装任何 MCP 服务器。请在上方添加 MCP 服务器。",
    "Build With Google Plugins": "使用 Google 插件构建",
    "Customize": "自定义",
    "Configure default behaviors, skills, and MCP servers.": "配置默认行为、技能和 MCP 服务器。",
    "to be installed. The browser subagent can be invoked by typing /browser in the conversation input box.": "才能运行。可以在对话输入框中输入 /browser 来调用浏览器子智能体。",
    "Build with Antigravity Plugins": "使用 Antigravity 插件构建",
    "Plugins are packaged collections of skills and MCPs to help the Agent in Antigravity work with Google developer products. You can always change your choices in Settings.": "插件是技能和 MCP 的打包集合，可帮助智能体更好地使用相关开发者产品。您随时可以在设置中更改选择。",
    "Core tools and knowledge required to develop for Android": "Android 开发所需的核心工具和知识",
    "Download": "下载",
    "Modern Web Guidance": "现代 Web 开发指南",
    "Keep your coding agent up to date with the latest web best practices.": "让您的编程智能体掌握最新的 Web 最佳实践。",
    "Delete": "删除",
    "Using the Antigravity Python SDK to build AI agents": "使用 Antigravity Python SDK 构建 AI 智能体",
    "Science": "科学与研究",
    "Curated collection of agent skills for science.": "为科学研究精选的智能体技能集合。",
    "Prototype, build & run modern apps users love with Firebase's backend, AI, and operational infrastructure.": "使用 Firebase 的后端、AI 和基础设施来构建并运行现代应用。",
    "Reliable automation, in-depth debugging, and performance analysis in Chrome": "在 Chrome 中进行可靠的自动化、深入的调试和性能分析",
    "When toggled on, Antigravity collects usage data to help Google enhance performance and features.": "开启后，系统会收集使用数据，以帮助提升性能和功能。",
    "Receive product updates, tips, and promotions from Google Antigravity via email.": "通过电子邮件接收产品更新、提示和促销信息。",
    "Verbose Agent Chat": "详细的思考过程",
    "Display and preserve intermediate thinking steps.": "显示并保留智能体的中间思考步骤。",
    "Conversation Width": "对话框宽度",
    "Configure the maximum width of the conversation panel.": "配置对话面板的最大显示宽度。",
    "System": "跟随系统",
    "Light": "浅色主题",
    "Dark": "深色主题",
    "Shortcuts": "快捷键",
    "Keyboard Shortcuts": "键盘快捷键",
    "Submit Feedback": "提交反馈",
    "Send Feedback": "发送反馈",
    "Check for Updates": "检查更新",
    "About": "关于",
    "Clear Chat": "清除对话",
    "Delete Chat": "删除对话",
    "Back": "返回",
    "Browser Actuation Permissions": "浏览器执行权限",
    "Terminal Command Permissions": "终端命令规则",
    "Network Access Permissions": "网络访问规则",
    "File Access Permissions": "文件访问规则",
    "Sandbox Execution Permissions": "沙箱外执行规则",
    "allow": "允许",
    "ask": "询问",
    "deny": "拒绝",
    "Allow": "允许",
    "Ask": "询问",
    "Deny": "拒绝",
    "Add": "添加",
    "Notifications": "通知",
    "Advanced Settings": "高级设置",
    "Automatic Check for Updates": "自动检查更新",
    "When enabled, you will be automatically prompted to restart the app when there is a new update available. When disabled, you can check for updates manually from the app menu.": "启用后，当有新更新可用时，将自动提示您重启应用。禁用时，您可以从应用菜单中手动检查更新。"
  ,
    "Pin Conversation": "固定对话",
    "Ask a quick question without interrupting the main conversation.": "在不中断主对话的情况下快速提问。",
    "Run until the specified goal is completely finished.": "运行直至指定目标完全完成。",
    "Run an instruction on a recurring schedule or as a one-time timer.": "按照循环计划或作为一次性定时器运行指令。",
    "Invoke a browser agent for web tasks.": "启动浏览器智能体处理网页任务。",
    "Interview me to align on a plan.": "采访我以对齐计划。",
    "Invoke a team of agents to autonomously tackle large projects.": "启动智能体团队自主处理大型项目。",
    "Reflect on recent successes or corrections to capture reusable skills or rules.": "反思最近的成功或纠正，以捕获可重用的技能或规则。",
    "Narrow": "窄",
    "Wide": "宽",
    "Catppuccin": "Catppuccin",
    "One Light": "One Light",
    "Solarized Light": "Solarized Light",
    "Retrieve and analyze AlphaFold predicted structures for a protein. Use when the user provides a specific UniProt Accession ID and wants structural confidence metrics (pLDDT), domain boundary analysis, or disorder assessment. Do not use if the user only has a protein name, gene name, or amino acid sequence — ask for a UniProt ID first.": "检索并分析 AlphaFold 预测的蛋白质结构。当用户提供特定 UniProt 访问 ID，并希望获取结构置信度指标 (pLDDT)、结构域边界分析或无序评估时使用。如果用户仅提供蛋白质名称、基因名称或氨基酸序列，则请勿使用 —— 先要求提供 UniProt ID。",
    "Analyzes genetic variant effects on gene expression (RNA-seq), chromatin accessibility (DNASE), histone marks (ChIP), and transcription factors using the AlphaGenome API. Use when the user asks about non-coding variant effects, pathogenicity, clinical significance, disease associations, functional effects, gene expression changes, splicing disruption, or regulatory effects in promoters and enhancers. Also use for resolving biological terms to tissue/cell-type ontologies (UBERON/CL) or analyzing variants in chr:pos:ref>alt format.": "使用 AlphaGenome API 分析遗传变异对基因表达 (RNA-seq)、染色质可及性 (DNASE)、组蛋白标记 (ChIP) 和转录因子的影响。当用户询问非编码变异效应、致病性、临床意义、疾病关联、功能影响、基因表达变化、剪接破坏或启动子和增强子中的调节作用时使用。也用于将生物学术语解析为组织/细胞类型本体 (UBERON/CL)，或分析 chr:pos:ref>alt 格式的变异。",
    "Provides a comprehensive guide, quick reference, and sitemap for Google Antigravity (AGY), including the Antigravity CLI (agy), Antigravity 2.0, Antigravity IDE, Python SDK, slash commands, keybindings, and customizations (skills, rules, MCP, sidecars). Activate this skill when the user asks questions about how to use, configure, or customize Antigravity, AGY, the agy CLI, the Antigravity IDE, or Antigravity 2.0.": "为 Google Antigravity (AGY) 提供综合指南、快速参考和站点地图，包括 Antigravity CLI (agy)、Antigravity 2.0、Antigravity IDE、Python SDK、斜杠命令、快捷键和自定义（技能、规则、MCP、sidecars）。当用户询问如何使用、配置或自定义 Antigravity、AGY、agy CLI、Antigravity IDE 或 Antigravity 2.0 时，激活此技能。",
    "Query the ChEMBL database for bioactive molecules, drug targets, bioactivity data, approved drugs, and chemical structures. Use when the user asks about compounds, targets, IC50/Ki values, drug mechanisms, or structure searches.": "查询 ChEMBL 数据库以获取生物活性分子、药物靶点、生物活性数据、获批药物和化学结构。当用户询问化合物、靶点、IC50/Ki 值、药物机制或结构搜索时使用。",
    "Query ClinicalTrials.gov via APIv2. Use when you want to search for trials by condition, drug, location, status, or phase; retrieve trial details by NCT ID; check eligibility/inclusion criteria; count trials across conditions or time periods; identify a sponsor's trial portfolio; find recruiting trials for patient matching.": "通过 APIv2 查询 ClinicalTrials.gov。当您希望按条件、药物、地点、状态或阶段搜索试验；通过 NCT ID 检索试验详细信息；检查资格/纳入标准；统计跨条件或时间段的试验；识别申办者的试验组合；为匹配患者寻找正在招募的试验时使用。",
    "Use when needing clinical significance, pathogenicity classifications (e.g., Pathogenic, Benign, VUS), clinical evidence rationales, or finding \"hard positive\" benchmark controls for human genomic variants.": "在需要临床意义、致病性分类（例如致病性、良性、VUS）、临床证据基本原理，或寻找人类基因组变异的“硬阳性”基准对照时使用。",
    "Instructions for handling API keys and credentials safely, verifying their presence, and prompting the user to add them if missing using a safe protocol.": "关于安全处理 API 密钥和凭据的说明，验证它们是否存在，并在缺失时使用安全协议提示用户添加。",
    "Use when you want to look up, map, and search for short genetic variants (SNPs, indels) in NCBI's dbSNP database. Resolves between rsIDs, genomic coordinates in VCF format, and HGVS strings. For an rsID, returns variant type, gene associations, clinical significance, allele frequencies, and genomic coordinates (GRCh38).": "当您想要在 NCBI 的 dbSNP 数据库中查找、映射和搜索短遗传变异 (SNPs, indels) 时使用。在 rsIDs、VCF 格式的基因组坐标和 HGVS 字符串之间进行解析。对于 rsID，返回变异类型、基因关联、临床意义、等位基因频率和基因组坐标 (GRCh38)。",
    "Query and search the EMBL-EBI Ontology Lookup Service (OLS) for biomedical ontology terms, definitions, and hierarchies across 250+ ontologies (e.g., GO, DOID, HP). Use when the user asks to search for terms, retrieve details, navigate hierarchies (parents, children, ancestors), look up properties and individuals, get autocomplete suggestions, or access ontology metadata and statistics.": "查询和搜索 EMBL-EBI Ontology Lookup Service (OLS)，获取超过 250 个本体（例如 GO、DOID、HP）中的生物医学本体术语、定义和层次结构。当用户请求搜索术语、检索详细信息、导航层次结构（父、子、祖先）、查找属性和个体、获取自动完成建议，或访问本体元数据和统计信息时使用。",
    "Query the ENCODE Registry of cis-Regulatory Elements (cCREs) via the SCREEN GraphQL API, or make custom queries to the ENCODE Portal REST API for experiments and files (ChIP-seq peaks, etc.). Use when you want to query regulatory annotations or raw experimental data across human cell types.": "通过 SCREEN GraphQL API 查询顺式调控元件 (cCREs) 的 ENCODE 注册表，或对实验和文件（ChIP-seq 峰等）进行 ENCODE Portal REST API 自定义查询。当您想要跨人类细胞类型查询调控注释或原始实验数据时使用。",
    "Query the Ensembl database to resolve gene, transcript, and protein IDs, fetch genomic or protein sequences, retrieve gene structures (exons), and get variant consequence and effect predictions (VEP). Use this skill as a primary ID translator, genomic sequence database and variant effect prediction tool.": "查询 Ensembl 数据库以解析基因、转录本和蛋白质 ID，获取基因组或蛋白质序列，检索基因结构（外显子），并获取变异后果和影响预测 (VEP)。将此技能用作主要 ID 翻译器、基因组序列数据库和变异影响预测工具。",
    "Performs 3D structural searches of proteins against various databases (PDB, AlphaFold, CATH, MGnify, etc.) using the Foldseek API. Use ONLY when the user provides a physical 3D coordinate file (.cif, .mmcif, or .pdb) and wants to find structurally similar proteins. Do NOT use if the user only provides a protein sequence, gene name, or UniProt ID.": "使用 Foldseek API 对不同数据库（PDB、AlphaFold、CATH、MGnify 等）中的蛋白质进行 3D 结构搜索。仅当用户提供物理 3D 坐标文件（.cif、.mmcif 或 .pdb）并希望找到结构相似的蛋白质时使用。如果用户仅提供蛋白质序列、基因名称或 UniProt ID，请勿使用。",
    "Query the Genome Aggregation Database (gnomAD). Use when determining the rarity or allele frequency of specific genetic variants, retrieving gene constraint metrics (pLI, LOEUF) to assess loss-of-function intolerance, finding variants in a genomic region or gene, or querying structural variants. Don't use for analyzing individual patient genomes, tracking somatic mutations in cancer (use COSMIC), or requesting raw sequencing reads (use ENA).": "查询基因组聚合数据库 (gnomAD)。在确定特定遗传变异的稀有度或等位基因频率、检索基因约束指标 (pLI, LOEUF) 以评估功能丧失不耐受性、寻找基因组区域或基因中的变异，或查询结构变异时使用。请勿用于分析个体患者基因组、追踪癌症中的体细胞突变（请用 COSMIC），或请求原始测序读数（请用 ENA）。",
    "Use when you want to retrieve quantitative RNA expression data and variant eQTL information from the GTEx (Genotype-Tissue Expression) Project across 54 non-diseased tissue sites.": "当您想要从 GTEx（基因型-组织表达）项目检索跨 54 个非疾病组织位点的定量 RNA 表达数据和变异 eQTL 信息时使用。",
    "Use when you want to retrieve semi-quantitative protein expression and spatial localisation data from the Human Protein Atlas (HPA).": "当您想要从人类蛋白质图谱 (HPA) 检索半定量蛋白质表达和空间定位数据时使用。",
    "Identify domains, families, and sites in proteins; find all proteins in a family or sharing a domain; explore species distribution for a domain; annotate genomes with protein families and GO terms. InterPro combines 14 databases (e.g., Pfam, CDD) into one searchable resource. InterPro-N significantly expands annotation and sequence coverage with deep learning. Includes domain architecture (IDA) search.": "识别蛋白质中的结构域、家族和位点；查找家族中或共享结构域的所有蛋白质；探索结构域的物种分布；使用蛋白质家族和 GO 术语注释基因组。InterPro 将 14 个数据库（例如 Pfam、CDD）结合到一个可搜索资源中。InterPro-N 通过深度学习显著扩展了注释和序列覆盖范围。包含结构域架构 (IDA) 搜索。",
    "Query the JASPAR database for Transcription Factor (TF) binding profiles. Use when retrieving Position Frequency Matrices (PFMs) or Position Weight Matrices (PWMs) for specific TFs, resolving gene symbols to JASPAR Matrix IDs, or getting TF metadata. Supports multiple output formats (MEME, TRANSFAC, PFM, JASPAR, YAML).": "查询 JASPAR 数据库以获取转录因子 (TF) 结合图谱。在检索特定 TF 的位置频率矩阵 (PFM) 或位置权重矩阵 (PWM)、将基因符号解析为 JASPAR Matrix ID，或获取 TF 元数据时使用。支持多种输出格式（MEME、TRANSFAC、PFM、JASPAR、YAML）。",
    "Search for scientific papers, preprints, and publications on arXiv. Extract metadata, abstracts, and download full-text PDFs or HTML versions of papers. Use when the user asks to find research papers, literature, or specific arXiv IDs.": "在 arXiv 上搜索科学论文、预印本和出版物。提取元数据、摘要，并下载论文的全文 PDF 或 HTML 版本。当用户请求查找研究论文、文献或特定 arXiv ID 时使用。",
    "Browse, filter, and download life sciences, biology, and medical preprints from bioRxiv and medRxiv. Supports fetching paper metadata by DOI, and browsing by date range with category and keyword filters. Keyword filtering is local, so date ranges MUST be narrow (1-4 weeks) with a category to prevent timeouts.": "浏览、筛选和下载 bioRxiv 与 medRxiv 中的生命科学、生物学和医学预印本。支持通过 DOI 获取论文元数据，以及按带分类和关键字筛选的日期范围进行浏览。关键字筛选在本地进行，因此日期范围必须较窄（1-4 周）并带有一个分类以防止超时。",
    "Search Europe PMC for scientific literature and download open-access full texts and PDFs. Retrieve full-text XML/plain text by PMCID, get citation lists and bibliography.": "在 Europe PMC 搜索科学文献，并下载开放获取的全文和 PDF。通过 PMCID 检索全文 XML/纯文本，获取引用列表和参考书目。",
    "Query the OpenAlex scholarly database for research papers, authors, institutions, topics, sources, publishers, funders, geo-locations, and keywords. Use when searching academic papers, resolving DOIs, downloading open-access PDFs, finding an author's publications, aggregating bibliometric data (citation counts, h-index, impact factor), exploring the research taxonomies, or performing DOI lookups.": "查询 OpenAlex 学术数据库以获取研究论文、作者、机构、主题、来源、出版商、资助者、地理位置和关键字。当搜索学术论文、解析 DOI、下载开放获取 PDF、查找作者的出版物、聚合文献计量数据（引用次数、h 指数、影响因子）、探索研究分类，或执行 DOI 查找时使用。",
    "Retrieve protein and nucleotide sequences from NCBI databases using E-utilities. Supports direct accession lookup, CDS translation, gene+organism search, locus lookup, PubMed-linked sequences, patent protein extraction, and organism+length fallback search. Use when you need to fetch biological sequences by accession, gene name, locus tag, PubMed ID, or patent number.": "使用 E-utilities 从 NCBI 数据库检索蛋白质和核苷酸序列。支持直接访问号查询、CDS 翻译、基因+生物体搜索、基因座查询、与 PubMed 链接的序列、专利蛋白质提取以及生物体+长度的回退搜索。当您需要通过访问号、基因名称、基因座标签、PubMed ID 或专利号获取生物序列时使用。",
    "Query, search, and download data from the openFDA API for drugs, devices, foods, tobacco, cosmetics, animal and veterinary products, substances, and transparency data. Use for FDA adverse events, recalls, labeling, approvals, shortages, 510(k) clearances, NDC lookups, and any FDA safety or regulatory data query across all 28 API endpoints.": "从 openFDA API 查询、搜索和下载药物、设备、食品、烟草、化妆品、动物及兽医产品、物质以及透明度数据。用于所有 28 个 API 端点的 FDA 不良事件、召回、标签、批准、短缺、510(k) 许可、NDC 查找，以及任何 FDA 安全或监管数据查询。",
    "Query Open Targets Platform for target-disease associations, drug target discovery, tractability/safety data, genetics/omics evidence, known drugs, for therapeutic target identification.": "查询 Open Targets Platform 以获取靶点-疾病关联、药物靶点发现、可操作性/安全性数据、遗传学/组学证据、已知药物，用于治疗靶点识别。",
    "Use when you want to search for or download experimentally-determined 3D structures for biomolecules (proteins, nucleic acids, bound ligands). Supports searching by sequence similarity, structure similarity, chemical and other attributes. Also use to get metadata about biomolecular structure experiments.": "当您想要搜索或下载实验确定的生物分子（蛋白质、核酸、结合配体）的 3D 结构时使用。支持按序列相似性、结构相似性、化学及其他属性进行搜索。也用于获取关于生物分子结构实验的元数据。",
    "Ancient text restoration, attribution, dating, contextualization, and embedding via Aeneas (Latin) / Ithaca (Ancient Greek). Use when asked to \"restore\", \"attribute\", \"date\", \"contextualize\", \"find parallels\", \"where was it written\", \"when was it written\", \"embed\", or \"analyze\" an ancient text, inscription, or epigraphic document, or when the user mentions \"Aeneas\", or \"Ithaca\".": "通过 Aeneas (拉丁语) / Ithaca (古希腊语) 进行古代文本还原、归属、年代测定、语境化和嵌入。当被要求“还原”、“归属”、“测定年代”、“语境化”、“寻找平行文献”、“写于何处”、“写于何时”、“嵌入”，或“分析”古代文本、铭文或碑文文档，或者用户提到 “Aeneas” 或 “Ithaca” 时使用。",
    "Performs multiple sequence alignment of proteins with EBI Clustal Omega. Use when you need to align multiple sequences to assess similarity, domain conservation, or key residue conservation. Supports up to 4000 sequences and a maximum file size of 4 MB. Do not use to search for homologous proteins in a database (use MMseqs2, BLAST), align non-protein sequences (DNA, RNA), perform structural alignment (use Foldseek, PyMOL), or if you only have a single sequence.": "使用 EBI Clustal Omega 执行蛋白质的多重序列比对。当您需要比对多条序列以评估相似性、结构域保守性或关键残基保守性时使用。最多支持 4000 条序列，最大文件大小为 4 MB。请勿用于在数据库中搜索同源蛋白质 (请用 MMseqs2, BLAST)、比对非蛋白质序列 (DNA, RNA)、执行结构比对 (请用 Foldseek, PyMOL)，或者如果您只有单条序列时。",
    "Searches for homologous protein sequences using MMseqs2 (fast, default) or BLAST (comprehensive, fallback). Trigger this whenever the user provides a protein sequence or FASTA file and asks to find homologues, sequence matches, or wants to infer protein function based on sequence similarity, but not when the user wants to infer protein function based on structural similarity.": "使用 MMseqs2（快速，默认）或 BLAST（全面，后备）搜索同源蛋白质序列。当用户提供蛋白质序列或 FASTA 文件并要求查找同源物、序列匹配，或者希望基于序列相似性（而非结构相似性）推断蛋白质功能时触发此操作。",
    "Query PubChem, search by name/CID/SMILES, retrieve properties, similarity/substructure searches, bioactivity, for cheminformatics. Use when a user asks about a specific chemical, drug, or molecule.": "查询 PubChem，按名称/CID/SMILES 搜索，检索属性、相似性/子结构搜索、生物活性，用于化学信息学。当用户询问特定化学品、药物或分子时使用。",
    "Search PubMed for scientific literature, including published clinical trials. Fetch abstracts and full text. Link published research to biological databases (gene, protein, nucleotide, PubChem) to discover associations between papers and specific compounds or genes. Verify medical spelling, match raw citations, and cache result sets for bulk processing. Interfaces NCBI E-utilities and PMC BioC APIs.": "在 PubMed 搜索科学文献，包括已发表的临床试验。获取摘要和全文。将已发表研究与生物数据库（基因、蛋白质、核苷酸、PubChem）链接，以发现论文与特定化合物或基因之间的关联。验证医学拼写，匹配原始引文，并缓存结果集以进行批量处理。对接 NCBI E-utilities 和 PMC BioC API。",
    "Visualize, analyze, and render protein and molecular structures using PyMOL. Use when the user wants to create images of protein structures, perform structural alignments or superposition, measure distances or contacts, highlight binding sites or active site residues, color by B-factor/pLDDT, or analyze protein-ligand interactions. Do not use for docking, molecular dynamics, or sequence-only analysis.": "使用 PyMOL 可视化、分析和渲染蛋白质及分子结构。当用户想要创建蛋白质结构图像、执行结构比对或叠加、测量距离或接触、突出显示结合位点或活性位点残基、按 B 因子/pLDDT 着色，或分析蛋白质-配体相互作用时使用。请勿用于对接、分子动力学或纯序列分析。",
    "Query the QuickGO and Evidence & Conclusion Ontology (ECO) REST API. Use this when you need to map genes to biological processes, molecular functions, or cellular components, find genes associated with a specific pathway/GO term, or explore the Gene Ontology hierarchy. Do not use for querying drug targets (use OpenTargets) or mechanistic signaling pathway diagrams (use KEGG).": "查询 QuickGO 和证据与结论本体 (ECO) REST API。当您需要将基因映射到生物过程、分子功能或细胞成分、查找与特定通路/GO 术语相关的基因，或探索基因本体层次结构时使用。请勿用于查询药物靶点 (请用 OpenTargets) 或机制信号通路图 (请用 KEGG)。",
    "Query the Reactome database (Analysis and Content Services). Use when the user asks about pathway analysis, gene list enrichment, retrieving results by token, finding unmapped or not-found identifiers, mapping identifiers, reaction participants (inputs, outputs), pathway hierarchy (including top-level pathways), diagram export, cross-reference mapping, or searching the knowledgebase.": "查询 Reactome 数据库（分析和内容服务）。当用户询问关于通路分析、基因列表富集、通过 token 检索结果、查找未映射或未找到的标识符、映射标识符、反应参与者（输入、输出）、通路层次结构（包括顶层通路）、图表导出、交叉引用映射，或搜索知识库时使用。",
    "Query the STRING database for protein-protein interactions (PPIs), functional enrichment, and homology. Use when the user asks about interactions between specific proteins, interaction evidence, confidence scores, protein interaction partners, or pathway enrichments.": "查询 STRING 数据库以获取蛋白质-蛋白质相互作用 (PPIs)、功能富集和同源性。当用户询问特定蛋白质之间的相互作用、相互作用证据、置信度分数、蛋白质相互作用伙伴，或通路富集时使用。",
    "Fetch Evolutionary Conservation scores (phyloP, phastCons) and Transcription Factor Binding Sites (TFBS) from the UCSC Genome Browser. Use when analyzing whether genomic variants or regions are evolutionarily conserved, functionally important, or bounded by TF regulators across major projects (ENCODE, JASPAR, ReMap).": "从 UCSC Genome Browser 获取进化保守性分数 (phyloP, phastCons) 和转录因子结合位点 (TFBS)。当分析基因组变异或区域在进化上是否保守、是否具有功能重要性，或是否在各大项目（ENCODE、JASPAR、ReMap）中受到 TF 调节因子的约束时使用。",
    "Queries the UniBind database for experimentally validated transcription factor (TF) binding sites. Use when retrieving direct TF-DNA interaction datasets, downloading binding site coordinates (BED/FASTA) for local analysis, or listing available datasets by species, cell line, or TF name. Don't use to query specific intervals, locations, genes, motif models or expression data.": "查询 UniBind 数据库以获取经实验验证的转录因子 (TF) 结合位点。当检索直接的 TF-DNA 相互作用数据集、下载结合位点坐标 (BED/FASTA) 以进行本地分析，或按物种、细胞系、TF 名称列出可用数据集时使用。请勿用于查询特定的区间、位置、基因、基序模型或表达数据。",
    "Access protein metadata, function, taxonomy, and sequences across UniProtKB, UniParc, and UniRef. Use when searching for proteins, mapping identifiers, or retrieving functional annotations and publications. Don't use for sequence alignment, protein folding, or sequence similarity search (use specialized skills for those tasks).": "在 UniProtKB、UniParc 和 UniRef 中访问蛋白质元数据、功能、分类和序列。在搜索蛋白质、映射标识符，或检索功能注释和出版物时使用。请勿用于序列比对、蛋白质折叠或序列相似性搜索（请使用用于这些任务的专门技能）。",
    "Checks whether the uv Python package manager is installed and installs it if missing. Ensures uv is on PATH. Use when another skill requires uv as a prerequisite.": "检查是否安装了 uv Python 包管理器，如果缺失则进行安装。确保 uv 在 PATH 中。当其他技能需要 uv 作为先决条件时使用。",
    "Distills a completed user workflow or interaction into a reusable agent skill. Use when the user asks to turn their workflow, interaction, or multi-step process into a skill, or when they say \"make this a skill\", \"create a skill from what we just did\", \"package this workflow\" or similar. Do not use for creating skills from scratch without an existing workflow (use a generic skill-creator for that).": "将完成的用户工作流或交互提炼为可重用的智能体技能。当用户要求将其工作流、交互或多步过程转换为技能，或当他们说“将这个变成技能”、“根据我们刚才做的创建一个技能”、“打包这个工作流”或类似话语时使用。请勿在没有现有工作流的情况下从头创建技能（为此请用通用的 skill-creator）。"
  };


  const translateDynamicRegex = (text) => {
    if (!text || typeof text !== 'string') return text;
    const t = text.trim();
    // 思考耗时匹配 (如: Thought for 12s / Thinking for 5s)
    if (/^Thought for \d+s$/.test(t)) {
      return text.replace(/^Thought for (\d+)s$/, "已深度思考 $1 秒");
    }
    if (/^Thinking for \d+s$/.test(t)) {
      return text.replace(/^Thinking for (\d+)s$/, "思考中 ($1 秒)");
    }
    // 带有项目数的规划继续执行 (如: Proceed with implementation plan and 2 more)
    if (/^Proceed with implementation plan and \d+/.test(t)) {
      return text.replace(/^Proceed with implementation plan and (\d+)/, "按实施规划及另外 $1 项继续执行");
    }
    // 子智能体列表计数 (如: Child Subagents (2))
    if (/^Child Subagents \(\d+\)$/.test(t)) {
      return text.replace(/^Child Subagents \((\d+)\)$/, "子级智能体 ($1)");
    }
    return text;
  };

  const translateText = (text) => {
    text = translateDynamicRegex(text);
      let t = text.trim();
      if (dynamicDict[t]) return text.replace(t, dynamicDict[t]);
      
      // 兼容带有下拉箭头的 Advanced Settings
      if (t.startsWith("Advanced Settings")) {
          return text.replace("Advanced Settings", "高级设置");
      }
      
      // 特殊前缀匹配
      if (t.startsWith("Your Plan: ")) {
          return text.replace("Your Plan: ", "当前套餐: ");
      }
      
      // 特殊规则匹配长句和时间
      if (t.includes("The browser subagent can be invoked by typing /browser in the conversation input box")) {
          return "才能正常运行。可以在对话输入框中输入 /browser 来调用浏览器子智能体。";
      }
      if (t.includes("will use your AI credits to fulfill model requests once you're out of model quota")) {
          return "开启后，当模型配额耗尽时，Antigravity 将使用您的 AI 额度处理模型请求。它将始终优先使用模型配额。";
      }
      if (t.includes("Within each group, models share a weekly limit and a 5-hour limit")) {
          return "在每个组中，模型共享周限额和 5 小时限额。配额消耗与 Token 成本成正比。因此，任务越短或使用更划算的模型，限额持续的时间就越长。5 小时限额有助于在所有用户之间公平分配容量，而您的周限额则直接与您的套餐等级挂钩。";
      }
      if (t.includes("You have used some of your weekly limit")) {
          return text.replace("You have used some of your weekly limit, it will fully refresh in", "您已使用了部分周限额，将在")
                     .replace("days,", "天")
                     .replace("hours.", "小时后完全刷新。");
      }
      if (t.includes("You have used some of your 5-hour limit")) {
          return text.replace("You have used some of your 5-hour limit, it will fully refresh in", "您已使用了部分 5 小时限额，将在")
                     .replace("hours,", "小时")
                     .replace("minutes.", "分钟后完全刷新。");
      }
      // 动态匹配 Show X breakdowns
      if (/^Show \d+ breakdowns?$/.test(t)) {
          return text.replace(/^Show (\d+) breakdowns?$/, "显示 $1 项明细");
      }
      return text;
  };

  const translatedNodes = new WeakSet();

  // 判断是否为流式对话、代码块或输入框等高频突变区域，避让这些区域以防破坏 React 虚拟 DOM
  const isDynamicContentZone = (node) => {
    try {
      let el = node.nodeType === 1 ? node : node.parentElement;
      while (el && el !== document.body) {
        const cls = (el.className || '').toString().toLowerCase();
        const id = (el.id || '').toString().toLowerCase();
        const tagName = (el.tagName || '').toLowerCase();
        if (
          tagName === 'textarea' ||
          tagName === 'input' ||
          cls.includes('monaco') ||
          cls.includes('chat') ||
          cls.includes('conversation') ||
          cls.includes('markdown') ||
          cls.includes('stream') ||
          cls.includes('message-content') ||
          cls.includes('terminal') ||
          cls.includes('xterm') ||
          id.includes('chat') ||
          id.includes('conversation')
        ) {
          return true;
        }
        el = el.parentElement;
      }
    } catch(e) {}
    return false;
  };

  const safeTranslateNode = (node) => {
    try {
      if (!node || translatedNodes.has(node)) return;
      translatedNodes.add(node);

      if (isDynamicContentZone(node)) return;

      if (node.nodeType === 3) { // TEXT_NODE
         const text = node.textContent;
         if (text && text.trim().length > 0) {
           const newText = translateText(text);
           if (newText !== text) {
             window.requestAnimationFrame(() => {
               try {
                 if (node.textContent === text) {
                   node.textContent = newText;
                 }
               } catch(e) {}
             });
           }
         }
      } else if (node.nodeType === 1) { // ELEMENT_NODE
         const tag = (node.nodeName || '').toUpperCase();
         if (tag !== 'SCRIPT' && tag !== 'STYLE' && tag !== 'TEXTAREA' && tag !== 'INPUT') {
             node.childNodes.forEach(safeTranslateNode);
         }
      }
    } catch(e) {}
  };

  const initTranslator = () => {
      try {
        if (document.body) safeTranslateNode(document.body);
        const observer = new MutationObserver((mutations) => {
          try {
            mutations.forEach((mutation) => {
              if (mutation.addedNodes) {
                mutation.addedNodes.forEach(safeTranslateNode);
              }
            });
          } catch(e) {}
        });
        observer.observe(document.body, { childList: true, subtree: true });
      } catch(e) {}
  };
  
  try {
      if (document.body) {
          initTranslator();
      } else {
          window.addEventListener('DOMContentLoaded', initTranslator);
      }
  } catch(e) {}
})();
"""

    content = content + "\n" + dom_translator_js
    # ---------------- 注入全局动态 DOM 翻译拦截器 ----------------
    
    # Save the modified file
    print(f"Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Translation completed successfully!")

if __name__ == "__main__":
    main()
