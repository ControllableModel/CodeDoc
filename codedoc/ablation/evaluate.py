"""
Ablation Study Evaluation
评估和对比不同消融实验的文档质量
"""
import json
import argparse
from pathlib import Path
from collections import defaultdict
import re


def count_tokens(text):
    """简单的token计数（按空格分词）"""
    return len(text.split())


def analyze_document(md_path):
    """分析单个文档的指标"""
    if not md_path.exists():
        return None
    
    content = md_path.read_text(encoding='utf-8')
    
    # 提取代码块
    code_blocks = re.findall(r'```[\s\S]*?```', content)
    code_content = '\n'.join(code_blocks)
    text_content = re.sub(r'```[\s\S]*?```', '', content)
    
    # 计算指标
    metrics = {
        "total_length": len(content),
        "total_tokens": count_tokens(content),
        "text_tokens": count_tokens(text_content),
        "code_tokens": count_tokens(code_content),
        "num_sections": len(re.findall(r'^##\s+', content, re.MULTILINE)),
        "num_code_blocks": len(code_blocks),
        "has_dependencies": "Dependencies" in content or "Uses" in content,
        "has_dependents": "Dependents" in content or "Used by" in content,
        "avg_section_length": 0
    }
    
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    if sections:
        metrics["avg_section_length"] = sum(len(s) for s in sections) / len(sections)
    
    return metrics


def compare_modes(base_dir):
    """对比不同模式的文档"""
    modes = ['full', 'no_dep', 'no_prompt', 'baseline']
    results = defaultdict(lambda: defaultdict(list))
    
    for mode in modes:
        mode_dir = Path(base_dir) / f"ablation_{mode}"
        if not mode_dir.exists():
            print(f"⚠️  Directory not found: {mode_dir}")
            continue
        
        print(f"\n📊 Analyzing {mode}...")
        
        for md_file in mode_dir.rglob("*.md"):
            metrics = analyze_document(md_file)
            if metrics:
                for key, value in metrics.items():
                    results[mode][key].append(value)
    
    return results


def calculate_statistics(values):
    """计算统计指标"""
    if not values:
        return {"mean": 0, "min": 0, "max": 0, "count": 0}
    
    return {
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "count": len(values)
    }


def generate_comparison_report(results, output_path):
    """生成对比报告"""
    report = [
        "# Ablation Study - Quality Evaluation Report\n\n",
        "## Overview\n\n",
        "This report compares documentation quality across different ablation modes.\n\n",
        "## Quantitative Metrics\n\n"
    ]
    
    # 汇总统计
    metrics_to_compare = [
        ("total_tokens", "Total Tokens", "Overall document length"),
        ("text_tokens", "Text Tokens", "Documentation text (excluding code)"),
        ("num_sections", "Sections", "Number of documentation sections"),
        ("num_code_blocks", "Code Blocks", "Number of code examples"),
        ("avg_section_length", "Avg Section Length", "Average characters per section")
    ]
    
    for metric_key, metric_name, description in metrics_to_compare:
        report.append(f"### {metric_name}\n\n")
        report.append(f"*{description}*\n\n")
        report.append("| Mode | Mean | Min | Max | Count |\n")
        report.append("|------|------|-----|-----|-------|\n")
        
        for mode in ['full', 'no_dep', 'no_prompt', 'baseline']:
            if mode in results and metric_key in results[mode]:
                stats = calculate_statistics(results[mode][metric_key])
                report.append(f"| {mode} | {stats['mean']:.1f} | {stats['min']:.1f} | {stats['max']:.1f} | {stats['count']} |\n")
        
        report.append("\n")
    
    # 依赖信息覆盖率
    report.append("### Dependency Information Coverage\n\n")
    report.append("| Mode | Has Dependencies | Has Dependents |\n")
    report.append("|------|------------------|----------------|\n")
    
    for mode in ['full', 'no_dep', 'no_prompt', 'baseline']:
        if mode in results:
            dep_count = sum(results[mode].get("has_dependencies", []))
            dep_total = len(results[mode].get("has_dependencies", []))
            dept_count = sum(results[mode].get("has_dependents", []))
            dept_total = len(results[mode].get("has_dependents", []))
            
            dep_pct = f"{dep_count}/{dep_total} ({100*dep_count/dep_total:.1f}%)" if dep_total > 0 else "N/A"
            dept_pct = f"{dept_count}/{dept_total} ({100*dept_count/dept_total:.1f}%)" if dept_total > 0 else "N/A"
            
            report.append(f"| {mode} | {dep_pct} | {dept_pct} |\n")
    
    report.append("\n")
    
    # 关键发现
    report.append("## Key Findings\n\n")
    
    if 'full' in results and 'no_dep' in results:
        full_tokens = calculate_statistics(results['full'].get('text_tokens', []))['mean']
        no_dep_tokens = calculate_statistics(results['no_dep'].get('text_tokens', []))['mean']
        diff_pct = ((full_tokens - no_dep_tokens) / no_dep_tokens * 100) if no_dep_tokens > 0 else 0
        
        report.append(f"### Impact of Dependency Information\n\n")
        report.append(f"- **Text length difference**: {diff_pct:+.1f}%\n")
        report.append(f"- Adding dependency information {'increases' if diff_pct > 0 else 'decreases'} documentation length by {abs(diff_pct):.1f}%\n\n")
    
    if 'full' in results and 'no_prompt' in results:
        full_tokens = calculate_statistics(results['full'].get('text_tokens', []))['mean']
        no_prompt_tokens = calculate_statistics(results['no_prompt'].get('text_tokens', []))['mean']
        diff_pct = ((full_tokens - no_prompt_tokens) / no_prompt_tokens * 100) if no_prompt_tokens > 0 else 0
        
        report.append(f"### Impact of Prompt Optimization\n\n")
        report.append(f"- **Text length difference**: {diff_pct:+.1f}%\n")
        report.append(f"- Prompt optimization {'increases' if diff_pct > 0 else 'decreases'} documentation length by {abs(diff_pct):.1f}%\n\n")
    
    report.append("## Recommendations\n\n")
    report.append("1. **Manual Quality Review**: Randomly sample documents from each mode for human evaluation\n")
    report.append("2. **User Study**: Have developers rate documentation usefulness\n")
    report.append("3. **Task-based Evaluation**: Test if documentation helps with specific tasks (e.g., bug fixing, feature addition)\n")
    report.append("4. **Automated Metrics**: Consider using BLEU, ROUGE, or BERTScore if reference documentation exists\n\n")
    
    Path(output_path).write_text("".join(report), encoding="utf-8")
    print(f"\n✅ Evaluation report saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ablation study results")
    parser.add_argument('--base_dir', type=str, default='ablation_results',
                       help='Base directory containing ablation results')
    parser.add_argument('--output', type=str, default='ablation_evaluation.md',
                       help='Output report path')
    
    args = parser.parse_args()
    
    print("🔍 Evaluating ablation study results...")
    print(f"Base directory: {args.base_dir}")
    
    results = compare_modes(args.base_dir)
    
    if not results:
        print("❌ No results found to evaluate")
        return
    
    generate_comparison_report(results, args.output)
    
    # Save raw data
    json_output = Path(args.output).with_suffix('.json')
    json_data = {mode: {k: v for k, v in metrics.items()} 
                 for mode, metrics in results.items()}
    json_output.write_text(json.dumps(json_data, indent=2), encoding="utf-8")
    print(f"✅ Raw data saved: {json_output}")


if __name__ == "__main__":
    main()
