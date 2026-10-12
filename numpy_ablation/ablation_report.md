# Ablation Study Report
**Generated:** 2026-01-19 18:17:56

## Experiment Configuration

| Mode | Dependencies | Prompt Optimization | Description |
|------|--------------|---------------------|-------------|
| full | ✅ | ✅ | Complete system with all features |
| no_dep | ❌ | ✅ | Without dependency information |
| no_prompt | ✅ | ❌ | Without prompt optimization |
| baseline | ❌ | ❌ | Minimal configuration |

## Execution Results

| Mode | Status | Time (s) | Output Directory |
|------|--------|----------|------------------|
| full | ✅ Success | 61.64 | `numpy_ablation\ablation_full` |
| no_dep | ✅ Success | 61.88 | `numpy_ablation\ablation_no_dep` |
| no_prompt | ✅ Success | 47.89 | `numpy_ablation\ablation_no_prompt` |
| baseline | ✅ Success | 46.53 | `numpy_ablation\ablation_baseline` |

## Analysis Instructions

To evaluate the effectiveness of each component:

1. **Quality Metrics**: Compare generated documentation quality across modes
   - Completeness: Does it cover all functionality?
   - Accuracy: Are descriptions correct?
   - Clarity: Is it easy to understand?
   - Context: Does it explain relationships?

2. **Quantitative Analysis**:
   - Document length (tokens/words)
   - Generation time
   - Coverage (% of functions documented)

3. **Comparative Analysis**:
   - `full` vs `no_dep`: Impact of dependency information
   - `full` vs `no_prompt`: Impact of prompt optimization
   - `full` vs `baseline`: Combined impact

## Detailed Logs

### FULL

**Status:** ✅ Success

**Output:**
```

  DEBUG: LLM response len=3237
  [OK] _NoValueType.__new__ (md_len=3237)
  DEBUG: LLM response len=3290
  [OK] _CopyMode.__bool__ (md_len=3290)
  -> numpy_ablation\ablation_full\tests\_globals.md

_pytesttester.py (classes: 1, funcs: 1)
  DEBUG: nav nodes = ['_array_api_info', '_configtool', '_distributor_init', '_expired_attrs_2_0', '_globals', '_pytesttester', 'conftest', 'dtypes', 'exceptions', 'matlib']...
  DEBUG: checking method key=_pytesttester__PytestTester____init__, name=PytestTester.__init__
  DEBUG: checking method key=_pytesttester__PytestTester____call__, name=PytestTester.__call__
  DEBUG: checking func key=_pytesttester___show_numpy_info, name=_show_numpy_info
  DEBUG: LLM response len=2733
  [OK] PytestTester.__init__ (md_len=2733)
  DEBUG: LLM response len=2792
  [OK] _show_numpy_info (md_len=2792)
  DEBUG: LLM response len=4309
  [OK] PytestTester.__call__ (md_len=4309)
  -> numpy_ablation\ablation_full\tests\_pytesttester.md

Generated docs for 7 items in 3 files

```

### NO_DEP

**Status:** ✅ Success

**Output:**
```
EBUG: LLM response len=3264
  [OK] _NoValueType.__new__ (md_len=3264)
  DEBUG: LLM response len=3618
  [OK] _CopyMode.__bool__ (md_len=3618)
  -> numpy_ablation\ablation_no_dep\tests\_globals.md

_pytesttester.py (classes: 1, funcs: 1)
  DEBUG: nav nodes = ['_array_api_info', '_configtool', '_distributor_init', '_expired_attrs_2_0', '_globals', '_pytesttester', 'conftest', 'dtypes', 'exceptions', 'matlib']...
  DEBUG: checking method key=_pytesttester__PytestTester____init__, name=PytestTester.__init__
  DEBUG: checking method key=_pytesttester__PytestTester____call__, name=PytestTester.__call__
  DEBUG: checking func key=_pytesttester___show_numpy_info, name=_show_numpy_info
  DEBUG: LLM response len=3523
  [OK] _show_numpy_info (md_len=3523)
  DEBUG: LLM response len=3297
  [OK] PytestTester.__init__ (md_len=3297)
  DEBUG: LLM response len=4031
  [OK] PytestTester.__call__ (md_len=4031)
  -> numpy_ablation\ablation_no_dep\tests\_pytesttester.md

Generated docs for 7 items in 3 files

```

### NO_PROMPT

**Status:** ✅ Success

**Output:**
```
LLM response len=2512
  [OK] _NoValueType.__new__ (md_len=2512)
  DEBUG: LLM response len=2008
  [OK] _CopyMode.__bool__ (md_len=2008)
  -> numpy_ablation\ablation_no_prompt\tests\_globals.md

_pytesttester.py (classes: 1, funcs: 1)
  DEBUG: nav nodes = ['_array_api_info', '_configtool', '_distributor_init', '_expired_attrs_2_0', '_globals', '_pytesttester', 'conftest', 'dtypes', 'exceptions', 'matlib']...
  DEBUG: checking method key=_pytesttester__PytestTester____init__, name=PytestTester.__init__
  DEBUG: checking method key=_pytesttester__PytestTester____call__, name=PytestTester.__call__
  DEBUG: checking func key=_pytesttester___show_numpy_info, name=_show_numpy_info
  DEBUG: LLM response len=1471
  [OK] PytestTester.__init__ (md_len=1471)
  DEBUG: LLM response len=2749
  [OK] PytestTester.__call__ (md_len=2749)
  DEBUG: LLM response len=4102
  [OK] _show_numpy_info (md_len=4102)
  -> numpy_ablation\ablation_no_prompt\tests\_pytesttester.md

Generated docs for 7 items in 3 files

```

### BASELINE

**Status:** ✅ Success

**Output:**
```
: LLM response len=1883
  [OK] _CopyMode.__bool__ (md_len=1883)
  DEBUG: LLM response len=2318
  [OK] _NoValueType.__new__ (md_len=2318)
  -> numpy_ablation\ablation_baseline\tests\_globals.md

_pytesttester.py (classes: 1, funcs: 1)
  DEBUG: nav nodes = ['_array_api_info', '_configtool', '_distributor_init', '_expired_attrs_2_0', '_globals', '_pytesttester', 'conftest', 'dtypes', 'exceptions', 'matlib']...
  DEBUG: checking method key=_pytesttester__PytestTester____init__, name=PytestTester.__init__
  DEBUG: checking method key=_pytesttester__PytestTester____call__, name=PytestTester.__call__
  DEBUG: checking func key=_pytesttester___show_numpy_info, name=_show_numpy_info
  DEBUG: LLM response len=1685
  [OK] PytestTester.__init__ (md_len=1685)
  DEBUG: LLM response len=2085
  [OK] _show_numpy_info (md_len=2085)
  DEBUG: LLM response len=2403
  [OK] PytestTester.__call__ (md_len=2403)
  -> numpy_ablation\ablation_baseline\tests\_pytesttester.md

Generated docs for 7 items in 3 files

```

