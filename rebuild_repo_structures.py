"""
重建 repo_structures/ 目录：
1. 从 RepoGraph_cache 中的 tags_*.json 重建 .pkl 图文件
2. 将 tags 文件复制到 repo_structures/graph/ 下
3. 生成 {instance_id}.json 结构文件（克隆仓库并解析）
"""
import json
import os
import pickle
import sys
import shutil
from pathlib import Path
from collections import Counter

import networkx as nx

# ============ 配置 ============
CACHE_DIR = "./RepoGraph_cache/RepoGraph_cache"  # tags_*.json 所在目录
OUTPUT_DIR = "./repo_structures"
GRAPH_DIR = os.path.join(OUTPUT_DIR, "graph")

# ============ Step 1: tags → pkl ============

def tag_to_graph(tags, verbose=False):
    """从 tags 列表重建 NetworkX MultiDiGraph。
    逻辑与 repograph/construct_graph.py 中的 CodeGraph.tag_to_graph() 一致。
    优化：用 dict 索引 name→def_tags，将 O(n²) ref-def 匹配降为 O(n)。
    """
    G = nx.MultiDiGraph()

    # ---- 1. 添加所有节点 ----
    for tag in tags:
        G.add_node(
            tag['name'],
            category=tag['category'],
            info=tag['info'],
            fname=tag['fname'],
            line=tag['line'],
            kind=tag['kind'],
        )

    # ---- 2. class → method 边 ----
    for tag in tags:
        if tag['category'] == 'class':
            for f in tag['info'].split('\t'):
                f = f.strip()
                if f:
                    G.add_edge(tag['name'], f)

    # ---- 3. ref → def 边（优化版：O(n) 代替 O(n²)） ----
    # 构建 name → [def_tag, ...] 索引
    defs_by_name = {}
    for tag in tags:
        if tag['kind'] == 'def':
            defs_by_name.setdefault(tag['name'], []).append(tag)

    for tag in tags:
        if tag['kind'] == 'ref':
            if tag['name'] in defs_by_name:
                for _ in defs_by_name[tag['name']]:
                    G.add_edge(tag['name'], tag['name'])

    return G


def rebuild_graphs():
    """Step 1 & 2: 从 tags JSON 重建 pkl，并复制 tags 到 graph/ 目录"""
    os.makedirs(GRAPH_DIR, exist_ok=True)

    cache_path = Path(CACHE_DIR)
    if not cache_path.exists():
        print(f"❌ 缓存目录不存在: {CACHE_DIR}")
        sys.exit(1)

    tag_files = sorted(cache_path.glob("tags_*.json"))
    if not tag_files:
        print(f"❌ 在 {CACHE_DIR} 中未找到 tags_*.json 文件")
        sys.exit(1)

    print(f"📦 找到 {len(tag_files)} 个 tags 文件")

    skipped = 0
    rebuilt = 0
    for tf in tag_files:
        # 提取 instance_id: tags_django__django-15814.json → django__django-15814
        instance_id = tf.stem.replace("tags_", "", 1)

        pkl_path = os.path.join(GRAPH_DIR, f"{instance_id}.pkl")
        target_tags_path = os.path.join(GRAPH_DIR, f"tags_{instance_id}.json")

        # 如果 pkl 已存在则跳过
        if os.path.exists(pkl_path):
            skipped += 1
            continue

        print(f"  🔨 [{rebuilt+1}/{len(tag_files)}] {instance_id} ...", end=" ")

        try:
            with open(tf, 'r', encoding='utf-8') as f:
                tags = json.load(f)

            # 构建图
            G = tag_to_graph(tags)

            # 保存 pkl
            with open(pkl_path, 'wb') as f:
                pickle.dump(G, f)

            # 复制 tags 到 graph/ 目录（如果尚未存在）
            if not os.path.exists(target_tags_path):
                shutil.copy2(str(tf), target_tags_path)

            print(f"✅ 节点={len(G.nodes)}, 边={len(G.edges)}")
            rebuilt += 1

        except Exception as e:
            print(f"❌ 失败: {e}")

    print(f"\n🏁 图重建完成: 新建 {rebuilt}, 跳过 {skipped}, 共 {len(tag_files)}")


# ============ Step 3: 生成 {instance_id}.json 结构文件 ============

def check_structure_files():
    """检查还有哪些 {instance_id}.json 结构文件缺失"""
    cache_path = Path(CACHE_DIR)
    tag_files = sorted(cache_path.glob("tags_*.json"))

    missing = []
    existing = []
    for tf in tag_files:
        instance_id = tf.stem.replace("tags_", "", 1)
        structure_file = os.path.join(OUTPUT_DIR, f"{instance_id}.json")
        if not os.path.exists(structure_file):
            missing.append(instance_id)
        else:
            existing.append(instance_id)

    return missing, existing


