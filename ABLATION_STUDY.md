# Ablation Study Guide

## 概述

消融实验用于验证系统中各个组件的有效性。本研究评估两个核心组件：
1. **依赖检索策略** (Dependency Retrieval): 是否包含函数/方法的调用关系信息
2. **Prompt 优化** (Prompt Optimization): 是否使用精心设计的 prompt 模板

## 实验设计

### 四种实验模式

| 模式 | 依赖信息 | Prompt优化 | 说明 |
|------|---------|-----------|------|
| `full` | ✅ | ✅ | 完整系统（对照组） |
| `no_dep` | ❌ | ✅ | 移除依赖信息 |
| `no_prompt` | ✅ | ❌ | 使用简化prompt |
| `baseline` | ❌ | ❌ | 最小配置（基线） |

### 评估维度

**定量指标：**
- 文档长度（tokens/words）
- 生成时间
- 覆盖率（文档化的函数比例）
- 结构完整性（sections数量）

**定性指标：**
- 完整性：是否涵盖所有功能
- 准确性：描述是否正确
- 清晰度：是否易于理解
- 上下文：是否解释了关系和用途

## 使用方法

### 1. 运行单个实验

```bash
# Full模式（默认）
python main.py --target_path ./sample --ablation_mode full

# 无依赖模式
python main.py --target_path ./sample --ablation_mode no_dep

# 无prompt优化模式
python main.py --target_path ./sample --ablation_mode no_prompt

# 基线模式
python main.py --target_path ./sample --ablation_mode baseline
```

输出目录会自动命名为 `docs_ablation_<mode>`

### 2. 批量运行所有实验

```bash
# 运行所有4种模式
python run_ablation.py --target_path ./sample

# 只运行特定模式
python run_ablation.py --target_path ./sample --modes full no_dep

# 自定义输出目录
python run_ablation.py --target_path ./sample --output_base ./my_ablation_results

# 测试模式（只处理tests文件夹）
python run_ablation.py --target_path ./Small-Size/numpy --test_mode
```

这会生成：
- `ablation_results/ablation_full/` - Full模式文档
- `ablation_results/ablation_no_dep/` - 无依赖模式文档
- `ablation_results/ablation_no_prompt/` - 无prompt优化文档
- `ablation_results/ablation_baseline/` - 基线模式文档
- `ablation_results/ablation_report.md` - 执行报告
- `ablation_results/ablation_results.json` - 原始结果数据

### 3. 评估和对比结果

```bash
# 分析生成的文档质量
python evaluate_ablation.py --base_dir ablation_results

# 自定义输出路径
python evaluate_ablation.py --base_dir ablation_results --output my_evaluation.md
```

这会生成：
- `ablation_evaluation.md` - 详细的对比报告
- `ablation_evaluation.json` - 量化指标数据

## 完整工作流示例

```bash
# Step 1: 运行所有消融实验
python run_ablation.py \
    --target_path ./Small-Size/numpy \
    --output_base ./numpy_ablation \
    --test_mode

# Step 2: 评估结果
python evaluate_ablation.py \
    --base_dir ./numpy_ablation \
    --output ./numpy_ablation_report.md

# Step 3: 查看报告
cat ./numpy_ablation_report.md
```

## 结果分析指南

### 1. 依赖信息的影响

对比 `full` vs `no_dep`：
- 文档长度差异 → 依赖信息增加了多少内容
- 上下文完整性 → 是否帮助理解函数用途
- 可用性 → 开发者是否能更快理解代码

### 2. Prompt优化的影响

对比 `full` vs `no_prompt`：
- 文档结构 → 优化后的prompt是否产生更好的组织
- 描述质量 → 是否更清晰、更专业
- 一致性 → 不同函数的文档风格是否统一

### 3. 综合影响

对比 `full` vs `baseline`：
- 整体提升幅度
- 两个组件是否有协同效应

### 4. 人工评估建议

从每个模式随机抽取5-10个文档，让3-5名开发者评分（1-5分）：

**评分维度：**
1. **完整性** - 是否涵盖所有重要信息
2. **准确性** - 描述是否正确无误
3. **清晰度** - 是否易于理解
4. **实用性** - 是否对实际开发有帮助
5. **整体质量** - 综合评价

**评估表格模板：**

| 文档 | 模式 | 完整性 | 准确性 | 清晰度 | 实用性 | 整体 | 备注 |
|------|------|--------|--------|--------|--------|------|------|
| func1.md | full | 5 | 4 | 5 | 5 | 5 | 依赖信息很有用 |
| func1.md | no_dep | 4 | 4 | 4 | 3 | 4 | 缺少上下文 |
| ... | ... | ... | ... | ... | ... | ... | ... |

## 统计显著性检验

如果需要发表论文，建议进行统计检验：

```python
from scipy import stats

# 示例：比较full和no_dep的文档长度
full_lengths = [...]  # 从评估结果中提取
no_dep_lengths = [...]

# t检验
t_stat, p_value = stats.ttest_ind(full_lengths, no_dep_lengths)
print(f"t-statistic: {t_stat}, p-value: {p_value}")

# 如果 p < 0.05，差异显著
```

## 可视化建议

使用生成的JSON数据创建图表：

```python
import matplotlib.pyplot as plt
import json

# 加载数据
with open('ablation_evaluation.json') as f:
    data = json.load(f)

# 绘制对比图
modes = ['full', 'no_dep', 'no_prompt', 'baseline']
text_tokens = [data[m]['text_tokens']['mean'] for m in modes]

plt.bar(modes, text_tokens)
plt.ylabel('Average Text Tokens')
plt.title('Documentation Length Across Ablation Modes')
plt.savefig('ablation_comparison.png')
```

## 论文写作建议

### Results部分结构

```markdown
### 5.1 Ablation Study

We conducted an ablation study to evaluate the contribution of:
(1) dependency retrieval strategy, and 
(2) prompt optimization.

**Experimental Setup:** We tested four configurations on [dataset description]...

**Quantitative Results:** Table X shows the metrics across modes...

**Qualitative Analysis:** Manual evaluation by N developers revealed...

**Key Findings:**
- Dependency information increased documentation completeness by X%
- Prompt optimization improved clarity scores by Y%
- Combined effect showed Z% improvement over baseline
```

### 表格示例

```markdown
Table 1: Ablation Study Results

| Mode | Avg Tokens | Sections | Dep Coverage | Quality Score |
|------|-----------|----------|--------------|---------------|
| Full | 245.3 | 4.2 | 87% | 4.3/5 |
| No Dep | 198.7 | 3.8 | 0% | 3.7/5 |
| No Prompt | 223.1 | 3.5 | 85% | 3.9/5 |
| Baseline | 176.4 | 3.1 | 0% | 3.2/5 |
```

## 常见问题

**Q: 为什么no_dep模式仍然显示有依赖信息？**
A: 检查 `--relevant` 参数是否正确设置为 False

**Q: 如何确保实验的公平性？**
A: 使用相同的LLM、相同的temperature、相同的测试集

**Q: 需要运行多少次实验？**
A: 建议至少3次，取平均值以减少随机性影响

**Q: 如何处理LLM的随机性？**
A: 设置 `temperature=0` 或运行多次取平均

## 扩展实验

可以进一步探索：
1. 不同prompt模板的对比
2. 不同依赖深度（1层 vs 2层 vs 全部）
3. 不同LLM模型的对比
4. 不同项目规模的影响

## 参考资料

- [Ablation Studies in NLP](https://arxiv.org/abs/2201.08239)
- [Evaluating Code Documentation Quality](https://arxiv.org/abs/2004.02311)
