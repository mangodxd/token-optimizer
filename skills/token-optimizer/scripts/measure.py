#!/usr/bin/env python3
"""
Token Overhead Measurement Script
Captures real token counts from Claude Code session logs + file-level estimates.
Used by Token Optimizer skill in Phase 0 (before) and Phase 5 (after).

Usage:
    python3 measure.py snapshot before    # Save pre-optimization snapshot
    python3 measure.py snapshot after     # Save post-optimization snapshot
    python3 measure.py compare            # Compare before vs after
    python3 measure.py report             # Full standalone report

Snapshots are saved to SNAPSHOT_DIR (default: ~/.claude/_backups/token-optimizer/)

Copyright (C) 2026 Alex Greenshpun
SPDX-License-Identifier: AGPL-3.0-only
"""

import json
import os
import glob
import re
import sys
import platform
from datetime import datetime
from pathlib import Path

CHARS_PER_TOKEN = 4.0

HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SNAPSHOT_DIR = CLAUDE_DIR / "_backups" / "token-optimizer"

# Tokens per skill frontmatter (loaded at startup)
TOKENS_PER_SKILL_APPROX = 100
# Tokens per command frontmatter (loaded at startup)
TOKENS_PER_COMMAND_APPROX = 50
# Tokens per MCP deferred tool name in Tool Search menu
TOKENS_PER_DEFERRED_TOOL = 15
# Average tools per MCP server (rough estimate when tool count unknown)
AVG_TOOLS_PER_SERVER = 8


def estimate_tokens_from_file(filepath):
    """Estimate tokens by reading file content (character count / 4)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return int(len(content) / CHARS_PER_TOKEN)
    except (FileNotFoundError, PermissionError, OSError):
        return 0


def estimate_tokens_from_frontmatter(filepath):
    """Estimate tokens from YAML frontmatter only (between --- delimiters)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Extract frontmatter between first pair of ---
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                frontmatter = content[3:end]
                return max(int(len(frontmatter) / CHARS_PER_TOKEN), 20)
        # No frontmatter found, use rough estimate
        return TOKENS_PER_SKILL_APPROX
    except (FileNotFoundError, PermissionError, OSError):
        return TOKENS_PER_SKILL_APPROX


