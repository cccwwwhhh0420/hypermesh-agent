# -*- coding: utf-8 -*-
"""HyperMesh TCP Bridge client implementation."""

import base64
import json
import os
import socket
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from hm_agent.config import HM_HOST, HM_PORT, HM_TIMEOUT, STATE_DIR


class HyperMeshConnectionError(Exception):
    """Exception raised when connection to HyperMesh bridge fails."""
    pass


class HyperMeshExecutionError(Exception):
    """Exception raised when Tcl execution fails in HyperMesh."""
    pass


def b64e(s: str) -> str:
    """Encode UTF-8 string to base64 ASCII string."""
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def b64d(s: str) -> str:
    """Decode base64 ASCII string to UTF-8 string."""
    return base64.b64decode(s).decode("utf-8", "replace")


def transact(line: str, host: str = HM_HOST, port: int = HM_PORT, timeout: float = HM_TIMEOUT) -> str:
    """Send a single-line command to HyperMesh TCP server and read response."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.sendall(line.encode("utf-8") + b"\n")
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
        return buf.split(b"\n", 1)[0].decode("utf-8", "replace").strip()
    except OSError as e:
        raise HyperMeshConnectionError(f"Cannot connect to HyperMesh bridge at {host}:{port}. Ensure HyperMesh is open with hm_bridge.tcl running. (Error: {e})")


def ping(host: str = HM_HOST, port: int = HM_PORT, timeout: float = 5.0) -> bool:
    """Check connectivity with HyperMesh TCP server."""
    try:
        return transact("ping", host=host, port=port, timeout=timeout) == "pong"
    except Exception:
        return False


def run_tcl(tcl: str, host: str = HM_HOST, port: int = HM_PORT, timeout: float = HM_TIMEOUT) -> Tuple[bool, str]:
    """Execute raw Tcl script inside HyperMesh and return (is_success, output_or_error)."""
    try:
        reply = transact("cmd " + b64e(tcl), host=host, port=port, timeout=timeout)
        if reply == "ok" or reply.startswith("ok "):
            res = b64d(reply[3:] if len(reply) > 3 else "")
            return True, res
        if reply == "err" or reply.startswith("err "):
            err = b64d(reply[4:] if len(reply) > 4 else "")
            return False, err
        return False, f"Unexpected response from bridge: {reply}"
    except HyperMeshConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Bridge communication error: {e}"


STATUS_SCRIPT = """
set out "COUNTS: "
foreach t {nodes lines surfaces comps solids elems loads mats props} {
  catch { *createmark $t 1 all; append out "  [string toupper $t]=[hm_marklength $t 1]" }
}
set out
"""


def get_status(host: str = HM_HOST, port: int = HM_PORT, timeout: float = 30.0) -> Tuple[bool, str]:
    """Retrieve entity counts summary from active HyperMesh session."""
    return run_tcl(STATUS_SCRIPT, host=host, port=port, timeout=timeout)


SNAPSHOT_SCRIPT = """
set out "COUNTS "
foreach t {nodes elems comps surfaces lines solids loads mats props systems} {
  *createmark $t 1 all
  append out "[string toupper $t]=[hm_marklength $t 1] "
}
append out "\n"
*createmark comps 1 all
set cids [hm_entitylist comps id all]
foreach id $cids {
  set nm [hm_getentityvalue comps $id "name" 1]
  catch {set col [hm_getentityvalue comps $id "color" 0]}
  *createmark comps 2 $id
  catch {*createmark elems 1 bycollector comps 2}
  set ne [hm_marklength elems 1]
  append out "COMP id=$id name=$nm color=$col elems=$ne\n"
}
append out "LOADS=[hm_entitylist loads id all]\n"
*createmark mats 1 all
set mids [hm_entitylist mats id all]
foreach mid $mids {
  set nm [hm_getvalue mats id=$mid dataname=name]
  set ci [hm_getvalue mats id=$mid dataname=cardimage]
  set fs {}
  foreach f {E G NU RHO} {
    if {![catch {set v [hm_getvalue mats id=$mid dataname=$f]}]} { lappend fs "$f=$v" }
  }
  append out "MAT id=$mid name=$nm cardimage=$ci [join $fs " "]\n"
}
*createmark designvars 1 all
set dvids [hm_entitylist designvars id all]
foreach dv $dvids {
  set dvn [hm_getvalue designvars id=$dv dataname=name]
  catch {set dvt [hm_getvalue designvars id=$dv dataname=type]}
  append out "DV id=$dv name=$dvn type=$dvt\n"
}
append out "NODEIDS=[lrange [hm_entitylist nodes id all] 0 300]\n"
append out "ELEMIDS=[lrange [hm_entitylist elems id all] 0 300]\n"
append out "LINEIDS=[hm_entitylist lines id all]\n"
set out
"""


def parse_snapshot(text: str) -> Dict[str, Any]:
    """Parse raw snapshot text from Tcl into structured dictionary."""
    data: Dict[str, Any] = {
        "counts": {},
        "comps": [],
        "mats": [],
        "designvars": [],
        "loads": [],
        "node_ids": [],
        "elem_ids": [],
        "line_ids": []
    }
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("COUNTS"):
            for kv in line[6:].split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    data["counts"][k.lower()] = int(v) if v.isdigit() else v
        elif line.startswith("COMP"):
            c: Dict[str, Any] = {}
            for kv in line[4:].split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    c[k] = int(v) if v.isdigit() else v
            data["comps"].append(c)
        elif line.startswith("DV"):
            m: Dict[str, Any] = {}
            for kv in line[2:].split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    m[k] = v
            data["designvars"].append(m)
        elif line.startswith("MAT"):
            m = {}
            for kv in line[3:].split():
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    m[k] = v
            data["mats"].append(m)
        elif line.startswith("LOADS="):
            data["loads"] = [int(x) for x in line[6:].split() if x.isdigit()]
        elif line.startswith("NODEIDS="):
            data["node_ids"] = [int(x) for x in line[8:].split() if x.isdigit()]
        elif line.startswith("ELEMIDS="):
            data["elem_ids"] = [int(x) for x in line[8:].split() if x.isdigit()]
        elif line.startswith("LINEIDS="):
            data["line_ids"] = [int(x) for x in line[8:].split() if x.isdigit()]
    return data


def take_snapshot(tag: Optional[str] = None, host: str = HM_HOST, port: int = HM_PORT, timeout: float = 120.0) -> Tuple[bool, str, Dict[str, Any]]:
    """Capture full model state snapshot and persist as JSON."""
    ok, r = run_tcl(SNAPSHOT_SCRIPT, host=host, port=port, timeout=timeout)
    if not ok:
        return False, f"Snapshot capture failed: {r}", {}
    data = parse_snapshot(r)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{tag}.json" if tag else f"{ts}.json"
    file_path = STATE_DIR / fname
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True, str(file_path), data


def load_snapshot(path_or_tag: str) -> Dict[str, Any]:
    """Load snapshot JSON file by absolute path, filename or tag match."""
    p = Path(path_or_tag)
    if p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    # Search in STATE_DIR
    target = STATE_DIR / (path_or_tag if path_or_tag.endswith(".json") else f"{path_or_tag}.json")
    if target.is_file():
        with open(target, "r", encoding="utf-8") as f:
            return json.load(f)

    # Fuzzy match tag in STATE_DIR
    files = sorted([f for f in STATE_DIR.glob("*.json") if path_or_tag in f.name])
    if files:
        with open(files[-1], "r", encoding="utf-8") as f:
            return json.load(f)

    raise FileNotFoundError(f"No snapshot found matching: {path_or_tag}")


def list_snapshots() -> List[Path]:
    """List all saved snapshot files sorted chronologically."""
    if not STATE_DIR.is_dir():
        return []
    return sorted(list(STATE_DIR.glob("*.json")))


def last_snapshots(n: int = 2) -> List[Path]:
    """Retrieve the most recent n snapshot files."""
    snaps = list_snapshots()
    return snaps[-n:] if len(snaps) >= n else snaps


WORKSPACE_SCRIPT = """
set wdir [file normalize [pwd]]
set cmd_file [file join $wdir "command1.tcl"]
set has_cmd [file exists $cmd_file]
set hms [glob -nocomplain -directory $wdir *.hm]
set fems [glob -nocomplain -directory $wdir *.fem]
list "DIR=$wdir" "CMD_FILE=$cmd_file" "HAS_CMD=$has_cmd" "HM_FILES=[join $hms {,}]" "FEM_FILES=[join $fems {,}]"
"""


def get_workspace_info(host: str = HM_HOST, port: int = HM_PORT, timeout: float = 30.0) -> Dict[str, Any]:
    """Query active HyperMesh instance working directory and model file paths."""
    ok, res = run_tcl(WORKSPACE_SCRIPT, host=host, port=port, timeout=timeout)
    if not ok:
        return {"error": res, "working_dir": None, "command_file": None}

    info: Dict[str, Any] = {
        "working_dir": None,
        "command_file": None,
        "has_command_file": False,
        "hm_files": [],
        "fem_files": []
    }
    for item in res.splitlines() if "\n" in res else [res]:
        for token in item.split():
            if token.startswith("DIR="):
                info["working_dir"] = token[4:]
            elif token.startswith("CMD_FILE="):
                info["command_file"] = token[9:]
            elif token.startswith("HAS_CMD="):
                info["has_command_file"] = token[8:] in ["1", "true", "True"]
            elif token.startswith("HM_FILES="):
                val = token[9:].strip()
                info["hm_files"] = [f for f in val.split(",") if f]
            elif token.startswith("FEM_FILES="):
                val = token[10:].strip()
                info["fem_files"] = [f for f in val.split(",") if f]
    return info


def read_command_log(tail_lines: int = 30, host: str = HM_HOST, port: int = HM_PORT, timeout: float = 30.0) -> str:
    """Read recent user actions recorded in the active HyperMesh instance's command1.tcl file."""
    ws = get_workspace_info(host=host, port=port, timeout=timeout)
    if "error" in ws and ws["error"]:
        return f"Error connecting to HyperMesh: {ws['error']}"

    cmd_path_str = ws.get("command_file")
    if not cmd_path_str:
        return "Cannot determine HyperMesh command1.tcl file path."

    p = Path(cmd_path_str)
    if not p.is_file():
        return f"HyperMesh working directory is '{ws.get('working_dir')}', but '{p.name}' does not exist yet."

    try:
        # Try UTF-8 then GBK encoding
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            with open(p, "r", encoding="gbk", errors="replace") as f:
                lines = f.readlines()

        if not lines:
            return f"The command log file ({p}) is currently empty."

        tail = lines[-tail_lines:] if len(lines) > tail_lines else lines
        header = f"Recent HyperMesh GUI Command Log ({p}) - Showing last {len(tail)} lines:\n"
        return header + "".join(tail).strip()
    except Exception as e:
        return f"Failed to read command log from {p}: {e}"




