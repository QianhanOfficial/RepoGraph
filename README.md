# RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph

# RepoGraph: 通过仓库级代码图增强AI软件工程

## 📜 Overview

## 📜 概述

We introduce RepoGraph, an effective plug-in repo-level module that offers the desired context and substantially boosts the LLMs' AI software engineering capability.

我们提出了RepoGraph，一个高效的即插即用仓库级模块，它提供所需的上下文，并显著提升大语言模型的AI软件工程能力。

## 🆕 News

## 🆕 新闻

We released the first version RepoGraph and its integration with [SWE-bench](https://www.swebench.com/) methods!

我们发布了第一个版本的RepoGraph及其与[SWE-bench](https://www.swebench.com/)方法的集成！

## 🤖 Code Setup

## 🤖 代码设置

### Foder and files

### 文件夹和文件

`repograph` contains the code for construct and retrieve related context from the graph.

`repograph` 包含了用于构建图并从中检索相关上下文的代码。

`agentless` and `SWE-agent` incorporates the integrated version of RepoGraph with the two methods.

`agentless` 和 `SWE-agent` 包含了RepoGraph与这两种方法的集成版本。

Currently this version may take a little long time to run for a repo. We provide a cached version for all repos in SWE-bench, download it from [huggingface datasets](https://huggingface.co/datasets/MrZilinXiao/RepoGraph) or [Google Drive](https://drive.google.com/file/d/1-0d-OgGoOf3i54bWcf8H0egjQyTSZ8dG/view?usp=sharing) and put it under `repo_structures`.

当前版本对一个仓库的运行可能需要较长时间。我们为SWE-bench中的所有仓库提供了缓存版本，可以从[huggingface datasets](https://huggingface.co/datasets/MrZilinXiao/RepoGraph)或[Google Drive](https://drive.google.com/file/d/1-0d-OgGoOf3i54bWcf8H0egjQyTSZ8dG/view?usp=sharing)下载，并将其放在`repo_structures`目录下。

### How to run?

### 如何运行？

To generate the repograph for a given repository, simply run:

要为给定的仓库生成repograph，只需运行：

```bash
python ./repograph/construct_graph.py <dir_to_repo>
```

This will produce two files, `tags_{instance_id}.jsonl` stores the line-level information and `{instance_id}.pkl` is the graph constructed using networkx.

这将生成两个文件，`tags_{instance_id}.jsonl` 存储行级信息，`{instance_id}.pkl` 是使用networkx构建的图。

## Integration with models on SWE-bench

## 与SWE-bench上的模型集成

### Procedural framework

### 过程式框架

For a procedural framework, RepoGraph could be integrated into every step of the pipeline. Refer to `--repo_graph` hyperparameter for controllability in different stages.

对于过程式框架，RepoGraph可以集成到流水线的每个步骤中。请参考`--repo_graph`超参数以控制不同阶段。

To run RepoGraph with Agentless, use command:

要在Agentless中运行RepoGraph，使用以下命令：

```bash
bash run_repograph_agentless.sh
```

### Agent framework

### 智能体框架

To integrate RepoGraph with agent framework such as SWE-agent, we simply add an extra action in its initial action space. Specifically, you can look up for `search_repo()` in corresponding dir. The signature is defined as:

要将RepoGraph与SWE-agent等智能体框架集成，我们只需在其初始动作空间中添加一个额外的动作。具体来说，您可以在相应目录中查找`search_repo()`。其签名定义如下：

```python
search_repo:
    docstring: searches in the current repository with a specific function or class, and returns the def and ref relations for the search term.
    signature: search_repo <search_term>
    arguments:
      - search_term (string) [required]: function or class to look for in the repository.
```

To run RepoGraph with SWE-agent, use command:

要在SWE-agent中运行RepoGraph，使用以下命令：

```bash
bash run_repograph_sweagent.sh
```

We are working on prepreints for details in RepoGraph and a more comprehensive/easy integration with exsiting models. Stay tuned!!

我们正在准备关于RepoGraph细节的预印本，以及与现有模型更全面/更简单的集成方案。敬请期待！！
