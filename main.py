#!/usr/bin/env python3
"""
Planning Pattern Market Research Assistant - Main Entry Point

Demonstrates the Planning pattern using Microsoft Agent Framework.

The Planning pattern creates a comprehensive strategy UPFRONT, then executes
it systematically. This contrasts with ReAct which continuously interleaves
reasoning and action in a loop.

Usage:
    python main.py "AI agent market size 2024-2026"
    python main.py "quantum computing enterprise adoption" --output quantum_report.md
    python main.py "autonomous vehicles market forecast" --provider openai --model gpt-4.1-mini

Author: GP (genmind.ch)
License: MIT
Blog Post: https://genmind.ch/posts/Planning-Pattern-for-AI-Agents-Strategic-Reasoning-Before-Action/
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from planning_workflow import PlanningMarketResearchWorkflow
from trajectory_tracing import TrajectoryTracer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment() -> tuple[bool, list[str]]:
    """
    Validate required environment variables are set.

    Returns:
        Tuple of (is_valid, list_of_missing_vars)
    """
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    required_vars = {
        "SERPER_API_KEY": "Serper API key for web search"
    }
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
    """
    Save market research report to file.

    Args:
        content: Report content (markdown)
        output_file: Output file path

    Raises:
        IOError: If file write fails
    """
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        size = output_path.stat().st_size

        logger.info(f"📝 Report saved to: {output_path}")
        logger.info(f"   File size: {size:,} bytes")

    except Exception as e:
        logger.error(f"Failed to save report: {str(e)}")
        raise IOError(f"Could not write to {output_file}: {str(e)}")


async def async_main(args):
    """Async main function."""
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
        output_dir=Path(args.trace_dir)
    )

    try:
        # Create workflow
        workflow = PlanningMarketResearchWorkflow(topic=args.topic, tracer=tracer)

        # Execute workflow
        result = await workflow.execute()

        # Save report
        save_report(result, args.output)

        # Calculate execution time
        duration = (datetime.now() - start_time).total_seconds()

        # Print success message
        print("\n" + "=" * 60)
        print("✅ SUCCESS")
        print("=" * 60)
        print(f"Report saved to: {args.output}")
        print(f"Execution time: {duration:.1f} seconds")
        if tracer.enabled:
            print(f"Trajectory: {tracer.file_path}")
            print(f"Summary: {tracer.summary_path}")
        print("\nNext steps:")
        print(f"  - Review the report: cat {args.output}")
        print("  - Open in your editor for refinement")
        print("  - Share with stakeholders")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Research interrupted by user (Ctrl+C)")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\n❌ ERROR: {str(e)}")
        logger.error("\nTroubleshooting tips:")
        logger.error("  1. Check your API keys in .env file")
        logger.error("  2. Verify internet connectivity")
        logger.error("  3. Check your provider API status")
        logger.error("  4. Try a simpler research topic")
        sys.exit(1)


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Planning Pattern Market Research Assistant (Microsoft Agent Framework)',
        epilog='Example: python main.py "AI agent market size 2024-2026"',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'topic',
        type=str,
        help='Research topic to analyze'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='planning_market_report.md',
        help='Output file path (default: planning_market_report.md)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Override model for selected provider'
    )

    parser.add_argument(
        '--provider',
        type=str,
        default=None,
        choices=['openai', 'anthropic'],
        help='Override LLM provider (default: env LLM_PROVIDER or openai)'
    )

    parser.add_argument(
        '--trace-dir',
        type=str,
        default=os.getenv("TRACE_DIR", "trajectories"),
        help='Directory for trajectory JSONL outputs'
    )

    parser.add_argument(
        '--no-trace',
        action='store_true',
        help='Disable trajectory tracing for this run'
    )

    args = parser.parse_args()

    if args.provider:
        os.environ['LLM_PROVIDER'] = args.provider
        logger.info(f"Using provider: {args.provider}")

    # Validate environment
    is_valid, missing_vars = validate_environment()
    if not is_valid:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.error("\nPlease configure your .env file (see .env.example)")
        sys.exit(1)

    # Override model if specified
    if args.model:
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if provider == "anthropic":
            os.environ['ANTHROPIC_MODEL'] = args.model
        else:
            os.environ['OPENAI_MODEL'] = args.model
        logger.info(f"Using model: {args.model}")

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = (
        os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")
        if provider == "anthropic"
        else os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    )

    # Print startup banner
    print("\n" + "=" * 60)
    print("🎯 Planning Pattern Market Research Assistant")
    print("   Framework: Microsoft Agent Framework")
    print("=" * 60)
    print(f"📋 Topic: {args.topic}")
    print(f"📝 Output: {args.output}")
    print(f"🧠 Provider: {provider}")
    print(f"🤖 Model: {model}")
    print("=" * 60 + "\n")

    # Run async main
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
