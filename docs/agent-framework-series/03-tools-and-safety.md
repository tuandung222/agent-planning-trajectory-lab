# 03 - Tools and Safety

## Mục tiêu

Thiết kế tools vừa hữu ích cho model, vừa an toàn cho production.

## Tool contracts

Mỗi tool cần rõ:

- Input schema (kiểu dữ liệu + constraints)
- Output schema (thành công/thất bại)
- Error semantics (tool tự trả lỗi hay ném exception)

## Case trong repo

- `web_search(query)`
  - gọi Serper API
  - trả JSON string đã format
- `calculator(expression)`
  - dùng AST parsing
  - không dùng `eval()`
- `save_findings(filename, content)`
  - sanitize filename
  - ghi vào thư mục kiểm soát

## Safety principles

- Input validation trước khi gọi external API.
- Timeout bắt buộc cho network calls.
- Sanitization cho filesystem path.
- Log tool call/result để audit.

## Quality tips

- Trả output ngắn gọn, nhất quán, machine-parsable khi có thể.
- Tránh output quá dài gây token waste.
