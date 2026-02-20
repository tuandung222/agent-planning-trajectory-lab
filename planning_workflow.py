#!/usr/bin/env python3
"""
Planning Pattern Workflow - Microsoft Agent Framework

Unlike ReAct which interleaves reasoning and action, the Planning pattern:
    1. Creates a comprehensive research plan upfront
    2. Executes the plan steps sequentially with tools
    3. Synthesizes findings into a final report

Architecture:
    Planner Agent → Executor Agent → Synthesis Agent

Author: GP (genmind.ch)
License: MIT
Blog Post: https://genmind.ch/posts/Planning-Pattern-for-AI-Agents-Strategic-Reasoning-Before-Action/
"""

import os
import logging
from typing import Any

from agent_framework import (
    Agent,
    WorkflowAgent,
    WorkflowBuilder,
    Message,
    Content,
)
from agent_framework.openai import OpenAIChatClient
from agent_framework.anthropic import AnthropicClient

from tools import web_search, calculator, save_findings
from trajectory_tracing import TrajectoryTracer, tracing_context

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PlanningMarketResearchWorkflow:
    """
    Planning Pattern workflow for market research automation.

    This workflow demonstrates the Planning pattern where an agent creates
    a comprehensive research strategy upfront, then executes it systematically.

    Phases:
        1. PLANNING: Create detailed research plan with specific steps
        2. EXECUTION: Execute each step using tools (search, calculate)
        3. SYNTHESIS: Compile findings into executive-ready report

    Contrast with ReAct:
        - ReAct: Think → Act → Observe → Think → Act... (continuous loop)
        - Planning: Plan → Execute All → Synthesize (one upfront strategy)
    """

    def __init__(self, topic: str, tracer: TrajectoryTracer | None = None):
        """
        Initialize the Planning workflow for market research.

        Args:
            topic: Research topic (e.g., "AI agent market size 2024-2026")
        """
        self.topic = topic
        self.tracer = tracer

        self.provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.model = self._resolve_model()
        self.client = self._build_client()

        logger.info(
            "Initializing Planning workflow with provider=%s model=%s",
            self.provider,
            self.model
        )

        # Build the workflow
        self.workflow = self._build_workflow()

    def _snapshot_messages(self, result: Any) -> None:
        """Persist compact snapshots of returned messages into trajectory logs."""
        if not self.tracer or not self.tracer.enabled:
            return
        messages = getattr(result, "messages", None)
        if not messages:
            return
        for msg in messages:
            role = getattr(msg, "role", "unknown")
            contents = getattr(msg, "contents", []) or []
            text_chunks = []
            for content in contents:
                text = getattr(content, "text", None)
                if text:
                    text_chunks.append(text)
            if text_chunks:
                self.tracer.log_message_snapshot(role=role, text="\n".join(text_chunks))

    def _resolve_model(self) -> str:
        """Resolve model name for selected provider."""
        if self.provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        if self.provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        raise ValueError(
            f"Unsupported LLM_PROVIDER={self.provider!r}. "
            "Use 'openai' or 'anthropic'."
        )

    def _build_client(self):
        """Create chat client for selected provider."""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable required when "
                    "LLM_PROVIDER=openai."
                )
            return OpenAIChatClient(
                api_key=api_key,
                model_id=self.model
            )

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable required when "
                "LLM_PROVIDER=anthropic."
            )
        return AnthropicClient(
            api_key=api_key,
            model_id=self.model
        )

    def _build_workflow(self) -> WorkflowAgent:
        """
        Build the three-phase Planning workflow.

        Returns:
            WorkflowAgent configured with Planning pattern
        """
        # PHASE 1: PLANNER AGENT
        # Creates comprehensive research plan upfront (key difference from ReAct)
        planner = Agent(
            client=self.client,
            name="planner",
            instructions=f"""You are a Strategic Research Planner AI for market research.

Your task: Create a comprehensive, detailed research plan for: "{self.topic}"

PLANNING PATTERN (not ReAct):
You must create a COMPLETE PLAN UPFRONT before any execution. Think strategically about:
- What information is needed?
- What sources to consult?
- What metrics to calculate?
- Optimal execution sequence

OUTPUT FORMAT - Structured Plan:
PLAN:
Step 1: [Specific search query or calculation]
  - Tool: web_search OR calculator
  - Query: "[exact query]"
  - Expected output: [what you'll learn]

Step 2: [Next specific action]
  - Tool: [tool name]
  - Query: "[exact query]"
  - Expected output: [what you'll learn]

[Continue for 5-8 steps]

FINAL SYNTHESIS:
- Combine findings from all steps
- Calculate key metrics (market size, growth rates, ROI)
- Structure as executive report

CRITICAL:
- Be SPECIFIC in each step (exact search queries, exact calculations)
- Plan should be COMPLETE before execution
- Each step should build on previous findings
- Include validation steps (cross-reference numbers, verify sources)

Create the plan now.""",
            tools=[]  # Planner doesn't execute tools, just creates plan
        )

        # PHASE 2: EXECUTOR AGENT
        # Executes the plan steps using tools
        executor = Agent(
            client=self.client,
            name="executor",
            instructions=f"""You are a Research Execution AI that follows plans precisely.

You will receive a RESEARCH PLAN from the Planner Agent.

Your task:
1. Execute each step of the plan IN ORDER
2. Use the provided tools (web_search, calculator) as specified
3. Document findings from each step
4. Pass all findings to the Synthesis Agent

EXECUTION RULES:
- Follow the plan EXACTLY - don't deviate or improvise
- Use tools as specified in each step
- If a step fails, note it and continue with remaining steps
- Collect ALL data before moving to synthesis

Available tools:
- web_search(query): Search web for market data
- calculator(expression): Calculate metrics (CAGR, growth rates, etc.)

Execute the plan now and collect all findings.""",
            tools=[web_search, calculator]
        )

        # PHASE 3: SYNTHESIS AGENT
        # Compiles findings into final report
        synthesis = Agent(
            client=self.client,
            name="synthesis",
            instructions=f"""You are a Research Synthesis AI that creates executive reports.

You will receive:
1. Original research plan
2. All findings from plan execution

Your task: Synthesize findings into a comprehensive market research report.

REPORT STRUCTURE:
# Market Research Report: {self.topic}

**Generated by**: Planning Pattern Market Research Assistant
**Date**: [Current date]
**Research Topic**: {self.topic}

---

## Executive Summary
[2-3 paragraphs summarizing key findings, market size, growth trends]

---

## Market Overview

### Current Market Size
[Present data with citations]

### Projected Growth
[Include calculations, growth rates, CAGR]

### Market Drivers
[Key factors driving market growth]

---

## Key Findings
[5-7 numbered findings with supporting data]

---

## Competitive Landscape
[Major players, market share if available]

---

## Recommendations
[3-5 actionable recommendations based on findings]

---

## Sources
[List all sources cited in the report]

---

QUALITY STANDARDS:
- Include specific numbers with sources
- Show calculations (e.g., "CAGR = ((47.1/5.43)^(1/6)-1)*100 = 43.2%")
- Cite every factual claim
- Use markdown formatting
- Professional executive tone

Generate the final report now.""",
            tools=[save_findings]  # Can optionally save the report
        )

        # Build sequential workflow: Planner → Executor → Synthesis
        builder = WorkflowBuilder(
            start_executor=planner,
            output_executors=[synthesis]
        )
        builder.add_chain([planner, executor, synthesis])

        # Build and return workflow agent
        workflow = builder.build().as_agent(name="planning_workflow")
        logger.info("Planning workflow built successfully")

        return workflow

    async def execute(self) -> str:
        """
        Execute the three-phase Planning workflow.

        Returns:
            Final market research report as markdown string

        Raises:
            RuntimeError: If workflow execution fails
        """
        try:
            if self.tracer:
                self.tracer.log_phase("workflow", "started", topic=self.topic)
            logger.info("\n" + "=" * 60)
            logger.info("🎯 PLANNING PATTERN WORKFLOW - START")
            logger.info("=" * 60)
            logger.info(f"Research Topic: {self.topic}\n")

            # Create initial message
            user_message = Message(
                role="user",
                contents=[Content.from_text(
                    f"Create and execute a market research plan for: {self.topic}"
                )]
            )

            # Execute workflow
            logger.info("📋 PHASE 1: Creating Research Plan...")
            logger.info("⚙️  PHASE 2: Executing Plan Steps...")
            logger.info("📊 PHASE 3: Synthesizing Final Report...\n")

            if self.tracer:
                self.tracer.log_phase("plan_execute_synthesize", "started")

            with tracing_context(self.tracer):
                result = await self.workflow.run([user_message])

            if self.tracer:
                self.tracer.log_phase("plan_execute_synthesize", "completed")

            # Extract final report from result
            if result and result.messages:
                self._snapshot_messages(result)
                final_message = result.messages[-1]
                if final_message.contents:
                    report = final_message.contents[0].text

                    logger.info("\n" + "=" * 60)
                    logger.info("✅ PLANNING WORKFLOW COMPLETE")
                    logger.info("=" * 60 + "\n")

                    if self.tracer:
                        self.tracer.complete(status="success", report_text=report)
                    return report
                else:
                    raise RuntimeError("Workflow produced no output content")
            else:
                raise RuntimeError("Workflow produced no messages")

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            if self.tracer:
                self.tracer.complete(status="error", error=str(e))
            raise RuntimeError(f"Planning workflow failed: {str(e)}")


async def create_market_research_workflow(
    topic: str,
    tracer: TrajectoryTracer | None = None
) -> PlanningMarketResearchWorkflow:
    """
    Factory function to create a Planning workflow instance.

    Args:
        topic: Research topic to investigate

    Returns:
        Configured PlanningMarketResearchWorkflow instance
    """
    return PlanningMarketResearchWorkflow(topic, tracer=tracer)


# Export public API
__all__ = ['PlanningMarketResearchWorkflow', 'create_market_research_workflow']
