#!/usr/bin/env python3
"""
直接从 raw_output 中提取 SEARCH/REPLACE 补丁，
绕过 Agentless 原有的 repo 克隆验证流程（Windows 兼容问题）。

用法: python patch_extractor.py
"""
import json
import os
import re

RESULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
REPAIR_DIR = os.path.join(RESULT_DIR, "repair")


def parse_search_replace_blocks(text):
    """解析 SEARCH/REPLACE 格式，返回 [(filename, search, replace), ...]"""
    # 匹配: ### filename 后紧跟 <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE
    pattern = r'###\s+(\S+)\s*\n.*?<<<<<<< SEARCH\s*\n(.*?)\n?=======\s*\n(.*?)\n?>>>>>>> REPLACE'
    matches = re.findall(pattern, text, re.DOTALL)
    
    results = []
    for filename, search_content, replace_content in matches:
        results.append({
            "filename": filename.strip(),
            "search": search_content,
            "replace": replace_content,
        })
    return results


def search_replace_to_diff(filename, search_text, replace_text):
    """将 SEARCH/REPLACE 块转换为 unified diff 格式"""
    search_lines = search_text.split('\n')
    replace_lines = replace_text.split('\n')
    
    diff_lines = [f"--- a/{filename}", f"+++ b/{filename}"]
    
    # Approximate @@ line (just use line 1)
    diff_lines.append(f"@@ -1,{len(search_lines)} +1,{len(replace_lines)} @@")
    
    for line in search_lines:
        diff_lines.append(f"-{line}" if line else "-")
    for line in replace_lines:
        diff_lines.append(f"+{line}" if line else "+")
    
    return "\n".join(diff_lines)


def extract_patches():
    """从 output.jsonl 提取所有补丁，写入 improved_normalized/processed 文件"""
    
    output_file = os.path.join(REPAIR_DIR, "output.jsonl")
    if not os.path.exists(output_file):
        print(f"ERROR: {output_file} not found")
        return

    # 加载原始输出
    with open(output_file, encoding="utf-8") as f:
        repair_data = [json.loads(line) for line in f if line.strip()]

    # 为每个 sample (0-9) 创建新的 normalized 输出
    total_instances = len(repair_data)
    extracted_count = 0
    instance_patches = {}  # instance_id -> best patch

    for sample_idx in range(10):
        patches = []
        for item in repair_data:
            instance_id = item["instance_id"]
            raw_outputs = item.get("raw_output", [])
            
            patch_text = ""
            raw_patch_text = ""
            
            if sample_idx < len(raw_outputs):
                ro = raw_outputs[sample_idx]
                if ro and ro.strip():
                    blocks = parse_search_replace_blocks(ro)
                    if blocks:
                        raw_patch_text = ro
                        # 生成 unified diff
                        diffs = []
                        for block in blocks:
                            diff = search_replace_to_diff(
                                block["filename"], block["search"], block["replace"]
                            )
                            diffs.append(diff)
                        patch_text = "\n".join(diffs)
                        
                        # 保存最佳补丁（取第一个有效的）
                        if instance_id not in instance_patches:
                            instance_patches[instance_id] = {
                                "patch": patch_text,
                                "raw": raw_patch_text,
                                "sample": sample_idx,
                            }
                        extracted_count += 1

            patches.append({
                "model_name_or_path": "agentless",
                "instance_id": instance_id,
                "model_patch": patch_text,
                "raw_model_patch": raw_patch_text,
                "normalized_patch": patch_text,
                "original_file_content": "",
            })

        # 写入 improved 文件
        filepath = os.path.join(REPAIR_DIR, f"output_{sample_idx}_improved.jsonl")
        with open(filepath, "w", encoding="utf-8") as f:
            for p in patches:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        print(f"  Written {filepath} ({len(patches)} entries)")
    
    print(f"\n{'='*60}")
    print(f" Patch extraction results")
    print(f"{'='*60}")
    print(f"  Total instances:           {total_instances}")
    print(f"  Instances with patches:    {len(instance_patches)}")
    print(f"  Extraction rate:           {len(instance_patches)/total_instances*100:.1f}%")
    
    # 统计补丁长度
    lens = [len(v["patch"]) for v in instance_patches.values()]
    if lens:
        print(f"  Avg patch length:          {sum(lens)/len(lens):.0f} chars")
        print(f"  Min/Max patch length:      {min(lens)}/{max(lens)} chars")
    
    # 按仓库分组
    repo_patches = {}
    for instance_id, info in instance_patches.items():
        repo = instance_id.split("__")[0]
        repo_patches[repo] = repo_patches.get(repo, 0) + 1
    
    print(f"\n  Patches by repository:")
    for repo in sorted(repo_patches.keys()):
        print(f"    {repo}: {repo_patches[repo]}")


if __name__ == "__main__":
    extract_patches()
