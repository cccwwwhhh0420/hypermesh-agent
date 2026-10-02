# -*- coding: utf-8 -*-
"""ReAct Agent engine for HyperMesh AI automation."""

import json
from typing import Any, Callable, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from hm_agent.agent.llm import LLMClient
from hm_agent.agent.prompts import HYPERMESH_SYSTEM_PROMPT
from hm_agent.config import MAX_AGENT_STEPS
from hm_agent.tools.registry import OPENAI_TOOLS_SCHEMA, dispatch_tool_call


class HyperMeshAgent:
    """ReAct autonomous agent driving HyperMesh 2022 via tool calls."""

    def __init__(self, llm_client: Optional[LLMClient] = None, console: Optional[Console] = None):
        self.llm = llm_client or LLMClient()
        self.console = console or Console()
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": HYPERMESH_SYSTEM_PROMPT}
        ]
        self._last_tool_sig: Optional[str] = None
        self._repeat_call_count: int = 0

    def reset(self) -> None:
        """Reset conversation history back to initial system prompt."""
        self.messages = [
            {"role": "system", "content": HYPERMESH_SYSTEM_PROMPT}
        ]
        self._last_tool_sig = None
        self._repeat_call_count = 0

    def run_turn(self, user_prompt: str) -> str:
        """Execute a full multi-step conversation turn with the user."""
        self.messages.append({"role": "user", "content": user_prompt})
        self._last_tool_sig = None
        self._repeat_call_count = 0

        step_count = 0
        final_response_text = ""

        while step_count < MAX_AGENT_STEPS:
            step_count += 1
            has_tool_call = False

            # Stream response from LLM with live thinking display
            token_gen, result_container = self.llm.chat_stream(self.messages, tools=OPENAI_TOOLS_SCHEMA)

            reasoning_chunks: List[str] = []
            streamed_content: List[str] = []

            with self.console.status("[dim cyan]Thinking & analyzing...[/dim cyan]", spinner="dots") as status:
                for token_type, delta in token_gen:
                    if token_type == "reasoning":
                        reasoning_chunks.append(delta)
                        last_line = "".join(reasoning_chunks).strip().splitlines()[-1] if reasoning_chunks else ""
                        if len(last_line) > 50:
                            last_line = last_line[-50:]
                        status.update(f"[dim cyan]Thinking: {last_line}[/dim cyan]")
                    elif token_type == "content":
                        streamed_content.append(delta)

            # If there was reasoning output, render it in a clean, compact dimmed panel
            if reasoning_chunks:
                full_thought = "".join(reasoning_chunks).strip()
                self.console.print(Panel(
                    f"[dim]{full_thought}[/dim]",
                    title="[dim]💭 Thought Process[/dim]",
                    border_style="dim",
                    padding=(0, 1)
                ))

            assistant_msg = result_container.get("message")
            if not assistant_msg:
                break

            self.messages.append(assistant_msg)
            tool_calls = assistant_msg.get("tool_calls")

            # If there are NO tool calls, this is the final answer — print it cleanly
            if not tool_calls:
                content = assistant_msg.get("content", "")
                if content:
                    final_response_text = content
                    self.console.print(f"\n[bold green]AI:[/bold green] {content}\n")
                break

            # If there ARE tool calls, process them directly
            has_tool_call = True
            for tc in tool_calls:
                fn = tc["function"]
                fn_name = fn["name"]
                fn_args = fn["arguments"]

                # DSH-style Repeat-Tool Guard: detect consecutive identical calls
                current_sig = f"{fn_name}:{fn_args.strip()}"
                if current_sig == self._last_tool_sig:
                    self._repeat_call_count += 1
                else:
                    self._last_tool_sig = current_sig
                    self._repeat_call_count = 1

                # Pretty print tool invocation
                self._display_tool_call(fn_name, fn_args)

                # Execute tool
                tool_output = dispatch_tool_call(fn_name, fn_args)

                # Pretty print tool result
                self._display_tool_result(fn_name, tool_output)

                # Append tool result to messages
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": tool_output
                })

                # Inject DSH loop reminder if model is stuck in repeated calls
                if self._repeat_call_count >= 2:
                    self.console.print("[dim yellow]  [DSH Guard] Repeated tool call detected. Injecting anti-loop reminder.[/dim yellow]")
                    self.messages.append({
                        "role": "system",
                        "content": (
                            f"[System Loop-Breaker Notice] Repeated call to '{fn_name}' detected ({self._repeat_call_count} times). "
                            "This call did not make progress. Do NOT run the exact same parameters again. "
                            "Analyze the last output/error, change your approach, or finish the task."
                        )
                    })

        if step_count >= MAX_AGENT_STEPS:
            self.console.print("[bold yellow]Warning: Reached maximum step limit for single turn.[/bold yellow]")

        return final_response_text


    def _display_tool_call(self, fn_name: str, args_json: str) -> None:
        """Render tool call header and arguments in terminal."""
        try:
            parsed = json.loads(args_json)
        except Exception:
            parsed = args_json

        if fn_name == "hypermesh_run_tcl" and isinstance(parsed, dict) and "script" in parsed:
            tcl_code = parsed["script"].strip()
            syntax = Syntax(tcl_code, "tcl", theme="monokai", line_numbers=True)
            self.console.print(Panel(syntax, title="[bold green]Executing Tcl in HyperMesh[/bold green]", border_style="green"))
        else:
            args_str = json.dumps(parsed, ensure_ascii=False, indent=2) if isinstance(parsed, (dict, list)) else str(parsed)
            self.console.print(f"\n[bold blue]Tool Call: {fn_name}[/bold blue]\n[dim]{args_str}[/dim]")

    def _display_tool_result(self, fn_name: str, output: str) -> None:
        """Render tool execution output summary in terminal."""
        lines = output.strip().splitlines()
        preview = "\n".join(lines[:12])
        if len(lines) > 12:
            preview += f"\n... ({len(lines) - 12} more lines truncated)"

        if output.startswith("ERROR") or "failed" in output.lower():
            self.console.print(Panel(preview, title=f"[bold red]{fn_name} Result (Error)[/bold red]", border_style="red"))
        else:
            self.console.print(Panel(preview, title=f"[bold cyan]{fn_name} Result[/bold cyan]", border_style="cyan"))
