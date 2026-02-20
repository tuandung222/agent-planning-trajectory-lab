#!/usr/bin/env python3
"""
Planning Pattern Market Research - Tool Definitions (Microsoft Agent Framework)

This module defines tools for use with Microsoft Agent Framework and Claude.
Unlike ReAct which interleaves reasoning and action, the Planning pattern
creates a complete research plan upfront, then executes tools sequentially.

Tools:
    - web_search: Search the web for current market information
    - calculator: Perform mathematical calculations for metrics
    - save_findings: Save research findings to markdown

Author: GP (genmind.ch)
License: MIT
Blog Post: https://genmind.ch/posts/Planning-Pattern-for-AI-Agents-Strategic-Reasoning-Before-Action/
"""

import os
import json
import ast
import operator
import time
from pathlib import Path
from typing import Annotated
import requests

from agent_framework import tool
from trajectory_tracing import get_current_tracer


@tool
async def web_search(query: Annotated[str, "The search query to execute"]) -> str:
    """
    Search the web for current information using Serper API.

    This tool enables the agent to access real-time market data,
    company information, industry reports, and other web content.

    Args:
        query: Search query string (e.g., "AI agent market size 2024-2026")

    Returns:
        Formatted JSON string with search results including titles, snippets, and URLs

    Raises:
        RuntimeError: If API key is missing or request fails

    Examples:
        >>> await web_search("Goldman Sachs AI agent deployment")
        >>> await web_search("Planning pattern vs ReAct benchmark")
    """
    tracer = get_current_tracer()
    started = time.perf_counter()
    if tracer:
        tracer.log_tool_call("web_search", query=query)

    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        message = (
            "SERPER_API_KEY environment variable not set. "
            "Get your free API key at https://serper.dev"
        )
        if tracer:
            tracer.log_tool_result(
                "web_search",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=message,
            )
        raise RuntimeError(message)

    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 10})
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()

        # Format results for LLM consumption
        formatted_results = []

        # Knowledge graph (if available) - highest quality
        if 'knowledgeGraph' in results:
            kg = results['knowledgeGraph']
            formatted_results.append({
                "type": "knowledge_graph",
                "title": kg.get('title', ''),
                "description": kg.get('description', ''),
                "source": kg.get('source', ''),
                "attributes": kg.get('attributes', {})
            })

        # Organic search results
        for item in results.get('organic', [])[:5]:
            formatted_results.append({
                "title": item.get('title', 'No title'),
                "snippet": item.get('snippet', 'No snippet'),
                "link": item.get('link', ''),
                "position": item.get('position', 0)
            })

        output = json.dumps(formatted_results, indent=2)
        if tracer:
            tracer.log_tool_result(
                "web_search",
                ok=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output

    except requests.Timeout:
        output = f"ERROR: Search timed out after 10 seconds for query: {query}"
        if tracer:
            tracer.log_tool_result(
                "web_search",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except requests.RequestException as e:
        output = f"ERROR: Search failed: {str(e)}"
        if tracer:
            tracer.log_tool_result(
                "web_search",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except json.JSONDecodeError:
        output = "ERROR: Failed to parse search results"
        if tracer:
            tracer.log_tool_result(
                "web_search",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output


@tool
async def calculator(
    expression: Annotated[str, "Mathematical expression to evaluate (e.g., '(10 * 5) / 2')"]
) -> str:
    """
    Safely evaluate mathematical expressions using AST parsing.

    Supports basic arithmetic operations: +, -, *, /, **, %
    Uses AST parsing instead of eval() to prevent code injection attacks.

    Args:
        expression: Mathematical expression as string

    Returns:
        Result as string, or error message if evaluation fails

    Security:
        Only allows safe mathematical operations. No arbitrary code execution.

    Examples:
        >>> await calculator("((47.1 / 5.43) ** (1/6) - 1) * 100")
        "43.2"
        >>> await calculator("192 / 100")
        "1.92"
    """
    tracer = get_current_tracer()
    started = time.perf_counter()
    if tracer:
        tracer.log_tool_call("calculator", expression=expression)

    ALLOWED_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    def _eval_node(node):
        """Recursively evaluate AST nodes safely."""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7
            return node.n
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op = ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op = ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            return op(operand)
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")

    try:
        tree = ast.parse(expression, mode='eval')
        result = _eval_node(tree.body)
        output = str(result)
        if tracer:
            tracer.log_tool_result(
                "calculator",
                ok=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except SyntaxError:
        output = f"ERROR: Invalid expression: {expression}"
        if tracer:
            tracer.log_tool_result(
                "calculator",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except ValueError as e:
        output = f"ERROR: {str(e)}"
        if tracer:
            tracer.log_tool_result(
                "calculator",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except ZeroDivisionError:
        output = "ERROR: Division by zero"
        if tracer:
            tracer.log_tool_result(
                "calculator",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output
    except Exception as e:
        output = f"ERROR: Calculation failed: {str(e)}"
        if tracer:
            tracer.log_tool_result(
                "calculator",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output


@tool
async def save_findings(
    filename: Annotated[str, "Name of markdown file to create"],
    content: Annotated[str, "Markdown content to write"]
) -> str:
    """
    Save research findings to a markdown file in the outputs directory.

    Args:
        filename: Name of file (e.g., "market_report.md")
        content: Markdown-formatted content to save

    Returns:
        Success message with file path and size

    Security:
        Sanitizes filename to prevent path traversal attacks.
        Only writes to outputs/ subdirectory.
    """
    tracer = get_current_tracer()
    started = time.perf_counter()
    if tracer:
        tracer.log_tool_call("save_findings", filename=filename, content_size=len(content))

    # Sanitize filename (prevent path traversal)
    safe_filename = os.path.basename(filename)
    if not safe_filename.endswith('.md'):
        safe_filename += '.md'

    # Create outputs directory
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / safe_filename

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        size = file_path.stat().st_size
        output = f"✅ Saved {size:,} bytes to {file_path}"
        if tracer:
            tracer.log_tool_result(
                "save_findings",
                ok=True,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output

    except Exception as e:
        output = f"ERROR: Failed to save file: {str(e)}"
        if tracer:
            tracer.log_tool_result(
                "save_findings",
                ok=False,
                latency_ms=int((time.perf_counter() - started) * 1000),
                result_preview=output,
            )
        return output


# Export all tools
__all__ = ['web_search', 'calculator', 'save_findings']