def main():
    print("=" * 60)
    print("RepoGraph repo_structures 重建工具")
    print("=" * 60)

    # Step 1 & 2: 重建 pkl + 复制 tags
    print("\n📌 Step 1 & 2: 重建 .pkl 图 + 复制 tags 文件\n")
    rebuild_graphs()

    # Step 3: 检查结构文件
    print("\n📌 Step 3: 检查 {instance_id}.json 结构文件\n")
    missing, existing = check_structure_files()
    print(f"  已存在: {len(existing)} 个")
    print(f"  缺失:   {len(missing)} 个")

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个结构文件。")
        print("   这些文件包含仓库的 AST 解析结构（类/函数的行号和文本内容）。")
        print("   运行以下命令生成（需要克隆仓库，耗时较长）：")
        print(f"\n   python rebuild_repo_structures.py --build-structures")
        print(f"\n   注意: 在 localize.py 中，如果 PROJECT_FILE_LOC 指向的文件不存在，")
        print(f"   代码会调用 get_project_structure_from_scratch() 自动克隆并生成结构。")
        print(f"   但 repair.py 没有这个 fallback，因此结构文件是必需的。")
    else:
        print("\n✅ 所有结构文件已就绪！")

    print("\n" + "=" * 60)
    print("目录结构：")
    if os.path.exists(GRAPH_DIR):
        pkl_count = len([f for f in os.listdir(GRAPH_DIR) if f.endswith('.pkl')])
        tags_count = len([f for f in os.listdir(GRAPH_DIR) if f.startswith('tags_')])
        print(f"  {GRAPH_DIR}/")
        print(f"    ├── *.pkl           × {pkl_count}")
        print(f"    └── tags_*.json     × {tags_count}")
    struct_count = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json') and not f.startswith('tags_')])
    print(f"  {OUTPUT_DIR}/")
    print(f"    └── *.json           × {struct_count} (结构文件)")
    print("=" * 60)


def build_structures():
    """生成 {instance_id}.json 结构文件（每个仓库克隆一次，切换 commit 复用）"""
    import subprocess
    import shutil
    import time
    from datasets import load_dataset

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agentless', 'get_repo_structure'))
    from get_repo_structure import create_structure, repo_to_top_folder

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("playground", exist_ok=True)

    swe_bench_data = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")

    # 按 repo 分组，每个 repo 只需克隆一次
    repo_instances = {}
    for bug in swe_bench_data:
        repo = bug["repo"]
        if repo not in repo_instances:
            repo_instances[repo] = []
        repo_instances[repo].append(bug)

    print(f"📦 共 {len(repo_instances)} 个仓库，{len(swe_bench_data)} 个实例\n")

    for repo_name, bugs in repo_instances.items():
        top_folder = repo_to_top_folder[repo_name]
        repo_path = os.path.join("playground", top_folder)
        start_time = time.time()

        # 克隆仓库（如果尚未克隆）
        if not os.path.exists(repo_path):
            print(f"⬇️  克隆 {repo_name} ...", end=" ", flush=True)
            try:
                subprocess.run(
                    ["git", "clone", f"https://github.com/{repo_name}.git", repo_path],
                    check=True, capture_output=True, text=True
                )
                print("✅")
            except subprocess.CalledProcessError as e:
                print(f"❌ 克隆失败: {e.stderr[:200]}")
                continue
        else:
            print(f"📂 {repo_name} 已存在，复用")

        # 对每个实例，checkout + 生成结构
        for i, bug in enumerate(bugs):
            instance_id = bug["instance_id"]
            structure_file = os.path.join(OUTPUT_DIR, f"{instance_id}.json")

            if os.path.exists(structure_file):
                continue

            try:
                # checkout 到指定 commit
                subprocess.run(
                    ["git", "-C", repo_path, "checkout", "--force", bug["base_commit"]],
                    check=True, capture_output=True, text=True
                )

                # 解析结构
                structure = create_structure(repo_path)

                d = {
                    "repo": bug["repo"],
                    "base_commit": bug["base_commit"],
                    "structure": structure,
                    "instance_id": instance_id,
                }

                with open(structure_file, 'w', encoding='utf-8') as f:
                    json.dump(d, f)

                if (i + 1) % 20 == 0 or i == len(bugs) - 1:
                    elapsed = time.time() - start_time
                    print(f"  📝 {repo_name}: {i+1}/{len(bugs)} ({elapsed:.0f}s)")

            except Exception as e:
                print(f"  ❌ {instance_id}: {e}")

        # 清理此仓库（释放磁盘空间）
        shutil.rmtree(repo_path, ignore_errors=True)
        elapsed = time.time() - start_time
        print(f"  🗑️  清理 {repo_name} (耗时 {elapsed:.0f}s)\n")

    # 统计
    existing = len([f for f in os.listdir(OUTPUT_DIR)
                    if f.endswith('.json') and not f.startswith('tags_')])
    print(f"🏁 结构文件生成完成: {existing}/300")


if __name__ == "__main__":
    if "--build-structures" in sys.argv:
        build_structures()
    else:
        main()
