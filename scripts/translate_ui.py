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

  const translateText = (text) => {
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

  const walkNode = (node) => {
    if (node.nodeType === 3) { // TEXT_NODE
       const newText = translateText(node.textContent);
       if (newText !== node.textContent) {
           node.textContent = newText;
       }
    } else if (node.nodeType === 1) { // ELEMENT_NODE
       if (node.nodeName !== 'SCRIPT' && node.nodeName !== 'STYLE') {
           node.childNodes.forEach(walkNode);
       }
    }
  };

  const initTranslator = () => {
      walkNode(document.body);
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach(walkNode);
          if (mutation.type === 'characterData') {
             const newText = translateText(mutation.target.textContent);
             if (newText !== mutation.target.textContent) {
                 mutation.target.textContent = newText;
             }
          }
        });
      });
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  };
  
  if (document.body) {
      initTranslator();
  } else {
      window.addEventListener('DOMContentLoaded', initTranslator);
  }
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
