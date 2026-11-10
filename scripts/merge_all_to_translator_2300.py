# -*- coding: utf-8 -*-
"""
merge_all_to_translator_2300.py
将 2.30.0 审计出的三大词典全面、安全、无死角地合并入 translate_ui.py
"""
import os
import re
import json

def clean_key_val(k, v):
    k = k.strip()
    v = v.strip()
    # 如果整个 k 被双引号包裹且内部没有多余的双引号，剥掉外层双引号
    if k.startswith('"') and k.endswith('"') and k[1:-1].count('"') == 0 and ':' not in k:
        k = k[1:-1]
    if v.startswith('"') and v.endswith('"') and v[1:-1].count('"') == 0 and ':' not in v:
        v = v[1:-1]
    return k, v

def main():
    repo_root = r"G:\Antigravity\Project-Chameleon-Repo"
    translate_ui_path = os.path.join(repo_root, "scripts", "translate_ui.py")
    
    with open(translate_ui_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 读取三大词典
    s_path = r"G:\Antigravity\scratch\settings_menus_audit_result.json"
    a_path = r"G:\Antigravity\scratch\agent_team_workflow_dict.json"
    c_path = r"G:\Antigravity\scratch\code_editor_terminal_dict.json"

    with open(s_path, "r", encoding="utf-8") as f:
        s_data = json.load(f)
    with open(a_path, "r", encoding="utf-8") as f:
        a_data = json.load(f)
    with open(c_path, "r", encoding="utf-8") as f:
        c_data = json.load(f)

    dict1 = s_data.get("translations", {})
    dict2 = {}
    dict2.update(a_data.get("translations", {}))
    dict2.update(a_data.get("dynamicDict", {}))
    dict3 = c_data

    all_raw = {}
    for d in [dict1, dict2, dict3]:
        for k, v in d.items():
            ck, cv = clean_key_val(k, v)
            all_raw[ck] = cv

    # 2. 安全过滤：严格执行【严禁裸短词策略】
    filtered_new = {}
    skipped = []
    
    for k, v in all_raw.items():
        raw_k = k.strip()
        # 处理那 6 个特殊裸词
        if raw_k == "Goals":
            filtered_new['title:"Goals"'] = 'title:"目标"'
            continue
        if raw_k in ["Subagents", "Working", "Completed", "Cancelled", "Proceed"]:
            skipped.append((k, v, "高危裸词枚举保护"))
            continue
            
        filtered_new[k] = v

    print(f"Total cleaned raw candidates: {len(all_raw)}")
    print(f"Skipped dangerous entries: {len(skipped)}")
    for s in skipped:
        print(f"  Skipped: {s[0]} -> {s[1]} ({s[2]})")
    print(f"Safe entries to merge: {len(filtered_new)}")

    # 3. 提取 translate_ui.py 中现有的 translations 键
    m_trans = re.search(r'translations\s*=\s*\{([\s\S]+?)\n\s*\}\n\s*print\("Applying translations\.\.\."\)', content)
    if not m_trans:
        raise RuntimeError("Could not locate translations dict in translate_ui.py")
    
    trans_body = m_trans.group(1)
    
    # 提取现有已有的键，避免重复插入
    existing_keys = set()
    for line in trans_body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        km = re.match(r'^(?:\"([^\"]+)\"|\'([^\']+)\'|([^:]+))\s*:', line)
        if km:
            k = km.group(1) or km.group(2) or km.group(3)
            if k:
                existing_keys.add(k.strip())

    to_add_static = {}
    for k, v in filtered_new.items():
        if k not in existing_keys:
            to_add_static[k] = v

    print(f"New static translations to add: {len(to_add_static)}")

    # 使用 json.dumps 保证 100% 合法 Python 字典语法
    addition_lines = ["\n        # --- 2.30.0 Audit Merged Entries ---"]
    for k, v in to_add_static.items():
        k_str = json.dumps(k, ensure_ascii=False)
        v_str = json.dumps(v, ensure_ascii=False)
        addition_lines.append(f'        {k_str}: {v_str},')

    new_trans_body = trans_body + "\n".join(addition_lines)
    content = content[:m_trans.start(1)] + new_trans_body + content[m_trans.end(1):]
    print("Successfully merged new entries into translations dict!")

    # 4. 合并入 dom_translator_js 中的 dynamicDict
    m_dyn = re.search(r'const dynamicDict\s*=\s*\{([\s\S]+?)\n\s*\};;;', content)
    if m_dyn:
        dyn_body = m_dyn.group(1)
        existing_dyn = set()
        for line in dyn_body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            km = re.match(r'^\"([^\"]+)\"\s*:', line)
            if km:
                existing_dyn.add(km.group(1).strip())

        to_add_dyn = {}
        for k, v in filtered_new.items():
            if ":" not in k and not k.startswith("title:") and not k.startswith("label:"):
                if k not in existing_dyn:
                    to_add_dyn[k] = v

        print(f"New dynamicDict entries to add: {len(to_add_dyn)}")
        dyn_lines = ["\n    // --- 2.30.0 Dynamic Audit Entries ---"]
        for k, v in to_add_dyn.items():
            k_str = json.dumps(k, ensure_ascii=False)
            v_str = json.dumps(v, ensure_ascii=False)
            dyn_lines.append(f'    {k_str}: {v_str},')
        
        new_dyn_body = dyn_body + "\n".join(dyn_lines)
        content = content[:m_dyn.start(1)] + new_dyn_body + content[m_dyn.end(1):]
        print("Successfully merged new entries into dynamicDict!")
    else:
        print("[!] Warning: dynamicDict not found in dom_translator_js")

    # 5. 将 15 组动态正则注入到 translateDynamicRegex
    m_reg = re.search(r'const translateDynamicRegex\s*=\s*\(text\)\s*=>\s*\{([\s\S]+?)\};\n\n\s*const translateText', content)
    if m_reg:
        regex_rules = a_data.get("dynamicRegex", [])
        js_regex_blocks = [
            "    if (!text || typeof text !== 'string') return text;",
            "    const t = text.trim();",
            "    // --- 2.30.0 Side Questions & Agent Team Dynamic Regex ---"
        ]
        for r in regex_rules:
            desc = r.get("description")
            pat = r.get("pattern")
            rep = r.get("replacement")
            js_regex_blocks.append(f"    // {desc}")
            js_regex_blocks.append(f"    if (/{pat}/.test(t)) {{")
            js_regex_blocks.append(f"      return text.replace(/{pat}/, \"{rep}\");")
            js_regex_blocks.append(f"    }}")

        if "2.30.0 Side Questions & Agent Team Dynamic Regex" not in content:
            new_reg_code = "\n" + "\n".join(js_regex_blocks) + "\n" + m_reg.group(1)
            content = content[:m_reg.start(1)] + new_reg_code + content[m_reg.end(1):]
            print(f"Successfully injected {len(regex_rules)} dynamic regex rules into translateDynamicRegex!")
        else:
            print("Dynamic regex rules already present, skipping.")
    else:
        print("[!] Warning: translateDynamicRegex not matched for injection!")

    # 6. 在斜杠命令注入中添加 /btw
    if '"/btw":' not in content:
        old_slash_str = '"boost":{{n:"深度增强 (/boost)",d:"启用多视角深度思考、战略规划与严格验证"}},"/boost":{{n:"深度增强 (/boost)",d:"启用多视角深度思考、战略规划与严格验证"}}}}'
        new_slash_str = '"boost":{{n:"深度增强 (/boost)",d:"启用多视角深度思考、战略规划与严格验证"}},"/boost":{{n:"深度增强 (/boost)",d:"启用多视角深度思考、战略规划与严格验证"}},"btw":{{n:"侧边提问 (/btw)",d:"在独立轻量面板中发起旁支提问，不阻塞主会话流"}},"/btw":{{n:"侧边提问 (/btw)",d:"在独立轻量面板中发起旁支提问，不阻塞主会话流"}}}}'
        if old_slash_str in content:
            content = content.replace(old_slash_str, new_slash_str)
            print("Successfully injected /btw into slash commands map!")
        else:
            print("[!] Warning: old_slash_str pattern not matched")

    # 7. 写回 translate_ui.py
    with open(translate_ui_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Finished merging all dictionaries into translate_ui.py successfully!")

if __name__ == "__main__":
    main()
