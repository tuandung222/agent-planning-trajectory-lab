# 01 - Mental Model

## Mục tiêu

Hiểu Agent Framework dưới góc nhìn kiến trúc, không chỉ API call.

## Core abstractions

- `Agent`: một actor dùng LLM + instructions + tools.
- `Tool`: capability gọi được từ agent.
- `Workflow`: đồ thị điều phối nhiều agent/executor.
- `WorkflowBuilder`: dựng graph + edges + output executors.

## Mindset

- Thiết kế từ **task decomposition** trước, code sau.
- Tách rõ:
  - reasoning responsibility (Planner/Synthesis)
  - execution responsibility (Executor + tools)
- Ưu tiên flow deterministic ở orchestration; để model linh hoạt trong boundaries rõ ràng.

## Mapping vào repo này

- Planner/Executor/Synthesis: `planning_workflow.py`
- Tool layer: `tools.py`
- Runtime entrypoint: `main.py`
- Trace data: `trajectory_tracing.py`

## Sai lầm phổ biến

- Đẩy quá nhiều logic vào 1 agent duy nhất.
- Tool không có contract rõ (input/output mơ hồ).
- Không có observability nên khó debug/huấn luyện lại.
