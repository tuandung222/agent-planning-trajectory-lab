# 04 - Workflows and Orchestration

## Mục tiêu

Biết cách thiết kế workflow nhiều agent có kiểm soát.

## Pattern đang dùng: Planning

`Plan -> Execute -> Synthesize`

- Planner: tạo kế hoạch upfront
- Executor: gọi tools theo kế hoạch
- Synthesis: tổng hợp report cuối

## Tại sao dùng workflow graph

- Tách trách nhiệm rõ ràng
- Dễ thêm branching/recovery path
- Dễ đo hiệu năng theo phase

## Minimal flow

1. Tạo 3 agents với instructions riêng.
2. Dùng `WorkflowBuilder(start_executor=..., output_executors=[...])`.
3. `add_chain([planner, executor, synthesis])`.
4. `build().as_agent(...)` và `run(...)`.

## Extension patterns

- Add validator agent giữa executor và synthesis.
- Add conditional edge cho replanning khi tool error rate cao.
- Split executor thành nhiều domain-specific executors.
