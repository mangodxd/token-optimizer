"""Shared fixtures for Token Optimizer test suite."""

import json
import os
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent / "skills" / "token-optimizer"
REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture
def skill_root():
    """Path to the token-optimizer skill directory."""
    return SKILL_ROOT


@pytest.fixture
def repo_root():
    """Path to the repository root."""
    return REPO_ROOT


@pytest.fixture
def tmp_claude_dir(tmp_path):
    """Create a temporary .claude directory structure for testing measure.py."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()

    # Global CLAUDE.md
    claude_md = claude_dir / "CLAUDE.md"
    claude_md.write_text("## Identity\n- Project: Test\n- Stack: Python\n\n## Key Paths\n- App: src/\n")

    # settings.json with MCP servers
    settings = {
        "mcpServers": {
            "test-server-1": {"command": "npx", "args": ["test-mcp"]},
            "test-server-2": {"command": "python3", "args": ["-m", "test_mcp"]},
        },
        "hooks": {
            "PreCompact": [{"type": "command", "command": "echo test"}],
        },
        "env": {
            "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70",
        },
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))

    # Skills directory
    skills_dir = claude_dir / "skills"
    skills_dir.mkdir()
    for name in ["morning", "evening", "test-skill"]:
        skill_dir = skills_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: A test skill for {name}\n---\n\n# {name}\nBody content.\n"
        )

    # Commands directory
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir()
    for name in ["sync", "update", "deploy"]:
        (commands_dir / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: Run {name}\n---\n\nCommand body.\n"
        )

    # .claudeignore
    (claude_dir / ".claudeignore").write_text("node_modules/\n*.log\n")

    # Rules directory
    rules_dir = claude_dir / "rules"
    rules_dir.mkdir()
    (rules_dir / "general.md").write_text("# General Rules\nAlways test before committing.\n")
    (rules_dir / "backend.md").write_text(
        "---\npaths:\n  - src/backend/**\n---\n# Backend Rules\nUse type hints.\n"
    )

    # Projects directory with MEMORY.md
    projects_dir = claude_dir / "projects" / "-tmp-test"
    memory_dir = projects_dir / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("# Memory\n\n## Test Memory Entry\nSome remembered fact.\n")

    return claude_dir


@pytest.fixture
def tmp_project_dir(tmp_path, tmp_claude_dir):
    """Create a temporary project directory with CLAUDE.md and CLAUDE.local.md."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("## Project\n- Stack: Rails\n")
    (project / "CLAUDE.local.md").write_text("## Local Overrides\n- Debug: true\n")
    return project
