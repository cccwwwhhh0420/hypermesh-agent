# -*- coding: utf-8 -*-
"""Tool registry and OpenAI schema exporter for HyperMesh AI Agent."""

import json
from typing import Any, Callable, Dict, List
from hm_agent.tools.hm_tools import (
    tool_hypermesh_diff,
    tool_hypermesh_get_workspace,
    tool_hypermesh_ping,
    tool_hypermesh_read_gui_log,
    tool_hypermesh_run_tcl,
    tool_hypermesh_search_docs,
    tool_hypermesh_snapshot,
    tool_hypermesh_status,
)


OPENAI_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "hypermesh_get_workspace",
            "description": "Get the current working directory of the live HyperMesh instance, list available .hm / .fem files in that folder, and get the exact path to command1.tcl.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_read_gui_log",
            "description": "Read the most recent user actions and commands recorded in the active HyperMesh instance's command1.tcl. Call this to check what operations the human engineer recently performed in the GUI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tail_lines": {
                        "type": "integer",
                        "description": "Number of recent command lines to read. Default is 30."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_run_tcl",
            "description": "Execute a Tcl script in the live Altair HyperMesh 2022 instance. Returns execution output or detailed error traceback.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "The complete Tcl script to execute in HyperMesh. Supports multi-line commands. Avoid using explicit 'return' statement at the top level."
                    }
                },
                "required": ["script"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_search_docs",
            "description": "Search the HyperMesh 2022 command reference (3650 commands) for exact syntax, parameter definitions, descriptions, and examples. Call this whenever you are unsure of a command's syntax or arguments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "The command name or keyword to search (e.g. '*createmark', 'hm_getvalue', 'optistruct', '*surfacemesh')."
                    },
                    "detail": {
                        "type": "boolean",
                        "description": "Whether to return full syntax and example documentation for the matched commands. Default is false (summary list)."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of matching commands to return. Default is 5."
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_status",
            "description": "Query current model summary statistics (counts of nodes, lines, surfaces, comps, solids, elems, loads, mats, props) from the active HyperMesh session.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_snapshot",
            "description": "Capture a full model state snapshot (components, materials, design variables, loads, entity counts) to detect modifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Optional tag name for the snapshot (e.g. 'before_meshing', 'after_loads')."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_diff",
            "description": "Compare two model snapshots to detect changes made by the user in the HyperMesh GUI or by previous scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "snap_a": {
                        "type": "string",
                        "description": "Filename or tag of first snapshot (baseline). If omitted, uses second-to-last snapshot."
                    },
                    "snap_b": {
                        "type": "string",
                        "description": "Filename or tag of second snapshot (current). If omitted, uses latest snapshot."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hypermesh_ping",
            "description": "Check whether HyperMesh bridge server is online and responding.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# Function mapping
TOOL_HANDLERS: Dict[str, Callable[..., str]] = {
    "hypermesh_get_workspace": tool_hypermesh_get_workspace,
    "hypermesh_read_gui_log": tool_hypermesh_read_gui_log,
    "hypermesh_run_tcl": tool_hypermesh_run_tcl,
    "hypermesh_search_docs": tool_hypermesh_search_docs,
    "hypermesh_status": tool_hypermesh_status,
    "hypermesh_snapshot": tool_hypermesh_snapshot,
    "hypermesh_diff": tool_hypermesh_diff,
    "hypermesh_ping": tool_hypermesh_ping,
}



def dispatch_tool_call(tool_name: str, arguments_json: str) -> str:
    """Parse tool arguments and dispatch to corresponding handler."""
    if tool_name not in TOOL_HANDLERS:
        return f"Error: Tool '{tool_name}' is not registered."

    handler = TOOL_HANDLERS[tool_name]
    try:
        kwargs = json.loads(arguments_json) if arguments_json.strip() else {}
        return handler(**kwargs)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON arguments: {e}"
    except TypeError as e:
        return f"Error invoking {tool_name}: {e}"
    except Exception as e:
        return f"Tool execution error ({tool_name}): {e}"
