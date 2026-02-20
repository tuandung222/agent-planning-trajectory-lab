# 02 - Clients and Providers

## Mục tiêu

Cấu hình và chọn provider đúng cho từng môi trường chạy.

## Trong project này

- Default: `OpenAIChatClient`
- Optional: `AnthropicClient`
- Chọn qua `LLM_PROVIDER` trong `.env` hoặc `--provider`

## Biến môi trường

- OpenAI path:
  - `LLM_PROVIDER=openai`
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
- Anthropic path:
  - `LLM_PROVIDER=anthropic`
  - `ANTHROPIC_API_KEY`
  - `ANTHROPIC_MODEL`

## Pattern khuyến nghị

- Mặc định model nhỏ/nhanh cho phần lớn request.
- Chỉ nâng model lớn cho tác vụ synthesis khó hoặc nhạy cảm chất lượng.
- Tách config theo environment (dev/staging/prod) thay vì hardcode.

## Debug checklist

- 401 auth error: sai key hoặc sai provider.
- model not found: model_id không hợp lệ với provider.
- timeout: kiểm tra network + retry policy tầng tool.
