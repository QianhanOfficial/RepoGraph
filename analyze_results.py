#!/usr/bin/env python3
"""RepoGraph 实验结果统计分析脚本"""
import json
import os
import sys
from collections import Counter, defaultdict

RESULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def load_jsonl(path):
    """加载 jsonl 文件"""
    data = []
    if not os.path.exists(path):
        print(f"  ⚠ 文件不存在: {path}")
        return data
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def analyze_localization():
    """Phase 1: 定位阶段统计"""
    print("=" * 60)
    print(" Phase 1: Fault Localization (故障定位)")
    print("=" * 60)

    loc_file = os.path.join(RESULT_DIR, "location", "loc_outputs_codegraph.jsonl")
    data = load_jsonl(loc_file)
    total = len(data)

    # 统计各阶段
    file_level_found = 0
    related_found = 0
    edit_loc_found = 0
    file_counts = Counter()
    found_files_list = []

    for item in data:
        found_files = item.get("found_files", [])
        if found_files:
            file_level_found += 1
            file_counts[len(found_files)] += 1
            found_files_list.append(found_files)

        rel = item.get("found_related_locs", [])
        if rel:
            # flatten list of lists
            flat_rel = []
            for r in rel:
                if isinstance(r, list):
                    flat_rel.extend([x for x in r if x and str(x).strip()])
                elif r and str(r).strip():
                    flat_rel.append(r)
            if flat_rel:
                related_found += 1

        edit_locs = item.get("found_edit_locs", [])
        if edit_locs:
            flat_edit = []
            for el in edit_locs:
                if isinstance(el, list):
                    flat_edit.extend([x for x in el if x and str(x).strip()])
                elif el and str(el).strip():
                    flat_edit.append(el)
            if flat_edit:
                edit_loc_found += 1

    print(f"\n  总实例数:       {total}")
    print(f"  文件级定位命中: {file_level_found}/{total} ({file_level_found/total*100:.1f}%)")
    print(f"  相关级定位命中: {related_found}/{total} ({related_found/total*100:.1f}%)")
    print(f"  行级定位命中:   {edit_loc_found}/{total} ({edit_loc_found/total*100:.1f}%)")
    print(f"\n  定位文件数分布:")
    for n in sorted(file_counts.keys()):
        print(f"    {n} 个文件: {file_counts[n]} 个实例 ({file_counts[n]/total*100:.1f}%)")

    return {
        "total": total,
        "file_level_hit": file_level_found,
        "file_level_rate": file_level_found / total * 100,
        "related_hit": related_found,
        "related_rate": related_found / total * 100,
        "edit_loc_hit": edit_loc_found,
        "edit_loc_rate": edit_loc_found / total * 100,
    }


def analyze_repair():
    """Phase 2: 修复阶段统计"""
    print("\n" + "=" * 60)
    print(" Phase 2: Repair (补丁生成)")
    print("=" * 60)

    repair_file = os.path.join(RESULT_DIR, "repair", "output.jsonl")
    data = load_jsonl(repair_file)
    total = len(data)

    with_output = 0
    with_nonempty_output = 0
    total_attempts = 0

    all_output_lens = []

    for item in data:
        raw_outputs = item.get("raw_output", [])
        all_generations = item.get("all_generations", [])
        try_counts = item.get("try_count", [])

        total_attempts += len(raw_outputs)

        for ro in raw_outputs:
            if ro is not None and str(ro).strip():
                with_output += 1
                break

        for gen_list in all_generations:
            if gen_list:
                for gen in gen_list:
                    if gen and str(gen).strip():
                        with_nonempty_output += 1
                        all_output_lens.append(len(str(gen)))
                        break
                if gen_list and any(g and str(g).strip() for g in gen_list):
                    break

    print(f"\n  总实例数:           {total}")
    print(f"  有raw_output:        {with_output}/{total} ({with_output/total*100:.1f}%)")
    print(f"  有all_generations:   {with_nonempty_output}/{total} ({with_nonempty_output/total*100:.1f}%)")
    print(f"  总API调用次数:       {total_attempts}")

    return {
        "total": total,
        "with_output": with_nonempty_output,
        "output_rate": with_nonempty_output / total * 100,
    }


