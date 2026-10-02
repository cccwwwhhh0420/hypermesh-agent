# -*- coding: utf-8 -*-
"""Main interactive CLI entry point for HyperMesh AI Agent."""

import sys
from pathlib import Path

# Ensure project directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hm_agent.agent.core import HyperMeshAgent
from hm_agent.agent.llm import LLMClient
from hm_agent.bridge.client import (
    diff_snapshots,
    get_status,
    list_snapshots,
    load_snapshot,
    ping,
    run_tcl,
    take_snapshot,
)
from hm_agent.config import (
    API_KEY,
    BASE_URL,
    HM_HOST,
    HM_PORT,
    MODEL_NAME,
)
from hm_agent.tools.doc_search import doc_searcher


def print_banner(console: Console) -> None:
    """Display startup banner with environment status."""
    is_connected = ping()
    bridge_status = "[bold green]ONLINE (Connected)[/bold green]" if is_connected else "[bold red]OFFLINE (127.0.0.1:23456)[/bold red]"
    
    doc_searcher.load()
    cmd_count = len(doc_searcher.commands)

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan")
    table.add_column()
    table.add_row("LLM Model:", f"[yellow]{MODEL_NAME}[/yellow] ({BASE_URL})")
    table.add_row("API Key:", "[green]Configured[/green]" if API_KEY else "[red]Missing (Set DEEPSEEK_API_KEY in .env)[/red]")
    table.add_row("HyperMesh Bridge:", bridge_status)
    table.add_row("Tcl Knowledgebase:", f"[green]{cmd_count} HyperMesh 2022 Commands Loaded[/green]")

    panel = Panel(
        table,
        title="[bold white]HyperMesh 2022 AI Command Center[/bold white]",
        subtitle="[dim]Type your prompt or /help for slash commands | Ctrl+C to exit[/dim]",
        border_style="blue"
    )
    console.print(panel)


def print_help(console: Console) -> None:
    """Print available slash commands."""
    table = Table(title="Available Slash Commands", border_style="cyan")
    table.add_column("Command", style="bold green")
    table.add_column("Description")
    table.add_row("/workspace, /pwd", "Show active HyperMesh directory, command1.tcl and .hm/.fem files")
    table.add_row("/log [n]", "Read the last n lines of user GUI actions from command1.tcl (default: 30)")
    table.add_row("/status", "Get current entity counts (nodes, elems, comps, loads, mats)")
    table.add_row("/run <tcl>", "Directly execute a Tcl script in HyperMesh without LLM")
    table.add_row("/search <query>", "Search the 3650 HyperMesh 2022 command documentation")
    table.add_row("/snapshot [tag]", "Capture and save a full model state snapshot")
    table.add_row("/diff [a] [b]", "Compare two snapshots to detect user modifications")
    table.add_row("/ping", "Check connection status with HyperMesh bridge")
    table.add_row("/reset", "Clear conversation history and start a new session")
    table.add_row("/help", "Show this help table")
    table.add_row("/exit, /quit", "Exit the CLI application")
    console.print(table)


