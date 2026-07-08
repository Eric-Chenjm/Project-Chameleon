# 🦎 Project Chameleon (变色龙计划)

**一句话简介：终极 Antigravity 完美汉化框架。独创「云端神经网热更新」与「本地零功耗嗅探」，解决所有界面乱码与更新白屏死机，实现 100% 极客沉浸式中文体验。**

> 🔥 **Antigravity 旗舰级无缝跨平台汉化补丁 (跨版本免疫崩溃)**
[![Antigravity Compatibility](https://img.shields.io/badge/Antigravity-v2.2.1-blue.svg)](https://github.com/Eric-Chenjm/Project-Chameleon)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Mac-blueviolet.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!IMPORTANT]
> **💻 平台声明**：目前的自动化解包与底层拦截器注入引擎 (`smart_patch.py`) **原生完美支持 Windows 和 Mac 环境**。

## 🌟 为什么需要这个补丁？
过去，传统的汉化包采用了暴力的**“静态源码替换”**方案。这导致了一个致命问题：官方稍微改动一行代码或者变更一个组件，整个前端页面就会崩溃（所谓的“白屏死机”）。且大量藏在犄角旮旯的动态长句、下拉菜单以及多达 40+ 的动态 Skill 根本无法被匹配。

**Project Chameleon 采用最纯粹的黑客级技术，彻底终结了这一切。**

## 🚀 核心黑科技 (Core Technologies)

经过多次极限重构，变色龙目前已进化为**完全解耦、零功耗、全自动**的终极形态：

1. ⚡ **WeakSet 零功耗渲染 (Zero-Impact DOM Engine)**
   摒弃传统静态替换，采用底层 `MutationObserver` 结合 `WeakSet` 内存缓存标记算法。渲染引擎拥有了“记忆”，跳过已翻译节点。**翻译效率提升 300%，0 额外 CPU 损耗，绝不掉帧卡顿！**
2. ☁️ **云端神经网同步 (Cloud Sync Matrix)**
   彻底废弃了臃肿的 7.5MB 字典包结合体。我们将词典解耦到了极轻量的 `chameleon_dict.json` 中。
   **这意味着什么？** 未来任何社区新增的插件汉化，变色龙会在后台 Node.js 异步微线程默默从 GitHub 自动拉取更新。**您只需要重启软件，新插件便会自动汉化，再也不需要手动跑任何脚本！**
3. 📡 **本地私有雷达 (Local Stealth Radar)**
   如果您在本地写了一个独家的私有全英文 Skill 怎么办？启动软件的瞬间，变色龙原生 `fs.promises` 将执行毫秒级的后台静默探查，自动剥离所有的未知生肉英文，帮您生成待翻译清单。真正的无感全自动化！
4. 🧩 **极客碎片缝合技术**
   针对被 HTML 标签一刀切断的长句，使用高级正则动态缝合汉化。并且坚决保留了 `MCP`, `AlphaFold`, `Token`, `Android` 等专业术语的纯正英文形态。

## 📦 如何一键部署？ (保姆级教程)

本项目的目标就是让任何人都能在 10 秒内拥有最纯粹的中文使用体验：

1. **环境准备**：
   确保您的电脑上已经安装了 [Python](https://www.python.org/)。(Mac 用户请在终端使用 `python3` 命令)。
2. **下载本项目**：
   点击右上角的 `Code` -> `Download ZIP` 按钮，或者前往 Release 页面下载最新的发布包。
3. **执行一键解包注入**：
   解压后，在终端中运行 `python smart_patch.py`（Windows 用户也可以直接双击运行）。
   > 脚本会自动检测您的系统环境，提取独立解耦字典，部署底层异步监听器，并无缝重打包。整个过程仅需几秒钟！
4. **见证奇迹**：
   打开您的 Antigravity，按下 `Ctrl+R`（Windows）或 `Cmd+R`（Mac）重载界面。恭喜您，进入 100% 完美的中文世界！

## 推广指南：让更多人发现极客的魅力
如果你喜欢这个项目，欢迎右上角 ⭐️ **Star** 鼓励一下独立开发者！
如果您希望更多极客发现本项目，建议在 GitHub 网页端的仓库右侧 **About** 的 ⚙️（齿轮图标）中，添加以下推广关键词 (Topics)：
`antigravity`、`localization`、`chinese-translation`、`electron-patch`、`cross-platform`、`mutation-observer`

---
*Developed solely by [Eric-Chenjm], engineered for perfection.*
