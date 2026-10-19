"""
Ablation Study Runner
运行所有消融实验并生成对比报告
"""
import subprocess
import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

from codedoc.config import default_template


def run_experiment(target_path, mode, output_base, args):
    """运行单个消融实验"""
    print(f"\n{'='*60}")
    print(f"Running Ablation Experiment: {mode.upper()}")
    print(f"{'='*60}")
    
    output_dir = Path(output_base) / f"ablation_{mode}"
    
    cmd = [
        sys.executable, "-m", "codedoc.cli",
        "--target_path", target_path,
        "--output_dir", str(output_dir),
        "--ablation_mode", mode,
        "--llm_url", args.llm_url,
        "--model", args.model,
        "--language", args.language,
        "--prompt_template", args.prompt_template
    ]

    # Credentials are passed through the environment, never as a CLI default.
    env = os.environ.copy()
    env["LLM_URL"] = args.llm_url
    env["MODEL"] = args.model
    if args.llm_key:
        env["LLM_KEY"] = args.llm_key
    elif not env.get("LLM_KEY"):
        raise RuntimeError(
            "No LLM API key available: set the LLM_KEY environment variable "
            "(see .env.example) or pass --llm_key <your-key>."
        )
    
    if args.test_mode:
        cmd.append("--test_mode")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    elapsed = time.time() - start_time
    
    return {
        "mode": mode,
        "output_dir": str(output_dir),
        "elapsed_time": elapsed,
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


def analyze_results(results, output_base):
    """分析实验结果并生成报告"""
    report_path = Path(output_base) / "ablation_report.md"
    
    report = [
        "# Ablation Study Report\n",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
        "## Experiment Configuration\n\n",
        "| Mode | Dependencies | Prompt Optimization | Description |\n",
        "|------|--------------|---------------------|-------------|\n",
        "| full | ✅ | ✅ | Complete system with all features |\n",
        "| no_dep | ❌ | ✅ | Without dependency information |\n",
        "| no_prompt | ✅ | ❌ | Without prompt optimization |\n",
        "| baseline | ❌ | ❌ | Minimal configuration |\n\n",
        "## Execution Results\n\n",
        "| Mode | Status | Time (s) | Output Directory |\n",
        "|------|--------|----------|------------------|\n"
    ]
    
    for r in results:
        status = "[OK] Success" if r["success"] else "[FAIL] Failed"
        report.append(f"| {r['mode']} | {status} | {r['elapsed_time']:.2f} | `{r['output_dir']}` |\n")
    
    report.append("\n## Analysis Instructions\n\n")
    report.append("To evaluate the effectiveness of each component:\n\n")
    report.append("1. **Quality Metrics**: Compare generated documentation quality across modes\n")
    report.append("   - Completeness: Does it cover all functionality?\n")
    report.append("   - Accuracy: Are descriptions correct?\n")
    report.append("   - Clarity: Is it easy to understand?\n")
    report.append("   - Context: Does it explain relationships?\n\n")
    report.append("2. **Quantitative Analysis**:\n")
    report.append("   - Document length (tokens/words)\n")
    report.append("   - Generation time\n")
    report.append("   - Coverage (% of functions documented)\n\n")
    report.append("3. **Comparative Analysis**:\n")
    report.append("   - `full` vs `no_dep`: Impact of dependency information\n")
    report.append("   - `full` vs `no_prompt`: Impact of prompt optimization\n")
    report.append("   - `full` vs `baseline`: Combined impact\n\n")
    report.append("## Detailed Logs\n\n")
    
    for r in results:
        report.append(f"### {r['mode'].upper()}\n\n")
        if r["success"]:
            report.append("**Status:** [OK] Success\n\n")
            report.append("**Output:**\n```\n")
            report.append(r["stdout"][-1000:] if len(r["stdout"]) > 1000 else r["stdout"])
            report.append("\n```\n\n")
        else:
            report.append("**Status:** [FAIL] Failed\n\n")
            report.append("**Error:**\n```\n")
            report.append(r["stderr"])
            report.append("\n```\n\n")
    
    report_path.write_text("".join(report), encoding="utf-8")
    print(f"\n[Report] Report generated: {report_path}")
    
    # Save JSON results
    json_path = Path(output_base) / "ablation_results.json"
    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Report] JSON results: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Run ablation study experiments")
    parser.add_argument('--target_path', type=str, required=True, help='Target project path')
    parser.add_argument('--output_base', type=str, default='ablation_results', help='Base output directory')
    parser.add_argument('--modes', type=str, nargs='+', default=['full', 'no_dep', 'no_prompt', 'baseline'],
                       choices=['full', 'no_dep', 'no_prompt', 'baseline'],
                       help='Ablation modes to run')
    parser.add_argument('--llm_key', type=str, default=os.getenv('LLM_KEY', ''),
                        help='LLM API key. Prefer the LLM_KEY environment variable (see .env.example).')
    parser.add_argument('--llm_url', type=str, default=os.getenv('LLM_URL', 'https://api.openai.com/v1'))
    parser.add_argument('--model', type=str, default=os.getenv('MODEL', 'gpt-4o-mini'))
    parser.add_argument('--language', type=str, default='English')
    parser.add_argument('--prompt_template', type=str, default=default_template())
    parser.add_argument('--test_mode', action='store_true', help='Run in test mode')
    
    args = parser.parse_args()
    
    output_base = Path(args.output_base)
    output_base.mkdir(parents=True, exist_ok=True)
    
    print(f"[Ablation] Starting Ablation Study")
    print(f"Target: {args.target_path}")
    print(f"Modes: {', '.join(args.modes)}")
    print(f"Output: {output_base}")
    
    results = []
    for mode in args.modes:
        try:
            result = run_experiment(args.target_path, mode, output_base, args)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Error in {mode}: {e}")
            results.append({
                "mode": mode,
                "success": False,
                "error": str(e),
                "elapsed_time": 0
            })
    
    analyze_results(results, output_base)
    
    print(f"\n[SUCCESS] Ablation study completed!")
    print(f"Results saved to: {output_base}")


if __name__ == "__main__":
    main()
