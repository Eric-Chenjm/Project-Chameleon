# Project Chameleon v3.0 (变色龙计划)

**面向 Google Antigravity 2.x–2.34.0+ 的跨版本免疫、双模高性能深度汉化架构。**

[![Antigravity Compatibility](https://img.shields.io/badge/Antigravity-v2.34.0%2B-blue.svg)](https://github.com/Eric-Chenjm/Project-Chameleon)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blueviolet.svg)](#)
[![Architecture](https://img.shields.io/badge/Engine-Chameleon%20v3%20Modular-success.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 一、v3.0 架构重构亮点（彻底告别官方更新全英文 & 崩溃）

经过对社区优秀开源方案的深度吸收与全面底层重构，Chameleon v3.0 彻底废除了“整文件覆盖 `dist/customScheme.js`”和“静态改写 12MB 混淆 `main.js`”的旧路线，重构为**数据解耦、协议零破坏、算力微任务化**的新一代双模架构：

| 模式 | 适用场景 | 核心原理 | 对 `app.asar` 与官方新版本的影响 |
| :--- | :--- | :--- | :--- |
| **模式 A：零改包 CDP 动态汉化**（推荐） | 追求跨版本升级免疫、不想改动安装目录 | 通过 `--remote-debugging-port=58321` 与 WebSocket 实时向页面及 `plugin://swarm` 注入 270KB 运行时引擎 | **100% 不碰 `app.asar`**！保留官方完整数字签名，官方更新至未来小版本依然立刻汉化 |
| **模式 B：ASAR 增量无损补丁** | 习惯直接点桌面原图标启动、希望同步汉化顶部菜单与系统托盘 | 仅在 `dist/preload.js`、`dist/menu.js`、`dist/tray.js`、`dist/main.js`（`plugin://` 子帧）执行标志位截断增量注入 | **保留原生 `dist/customScheme.js` 零改动**（保住 `agy-browser-stream` 等新协议），`--unpack` 隔离体积保持官方原版轻量，支持一键还原 |

---

## 二、核心工程特性

1. **模块化词典资产 (`src/dict/`)**：将 `3,365+` 条纯净、零代码混淆词条拆分为 `common`、`settings`、`chat-agent`、`editor-terminal`、`marketplace`、`plugins-swarm` 6 大领域 JSON，配合 `tools/dict_cli.py` 一键体检（`lint` / `stats` / `find` / `add`）。
2. **微秒级高性能 DOM 引擎 (`src/runtime/`)**：
   - 预编译 `O(1)` 大小写不敏感 `Map` 索引 + ASCII 极速短路 + 有界 LRU 字符串缓存；
   - `queueMicrotask` 微任务并发合并 + DOM 树祖先包含剪枝，消除嵌套递归卡顿；
   - **叶子 `TextNode` 物理隔离**：绝不修改容器 `.textContent` 或 `INPUT.value` / `TEXTAREA.value`，免疫 React Fiber `removeChild` 崩溃，免疫 Monaco 编辑器、xterm 终端、代码与对话正文。
3. **右下角悬浮「中/英」实时切换球**：
   - `WeakMap` 双轨记忆所有节点原文与属性；
   - **左键单击**：毫秒级中/英文原版无损热切换（无需重启）；
   - **右键 / 双击菜单**：支持勾选「**专业选项名保留英文**」（保留 `Extra High`、`Turbo`、`Request Review` 等英文对照）或一键整页重扫。
4. **AI 只读界面巡检 (`tools/live_audit.py`)**：通过 CDP 读取当前窗口中尚未收录的英文控件文本，几秒精准输出增量词条清单，告别盲目扒取 12MB 混淆 Bundle。

---

## 三、快速使用

```bash
# 方式 1（推荐·零改包 CDP 模式，升级免疫）
python chameleon.py --cdp
# Windows 亦可直接双击：一键启动_CDP零改包汉化.bat

# 方式 2（ASAR 增量无损补丁模式，免开调试端口，含原生菜单/托盘）
# 请先手动完全退出 Antigravity（含系统托盘）
python chameleon.py --patch
# Windows 亦可直接双击：一键安装_增量无损补丁.bat

# 查看当前客户端状态与官方协议完整性
python chameleon.py --status

# 一键还原纯净官方原版
python chameleon.py --restore
```

---

## 四、目录结构与开发校验

```text
├── chameleon.py                  # 统一双模主控制台入口
├── src/
│   ├── dict/*.json               # 6 大领域模块化 JSON 词典 (3,365+ 条)
│   ├── native-menu.json          # Electron 原生顶部菜单与托盘翻译映射
│   ├── runtime/
│   │   ├── rules.js              # 动态正则、倒计时、权限目标保护与免疫守卫
│   │   └── engine.js             # O(1) 引擎、微任务调度、WeakMap 切换与悬浮球
│   └── patcher/
│       ├── cdp_injector.py       # 零侵入 CDP 热注入守护模块
│       └── asar_patcher.py       # 标志截断式 ASAR 增量注入与纯净还原模块
├── tools/
│   ├── build_overlay.py          # 编译与 Node 语法验证 dist/chameleon-overlay.js
│   ├── dict_cli.py               # 词典增删查与自动化 Lint 体检门禁
│   └── live_audit.py             # 运行时可见英文差异巡检工具
└── tests/
    ├── engine.test.mjs           # Node.js 运行时规则、权限保护与沙箱编译测试
    └── test_v3_patcher.py        # 增量补丁幂等性、可逆性、语法与零强杀测试
```

运行全套自检与自动化测试：

```bash
python tools/dict_cli.py lint
python tools/build_overlay.py --check
node --test tests/engine.test.mjs
python -m unittest discover -s tests -p "test_*.py" -v
```
