# -*- coding: utf-8 -*-
"""Tool definitions and execution handlers for HyperMesh AI Agent."""

from typing import Any, Dict, List, Optional
from hm_agent.bridge.client import (
    diff_snapshots,
    get_status,
    get_workspace_info,
    last_snapshots,
    list_snapshots,
    load_snapshot,
    ping,
    read_command_log,
    run_tcl,
    take_snapshot,
)
from hm_agent.tools.doc_search import doc_searcher


def tool_hypermesh_get_workspace() -> str:
    """Get active HyperMesh workspace directory, associated .hm/.fem files, and command1.tcl status."""
    info = get_workspace_info()
    if "error" in info and info["error"]:
        return f"Failed to get workspace info: {info['error']}"
    lines = [
        f"Working Directory: {info.get('working_dir')}",
        f"Command Log File: {info.get('command_file')} (Exists: {info.get('has_command_file')})",
    ]
    hm_files = info.get("hm_files", [])
    if hm_files:
        lines.append(f"Found .hm Files in Directory: {hm_files}")
    fem_files = info.get("fem_files", [])
    if fem_files:
        lines.append(f"Found .fem Files in Directory: {fem_files}")
    return "\n".join(lines)


def tool_hypermesh_read_gui_log(tail_lines: int = 30) -> str:
    """Read the latest Tcl commands recorded by HyperMesh when the user operates the GUI."""
    return read_command_log(tail_lines=tail_lines)



def tool_hypermesh_ping() -> str:
    """Check whether HyperMesh bridge server is online and responding."""
    is_alive = ping()
    if is_alive:
        return "HyperMesh bridge is ONLINE and connected (127.0.0.1:23456)."
    return "HyperMesh bridge is OFFLINE. Please ensure HyperMesh is open with hm_bridge.tcl loaded."


def tool_hypermesh_run_tcl(script: str) -> str:
    """Execute Tcl script in HyperMesh and return output or error message."""
    if not script.strip():
        return "Error: Empty Tcl script provided."
    ok, res = run_tcl(script)
    if ok:
        return f"SUCCESS:\n{res}" if res else "SUCCESS (Command executed with no output)."
    return f"ERROR:\n{res}"


def tool_hypermesh_search_docs(keyword: str, detail: bool = False, limit: int = 5) -> str:
    """Search HyperMesh 2022 command documentation for syntax, parameters, and examples."""
    return doc_searcher.search(query=keyword, limit=limit, full_detail=detail)


def tool_hypermesh_status() -> str:
    """Get current entity counts (nodes, elems, comps, loads, mats) from HyperMesh."""
    ok, res = get_status()
    if ok:
        return f"HyperMesh Status:\n{res}"
    return f"Failed to get status: {res}"


def tool_hypermesh_snapshot(tag: Optional[str] = None) -> str:
    """Take a full snapshot of current HyperMesh model entities to detect changes."""
    ok, path, data = take_snapshot(tag=tag)
    if ok:
        counts = data.get("counts", {})
        counts_str = ", ".join([f"{k.upper()}={v}" for k, v in counts.items()])
        return f"Snapshot captured successfully and saved to: {path}\nSummary: {counts_str}"
    return f"Snapshot failed: {path}"


def tool_hypermesh_diff(snap_a: Optional[str] = None, snap_b: Optional[str] = None) -> str:
    """Compare two model snapshots to detect manual user edits or script modifications."""
    try:
        snaps = list_snapshots()
        if not snaps:
            return "No snapshots available. Please run hypermesh_snapshot first."

        if snap_a is None or snap_b is None:
            if len(snaps) < 2:
                return f"Need at least 2 snapshots to diff. Found {len(snaps)}: {[s.name for s in snaps]}"
            path_a = str(snaps[-2])
            path_b = str(snaps[-1])
        else:
            path_a = snap_a
            path_b = snap_b

        data_a = load_snapshot(path_a)
        data_b = load_snapshot(path_b)
        res = diff_snapshots(data_a, data_b)
        return f"Snapshot Diff (A: {path_a} -> B: {path_b}):\n{res}"
    except Exception as e:
        return f"Diff failed: {e}"
