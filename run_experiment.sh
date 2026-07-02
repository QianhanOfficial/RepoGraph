#!/usr/bin/env bash
# ============================================================
# RepoGraph + Agentless 实验运行脚本
# Python 3.9 (conda) + DeepSeek API
# 使用方法: bash run_experiment.sh
# ============================================================
set -e

# ---- 环境变量（运行前请设置）----
# export OPENAI_API_KEY="your-api-key"
# export OPENAI_BASE_URL="https://api.deepseek.com"

# ---- Python 3.9 ----
PYTHON="D:/Anaconda/envs/python39/python.exe"

# ---- PYTHONPATH ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${SCRIPT_DIR}/agentless"

echo "============================================"
echo " RepoGraph + Agentless 实验"
echo " Python : $($PYTHON --version)"
echo " API    : $OPENAI_BASE_URL"
echo " Model  : deepseek-v4-pro"
echo "============================================"

# ---- 清理旧结果 ----
rm -rf results
mkdir -p results/location results/repair

# ===== Phase 1: 故障定位 =====
echo ""
echo "===== Phase 1/3: Localization ====="
$PYTHON agentless/fl/localize.py \
    --file_level \
    --related_level \
    --fine_grain_line_level \
    --output_folder=results/location \
    --top_n=3 \
    --compress \
    --context_window=10 \
    --repo_graph
echo "✅ Phase 1 完成"

# ===== Phase 2: 修复生成 =====
echo ""
echo "===== Phase 2/3: Repair ====="
$PYTHON agentless/repair/repair.py \
    --loc_file=results/location/loc_outputs_codegraph.jsonl \
    --output_folder=results/repair \
    --loc_interval \
    --top_n=3 \
    --context_window=10 \
    --max_samples=10 \
    --cot \
    --diff_format \
    --gen_and_process \
    --repo_graph
echo "✅ Phase 2 完成"

# ===== Phase 3: 重排序 =====
echo ""
echo "===== Phase 3/3: Rerank ====="
$PYTHON agentless/repair/rerank.py \
    --patch_folder=results/repair \
    --num_samples=10 \
    --deduplicate \
    --plausible
echo "✅ Phase 3 完成"

echo ""
echo "============================================"
echo " 🏁 实验完成！"
echo " 结果位置: results/"
echo "============================================"
