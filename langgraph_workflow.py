#!/usr/bin/env python3
"""
Planning Pattern Workflow (LangGraph implementation).

Architecture:
    Planner Node -> Executor Node -> Synthesis Node

This module provides a LangGraph-native implementation while preserving
the same tool layer and trajectory tracing contract used by the existing
Agent Framework version.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from tools import web_search, calculator, save_findings
from trajectory_tracing import TrajectoryTracer, tracing_context


logger = logging.getLogger(__name__)


class PlanningState(TypedDict, total=False):
    topic: str
    plan_text: str
    steps: list[dict[str, Any]]
    findings: list[dict[str, Any]]
    report: str
    errors: list[str]


def _extract_text(response: Any) -> str:
    """Extract plain text from LangChain message response."""
    content = getattr(response, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    chunks.append(str(text))
            else:
                chunks.append(str(item))
        return "\n".join(chunks)
    return str(content)


def _extract_json_block(text: str) -> str | None:
    """Extract JSON block from markdown-fenced text."""
    fenced = re.findall(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced[0]
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    if stripped.startswith("[") and stripped.endswith("]"):
        return stripped
    return None


def _fallback_steps(topic: str) -> list[dict[str, Any]]:
    """Fallback steps if planning JSON parsing fails."""
    return [
        {
            "id": "step_1",
            "tool": "web_search",
            "input": f"{topic} market size current year",
            "expected_output": "Current market size estimate with source links.",
        },
        {
            "id": "step_2",
            "tool": "web_search",
            "input": f"{topic} forecast CAGR 2024 2026",
            "expected_output": "Growth rate projections and forecast values.",
        },
        {
            "id": "step_3",
            "tool": "web_search",
            "input": f"{topic} top players and competitive landscape",
            "expected_output": "Key players and market positioning.",
        },
        {
            "id": "step_4",
            "tool": "calculator",
            "input": "((10.9 / 3.66) ** (1/3) - 1) * 100",
            "expected_output": "Sample CAGR computation template.",
        },
    ]


class LangGraphPlanningWorkflow:
    """Planning workflow implemented with LangGraph."""

    def __init__(self, topic: str, tracer: TrajectoryTracer | None = None):
        self.topic = topic
        self.tracer = tracer
        self.provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.model = self._resolve_model()
        self.llm = self._build_llm()
        self.graph = self._build_graph()

        logger.info(
            "Initializing LangGraph workflow with provider=%s model=%s",
            self.provider,
            self.model,
        )

    def _resolve_model(self) -> str:
        if self.provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        raise ValueError(
            f"Unsupported LLM_PROVIDER={self.provider!r}. Use 'openai' or 'anthropic'."
        )

    def _build_llm(self):
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable required when LLM_PROVIDER=openai."
                )
            return ChatOpenAI(
                model=self.model,
                api_key=api_key,
                temperature=0,
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable required when LLM_PROVIDER=anthropic."
            )
        return ChatAnthropic(
            model=self.model,
            api_key=api_key,
            temperature=0,
        )

    async def _plan_node(self, state: PlanningState) -> PlanningState:
        topic = state["topic"]
        if self.tracer:
            self.tracer.log_phase("planning", "started", topic=topic, framework="langgraph")

        prompt = f"""
You are a planner for a market research agent.
Create a COMPLETE plan for topic: "{topic}".

Return JSON only in this schema:
{{
  "plan_text": "high-level strategy",
  "steps": [
    {{
      "id": "step_1",
      "tool": "web_search" | "calculator",
      "input": "tool input string",
      "expected_output": "what this step should produce"
    }}
  ]
}}

