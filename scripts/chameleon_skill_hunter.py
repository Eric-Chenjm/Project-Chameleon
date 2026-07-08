import os
import json
import re

def is_english_text(text):
    """
    检查文本是否为全英文（即不包含中文字符）。
    """
    if not text:
        return False
    # 如果包含任何中文字符，则认为不是纯英文
    return not bool(re.search(r'[\u4e00-\u9fff]', text))

def extract_frontmatter(file_path):
    """
    提取 SKILL.md 的 frontmatter 中的 name 和 description
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    
    # 提取以 --- 开头和结尾的部分
    match = re.search(r'^---\s*(.*?)\s*---', content, re.DOTALL)
    if not match:
        return None
        
    frontmatter = match.group(1)
    
    name_match = re.search(r'^name:\s*(.*?)$', frontmatter, re.MULTILINE)
    desc_match = re.search(r'^description:\s*(.*?)$', frontmatter, re.MULTILINE)
    
    if name_match and desc_match:
        name = name_match.group(1).strip().strip("'\"")
        description = desc_match.group(1).strip().strip("'\"")
        return {"name": name, "description": description, "path": file_path}
        
    return None

def main():
    search_dirs = [
        r"C:\Users\90513\.gemini\config\skills",
        r"C:\Users\90513\.gemini\config\plugins"
    ]
    
    new_skills = []
    
    print("Searching for SKILL.md files...")
    for directory in search_dirs:
        if not os.path.exists(directory):
            print(f"Warning: Directory not found: {directory}")
            continue
            
        for root, dirs, files in os.walk(directory):
            if "SKILL.md" in files:
                file_path = os.path.join(root, "SKILL.md")
                skill_info = extract_frontmatter(file_path)
                
                if skill_info:
                    # 判断描述是否为英文（以此作为是否需要汉化的依据）
                    if is_english_text(skill_info["description"]):
                        new_skills.append(skill_info)

    output_file = "new_skills_to_translate.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(new_skills, f, indent=4, ensure_ascii=False)
        print(f"Found {len(new_skills)} English skills to translate.")
        print(f"Dumped to {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

if __name__ == "__main__":
    main()
