# -*- coding: utf-8 -*-
"""HyperMesh 2022 command documentation search engine."""

import re
from typing import Dict, List, Optional
from hm_agent.config import COMMAND_INDEX_PATH, COMMAND_REF_PATH


class CommandDocSearch:
    """Fast in-memory index and search engine for HyperMesh 2022 command reference."""

    def __init__(self):
        self.commands: List[str] = []
        self.doc_sections: Dict[str, str] = {}
        self._loaded: bool = False

    def load(self) -> None:
        """Load and index command reference files into memory."""
        if self._loaded:
            return

        # Load command index
        if COMMAND_INDEX_PATH.exists():
            with open(COMMAND_INDEX_PATH, "r", encoding="utf-8", errors="replace") as f:
                self.commands = [line.strip() for line in f if line.strip()]

        # Load and split markdown documentation
        if COMMAND_REF_PATH.exists():
            with open(COMMAND_REF_PATH, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Split by section headers: "## command_name"
            pattern = re.compile(r"^##\s+([^\r\n]+)", re.MULTILINE)
            matches = list(pattern.finditer(content))

            for i, match in enumerate(matches):
                cmd_name = match.group(1).strip()
                start_pos = match.start()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                section_text = content[start_pos:end_pos].strip()
                self.doc_sections[cmd_name.lower()] = section_text
                if cmd_name not in self.commands:
                    self.commands.append(cmd_name)

        self._loaded = True

    def get_command_details(self, cmd_name: str) -> Optional[str]:
        """Get full documentation section for a specific command name."""
        self.load()
        cleaned = cmd_name.strip().lower()
        if cleaned in self.doc_sections:
            return self.doc_sections[cleaned]

        # Try prefix matching if exact match not found
        for key, section in self.doc_sections.items():
            if key == cleaned or key.endswith(cleaned) or cleaned.endswith(key):
                return section

        return None

    def search(self, query: str, limit: int = 5, full_detail: bool = False) -> str:
        """Search commands by keyword with optional full documentation."""
        self.load()
        q = query.strip().lower()
        if not q:
            return "Error: query string is empty."

        # Exact match check first
        if q in self.doc_sections and (limit == 1 or full_detail):
            return self.doc_sections[q]

        # Find matching command names
        matched_cmds: List[str] = []
        for cmd in self.commands:
            if q in cmd.lower():
                matched_cmds.append(cmd)

        # If name matching is low, search inside documentation contents
        if len(matched_cmds) < limit:
            for cmd_lower, section in self.doc_sections.items():
                if cmd_lower not in [m.lower() for m in matched_cmds]:
                    if q in section.lower():
                        matched_cmds.append(cmd_lower)
                        if len(matched_cmds) >= limit * 2:
                            break

        if not matched_cmds:
            return f"No commands found matching '{query}' in HyperMesh 2022 command reference."

        selected = matched_cmds[:limit]
        if full_detail:
            results = []
            for cmd in selected:
                detail = self.get_command_details(cmd)
                if detail:
                    results.append(detail)
                else:
                    results.append(f"## {cmd}\n(No extended documentation found)")
            return "\n\n---\n\n".join(results)
        else:
            lines = [f"Found {len(matched_cmds)} matching command(s) (showing top {len(selected)}):"]
            for cmd in selected:
                detail = self.get_command_details(cmd)
                if detail:
                    # Extract syntax line if available
                    syntax_match = re.search(r"\*\*语法\*\*:\s*`([^`]+)`", detail)
                    syntax = syntax_match.group(1) if syntax_match else cmd
                    lines.append(f"- `{cmd}`: {syntax}")
                else:
                    lines.append(f"- `{cmd}`")
            lines.append("\nTip: Call search with full_detail=true or search for the exact command name to view complete parameters and examples.")
            return "\n".join(lines)


# Global singleton instance
doc_searcher = CommandDocSearch()