Rules:
- 4 to 7 steps total.
- Prefer web_search for evidence gathering.
- Use calculator only for metric computations.
- Ensure steps are sequential and coherent.
"""
        response = await self.llm.ainvoke(prompt)
        plan_raw = _extract_text(response)

        if self.tracer:
            self.tracer.log_message_snapshot("planner", plan_raw)

        parsed_steps: list[dict[str, Any]]
        parsed_plan_text: str
        errors = list(state.get("errors", []))

        json_block = _extract_json_block(plan_raw)
        if json_block:
            try:
                payload = json.loads(json_block)
                parsed_steps = payload.get("steps", []) or []
                parsed_plan_text = payload.get("plan_text", "") or "Planner generated a structured plan."
            except Exception as e:
                errors.append(f"plan_json_parse_failed: {str(e)}")
                parsed_steps = _fallback_steps(topic)
                parsed_plan_text = "Fallback plan used due to JSON parse failure."
        else:
            errors.append("plan_json_missing")
            parsed_steps = _fallback_steps(topic)
            parsed_plan_text = "Fallback plan used because planner did not return JSON."

        if not parsed_steps:
            parsed_steps = _fallback_steps(topic)
            errors.append("plan_steps_empty")

        if self.tracer:
            self.tracer.log_phase(
                "planning",
                "completed",
                step_count=len(parsed_steps),
                used_fallback=bool(errors),
            )

        return {
            "plan_text": parsed_plan_text,
            "steps": parsed_steps,
            "errors": errors,
        }

    async def _execute_node(self, state: PlanningState) -> PlanningState:
        steps = state.get("steps", [])
        errors = list(state.get("errors", []))
        findings: list[dict[str, Any]] = []

        if self.tracer:
            self.tracer.log_phase("execution", "started", step_count=len(steps))

        with tracing_context(self.tracer):
            for i, step in enumerate(steps, start=1):
                tool_name = str(step.get("tool", "")).strip()
                tool_input = str(step.get("input", "")).strip()
                step_id = step.get("id", f"step_{i}")

                if not tool_name or not tool_input:
                    message = f"invalid_step_definition: {step}"
                    errors.append(message)
                    findings.append(
                        {
                            "step_id": step_id,
                            "tool": tool_name or "unknown",
                            "input": tool_input,
                            "ok": False,
                            "output": f"ERROR: {message}",
                        }
                    )
                    continue

                try:
                    if tool_name == "web_search":
                        output = await web_search(tool_input)
                    elif tool_name == "calculator":
                        output = await calculator(tool_input)
                    else:
                        output = f"ERROR: Unsupported tool '{tool_name}'"
                        errors.append(output)

                    ok = not str(output).startswith("ERROR:")
                    findings.append(
                        {
                            "step_id": step_id,
                            "tool": tool_name,
                            "input": tool_input,
                            "ok": ok,
                            "output": output,
                            "expected_output": step.get("expected_output", ""),
                        }
                    )
                except Exception as e:
                    message = f"ERROR: tool_execution_failed({tool_name}): {str(e)}"
                    errors.append(message)
                    findings.append(
                        {
                            "step_id": step_id,
                            "tool": tool_name,
                            "input": tool_input,
                            "ok": False,
                            "output": message,
                            "expected_output": step.get("expected_output", ""),
                        }
                    )

        if self.tracer:
            self.tracer.log_phase(
                "execution",
                "completed",
                step_count=len(findings),
                error_count=len([f for f in findings if not f.get("ok", False)]),
            )

        return {
            "findings": findings,
            "errors": errors,
        }

    async def _synthesis_node(self, state: PlanningState) -> PlanningState:
        topic = state["topic"]
        plan_text = state.get("plan_text", "")
        findings = state.get("findings", [])
        errors = state.get("errors", [])

        if self.tracer:
            self.tracer.log_phase("synthesis", "started", finding_count=len(findings))

        findings_json = json.dumps(findings, ensure_ascii=True, indent=2)
        errors_json = json.dumps(errors, ensure_ascii=True, indent=2)
        prompt = f"""
You are a research synthesis agent.

Topic: {topic}
Plan summary:
{plan_text}

Findings JSON:
{findings_json}

Execution errors JSON:
{errors_json}

Write a professional markdown report with:
1) Executive Summary
2) Market Overview
3) Key Findings
4) Competitive Landscape
5) Recommendations
6) Sources

Requirements:
- Cite links from findings when available.
- Clearly state uncertainty or missing data if errors exist.
- Do NOT invent numbers without a source in findings.
"""
        response = await self.llm.ainvoke(prompt)
        report = _extract_text(response)

        # Keep tool tracing parity with the existing implementation.
        with tracing_context(self.tracer):
            await save_findings("langgraph_market_report.md", report)

        if self.tracer:
            self.tracer.log_message_snapshot("synthesis", report)
            self.tracer.log_phase("synthesis", "completed")

        return {"report": report}

    def _build_graph(self):
        builder = StateGraph(PlanningState)
        builder.add_node("plan", self._plan_node)
        builder.add_node("execute", self._execute_node)
        builder.add_node("synthesize", self._synthesis_node)

        builder.add_edge(START, "plan")
        builder.add_edge("plan", "execute")
        builder.add_edge("execute", "synthesize")
        builder.add_edge("synthesize", END)
        return builder.compile()

    async def execute(self) -> str:
        try:
            if self.tracer:
                self.tracer.log_phase("workflow", "started", topic=self.topic, framework="langgraph")

            result = await self.graph.ainvoke({"topic": self.topic})
            report = result.get("report", "")
            if not report:
                raise RuntimeError("LangGraph workflow produced empty report.")

            if self.tracer:
                self.tracer.complete(status="success", report_text=report)
            return report
        except Exception as e:
            if self.tracer:
                self.tracer.complete(status="error", error=str(e))
            raise RuntimeError(f"LangGraph workflow failed: {str(e)}")

