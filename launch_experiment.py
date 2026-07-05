#!/usr/bin/env python3
"""RepoGraph + Agentless 实验启动器"""
import subprocess
import sys
import os

# API 配置
os.environ['OPENAI_API_KEY'] = 'sk-0bf8bee2fddb4e62aac3dd52366f564e'
os.environ['OPENAI_BASE_URL'] = 'https://api.deepseek.com'

# 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ['PYTHONPATH'] = f"{SCRIPT_DIR};{SCRIPT_DIR}/agentless"
PYTHON = "D:/Anaconda/envs/python39/python.exe"

# 清理旧结果
import shutil
shutil.rmtree('results', ignore_errors=True)
os.makedirs('results/location', exist_ok=True)
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

# Phase 1: Localization
run([
    PYTHON, 'agentless/fl/localize.py',
    '--file_level', '--related_level', '--fine_grain_line_level',
    '--output_folder=results/location', '--output_file=loc_outputs_codegraph.jsonl',
    '--top_n=3', '--compress',
    '--context_window=10', '--repo_graph',
], 'Phase 1/3: Localization')

# Phase 2: Repair
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
