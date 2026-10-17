# -*- coding: utf-8 -*-
"""
汉化 bundle 安全校验器
检查翻译后的 Antigravity UI bundle 是否把"程序标识"也汉化了。
任何一项不为 0，都说明界面文案翻译侵入了代码逻辑，会导致会话白屏 / 快捷键失效等问题。
用法: python verify_bundle.py <bundle.js>
"""
import re
import sys
import collections

CJK = r'[^"\n\\]*[\u4e00-\u9fff][^"\n\\]*'

SENS_KEYS = (
    "type|kind|role|id|key|name|class|className|state|status|mode|action|event|category|"
    "level|severity|direction|variant|source|target|language|value|view|screen|group|step|"
    "phase|stage|result|reason|origin|icon|color|unit|format|method|op|channel|provider|"
    "model|engine|backend|scope|owner|author|sender|intent|outcome|tab|section|pane|part|"
    "field|prop|attr|selector|tag|ns|prefix|suffix|alias|code|slug|token|topic|targetScreen|"
    "activeScreen|modalType|home|unsandboxed|binding|shortcut|command|when|scheme|protocol|"
    "extension|package|module|file|path|convoState|itemType|nodeType|blockType|entryType|"
    "viewType|paneType|argName|param|option|flag|groupKey|displayName"
)

CHECKS = [
    ("相等比较中的中文", r'(?:===|!==|==)\s*"(' + CJK + r')"'),
    ("switch case 中文", r'\bcase\s*"(' + CJK + r')"\s*:'),
    ("枚举属性中文值", r'\b(?:' + SENS_KEYS + r')\s*:\s*"(' + CJK + r')"'),
    ("对象键被译成中文", r'(?:\{|,)\s*"(' + CJK + r')"\s*:'),
]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("用法: python verify_bundle.py <bundle.js>")
        return 1
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    print(f"校验文件: {path}")
    print(f"文件大小: {len(content)} 字符\n")

    total_bad = 0
    for label, pattern in CHECKS:
        hits = collections.Counter()
        for m in re.finditer(pattern, content):
            frag = content[max(0, m.start() - 60):m.end() + 15].replace('\n', ' ')
            hits[frag] += 1
        total = sum(hits.values())
        total_bad += total
        status = "OK" if total == 0 else "发现问题"
        print(f"[{status}] {label}: {total} 处")
        for frag, n in hits.most_common(8):
            print(f"    x{n}  ...{frag[-105:]}")
        print()

    print("=" * 60)
    if total_bad == 0:
        print("校验通过：未发现程序标识被汉化的情况。")
    else:
        print(f"校验失败：仍有 {total_bad} 处程序标识被汉化。")
    return 0 if total_bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
