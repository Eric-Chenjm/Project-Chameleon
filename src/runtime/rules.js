'use strict';

/**
 * Project Chameleon v3.0 — 运行时动态规则与安全守卫模块
 * 包含：时间/倒计时格式化、安全正则规则列表、权限目标保护、专业英文保留开关、DOM 免疫判定。
 */

// 统一配额/耗时文本格式化（严格使用边界与纯回调防 $ 注入）
function formatDurationCn(raw) {
  return String(raw || '')
    .trim()
    .replace(/^<\s*1\s*m(?:in(?:ute)?s?)?$/i, '不到 1 分钟')
    .replace(/(\d+)\s*mo\b/gi, '$1 个月 ')
    .replace(/(\d+)\s*d(?:ays?)?\b/gi, '$1 天 ')
    .replace(/(\d+)\s*h(?:(?:ou)?rs?)?\b/gi, '$1 小时 ')
    .replace(/(\d+)\s*m(?:in(?:ute)?s?)?\b(?!\s*o)/gi, '$1 分钟 ')
    .replace(/(\d+)\s*s(?:ec(?:ond)?s?)?\b/gi, '$1 秒 ')
    .replace(/\s+/g, ' ')
    .trim();
}

// 默认允许保留原文的产品/协议/模型白名单，以及可通过悬浮球切换「专业选项保留英文」的枚举项
const ENGLISH_LABEL_PRESET = new Set([
  'this conversation',
  'request review',
  'default',
  'auto',
  'turbo',
  'extra high',
  'extra',
  'high',
  'medium',
  'low',
  'max',
  'planning',
  'fast',
]);

// 权限提示安全模板（仅翻译外部固定句式，绝对保留命令/路径/URL原文，且支持幂等）
function translatePermissionTemplate(trimmed) {
  if (!trimmed) return null;
  if (/^(?:允许|是否允许|是否保存规则以始终允许|禁止|始终允许)/.test(trimmed)) {
    return trimmed; // 已翻译文本直接原样返回保证幂等
  }
  let m;
  if ((m = trimmed.match(/^Yes,\s*and always allow '([\s\S]+)' in this conversation$/))) {
    return `允许，并在当前会话中始终允许 '${m[1]}'`;
  }
  if ((m = trimmed.match(/^Save rule to always allow ([\s\S]+)\?$/))) {
    return `是否保存规则以始终允许 ${m[1]}？`;
  }
  if ((m = trimmed.match(/^Allow ([\s\S]+)\?$/))) {
    // 排除纯长句误匹配，如果目标包含命令/路径/URL/工具或合理短语则翻译
    return `是否允许 ${m[1]}？`;
  }
  if ((m = trimmed.match(/^Deny ([\s\S]+)\?$/))) {
    return `是否拒绝 ${m[1]}？`;
  }
  return null;
}

// 快捷键冲突与录制模板
function translateShortcutTemplate(trimmed) {
  let m;
  if ((m = trimmed.match(/^Conflicts with "([^"]+)" \(press Enter to replace\)$/))) {
    return `与“${m[1]}”快捷键冲突（按 Enter 键替换）`;
  }
  if ((m = trimmed.match(/^Conflict: also assigned to ([\s\S]+)$/))) {
    return `按键冲突：该快捷键同时已分配给 ${m[1]}`;
  }
  if ((m = trimmed.match(/^Recording shortcut for ([\s\S]+)\. Press keys to bind, Enter to save, Escape to cancel\.$/))) {
    return `正在为“${m[1]}”录制快捷键。按下组合键绑定，按 Enter 保存，按 Escape 取消。`;
  }
  if ((m = trimmed.match(/^Shortcut ([^\s]+) for ([\s\S]+)$/))) {
    return `“${m[2]}”的快捷键：${m[1]}`;
  }
  if ((m = trimmed.match(/^Remove shortcut ([^\s]+) for ([\s\S]+)$/))) {
    return `移除“${m[2]}”的快捷键 ${m[1]}`;
  }
  if ((m = trimmed.match(/^Add shortcut for ([\s\S]+)$/))) {
    return `为“${m[1]}”添加快捷键`;
  }
  if ((m = trimmed.match(/^Reset ([\s\S]+) to default$/))) {
    return `将“${m[1]}”恢复为默认快捷键`;
  }
  return null;
}

