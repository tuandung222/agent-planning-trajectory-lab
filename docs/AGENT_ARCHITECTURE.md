# Agent Architecture

This document explains the architecture and runtime flow of the Planning-pattern agent in a concise, production-style format.

## 1. System Architecture

```mermaid
flowchart LR
    U["User (CLI / Notebook)"] --> M["main.py"]
    M --> C["Config Loader (.env + args)"]
    C --> W["PlanningMarketResearchWorkflow"]

    W --> P["Planner Agent (LLM)"]
    W --> E["Executor Agent (LLM + Tools)"]
    W --> S["Synthesis Agent (LLM + save_findings)"]

    E --> T1["web_search (Serper API)"]
    E --> T2["calculator (safe AST)"]
    S --> T3["save_findings (local markdown)"]

    P --> L["LLM Provider Router"]
    E --> L
    S --> L
    L --> O["OpenAIChatClient (default)"]
    L --> A["AnthropicClient (optional)"]

    S --> R["Final Report"]
    R --> F["planning_market_report.md"]
```

## 2. Runtime Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI as main.py
    participant WF as Workflow
    participant Planner as Planner Agent
    participant Executor as Executor Agent
    participant Tools as Tool Layer
    participant Synth as Synthesis Agent

    User->>CLI: topic + provider/model args
    CLI->>WF: create + validate config
    WF->>Planner: Phase 1 - build complete plan
    Planner-->>WF: structured plan text

    WF->>Executor: Phase 2 - execute plan steps
    loop For each plan step
        Executor->>Tools: web_search/calculator
        Tools-->>Executor: step result
    end
    Executor-->>WF: aggregated findings

    WF->>Synth: Phase 3 - synthesize report
    Synth-->>WF: final markdown report
    WF-->>CLI: result
    CLI-->>User: saved file path + execution summary
```

## 3. Failure and Recovery Path

```mermaid
flowchart TD
    A["Start run"] --> B{"Config valid?"}
    B -- No --> B1["Stop: missing/invalid env vars"]
    B -- Yes --> C{"LLM auth valid?"}
    C -- No --> C1["Stop: 401/auth error"]
    C -- Yes --> D{"Tool call succeeds?"}
    D -- No --> D1["Tool returns ERROR text"]
    D1 --> E["Executor continues next step"]
    D -- Yes --> E
    E --> F{"Synthesis succeeds?"}
    F -- No --> F1["Raise runtime error"]
    F -- Yes --> G["Write output report"]
```

## 4. Design Notes

- Pattern: `Plan -> Execute -> Synthesize`
- Provider abstraction:
  - default: OpenAI (`OPENAI_API_KEY`, `OPENAI_MODEL`)
  - optional: Anthropic (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`)
- Tool safety:
  - calculator uses AST parsing, not `eval()`
  - file output path is sanitized in `save_findings`
- Operational behavior:
  - workflow is resilient to single-step tool failures (captures errors and continues)
  - final report quality depends on both web search quality and model quality