def analyze_rerank():
    """Phase 3: 重排序阶段统计"""
    print("\n" + "=" * 60)
    print(" Phase 3: Rerank (补丁排序)")
    print("=" * 60)

    # 直接统计 output.jsonl 中真正有内容的 raw_output
    repair_file = os.path.join(RESULT_DIR, "repair", "output.jsonl")
    if not os.path.exists(repair_file):
        print("\n  无 output.jsonl")
        return {"total_patches": 0, "nonempty_patches": 0, "patch_rate": 0, "resolved_instances": 0}

    data = load_jsonl(repair_file)
    # 统计有 SEARCH/REPLACE 或 ```diff 等补丁格式的输出
    instances_with_diff = 0
    output_with_search_replace = 0
    all_patches_count = 0

    for item in data:
        raw_outputs = item.get("raw_output", [])
        has_diff = False
        for ro in raw_outputs:
            if ro and str(ro).strip():
                all_patches_count += 1
                if "SEARCH" in str(ro) or "<<<<<<" in str(ro) or "```diff" in str(ro):
                    output_with_search_replace += 1
                    if not has_diff:
                        has_diff = True
                        instances_with_diff += 1

    # 检查 processed 文件
    processed_with_patch = 0
    total_processed = 0
    for i in range(10):
        path = os.path.join(RESULT_DIR, "repair", f"output_{i}_processed.jsonl")
        if os.path.exists(path):
            d = load_jsonl(path)
            total_processed += len(d)
            for item in d:
                mp = item.get("model_patch", "") or ""
                if mp and str(mp).strip():
                    processed_with_patch += 1

    # 检查 normalized 中 model_patch
    norm_with_patch = 0
    total_normalized = 0
    for i in range(10):
        path = os.path.join(RESULT_DIR, "repair", f"output_{i}_normalized.jsonl")
        if os.path.exists(path):
            d = load_jsonl(path)
            total_normalized += len(d)
            for item in d:
                mp = item.get("model_patch", "") or item.get("normalized_patch", "") or ""
                if mp and str(mp).strip():
                    norm_with_patch += 1

    total_instances = len(data)
    print(f"\n  有raw_output实例:           {all_patches_count} 个输出")
    print(f"  含SEARCH/REPLACE格式:        {output_with_search_replace} 个")
    print(f"  有补丁的实例数:              {instances_with_diff}/{total_instances} ({instances_with_diff/total_instances*100:.1f}%)")
    print(f"  Processed 成功提取补丁:      {processed_with_patch}/{total_processed} ({processed_with_patch/total_processed*100:.1f}%)" if total_processed else f"  Processed 成功提取补丁:      0")
    print(f"  Normalized 含 model_patch:   {norm_with_patch}/{total_normalized} ({norm_with_patch/total_normalized*100:.1f}%)" if total_normalized else f"  Normalized 含 model_patch:   0")

    return {
        "total_patches": total_processed,
        "nonempty_patches": processed_with_patch,
        "patch_rate": processed_with_patch / total_processed * 100 if total_processed else 0,
        "resolved_instances": instances_with_diff,
    }


def analyze_log(log_path, label):
    """解析日志中的 API 调用信息"""
    if not os.path.exists(log_path):
        return {}

    with open(log_path, encoding="utf-8", errors="replace") as f:
        content = f.read()

    stats = {
        "label": label,
        "lines": len(content.split("\n")),
        "size_kb": os.path.getsize(log_path) / 1024,
        "prompts": content.count("prompting with message:"),
        "prompt_lines": content.count("prompting with message:\n"),
        "usage_lines": content.count('"prompt_tokens"'),
    }
    return stats


def main():
    print("╔" + "═" * 58 + "╗")
    print("║" + "  RepoGraph + Agentless 实验结果分析".center(50) + "║")
    print("╚" + "═" * 58 + "╝")
    print(f"  结果目录: {RESULT_DIR}\n")

    # Phase 1
    loc_stats = analyze_localization()

    # Phase 2
    repair_stats = analyze_repair()

    # Phase 3
    rerank_stats = analyze_rerank()

    # 日志分析
    print("\n" + "=" * 60)
    print(" 日志统计")
    print("=" * 60)
    localize_log = os.path.join(RESULT_DIR, "location", "localize.log")
    repair_log = os.path.join(RESULT_DIR, "repair", "repair.log")

    loc_log = analyze_log(localize_log, "Localization")
    rep_log = analyze_log(repair_log, "Repair")

    print(f"\n  Localize log: {loc_log.get('lines', 0)} 行, {loc_log.get('size_kb', 0):.0f} KB")
    print(f"  Repair log:   {rep_log.get('lines', 0)} 行, {rep_log.get('size_kb', 0):.0f} KB")

    # 总结
    print("\n" + "=" * 60)
    print(" 总结")
    print("=" * 60)

    total_instances = loc_stats["total"]
    print(f"\n  ┌─────────────────────────────────────────┬──────────┐")
    print(f"  │ 指标                                    │   数值   │")
    print(f"  ├─────────────────────────────────────────┼──────────┤")
    print(f"  │ 总实例数                                │ {total_instances:>6}   │")
    print(f"  │ Phase 1 文件级定位命中率                 │ {loc_stats['file_level_rate']:>5.1f}%  │")
    print(f"  │ Phase 1 相关级定位命中率                 │ {loc_stats['related_rate']:>5.1f}%  │")
    print(f"  │ Phase 1 行级定位命中率                   │ {loc_stats['edit_loc_rate']:>5.1f}%  │")
    print(f"  │ Phase 2 模型有输出比例                   │ {repair_stats['output_rate']:>5.1f}%  │")
    print(f"  │ Phase 2 生成SEARCH/REPLACE补丁实例       │ {rerank_stats['resolved_instances']:>6}   │")
    print(f"  │ Phase 3 成功提取 diff 补丁               │ {rerank_stats['nonempty_patches']:>6}   │")
    print(f"  └─────────────────────────────────────────┴──────────┘")


if __name__ == "__main__":
    main()
