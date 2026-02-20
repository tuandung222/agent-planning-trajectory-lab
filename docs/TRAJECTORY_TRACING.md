# Trajectory Tracing for Training Data

Tài liệu này giải trình cách thu thập trajectory data từ agent workflow để phục vụ huấn luyện và đánh giá mô hình.

## 1. Mục tiêu

Trajectory tracing trong project này nhằm thu thập dữ liệu theo từng run:
- bối cảnh run: `topic`, `provider`, `model`
- tiến trình thực thi: phase bắt đầu/kết thúc
- hành vi công cụ: input/output của `web_search`, `calculator`, `save_findings`
- kết quả cuối: report hash, report length, trạng thái thành công/thất bại

Định dạng lưu trữ:
- Event stream: `trajectories/<run_id>.jsonl`
- Run summary: `trajectories/<run_id>.summary.json`

## 2. Nguyên lý thiết kế

### 2.1 Event-sourcing mindset

Không lưu một object lớn cuối cùng, mà lưu chuỗi sự kiện theo thời gian.  
Lợi ích:
- dễ replay và debug từng bước
- dễ lọc dữ liệu để tạo dataset huấn luyện theo mục đích
- dễ mở rộng schema mà không phá dữ liệu cũ

### 2.2 Training-first mindset

Không chỉ “log để xem”, mà log để dùng cho:
- SFT dataset: map từ `user query` sang `tool-augmented output`
- Preference/RM dataset: so sánh trajectory tốt/xấu
- Failure mining: gom nhóm lỗi để xây bộ regression test

### 2.3 Privacy/security mindset

- chỉ lưu preview thay vì raw full output khi không cần
- lưu hash (`sha256`) cho report/text để truy vết integrity
- tuyệt đối không commit `.env` và API keys

## 3. Điểm cài đặt trong code

### 3.1 Tracer core

File: `trajectory_tracing.py`

Chức năng chính:
- `TrajectoryTracer`: writer JSONL + summary
- `tracing_context(...)`: truyền tracer qua `contextvars` để tools đọc được run context
- event helpers: `log_phase`, `log_tool_call`, `log_tool_result`, `log_message_snapshot`, `complete`

### 3.2 Workflow-level tracing

File: `planning_workflow.py`

Đã gắn tracing tại:
- bắt đầu workflow
- phase `plan_execute_synthesize` start/completed
- snapshot message từ `result.messages`
- kết thúc run: `success` hoặc `error`

### 3.3 Tool-level tracing

File: `tools.py`

Mỗi tool đều log:
- `tool_call` với arguments chính
- `tool_result` với trạng thái `ok`, `latency_ms`, `result_preview`

Điều này tạo dữ liệu trajectory giàu tín hiệu cho model training và error analysis.

### 3.4 CLI-level tracing

File: `main.py`

Thêm options:
- `--trace-dir`: thư mục output trajectory
- `--no-trace`: tắt tracing cho 1 run

Mặc định bật tracing (trừ khi dùng `--no-trace`).

## 4. Schema sự kiện (JSONL)

Mỗi dòng là một JSON object:

```json
{
  "ts_utc": "2026-02-20T10:00:00.123+00:00",
  "run_id": "run_ab12cd34ef56",
  "idx": 7,
  "event_type": "tool_result",
  "payload": {
    "tool": "web_search",
    "ok": true,
    "latency_ms": 534,
    "result_preview": "[{\"title\": \"...\"}]"
  }
}
```

Event types chính:
- `run_started`
- `phase`
- `tool_call`
- `tool_result`
- `message_snapshot`
- `run_completed`
- `final_report`

## 5. Cách chạy và thu dữ liệu

Bật mặc định qua `.env`:

```dotenv
TRACE_TRAJECTORY=true
TRACE_DIR=trajectories
```

Chạy:

```bash
python main.py "AI agent market size 2024-2026"
```

Sau run:
- JSONL: `trajectories/<run_id>.jsonl`
- summary: `trajectories/<run_id>.summary.json`

Tắt tracing tạm thời:

```bash
python main.py "topic" --no-trace
```

## 6. Dùng trajectory cho training

Pipeline gợi ý:
1. Lọc run thành công, loại run lỗi hạ tầng thuần túy
2. Trích cặp `(input -> output)` cho supervised fine-tuning
3. Trích `(state, action, reward-proxy)` cho offline RL / policy improvement
4. Gắn label chất lượng (manual hoặc heuristic) để tạo preference pairs
5. Duy trì benchmark tập cố định để theo dõi regression

## 7. Tư duy triển khai thực chiến

- Log đủ để học, không log mọi thứ vô nghĩa
- Ưu tiên tính nhất quán schema hơn việc thêm field ad-hoc
- Bất kỳ thay đổi lớn nào của agent phải đi kèm migration/compat plan cho trace schema
- Xem trace data là “dữ liệu sản phẩm”, không chỉ là debug artifact
