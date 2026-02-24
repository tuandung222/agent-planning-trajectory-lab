# Test Report - Plan-and-Execute Agent Framework

Date: 2026-02-24
Environment: conda `vllm` (Python 3.12.9)
Project path: `/Users/admin/TuanDung/repos/plan-execute-synthesize-agent`

## Scope

Validated implementations delivered so far:
- OpenAI-first provider integration
- Anthropic optional provider path
- Agent Framework runtime (`main.py`)
- LangGraph runtime (`main_langgraph.py`)
- Tool layer (`web_search`, `calculator`, `save_findings`)
- Trajectory tracing pipeline (`trajectory_tracing.py`)
- Notebook UX (`planning_pattern_interactive_lab.ipynb`)

## Test Matrix

| ID | Test | Command / Method | Result | Notes |
|---|---|---|---|---|
| T1 | Static compile | `python -m py_compile main.py main_langgraph.py planning_workflow.py langgraph_workflow.py tools.py trajectory_tracing.py` | PASS | No syntax errors |
| T2.1 | `calculator` valid expression | Direct async tool call | PASS | Returned numeric value `43.8738297571597` |
| T2.2 | `calculator` invalid expression | Direct async tool call | PASS | Returned controlled error: `ERROR: Invalid expression...` |
| T2.3 | `web_search` no-key mode | Direct async tool call | PASS | Returned DuckDuckGo/Wikipedia-backed results |
| T2.4 | `save_findings` write output | Direct async tool call | PASS | File created under `outputs/test_tool_output.md` |
| T3 | Agent Framework integration (OpenAI + no Serper key) | `main.py ... --provider openai ...` | PASS | Report + trace generated |
| T4 | LangGraph integration (OpenAI + no Serper key) | `main_langgraph.py ... --provider openai ...` | PASS | Report + trace generated |
| T5.1 | Provider matrix: Anthropic branch without key | `main.py ... --provider anthropic` with empty key | PASS | Correct fail-fast message for missing `ANTHROPIC_API_KEY` |
| T5.2 | Provider matrix: OpenAI default path | Multiple OpenAI runs | PASS | Stable success |
| T6 | Tracing schema validation | Parsed JSONL event types + summary JSON | PASS | Required events present in successful traced runs |
| T7 | CLI no-trace behavior | `main.py ... --no-trace` | PASS | No JSONL and no summary artifacts emitted after tracer patch |
| T8 | Notebook end-to-end execution | `jupyter nbconvert --execute ...` | PASS | Executed notebook written to `test_outputs/planning_pattern_interactive_lab.tested.ipynb` |
| T9 | README command regression | Executed documented core commands (`main.py`, `main_langgraph.py`) | PASS | Commands work as documented |
| T10 | LangGraph calculator input validator | Direct helper test + executor step simulation | PASS | Natural-language calculator input is rejected before tool execution |
| T11 | LangGraph regression smoke after fixes | `main_langgraph.py ...` with tracing | PASS | Successful run with `tool_error_count: 0` in summary |

## Artifacts Produced

- Agent Framework report: `test_outputs/af_smoke.md`
- LangGraph report: `test_outputs/langgraph_smoke.md`
- No-trace report: `test_outputs/af_no_trace.md`
- Trace JSONL (AF): `test_outputs/trajectories/run_e75546cef317.jsonl`
- Trace summary (AF): `test_outputs/trajectories/run_e75546cef317.summary.json`
- Trace JSONL (LangGraph): `test_outputs/trajectories/run_0bc491ecac3c.jsonl`
- Trace summary (LangGraph): `test_outputs/trajectories/run_0bc491ecac3c.summary.json`
- No-trace summary artifact: `test_outputs/no_trace_dir/run_c40067ee6be3.summary.json`
- Executed notebook: `test_outputs/planning_pattern_interactive_lab.tested.ipynb`
- Strict no-trace directory after fix: `test_outputs/no_trace_fix/` (empty)
- LangGraph post-fix report: `test_outputs/langgraph_fix_smoke.md`
- LangGraph post-fix trace summary: `test_outputs/trajectories_fix/run_ec9f6d9740ac.summary.json`

## Key Observations

1. Core functionality is operational for both runtimes.
2. Tracing structure is consistent and usable for trajectory analysis/training curation.
3. No-key search fallback path works (DuckDuckGo + Wikipedia).
4. Planner may still emit non-math calculator text in some runs, but executor-side validation now blocks it early with explicit error messaging.

## Findings / Risks

### [RESOLVED] `--no-trace` summary artifact leak

- Fix applied in `trajectory_tracing.py`: `complete()`, `log_tool_call()`, `log_tool_result()` now short-circuit when `enabled=False`.
- Retest evidence: `test_outputs/no_trace_fix/` remains empty after a full workflow run with `--no-trace`.

### [RESOLVED] Planner-to-calculator format guard (LangGraph)

- Fix applied in `langgraph_workflow.py`:
  - Added `_is_valid_calculator_expression()`
  - Added stricter planner rule for calculator inputs
  - Added executor-side pre-validation and clear error message
- Retest evidence:
  - `"Calculate CAGR from step 3"` => rejected by validator
  - Post-fix LangGraph smoke run completed with `tool_error_count: 0`

## Recommended Fixes

1. Add automated smoke tests:
- Add `pytest` async smoke tests for `tools.py` and lightweight integration tests with mocked LLM responses.

## Overall Verdict

Implementation status: **GOOD (with critical fixes applied)**

- Main features requested are running end-to-end.
- Tracing is functional and produces trajectory data.
- Previous `--no-trace` and calculator-format robustness gaps are now fixed and retested.
