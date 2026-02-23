#!/usr/bin/env python3
"""
LangGraph entrypoint for Planning Pattern Market Research Assistant.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from langgraph_workflow import LangGraphPlanningWorkflow
from trajectory_tracing import TrajectoryTracer


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_environment() -> tuple[bool, list[str]]:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    required_vars: dict[str, str] = {}
    if provider == "openai":
        required_vars["OPENAI_API_KEY"] = "OpenAI API key for LLM calls"
    elif provider == "anthropic":
        required_vars["ANTHROPIC_API_KEY"] = "Anthropic API key for LLM calls"
    else:
        required_vars["LLM_PROVIDER"] = "Must be either 'openai' or 'anthropic'"

    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")

    return len(missing) == 0, missing


def save_report(content: str, output_file: str) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    logger.info("📝 Report saved to: %s", output_path)
    logger.info("   File size: %s bytes", f"{output_path.stat().st_size:,}")


async def async_main(args: argparse.Namespace) -> None:
    start_time = datetime.now()
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = (
        os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        if provider == "anthropic"
        else os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    )

    tracer = TrajectoryTracer(
        topic=args.topic,
        provider=provider,
        model=model,
        enabled=not args.no_trace,
        output_dir=Path(args.trace_dir),
    )

    try:
        workflow = LangGraphPlanningWorkflow(topic=args.topic, tracer=tracer)
        report = await workflow.execute()
        save_report(report, args.output)

        duration = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("✅ SUCCESS (LangGraph)")
        print("=" * 60)
        print(f"Report saved to: {args.output}")
        print(f"Execution time: {duration:.1f} seconds")
        if tracer.enabled:
            print(f"Trajectory: {tracer.file_path}")
            print(f"Summary: {tracer.summary_path}")
        print("=" * 60 + "\n")
    except KeyboardInterrupt:
        logger.warning("Interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        logger.error("❌ ERROR: %s", str(e))
        logger.error("Troubleshooting:")
        logger.error("  1. Check provider key in .env")
        logger.error("  2. Check internet connectivity")
        logger.error("  3. Verify model/provider compatibility")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Planning Pattern Assistant (LangGraph)",
        epilog='Example: python main_langgraph.py "AI agent market size 2024-2026"',
    )
    parser.add_argument("topic", type=str, help="Research topic to analyze")
    parser.add_argument(
        "--output",
        type=str,
        default="planning_market_report_langgraph.md",
        help="Output file path",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model for selected provider",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        choices=["openai", "anthropic"],
        help="Override LLM provider",
    )
    parser.add_argument(
        "--trace-dir",
        type=str,
        default=os.getenv("TRACE_DIR", "trajectories"),
        help="Directory for trajectory JSONL outputs",
    )
    parser.add_argument(
        "--no-trace",
        action="store_true",
        help="Disable trajectory tracing for this run",
    )
    args = parser.parse_args()

    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider
        logger.info("Using provider: %s", args.provider)

    if args.model:
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if provider == "anthropic":
            os.environ["ANTHROPIC_MODEL"] = args.model
        else:
            os.environ["OPENAI_MODEL"] = args.model
        logger.info("Using model: %s", args.model)

    ok, missing = validate_environment()
    if not ok:
        logger.error("❌ Missing required environment variables:")
        for item in missing:
            logger.error("   - %s", item)
        sys.exit(1)

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = (
        os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        if provider == "anthropic"
        else os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    )
    print("\n" + "=" * 60)
    print("🎯 Planning Pattern Assistant (LangGraph)")
    print("=" * 60)
    print(f"📋 Topic: {args.topic}")
    print(f"📝 Output: {args.output}")
    print(f"🧠 Provider: {provider}")
    print(f"🤖 Model: {model}")
    print("=" * 60 + "\n")

    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()