def count_lines(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except (FileNotFoundError, PermissionError, OSError):
        return 0


def resolve_real_path(filepath):
    """Resolve symlinks to avoid double-counting."""
    try:
        return filepath.resolve()
    except OSError:
        return filepath


def cwd_to_project_dir_name():
    """Convert cwd to Claude Code project directory name format.

    Claude Code encodes project paths by replacing / with - and dropping leading -.
    e.g., /Users/alex/myproject -> -Users-alex-myproject
    """
    cwd = str(Path.cwd())
    return "-" + cwd.replace("/", "-").lstrip("-")


def find_projects_dir():
    """Find the Claude Code projects directory matching the current working directory."""
    projects_base = CLAUDE_DIR / "projects"
    if not projects_base.exists():
        return None

    # Try to match current working directory first
    expected_name = cwd_to_project_dir_name()
    expected_dir = projects_base / expected_name
    if expected_dir.exists():
        return expected_dir

    # Fallback: try parent directories (user may be in a subdirectory)
    cwd = Path.cwd()
    for parent in list(cwd.parents)[:5]:
        parent_name = "-" + str(parent).replace("/", "-").lstrip("-")
        parent_dir = projects_base / parent_name
        if parent_dir.exists():
            return parent_dir

    # Last resort: most recently modified (with warning)
    dirs = [d for d in projects_base.iterdir() if d.is_dir()]
    if not dirs:
        return None
    result = max(dirs, key=lambda d: d.stat().st_mtime)
    print(f"  [Warning] Could not match cwd to project dir. Using most recent: {result.name}")
    return result


def get_session_baselines(limit=10):
    """Extract first-message token counts from recent JSONL session logs."""
    projects_dir = find_projects_dir()
    if not projects_dir:
        return []

    jsonl_files = sorted(
        glob.glob(str(projects_dir / "*.jsonl")),
        key=os.path.getmtime,
        reverse=True,
    )

    baselines = []
    for jf in jsonl_files[:limit]:
        try:
            mtime = os.path.getmtime(jf)
            first_usage = None
            with open(jf, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if "message" in data and isinstance(data["message"], dict):
                            msg = data["message"]
                            if "usage" in msg:
                                u = msg["usage"]
                                first_usage = (
                                    u.get("input_tokens", 0)
                                    + u.get("cache_creation_input_tokens", 0)
                                    + u.get("cache_read_input_tokens", 0)
                                )
                                break
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue

            if first_usage:
                baselines.append({
                    "date": datetime.fromtimestamp(mtime).isoformat(),
                    "baseline_tokens": first_usage,
                })
        except (PermissionError, OSError):
            continue

    return baselines


def get_mcp_config_paths():
    """Return MCP config paths for the current platform."""
    paths = [
        CLAUDE_DIR / "settings.json",  # Claude Code primary config
    ]

    system = platform.system()
    if system == "Darwin":
        paths.append(HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json")
    elif system == "Linux":
        paths.append(HOME / ".config" / "Claude" / "claude_desktop_config.json")

    return paths


def count_mcp_tools_and_servers():
    """Count MCP servers and estimate deferred tool overhead."""
    server_count = 0
    tool_count_estimate = 0
    seen_names = set()
    server_names = []

    for config_path in get_mcp_config_paths():
        if not config_path.exists():
            continue
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            servers = config.get("mcpServers", config.get("mcp_servers", {}))
            for name in servers:
                if name not in seen_names:
                    seen_names.add(name)
                    server_names.append(name)
                    server_count += 1
        except (json.JSONDecodeError, PermissionError, OSError):
            continue

    # Estimate tool count: avg tools per server
    tool_count_estimate = server_count * AVG_TOOLS_PER_SERVER
    # Deferred tool tokens: ~15 tokens per tool name in Tool Search menu
    tokens = tool_count_estimate * TOKENS_PER_DEFERRED_TOOL

    return {
        "server_count": server_count,
        "server_names": server_names,
        "tool_count_estimate": tool_count_estimate,
        "tokens": tokens,
        "note": f"Estimated ~{AVG_TOOLS_PER_SERVER} tools/server x ~{TOKENS_PER_DEFERRED_TOOL} tokens/tool (Tool Search deferred)",
    }


def _has_paths_frontmatter(filepath):
    """Check if a rules file has paths: frontmatter (path-scoped rule)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(2048)  # Only need to check frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                frontmatter = content[3:end]
                return "paths:" in frontmatter
        return False
    except (FileNotFoundError, PermissionError, OSError):
        return False


def _detect_imports(claude_md_path):
    """Detect @import patterns in a CLAUDE.md file and estimate token cost."""
    imports = []
    try:
        with open(claude_md_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # Match lines starting with @ followed by a path-like string
        pattern = re.compile(r'^@(\S+\.(?:md|txt|yaml|yml|json))\s*$', re.MULTILINE)
        project_root = claude_md_path.parent.resolve()
        for match in pattern.finditer(content):
            import_path = match.group(1)
            resolved = (project_root / import_path).resolve()
            # Security: ensure resolved path stays under project root
            try:
                resolved.relative_to(project_root)
            except ValueError:
                continue  # Skip path traversal attempts
            tokens = estimate_tokens_from_file(resolved) if resolved.exists() else 0
            imports.append({
                "pattern": f"@{import_path}",
                "resolved_path": str(resolved),
                "exists": resolved.exists(),
                "tokens": tokens,
            })
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return imports


TOKEN_RELEVANT_ENV_VARS = [
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE",
    "CLAUDE_CODE_MAX_THINKING_TOKENS",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
    "MAX_MCP_OUTPUT_TOKENS",
    "ENABLE_TOOL_SEARCH",
    "CLAUDE_CODE_DISABLE_AUTO_MEMORY",
    "CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING",
    "BASH_MAX_OUTPUT_LENGTH",
]


def _check_settings_env(settings_path):
    """Check settings.json for token-relevant environment variables."""
    result = {"found": {}, "settings_exists": settings_path.exists()}
    if not settings_path.exists():
        return result
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        env = settings.get("env", {})
        for var in TOKEN_RELEVANT_ENV_VARS:
            if var in env:
                result["found"][var] = env[var]
    except (json.JSONDecodeError, PermissionError, OSError):
        pass
    return result


def _get_frontmatter_description_length(filepath):
    """Get the character length of the description field in YAML frontmatter."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(4096)
        if not content.startswith("---"):
            return 0
        end = content.find("---", 3)
        if end <= 0:
            return 0
        frontmatter = content[3:end]
        lines = frontmatter.split("\n")
        desc_text = ""
        in_desc = False
        for line in lines:
            if line.startswith("description:"):
                value = line[len("description:"):].strip()
                if value in ("|", ">", "|+", "|-", ">+", ">-"):
                    # Multi-line block scalar
                    in_desc = True
                    continue
                # Single-line value (possibly quoted)
                if value.startswith('"') and value.endswith('"'):
                    desc_text = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    desc_text = value[1:-1]
                else:
                    desc_text = value
                break
            elif in_desc:
                if line and (line[0] == " " or line[0] == "\t"):
                    desc_text += line.strip() + " "
                else:
                    break
        return len(desc_text.strip())
    except (FileNotFoundError, PermissionError, OSError):
        return 0


def measure_components():
    """Measure all controllable token overhead components."""
    components = {}
    seen_real_paths = set()

    # CLAUDE.md files (with symlink dedup)
    for name, path in [
        ("claude_md_global", CLAUDE_DIR / "CLAUDE.md"),
        ("claude_md_home", HOME / "CLAUDE.md"),
    ]:
        real = resolve_real_path(path)
        if real in seen_real_paths:
            components[name] = {"path": str(path), "exists": False, "tokens": 0, "lines": 0, "note": "duplicate (symlink)"}
            continue
        if path.exists():
            seen_real_paths.add(real)
        components[name] = {
            "path": str(path),
            "exists": path.exists(),
            "tokens": estimate_tokens_from_file(path),
            "lines": count_lines(path),
        }

    # Find project CLAUDE.md files in cwd and parents
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents)[:3]:
        if parent == HOME:
            continue  # Already checked ~/CLAUDE.md
        claude_md = parent / "CLAUDE.md"
        if claude_md.exists():
            real = resolve_real_path(claude_md)
            if real not in seen_real_paths:
                seen_real_paths.add(real)
                components[f"claude_md_project_{parent.name}"] = {
                    "path": str(claude_md),
                    "exists": True,
                    "tokens": estimate_tokens_from_file(claude_md),
                    "lines": count_lines(claude_md),
                }

    # MEMORY.md
    projects_dir = find_projects_dir()
    if projects_dir:
        memory_path = projects_dir / "memory" / "MEMORY.md"
        components["memory_md"] = {
            "path": str(memory_path),
            "exists": memory_path.exists(),
            "tokens": estimate_tokens_from_file(memory_path) if memory_path.exists() else 0,
            "lines": count_lines(memory_path) if memory_path.exists() else 0,
        }

    # Skills (read actual frontmatter size + check description quality in single pass)
    skills_dir = CLAUDE_DIR / "skills"
    skill_count = 0
    skill_tokens = 0
    skill_names = []
    verbose_skills = []
    if skills_dir.exists():
        for item in sorted(skills_dir.iterdir()):
            skill_md = item / "SKILL.md"
            if item.is_dir() and skill_md.exists():
                skill_count += 1
                skill_names.append(item.name)
                skill_tokens += estimate_tokens_from_frontmatter(skill_md)
                desc_len = _get_frontmatter_description_length(skill_md)
                if desc_len > 200:
                    verbose_skills.append({
                        "name": item.name,
                        "description_chars": desc_len,
                    })
    components["skills"] = {
        "count": skill_count,
        "tokens": skill_tokens,
        "names": skill_names,
    }

    # Commands (read actual file sizes for frontmatter estimate)
    commands_dir = CLAUDE_DIR / "commands"
    cmd_count = 0
    cmd_tokens = 0
    cmd_names = []
    if commands_dir.exists():
        for f in sorted(commands_dir.glob("*.md")):
            cmd_count += 1
            cmd_names.append(f.stem)
            cmd_tokens += estimate_tokens_from_frontmatter(f)
        for subdir in sorted(commands_dir.iterdir()):
            if subdir.is_dir():
                for f in sorted(subdir.glob("*.md")):
                    cmd_count += 1
                    cmd_names.append(f"{subdir.name}/{f.stem}")
                    cmd_tokens += estimate_tokens_from_frontmatter(f)
    components["commands"] = {
        "count": cmd_count,
        "tokens": cmd_tokens,
        "names": cmd_names,
    }

    # MCP servers and deferred tools
    mcp = count_mcp_tools_and_servers()
    components["mcp_tools"] = {
        "server_count": mcp["server_count"],
        "server_names": mcp["server_names"],
        "tool_count_estimate": mcp["tool_count_estimate"],
        "tokens": mcp["tokens"],
        "note": mcp["note"],
    }

    # .claudeignore (check both global and project-level)
    global_ignore = CLAUDE_DIR / ".claudeignore"
    project_ignore = cwd / ".claudeignore"
    components["claudeignore"] = {
        "global_exists": global_ignore.exists(),
        "project_exists": project_ignore.exists(),
        "exists": global_ignore.exists() or project_ignore.exists(),
    }

    # Read settings.json once (used for hooks, env vars, MCP)
    settings_path = CLAUDE_DIR / "settings.json"
    _cached_settings = None
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                _cached_settings = json.load(f)
        except (json.JSONDecodeError, PermissionError, OSError):
            pass

    # Hooks
    hooks_configured = False
    hook_names = []
    if _cached_settings:
        hooks = _cached_settings.get("hooks", {})
        if hooks:
            hooks_configured = True
            hook_names = list(hooks.keys())
    components["hooks"] = {
        "configured": hooks_configured,
        "names": hook_names,
    }

    # .claude/rules/ directory
    rules_dir = CLAUDE_DIR / "rules"
    rules_count = 0
    rules_tokens = 0
    rules_files = []
    rules_always_loaded = 0
    if rules_dir.exists() and rules_dir.is_dir():
        for f in sorted(rules_dir.iterdir()):
            if f.is_file() and f.suffix == ".md":
                rules_count += 1
                tokens = estimate_tokens_from_file(f)
                rules_tokens += tokens
                has_paths = _has_paths_frontmatter(f)
                rules_files.append({
                    "name": f.name,
                    "tokens": tokens,
                    "path_scoped": has_paths,
                })
                if not has_paths:
                    rules_always_loaded += 1
    components["rules"] = {
        "count": rules_count,
        "tokens": rules_tokens,
        "files": rules_files,
        "always_loaded": rules_always_loaded,
    }

    # @imports in CLAUDE.md
    imports_tokens = 0
    imports_found = []
    for key in components:
        if key.startswith("claude_md") and components[key].get("exists"):
            found = _detect_imports(Path(components[key]["path"]))
            for imp in found:
                imports_tokens += imp["tokens"]
            imports_found.extend(found)
    components["imports"] = {
        "count": len(imports_found),
        "tokens": imports_tokens,
        "files": imports_found,
    }

    # CLAUDE.local.md
    claude_local = cwd / "CLAUDE.local.md"
    components["claude_local_md"] = {
        "path": str(claude_local),
        "exists": claude_local.exists(),
        "tokens": estimate_tokens_from_file(claude_local) if claude_local.exists() else 0,
        "lines": count_lines(claude_local) if claude_local.exists() else 0,
    }

    # settings.json env vars (token-relevant) — use cached settings
    if _cached_settings:
        env = _cached_settings.get("env", {})
        found_vars = {var: env[var] for var in TOKEN_RELEVANT_ENV_VARS if var in env}
        components["settings_env"] = {"found": found_vars, "settings_exists": True}
    else:
        components["settings_env"] = {"found": {}, "settings_exists": settings_path.exists()}

    # settings.local.json existence
    settings_local = CLAUDE_DIR / "settings.local.json"
    project_settings_local = cwd / ".claude" / "settings.local.json"
    components["settings_local"] = {
        "global_exists": settings_local.exists(),
        "project_exists": project_settings_local.exists(),
        "exists": settings_local.exists() or project_settings_local.exists(),
    }

    # Skill frontmatter quality (collected during skills scan above)
    components["skill_frontmatter_quality"] = {
        "verbose_count": len(verbose_skills),
        "verbose_skills": verbose_skills,
    }

    # Fixed overhead
    components["core_system"] = {
        "tokens": 15000,
        "note": "System prompt (~3,000) + built-in tools (~12,000). Fixed. Source: Piebald-AI tracking, v2.1.59.",
    }

    return components


def calculate_totals(components):
    """Calculate total controllable and estimated overhead."""
    controllable = 0
    fixed = 0
    # Keys that don't contribute direct token overhead (metadata only)
    non_token_keys = {
        "claudeignore", "hooks", "settings_env", "settings_local",
        "skill_frontmatter_quality",
    }

    for name, info in components.items():
        if name in non_token_keys:
            continue
        tokens = info.get("tokens", 0)
        if name == "core_system":
            fixed += tokens
        else:
            controllable += tokens

    return {
        "controllable_tokens": controllable,
        "fixed_tokens": fixed,
        "estimated_total": controllable + fixed,
    }


def sanitize_label(label):
    """Sanitize snapshot label to prevent path traversal."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', label):
        print("[Error] Snapshot label must contain only letters, numbers, hyphens, underscores.")
        sys.exit(1)
    return label


def take_snapshot(label):
    """Save a measurement snapshot (before or after)."""
    label = sanitize_label(label)

    try:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(str(SNAPSHOT_DIR), 0o700)
    except OSError as e:
        print(f"[Error] Cannot create snapshot directory: {e}")
        sys.exit(1)

    components = measure_components()
    baselines = get_session_baselines(5)
    totals = calculate_totals(components)

    snapshot = {
        "label": label,
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "session_baselines": baselines,
        "totals": totals,
    }

    filepath = SNAPSHOT_DIR / f"snapshot_{label}.json"
    if filepath.exists():
        print(f"  [Note] Overwriting existing snapshot '{label}'")
    fd = os.open(str(filepath), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, default=str)

    print(f"\n[Token Optimizer] Snapshot '{label}' saved to {filepath}")
    print(f"  [Note] Snapshot contains system config details. Do not share publicly.")
    print_snapshot_summary(snapshot)
    return snapshot


def print_snapshot_summary(snapshot):
    """Print a human-readable summary of a snapshot."""
    c = snapshot["components"]
    t = snapshot["totals"]

    print(f"\n{'=' * 55}")
    print(f"  Snapshot: {snapshot['label']} ({snapshot['timestamp'][:16]})")
    print(f"{'=' * 55}")

    # CLAUDE.md files
    claude_total = 0
    for key in c:
        if key.startswith("claude_md"):
            tokens = c[key].get("tokens", 0)
            if tokens > 0:
                claude_total += tokens
                lines = c[key].get("lines", 0)
                print(f"  {key:<35s} {tokens:>6,} tokens  [{lines} lines]")
    if claude_total == 0:
        print(f"  {'CLAUDE.md':<35s}     0 tokens  [not found]")

    # MEMORY.md
    if "memory_md" in c:
        mem = c["memory_md"]
        print(f"  {'MEMORY.md':<35s} {mem.get('tokens', 0):>6,} tokens  [{mem.get('lines', 0)} lines]")

    # Skills
    s = c.get("skills", {})
    print(f"  {'Skills (frontmatter)':<35s} {s.get('tokens', 0):>6,} tokens  [{s.get('count', 0)} skills]")

    # Commands
    cmd = c.get("commands", {})
    print(f"  {'Commands (frontmatter)':<35s} {cmd.get('tokens', 0):>6,} tokens  [{cmd.get('count', 0)} commands]")

    # MCP
    mcp = c.get("mcp_tools", {})
    mcp_tokens = mcp.get("tokens", 0)
    srv_count = mcp.get("server_count", 0)
    tool_est = mcp.get("tool_count_estimate", 0)
    print(f"  {'MCP deferred tools (est.)':<35s} {mcp_tokens:>6,} tokens  [{srv_count} servers, ~{tool_est} tools]")

    # Rules
    rules = c.get("rules", {})
    if rules.get("count", 0) > 0:
        print(f"  {'Rules (.claude/rules/)':<35s} {rules.get('tokens', 0):>6,} tokens  [{rules.get('count', 0)} files, {rules.get('always_loaded', 0)} always-loaded]")

    # @imports
    imports = c.get("imports", {})
    if imports.get("count", 0) > 0:
        print(f"  {'@imports in CLAUDE.md':<35s} {imports.get('tokens', 0):>6,} tokens  [{imports.get('count', 0)} imports]")

    # CLAUDE.local.md
    cl = c.get("claude_local_md", {})
    if cl.get("exists"):
        print(f"  {'CLAUDE.local.md':<35s} {cl.get('tokens', 0):>6,} tokens  [{cl.get('lines', 0)} lines]")

    # Core
    core = c.get("core_system", {})
    print(f"  {'Core system (fixed)':<35s} {core.get('tokens', 0):>6,} tokens")

    print(f"  {'=' * 53}")
    print(f"  {'ESTIMATED TOTAL':<35s} {t['estimated_total']:>6,} tokens")
    pct_of_200k = t['estimated_total'] / 200_000 * 100
    print(f"  {'Context used before typing':<35s} {pct_of_200k:>5.1f}% of 200K window")

    # Session baselines
    baselines = snapshot.get("session_baselines", [])
    if baselines:
        avg = sum(b["baseline_tokens"] for b in baselines) / len(baselines)
        print(f"\n  Real session baseline (avg of {len(baselines)}): {avg:,.0f} tokens")
        print(f"  (includes system reminders, conversation history, etc.)")

    # Extras
    ignore = c.get("claudeignore", {})
    hooks = c.get("hooks", {})
    ignore_str = "Global" if ignore.get("global_exists") else ""
    if ignore.get("project_exists"):
        ignore_str += ("+Project" if ignore_str else "Project")
    print(f"\n  .claudeignore: {ignore_str if ignore_str else 'MISSING'}")
    print(f"  Hooks: {', '.join(hooks.get('names', [])) if hooks.get('configured') else 'NONE'}")

    # Settings env vars
    settings_env = c.get("settings_env", {})
    found_vars = settings_env.get("found", {})
    if found_vars:
        print(f"  Settings env vars: {', '.join(f'{k}={v}' for k, v in found_vars.items())}")

    # Settings local
    settings_local = c.get("settings_local", {})
    if settings_local.get("exists"):
        print(f"  settings.local.json: Found")

    # Verbose skill descriptions
    quality = c.get("skill_frontmatter_quality", {})
    verbose_count = quality.get("verbose_count", 0)
    if verbose_count > 0:
        names = [s["name"] for s in quality.get("verbose_skills", [])]
        print(f"  Verbose skill descriptions (>200 chars): {verbose_count} ({', '.join(names[:5])}{'...' if verbose_count > 5 else ''})")


def compare_snapshots():
    """Compare before and after snapshots."""
    before_path = SNAPSHOT_DIR / "snapshot_before.json"
    after_path = SNAPSHOT_DIR / "snapshot_after.json"

    if not before_path.exists():
        print("\n[Error] No 'before' snapshot found. Run: python3 measure.py snapshot before")
        return

    if not after_path.exists():
        print("\n[Error] No 'after' snapshot found. Run: python3 measure.py snapshot after")
        return

    with open(before_path, "r", encoding="utf-8") as f:
        before = json.load(f)
    with open(after_path, "r", encoding="utf-8") as f:
        after = json.load(f)

    bc = before["components"]
    ac = after["components"]

    print(f"\n{'=' * 65}")
    print(f"  TOKEN OPTIMIZER - BEFORE vs AFTER")
    print(f"  Before: {before['timestamp'][:16]}")
    print(f"  After:  {after['timestamp'][:16]}")
    print(f"{'=' * 65}")

    print(f"\n  {'Component':<25s} {'Before':>8s} {'After':>8s} {'Saved':>8s} {'%':>6s}")
    print(f"  {'-' * 57}")

    rows = []

    # CLAUDE.md total
    before_claude = sum(
        bc[k].get("tokens", 0) for k in bc if k.startswith("claude_md")
    )
    after_claude = sum(
        ac[k].get("tokens", 0) for k in ac if k.startswith("claude_md")
    )
    rows.append(("CLAUDE.md (all)", before_claude, after_claude))

    # MEMORY.md
    rows.append((
        "MEMORY.md",
        bc.get("memory_md", {}).get("tokens", 0),
        ac.get("memory_md", {}).get("tokens", 0),
    ))

    # Skills
    rows.append((
        "Skills",
        bc.get("skills", {}).get("tokens", 0),
        ac.get("skills", {}).get("tokens", 0),
    ))

    # Commands
    rows.append((
        "Commands",
        bc.get("commands", {}).get("tokens", 0),
        ac.get("commands", {}).get("tokens", 0),
    ))

    # MCP (now included!)
    rows.append((
        "MCP deferred tools",
        bc.get("mcp_tools", bc.get("mcp_servers", {})).get("tokens", 0),
        ac.get("mcp_tools", ac.get("mcp_servers", {})).get("tokens", 0),
    ))

    # Rules
    rows.append((
        "Rules (.claude/rules/)",
        bc.get("rules", {}).get("tokens", 0),
        ac.get("rules", {}).get("tokens", 0),
    ))

    # @imports
    rows.append((
        "@imports",
        bc.get("imports", {}).get("tokens", 0),
        ac.get("imports", {}).get("tokens", 0),
    ))

    # CLAUDE.local.md
    rows.append((
        "CLAUDE.local.md",
        bc.get("claude_local_md", {}).get("tokens", 0),
        ac.get("claude_local_md", {}).get("tokens", 0),
    ))

    total_before = 0
    total_after = 0
    total_saved = 0

    for name, bv, av in rows:
        saved = bv - av
        pct = f"{saved / bv * 100:.0f}%" if bv > 0 else "-"
        total_before += bv
        total_after += av
        total_saved += saved
        print(f"  {name:<25s} {bv:>7,} {av:>7,} {saved:>+7,} {pct:>6s}")

    print(f"  {'-' * 57}")
    total_pct = f"{total_saved / total_before * 100:.0f}%" if total_before > 0 else "-"
    print(f"  {'CONTROLLABLE TOTAL':<25s} {total_before:>7,} {total_after:>7,} {total_saved:>+7,} {total_pct:>6s}")

    # Context budget impact (not dollar amounts)
    if total_saved > 0:
        before_pct = (total_before + 15000) / 200_000 * 100
        after_pct = (total_after + 15000) / 200_000 * 100
        print(f"\n  Context budget: {before_pct:.1f}% -> {after_pct:.1f}% of 200K window")
        print(f"  That's {total_saved:,} more tokens for actual work per message.")

    # .claudeignore and hooks changes
    print(f"\n  .claudeignore: {'MISSING' if not bc.get('claudeignore', {}).get('exists') else 'Yes'} -> {'MISSING' if not ac.get('claudeignore', {}).get('exists') else 'Yes'}")
    bh = bc.get("hooks", {})
    ah = ac.get("hooks", {})
    print(f"  Hooks: {'None' if not bh.get('configured') else ', '.join(bh.get('names', []))} -> {'None' if not ah.get('configured') else ', '.join(ah.get('names', []))}")

    # Archived skills
    before_skills = set(bc.get("skills", {}).get("names", []))
    after_skills = set(ac.get("skills", {}).get("names", []))
    archived = before_skills - after_skills
    if archived:
        print(f"\n  Skills archived: {', '.join(sorted(archived))}")

    # Archived commands
    before_cmds = set(bc.get("commands", {}).get("names", []))
    after_cmds = set(ac.get("commands", {}).get("names", []))
    archived_cmds = before_cmds - after_cmds
    if archived_cmds:
        print(f"  Commands archived: {', '.join(sorted(archived_cmds))}")

    # Session baseline comparison (with honest caveat)
    bb = before.get("session_baselines", [])
    ab = after.get("session_baselines", [])
    if bb and ab:
        avg_before = sum(b["baseline_tokens"] for b in bb) / len(bb)
        avg_after = sum(b["baseline_tokens"] for b in ab) / len(ab)
        if abs(avg_before - avg_after) < 100:
            print(f"\n  Session baselines: {avg_before:,.0f} -> {avg_after:,.0f} tokens")
            print(f"  [Note] These are from the same recent sessions. Start new sessions")
            print(f"         after optimizing to see real baseline changes.")
        else:
            print(f"\n  Real session baseline: {avg_before:,.0f} -> {avg_after:,.0f} tokens")

    print(f"\n{'=' * 65}")


def full_report():
    """Print a standalone full report."""
    components = measure_components()
    baselines = get_session_baselines(10)
    totals = calculate_totals(components)

    snapshot = {
        "label": "current",
        "timestamp": datetime.now().isoformat(),
        "components": components,
        "session_baselines": baselines,
        "totals": totals,
    }

    print(f"\n{'=' * 55}")
    print(f"  TOKEN OVERHEAD REPORT")
    print(f"{'=' * 55}")

    print_snapshot_summary(snapshot)

    if baselines:
        print(f"\n  --- Recent Session Baselines (from JSONL logs) ---")
        for b in baselines:
            dt = b["date"][:16]
            print(f"    {dt}  {b['baseline_tokens']:>7,} tokens")

    print(f"\n{'=' * 55}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] == "report":
        full_report()
    elif args[0] == "snapshot" and len(args) > 1:
        take_snapshot(args[1])
    elif args[0] == "compare":
        compare_snapshots()
    else:
        print("Usage:")
        print("  python3 measure.py report              # Full report")
        print("  python3 measure.py snapshot before      # Save pre-optimization snapshot")
        print("  python3 measure.py snapshot after       # Save post-optimization snapshot")
        print("  python3 measure.py compare              # Compare before vs after")
