# 06 - Notebook and Experimentation

## Mục tiêu

Hỗ trợ DS/AI Researcher thử nghiệm nhanh mà vẫn giữ reproducibility.

## Notebook chính

- `planning_pattern_interactive_lab.ipynb`

## Flow đề xuất trong notebook

1. Setup dependencies
2. Validate provider/key
3. Test tools độc lập
4. Instantiate workflow
5. Run end-to-end inference
6. Inspect output + traces

## Best practices

- Một cell = một mục tiêu rõ ràng.
- Capture seed/config ở đầu notebook.
- Không hardcode secrets trong notebook.
- Export executed notebook khi cần share kết quả.

## Bridge notebook -> production

- Khi experiment ổn định, chuyển logic sang module Python.
- Giữ notebook như tài liệu khám phá và benchmark sandbox.