def diff_snapshots(snap_a: Dict[str, Any], snap_b: Dict[str, Any]) -> str:
    """Compare two snapshots and return human/AI readable diff summary."""
    lines: List[str] = []

    # Entity count differences
    counts_a = snap_a.get("counts", {})
    counts_b = snap_b.get("counts", {})
    keys = sorted(set(counts_a.keys()) | set(counts_b.keys()))
    count_diffs = []
    for k in keys:
        va = counts_a.get(k, 0)
        vb = counts_b.get(k, 0)
        if va != vb:
            delta = vb - va
            sign = f"+{delta}" if delta > 0 else str(delta)
            count_diffs.append(f"{k.upper()}: {va} -> {vb} ({sign})")
    if count_diffs:
        lines.append("Entity Count Changes:\n  " + ", ".join(count_diffs))
    else:
        lines.append("Entity Counts: Unchanged")

    # Component changes
    comps_a = {c.get("id"): c for c in snap_a.get("comps", [])}
    comps_b = {c.get("id"): c for c in snap_b.get("comps", [])}
    added_c = set(comps_b.keys()) - set(comps_a.keys())
    removed_c = set(comps_a.keys()) - set(comps_b.keys())
    if added_c:
        lines.append(f"Added Components: {[comps_b[i].get('name', i) for i in added_c]}")
    if removed_c:
        lines.append(f"Removed Components: {[comps_a[i].get('name', i) for i in removed_c]}")

    # Material changes
    mats_a = {m.get("id"): m for m in snap_a.get("mats", [])}
    mats_b = {m.get("id"): m for m in snap_b.get("mats", [])}
    added_m = set(mats_b.keys()) - set(mats_a.keys())
    removed_m = set(mats_a.keys()) - set(mats_b.keys())
    if added_m:
        lines.append(f"Added Materials: {[mats_b[i].get('name', i) for i in added_m]}")
    if removed_m:
        lines.append(f"Removed Materials: {[mats_a[i].get('name', i) for i in removed_m]}")
    for mid in set(mats_a.keys()) & set(mats_b.keys()):
        ma, mb = mats_a[mid], mats_b[mid]
        diff_props = []
        for prop in ["E", "G", "NU", "RHO", "cardimage", "name"]:
            if ma.get(prop) != mb.get(prop) and (prop in ma or prop in mb):
                diff_props.append(f"{prop}: {ma.get(prop)} -> {mb.get(prop)}")
        if diff_props:
            lines.append(f"Modified Material ID {mid} ({mb.get('name', '')}): {', '.join(diff_props)}")

    # Design variables
    dvs_a = {d.get("name"): d for d in snap_a.get("designvars", [])}
    dvs_b = {d.get("name"): d for d in snap_b.get("designvars", [])}
    added_dv = set(dvs_b.keys()) - set(dvs_a.keys())
    removed_dv = set(dvs_a.keys()) - set(dvs_b.keys())
    if added_dv:
        lines.append(f"Added Design Variables: {list(added_dv)}")
    if removed_dv:
        lines.append(f"Removed Design Variables: {list(removed_dv)}")

    return "\n".join(lines) if lines else "No detectable differences between snapshots."
