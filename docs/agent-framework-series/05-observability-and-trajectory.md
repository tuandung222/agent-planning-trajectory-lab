# 05 - Observability and Trajectory

## Mục tiêu

Thu trajectory data đủ tốt để phục vụ training, đánh giá, và debug.

## Tracing trong project này

- Core tracer: `trajectory_tracing.py`
- Workflow hooks: `planning_workflow.py`
- Tool hooks: `tools.py`
- Runtime controls: `main.py` (`--trace-dir`, `--no-trace`)

## Artifacts

- Event stream: `trajectories/<run_id>.jsonl`
- Summary: `trajectories/<run_id>.summary.json`

## Event types chính

- `run_started`
- `phase`
- `tool_call`
- `tool_result`
- `message_snapshot`
- `run_completed`
- `final_report`

## Training-oriented mindset

- Log để **học lại** được hành vi, không chỉ để debug.
- Ưu tiên schema ổn định và versioning rõ.
- Giữ được khả năng nối run-level metrics với quality labels.

## Quick commands

```bash
python main.py "topic" --trace-dir trajectories
python main.py "topic" --no-trace
```

Xem chi tiết: `../TRAJECTORY_TRACING.md`
