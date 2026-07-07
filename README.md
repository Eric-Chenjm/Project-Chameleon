# 🦎 Project Chameleon (变色龙计划)
**一句话简介：完美解决 Antigravity 界面乱码与更新白屏死机问题，通过外挂变色龙引擎实现全界面 100% 沉浸式中文汉化。**

> 🔥 **Antigravity 旗舰级无缝跨平台汉化补丁 (跨版本免疫崩溃)**
[![Antigravity Compatibility](https://img.shields.io/badge/Antigravity-v2.2.1-blue.svg)](https://github.com/Eric-Chenjm/Project-Chameleon)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac-blueviolet.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!IMPORTANT]
> **💻 平台声明**：目前的自动化解包与热注入引擎 (`smart_patch.py`) **原生支持 Windows 和 Mac 环境**。

## 🌟 为什么需要这个补丁？
过去，传统的汉化包采用了暴力的**“静态源码替换”**方案。这导致了一个致命问题：一旦官方版本更新，稍微改动一行代码或者变更一个组件 ID，就会导致整个前端页面崩溃（所谓的“白屏死机”），甚至导致左侧侧边栏消失。
更有甚者，大量藏在犄角旮旯的“动态长句”以及小写枚举项根本无法通过静态搜索匹配到。

**Project Chameleon 彻底终结了这一切。**

## 🚀 核心黑科技：DOM 变色龙挂载引擎
我们不仅翻译了数百条底层文本，更将一套原生的 Javascript `MutationObserver` 引擎强行植入到了渲染网关的最末端！
- **不死兼容**：无论未来的官方版本如何重构底层 React 组件，只要那些基础设置项的英文字母没有改头换面，我们的**变色龙引擎都能在渲染出画面的前一毫秒，精准拦截并化为中文！**
- **碎片缝合技术**：针对那些被 HTML 标签（如 `<a>`）一刀切断的长句，我们使用了高级的正则与 `.includes()` 捕获机制，自动进行缝合汉化。
- **极客本色**：我们坚持保留了 `MCP`, `Token`, `Android`, `Chrome DevTools` 等专有名词的纯正英文形态，拒绝土味的机翻。

## 📦 如何一键部署？ (保姆级教程)

本项目的目标就是让任何人都能在 10 秒内拥有最纯粹的中文使用体验：

1. **环境准备**：
   确保您的电脑上已经安装了 [Python](https://www.python.org/)。

2. **下载本项目**：
   点击右上角的 `Code` -> `Download ZIP` 按钮，或者前往 Release 页面下载最新的发布包。

3. **执行一键解包注入**：
   解压后，在终端中运行 `python smart_patch.py`（Windows 用户也可以直接双击运行）。
   > 该脚本会自动检测您的系统环境并找到官方 `app.asar` 进行安全解包、动态词典的热注入以及无缝重新打包。整个过程仅需十几秒！

4. **见证奇迹**：
   打开您的 Antigravity，按下 `Ctrl+R`（重载界面）。恭喜您，进入 100% 的中文世界！

## 🛠️ 参与贡献
如果你发现了未来版本中官方新增了我们未曾见过的“天外词汇”，欢迎通过 PR 或 Issue 提交！
由于采用了外挂 DOM 引擎，我们只需在 `scripts/translate_ui.py` 的字典里补上两行代码即可，维护成本无限趋近于零！

## 推广指南：如何让更多人看到？
如果您希望更多极客发现本项目，建议您在 GitHub 网页端的仓库右侧点击 `About` 旁边的 ⚙️（齿轮图标），并在 **Topics** 中添加以下推广关键词：
`antigravity`、`localization`、`chinese-translation`、`electron-patch`、`cross-platform`、`mutation-observer`

---
*Developed solely by [Eric-Chenjm], engineered for perfection.*
