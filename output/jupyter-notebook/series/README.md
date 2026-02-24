# Planning Notebook Series (DS / AI Engineer)

This series is designed for practical research on planning strategies for agentic systems.

## Notebooks

1. `01_foundations_agentic_planning.ipynb`
2. `02_pattern_comparison_react_vs_plan_execute.ipynb`
3. `03_state_action_tool_design.ipynb`
4. `04_langgraph_planning_workflow_basics.ipynb`
5. `05_search_and_tooling_no_api_mode.ipynb`
6. `06_trajectory_tracing_for_training.ipynb`
7. `07_evaluation_harness_and_metrics.ipynb`
8. `08_failure_analysis_and_guardrails.ipynb`
9. `09_trajectory_to_training_dataset.ipynb`
10. `10_end_to_end_research_agent_lab.ipynb`

## Execution

Run from repository root:

```bash
conda activate vllm
jupyter nbconvert --to notebook --execute output/jupyter-notebook/series/01_foundations_agentic_planning.ipynb --output 01_foundations_agentic_planning.executed.ipynb --output-dir test_outputs/notebook_series_exec
```

You can execute all notebooks in sequence using a shell loop.

## Notes

- Notebook 10 supports real inference mode with `RUN_REAL_INFERENCE=True`.
- Default settings keep the series reproducible and fast.
