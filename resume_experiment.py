#!/usr/bin/env python3
"""续跑修复阶段 - 不删除已有结果"""
import subprocess
import sys
import os

os.environ['OPENAI_API_KEY'] = 'sk-0bf8bee2fddb4e62aac3dd52366f564e'
os.environ['OPENAI_BASE_URL'] = 'https://api.deepseek.com'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = f"{SCRIPT_DIR};{SCRIPT_DIR}/agentless"
PYTHON = "D:/Anaconda/envs/python39/python.exe"

# 不清理已有结果！
os.makedirs('results/repair', exist_ok=True)

def run(cmd, desc):
    print(f"\n{'='*60}")
    print(f" {desc}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"❌ {desc} 失败 (exit={result.returncode})")
        sys.exit(1)
    print(f"✅ {desc} 完成")

# Phase 2: Repair (会自动跳过已处理过的实例)
run([
    PYTHON, 'agentless/repair/repair.py',
    '--loc_file=results/location/loc_outputs_codegraph.jsonl',
    '--output_folder=results/repair', '--loc_interval', '--top_n=3',
    '--context_window=10', '--max_samples=10', '--cot', '--diff_format',
    '--gen_and_process', '--repo_graph',
], 'Phase 2/3: Repair')

# Phase 3: Rerank
run([
    PYTHON, 'agentless/repair/rerank.py',
    '--patch_folder=results/repair', '--num_samples=10',
    '--deduplicate', '--plausible',
], 'Phase 3/3: Rerank')

print(f"\n{'='*60}")
print(" 🏁 实验完成！结果在 results/ 目录下")
print(f"{'='*60}")
