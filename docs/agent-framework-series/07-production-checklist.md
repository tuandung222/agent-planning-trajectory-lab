# 07 - Production Checklist

## 1. Reliability

- [ ] Provider fallback policy rõ ràng
- [ ] Timeout/retry cho mọi external calls
- [ ] Structured error handling theo phase

## 2. Security

- [ ] Không commit `.env` và secrets
- [ ] Input sanitization cho tools filesystem/network
- [ ] Principle of least privilege cho API keys

## 3. Cost and latency

- [ ] Theo dõi token/latency theo phase
- [ ] Caching cho query lặp lại
- [ ] Model tiering (fast model default)

## 4. Data and tracing

- [ ] Trajectory tracing bật mặc định ở staging
- [ ] Data retention policy cho traces
- [ ] PII scrubbing trước khi đưa vào training datasets

## 5. Quality

- [ ] Golden set regression tests
- [ ] Human review loop cho report quality
- [ ] Metrics: error rate, completion rate, tool success rate

## 6. Operations

- [ ] Dashboards + alerts
- [ ] Runbook cho 401/429/timeout/tool failures
- [ ] Rollout strategy: canary -> ramp-up -> full rollout