def handle_slash_command(cmd_line: str, agent: HyperMeshAgent, console: Console) -> bool:
    """Process slash command. Returns True if handled."""
    parts = cmd_line.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ["/exit", "/quit"]:
        console.print("[bold yellow]Exiting HyperMesh AI Command Center. Goodbye![/bold yellow]")
        sys.exit(0)

    elif cmd == "/help":
        print_help(console)
        return True

    elif cmd == "/ping":
        if ping():
            console.print("[bold green]HyperMesh bridge is ONLINE and responding.[/bold green]")
        else:
            console.print("[bold red]HyperMesh bridge is OFFLINE. Ensure HyperMesh has hm_bridge.tcl running.[/bold red]")
        return True

    elif cmd in ["/workspace", "/pwd"]:
        from hm_agent.tools.hm_tools import tool_hypermesh_get_workspace
        res = tool_hypermesh_get_workspace()
        console.print(Panel(res, title="HyperMesh Active Workspace", border_style="cyan"))
        return True

    elif cmd == "/log":
        from hm_agent.tools.hm_tools import tool_hypermesh_read_gui_log
        lines = int(arg) if arg.isdigit() else 30
        res = tool_hypermesh_read_gui_log(tail_lines=lines)
        console.print(Panel(res, title="HyperMesh GUI Command Log", border_style="cyan"))
        return True

    elif cmd == "/status":
        ok, res = get_status()
        if ok:
            console.print(Panel(res, title="HyperMesh Model Status", border_style="green"))
        else:
            console.print(f"[bold red]Failed to get status: {res}[/bold red]")
        return True


    elif cmd == "/run":
        if not arg:
            console.print("[yellow]Usage: /run <tcl script>[/yellow]")
            return True
        ok, res = run_tcl(arg)
        if ok:
            console.print(Panel(res if res else "(Success - No output)", title="Tcl Execution Output", border_style="green"))
        else:
            console.print(Panel(res, title="Tcl Execution Error", border_style="red"))
        return True

    elif cmd == "/search":
        if not arg:
            console.print("[yellow]Usage: /search <keyword>[/yellow]")
            return True
        res = doc_searcher.search(arg, limit=5, full_detail=False)
        console.print(Panel(res, title=f"Documentation Search: '{arg}'", border_style="cyan"))
        return True

    elif cmd == "/snapshot":
        ok, path, data = take_snapshot(tag=arg if arg else None)
        if ok:
            counts = data.get("counts", {})
            counts_str = ", ".join([f"{k.upper()}={v}" for k, v in counts.items()])
            console.print(f"[bold green]Snapshot saved:[/bold green] {path}\n[dim]Summary: {counts_str}[/dim]")
        else:
            console.print(f"[bold red]Snapshot failed: {path}[/bold red]")
        return True

    elif cmd == "/diff":
        snaps = list_snapshots()
        if not snaps:
            console.print("[yellow]No snapshots available. Use /snapshot to create one first.[/yellow]")
            return True
        tokens = arg.split()
        if len(tokens) >= 2:
            snap_a, snap_b = tokens[0], tokens[1]
        elif len(snaps) >= 2:
            snap_a, snap_b = str(snaps[-2]), str(snaps[-1])
        else:
            console.print(f"[yellow]Need at least 2 snapshots. Only found 1: {snaps[0].name}[/yellow]")
            return True

        try:
            da = load_snapshot(snap_a)
            db = load_snapshot(snap_b)
            diff_text = diff_snapshots(da, db)
            console.print(Panel(diff_text, title=f"Diff: {Path(snap_a).name} vs {Path(snap_b).name}", border_style="cyan"))
        except Exception as e:
            console.print(f"[bold red]Diff failed: {e}[/bold red]")
        return True

    elif cmd in ["/reset", "/clear"]:
        agent.reset()
        console.print("[bold green]Conversation context reset.[/bold green]")
        return True

    return False


def main() -> None:
    """Run interactive REPL loop."""
    console = Console()
    print_banner(console)

    llm = LLMClient()
    agent = HyperMeshAgent(llm_client=llm, console=console)

    if not llm.is_configured():
        console.print(
            "\n[bold yellow]Notice:[/bold yellow] No API Key detected. "
            "You can still use slash commands (e.g. [bold green]/run[/bold green], [bold green]/search[/bold green], [bold green]/status[/bold green]), "
            "or configure [bold cyan].env[/bold cyan] to enable AI chat.\n"
        )

    while True:
        try:
            user_input = console.input("\n[bold white]HyperMesh-AI >[/bold white] ").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                if handle_slash_command(user_input, agent, console):
                    continue

            # Run agent conversation turn
            try:
                agent.run_turn(user_input)
            except Exception as e:
                console.print(f"[bold red]Agent error: {e}[/bold red]")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Exiting...[/bold yellow]")
            break


if __name__ == "__main__":
    main()