// 动态参数与交互模板规则（统一使用函数回调，彻底规避 $ 字符篡改与换行污染）
const DYNAMIC_RULES = [
  // --- 配额、模型选择与倒计时 ---
  [/^Resets in (<1m|(?:\d+\s*[dhms]\s*)+)$/i, (_, dur) => `${formatDurationCn(dur)}后重置`],
  [/^(.+?)\s+Pick a model to change it\.$/, (_, mName) => `${mName} 请选择一个模型以修改它。`],
  [/^Your quota for (.+?) will reset on (.+?)\. Switch to another available model to continue\.$/, (_, model, dt) => `您的 ${model} 配额将于 ${dt} 重置。请切换至其他可用模型继续。`],
  [/^Your quota for (.+?) has been reached\. Switch to another available model to continue\.$/, (_, model) => `您的 ${model} 配额已用尽。请切换至其他可用模型继续。`],
  [/^Select model, current: (.+)$/, (_, model) => `选择模型，当前：${model}`],
  [/^Select model with (.+)$/, (_, cap) => `选择包含 ${cap} 的模型`],
  [/^Available AI Credits: (.+)$/, (_, amt) => `可用 AI 额度：${amt}`],
  [/^Compare responses from (\d+) models side-by-side to find the best result\.$/, (_, n) => `并排比较 ${n} 个模型的回复，选出最佳结果。`],

  // --- 思考与耗时（仅精准匹配状态标签，不改写对话正文）---
  [/^Thought for ((?:\d+\s*[dhms]\b\s*)+)$/i, (_, dur) => `已深度思考 ${formatDurationCn(dur)}`],
  [/^Thought for (\d+) seconds?$/i, (_, n) => `已思考 ${n} 秒`],
  [/^Thinking for (\d+)s$/i, (_, n) => `思考中 (${n} 秒)`],
  [/^Thinking \((\d+)s\)[….]*$/i, (_, n) => `思考中 (${n} 秒)…`],
  [/^Still thinking, (\d+) seconds?$/i, (_, n) => `仍在思考，已耗时 ${n} 秒`],
  [/^Worked for ((?:\d+\s*[dhms]\b\s*)+)\.?$/i, (_, dur) => `耗时 ${formatDurationCn(dur)}`],
  [/^Working · (\d+)s$/, (_, n) => `运行中 · ${n} 秒`],

  // --- 轮次、步骤、队列与批注 ---
  [/^Go to turn (\d+) of (\d+)$/, (_, a, b) => `跳转到第 ${a} 轮（共 ${b} 轮）`],
  [/^Turn (\d+) of (\d+)$/, (_, a, b) => `第 ${a} 轮（共 ${b} 轮）`],
  [/^Turns (\d+)[–-](\d+)$/, (_, a, b) => `第 ${a}–${b} 轮`],
  [/^Turn (\d+)$/, (_, a) => `第 ${a} 轮`],
  [/^Step (\d+) of (\d+)$/, (_, a, b) => `第 ${a} 步（共 ${b} 步）`],
  [/^Show (\d+) earlier steps?$/, (_, n) => `展开更早的 ${n} 个步骤`],
  [/^Load older messages, showing (\d+) of (\d+)$/, (_, a, b) => `加载更早消息（显示 ${a}/${b}）`],
  [/^(\d+) (?:earlier|later) steps are not loaded, so they are not on the timeline\. Scroll the step grid in the Context Window tab to load them\.$/, (_, n) => `${n} 个较早/较晚的步骤尚未加载，因此未在时间线上显示。请在“上下文窗口”选项卡中滚动步骤网格进行加载。`],
  [/^Message queued\. (\d+) messages? in queue\.$/, (_, n) => `消息已入队，当前队列中共有 ${n} 条消息。`],
  [/^Send all \((\d+)\)$/, (_, n) => `全部发送 (${n})`],
  [/^See all \((\d+)\)$/, (_, n) => `查看全部 (${n})`],
  [/^See (\d+) more$/, (_, n) => `查看更多 (${n})`],
  [/^\+(\d+) more \(Show all\)$/, (_, n) => `另外 +${n} 项（展开全部）`],
  [/^Comment \((\d+)\)$/, (_, n) => `批注 (${n})`],
  [/^Review (\d+) comments?$/, (_, n) => `查看 ${n} 条评论`],
  [/^Proceed with implementation plan and (\d+) comments?$/, (_, n) => `继续执行实施规划并附带 ${n} 条批注`],
  [/^Proceed with implementation plan and (\d+)$/, (_, n) => `按实施规划及另外 ${n} 项继续执行`],
  [/^Proceed • (\d+)$/, (_, n) => `继续执行 • ${n}`],
  [/^(\d+) comments? in (.+)$/, (_, n, target) => `${target} 中的 ${n} 条批注`],
  [/^(\d+) files? changed$/, (_, n) => `${n} 个文件已更改`],
  [/^Select at most (\d+) items?$/, (_, n) => `最多选择 ${n} 项`],

  // --- 子智能体、侧边提问与工作流 ---
  [/^Show (\d+) more subagents?$/, (_, n) => `展开另外 ${n} 个子智能体`],
  [/^Child Subagents \((\d+)\)$/, (_, n) => `子级智能体 (${n})`],
  [/^(\d+) Child Subagents?$/, (_, n) => `${n} 个子智能体`],
  [/^\((\d+) subagents?\)$/, (_, n) => `(${n} 个子智能体)`],
  [/^(\d+) subagents?$/, (_, n) => `${n} 个子智能体`],
  [/^subagent of "(.+)"$/, (_, parent) => `隶属于 "${parent}" 的子智能体`],
  [/^Open Subagent: (.+)$/, (_, name) => `打开子智能体：${name}`],
  [/^Invoked subagent: (.+)$/, (_, name) => `已调用子智能体：${name}`],
  [/^Agent finished: (.+)$/, (_, name) => `智能体已完成：${name}`],
  [/^Agent permissions preset selector, current: (.+)$/, (_, p) => `智能体权限预设选择器，当前：${p}`],
  [/^Agent permissions preset: (.+)$/, (_, p) => `智能体权限预设：${p}`],
  [/^Where the agent runs, current: (.+)$/, (_, p) => `智能体运行位置，当前：${p}`],
  [/^(\d+) Help · (\d+) Side Questions?$/, (_, h, q) => `${h} 项帮助 · ${q} 个侧边提问`],
  [/^(\d+) Help$/, (_, h) => `${h} 项帮助`],
  [/^(\d+) Side Questions?$/, (_, q) => `${q} 个侧边提问`],
  [/^View (\d+) help(?: items?)? and (\d+) side questions?$/, (_, h, q) => `查看 ${h} 项帮助与 ${q} 个侧边提问`],
  [/^View (\d+) help(?: items?)?$/, (_, h) => `查看 ${h} 项帮助`],
  [/^View (\d+) side questions?$/, (_, q) => `查看 ${q} 个侧边提问`],
  [/^Question (\d+) of (\d+)$/, (_, a, b) => `第 ${a} 个问题，共 ${b} 个`],
  [/^Side Question: (.+)$/, (_, title) => `侧边提问：${title}`],
  [/^Edit side question title: (.+)$/, (_, title) => `编辑侧边提问标题：${title}`],
  [/^Delete side question: (.+)$/, (_, title) => `删除侧边提问：${title}`],
  [/^Side question failed: (.+)$/, (_, err) => `侧边提问失败：${err}`],
  [/^Are you sure you want to delete the project ([^?]+)\?$/, (_, name) => `您确定要删除项目“${name}”吗？`],

  // --- 终端、工具调用、浏览器、Git 与 SSH ---
  [/^Ran command:\s*(.+)$/, (_, cmd) => `已运行命令：${cmd}`],
  [/^Running command:\s*(.+)$/, (_, cmd) => `正在运行命令：${cmd}`],
  [/^Process exited with code (-?\d+)\.?$/, (_, code) => `进程已退出，退出代码：${code}`],
  [/^Exited with code (-?\d+)\.?$/, (_, code) => `已退出，退出代码：${code}`],
  [/^Failed with exit code:?\s*(-?\d+)\.?$/, (_, code) => `执行失败，退出代码：${code}`],
  [/^Terminal process (.+) exited with non-zero code (-?\d+)$/, (_, name, code) => `终端进程 ${name} 已退出，非零退出代码：${code}`],
  [/^Waiting for command completion \(up to (\d+) seconds?\)$/, (_, s) => `正在等待命令完成（最多 ${s} 秒）`],
  [/^Closed (\d+) terminals?$/, (_, n) => `已关闭 ${n} 个终端`],
  [/^Using browser · (.+) \((\d+)s\)$/, (_, target, s) => `正在使用浏览器 · ${target} (${s} 秒)`],
  [/^Using browser \((\d+)s\)$/, (_, s) => `正在使用浏览器 (${s} 秒)`],
  [/^Using browser · (.+)$/, (_, target) => `正在使用浏览器 · ${target}`],
  [/^Opened browser: (.+)$/, (_, u) => `已打开浏览器：${u}`],
  [/^Read URL: (.+)$/, (_, u) => `已读取网址：${u}`],
  [/^Searched for files: (.+)$/, (_, q) => `已搜索文件：${q}`],
  [/^Searched for "(.+)"$/, (_, q) => `已搜索“${q}”`],
  [/^Code search: "(.+)"$/, (_, q) => `代码搜索：“${q}”`],
  [/^Searched web: "(.+)"$/, (_, q) => `网页搜索：“${q}”`],
  [/^Listed directory (.+)$/, (_, dir) => `已列出目录：${dir}`],
  [/^Used MCP tool: (.+)$/, (_, tool) => `已使用 MCP 工具：${tool}`],
  [/^Fix with Agent: (.+)$/, (_, item) => `使用智能体修复：${item}`],
  [/^View Diff for (.+)$/, (_, f) => `查看差异对比：${f}`],
  [/^Push (\d+) commits? to (.+)$/, (_, n, r) => `推送 ${n} 个提交到 ${r}`],
  [/^Pushed (\d+) commits? to (.+)\.$/, (_, n, r) => `已推送 ${n} 个提交到 ${r}。`],
  [/^Pushed to (.+)\.$/, (_, r) => `已推送到 ${r}。`],
  [/^Committed to (.+)\.$/, (_, b) => `已提交到 ${b}。`],
  [/^Publish (.+) to origin$/, (_, b) => `发布 ${b} 到 origin`],
  [/^Published (.+) to origin\.$/, (_, b) => `已发布 ${b} 到 origin。`],
  [/^Worktree from (.+)$/, (_, b) => `基于 ${b} 创建 Worktree`],
  [/^Work in (.+)$/, (_, dir) => `工作于 ${dir}`],
  [/^This window's agents, files, and terminals are on (.+)\.$/, (_, host) => `当前窗口的智能体、文件与终端均位于 ${host}。`],
  [/^No server is listening on port (\d+) inside the remote workspace\. Start it, or ask the agent to, then retry\.$/, (_, port) => `远程工作区内的端口 ${port} 上没有正在监听的服务。请启动服务（或让智能体启动）后重试。`],
  [/^SSH Config \((.+)\)$/, (_, f) => `SSH 配置 (${f})`],
  [/^SSH config: (.+)$/, (_, f) => `SSH 配置：${f}`],
  [/^No hosts in (.+) yet\. Type one above\.$/, (_, f) => `${f} 中暂无主机。请在上方输入。`],
  [/^Connected to (.+)$/, (_, target) => `已连接到 ${target}`],
  [/^Connecting to (.+?)[….]*$/, (_, target) => `正在连接到 ${target}…`],

  // --- Cookies / 扩展 / 设置动态标题 / 首页问候 ---
  [/^Deleted cookies for (.+)$/, (_, domain) => `已清除 ${domain} 的 Cookie`],
  [/^Delete cookies for (.+)$/, (_, domain) => `清除 ${domain} 的 Cookie`],
  [/^(\d+) cookies?$/, (_, n) => `${n} 个 Cookie`],
  [/^The (.+) MCP server requires configuration parameters before it can be started\.$/, (_, srv) => `MCP 服务器“${srv}”需要先完善配置参数才能启动。`],
  [/^Add bundle (.+)$/, (_, name) => `添加插件包 ${name}`],
  [/^Adding plugins from (.+)$/, (_, src) => `正在从 ${src} 添加插件`],
  [/^Plugins in (.+)$/, (_, src) => `${src} 中的插件`],
  [/^Search for "(.+)" in the Marketplace$/, (_, q) => `在市场中搜索“${q}”`],
  [/^Select (.+) Theme$/, (_, theme) => `选择 ${theme} 主题`],
  [/^Low contrast ratio \(([\d.]+):1\)\. Text may be hard to read\.$/, (_, r) => `色彩对比度过低 (${r}:1)，文字可能难以辨识。`],
  [/^Hey (.+), what should we build today\?$/, (_, u) => `你好 ${u}，今天我们构建些什么？`],
  [/^Welcome back, (.+)\. Where should we pick up\?$/, (_, u) => `欢迎回来，${u}。我们从哪里继续？`],
  [/^Good to see you, (.+)\. What's next\?$/, (_, u) => `很高兴见到你，${u}。接下来做什么？`],
  [/^Marked (\d+) conversations? as read$/, (_, n) => `已将 ${n} 个对话标记为已读`],
  [/^Sort and filter conversations \((\d+) active\)$/, (_, n) => `排序和筛选对话（${n} 项生效中）`],
  [/^Filter skills and rules: (.+)$/, (_, q) => `筛选技能和规则：${q}`],
  [/^Deleted "(.+)"\.$/, (_, name) => `已删除“${name}”。`],
  [/^Enabled "(.+)"\.$/, (_, name) => `已启用“${name}”。`],
  [/^Started "(.+)"\.$/, (_, name) => `已启动“${name}”。`],
  [/^Restarted "(.+)"\.$/, (_, name) => `已重启“${name}”。`],
  [/^Unnamed Agent (\d+)$/, (_, n) => `未命名智能体 ${n}`],
  [/^Unnamed skill (\d+)$/, (_, n) => `未命名技能 ${n}`],
  [/^Rule (\d+)$/, (_, n) => `规则 ${n}`],
  [/^Automation (\d+)$/, (_, n) => `自动化任务 ${n}`],
  [/^UI Extension (\d+)$/, (_, n) => `UI 扩展 ${n}`],
  [/^Downloads, (\d+)% complete$/, (_, p) => `下载进度 ${p}%`],
  [/^(\d+[smhd]) timer: (.+)$/, (_, dur, label) => `${dur} 定时器：${label}`],
];

// 硬免疫 DOM 节点与安全子树判定（严禁破坏 Monaco/Terminal/用户输入/对话正文/侧边栏用户自定义项目名）
const IMMUNE_TAGS = new Set([
  'SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'SVG', 'PATH',
  'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'CODE', 'PRE', 'KBD', 'SAMP',
]);

function isImmuneElement(el) {
  if (!el || el.nodeType !== 1) return false;
  if (IMMUNE_TAGS.has(el.tagName)) return true;
  if (el.isContentEditable) return true;
  if (el.dataset && (el.dataset.chameleonIgnore === '1' || el.dataset.chameleonToggle === '1')) return true;
  const cls = typeof el.className === 'string' ? el.className : '';
  if (
    cls.includes('monaco-editor') ||
    cls.includes('xterm') ||
    cls.includes('cm-editor') ||
    cls.includes('CodeMirror') ||
    cls.includes('ProseMirror')
  ) {
    return true;
  }
  return false;
}

// 判断给定节点或其祖先是否位于不可翻译的内容/编辑区
function shouldSkipNode(node) {
  if (!node) return true;
  let cur = node.nodeType === 1 ? node : node.parentElement;
  let depth = 0;
  while (cur && depth < 32) {
    if (isImmuneElement(cur)) return true;
    const cls = typeof cur.className === 'string' ? cur.className : '';
    const id = typeof cur.id === 'string' ? cur.id : '';
    // 对话流用户消息内容/Markdown模型输出正文必须免疫（但允许外层按钮/状态/工具卡片标题汉化，因此只免疫真正装用户/AI正文的 markdown/prose/user-input 容器）
    if (
      cls.includes('user-input-step') ||
      cls.includes('prose ') ||
      cls === 'prose' ||
      cls.includes('markdown-body') ||
      cls.includes('cm-content') ||
      cls.includes('view-lines') ||
      id === 'chameleon-toggle-root'
    ) {
      return true;
    }
    // 跳过跨 ShadowRoot 边界时继续检查 host
    const next = cur.parentElement;
    if (!next && cur.getRootNode && cur.getRootNode().host) {
      cur = cur.getRootNode().host;
    } else {
      cur = next;
    }
    depth++;
  }
  return false;
}

// 仅在导航/侧边栏菜单按钮上下文中把独立 "Running" 译为 "后台运行项"，防止误翻普通运行状态文本
function translateContextAware(node, trimmed) {
  if (trimmed === 'Running' && node && node.parentElement) {
    const p = node.parentElement.closest('nav, aside, [role="tablist"], [role="menu"], [role="menuitem"], button');
    if (p && p.closest('nav, aside, [role="tablist"]')) {
      return '后台运行项';
    }
  }
  return null;
}

// 核心单文本翻译流水线
function translateSingleText(text, ctx, sourceNode = null) {
  if (!text || typeof text !== 'string') return text;
  // 极速 ASCII 字母短路：无字母则 0 开销立即返回
  if (!/[a-zA-Z]/.test(text)) return text;

  const trimmed = text.trim();
  if (!trimmed || trimmed.length > 600) return text;
  // 跳过明显是文件路径、URL、纯命令、或含换行代码块的内容
  if (/^(?:https?:|plugin:\/\/|agy-|file:\/\/|\/|\\|[A-Za-z]:\\)/.test(trimmed)) return text;

  const {
    dictionary,
    lowerDictionary,
    customDictionary,
    englishLabelsMode,
    stringCache,
    cacheSet,
    replaceTrimmed,
  } = ctx;

  // 若开启「专业选项保留英文」，命中预设标签直接原样返回
  const lower = trimmed.toLowerCase();
  if (englishLabelsMode && ENGLISH_LABEL_PRESET.has(lower)) {
    return text;
  }

  // 自定义规则最高优先级（空字符串译文代表强制保持原文）
  if (customDictionary && customDictionary.has(lower)) {
    const customTarget = customDictionary.get(lower);
    return customTarget ? replaceTrimmed(text, trimmed, customTarget) : text;
  }

  const cacheKey = (englishLabelsMode ? 'E:' : 'Z:') + trimmed;
  if (stringCache.has(cacheKey)) {
    const hit = stringCache.get(cacheKey);
    return hit === trimmed ? text : replaceTrimmed(text, trimmed, hit);
  }

  // 1) 上下文安全精准翻译（直接返回，不写入通用 stringCache 以防污染非导航区的相同单词）
  if (sourceNode) {
    const ctxHit = translateContextAware(sourceNode, trimmed);
    if (ctxHit !== null) {
      return replaceTrimmed(text, trimmed, ctxHit);
    }
  }

  // 2) 精确词典 O(1) 命中 -> 小写哈希表 O(1) 命中
  let translated = dictionary[trimmed];
  if (translated === undefined) {
    translated = lowerDictionary.get(lower);
  }

  // 2) 权限/快捷键安全模板匹配
  if (translated === undefined) {
    translated = translatePermissionTemplate(trimmed) || translateShortcutTemplate(trimmed) || undefined;
  }

  // 3) 带快捷键后缀分离匹配，如 "Close Tab (Ctrl+W)" / "Copy..."
  if (translated === undefined) {
    const suffixMatch = trimmed.match(/^(.+?)\s*(\((?:Ctrl|Cmd|Alt|Shift|Meta|⌘|⌥|⇧|⌃)[^)]+\))$/i);
    if (suffixMatch) {
      const base = suffixMatch[1].trim();
      const baseTrans = dictionary[base] || lowerDictionary.get(base.toLowerCase());
      if (baseTrans) {
        translated = `${baseTrans} ${suffixMatch[2]}`;
      }
    }
  }

  // 4) 动态正则规则流水线
  if (translated === undefined) {
    for (let i = 0; i < DYNAMIC_RULES.length; i++) {
      const [re, replacer] = DYNAMIC_RULES[i];
      if (re.test(trimmed)) {
        translated = trimmed.replace(re, replacer);
        break;
      }
    }
  }

  const finalCore = translated !== undefined ? translated : trimmed;
  cacheSet(cacheKey, finalCore);
  return finalCore === trimmed ? text : replaceTrimmed(text, trimmed, finalCore);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    formatDurationCn,
    ENGLISH_LABEL_PRESET,
    translatePermissionTemplate,
    translateShortcutTemplate,
    DYNAMIC_RULES,
    isImmuneElement,
    shouldSkipNode,
    translateSingleText,
  };
}
