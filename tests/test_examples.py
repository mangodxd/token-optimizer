"""Tests for example files: validity and constraints."""

import json
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent / "skills" / "token-optimizer"
EXAMPLES_DIR = SKILL_ROOT / "examples"


class TestClaudeIgnoreTemplate:
    """claudeignore-template should be valid gitignore syntax."""

    def test_file_exists(self):
        assert (EXAMPLES_DIR / "claudeignore-template").exists()

    def test_valid_gitignore_syntax(self):
        """Each non-comment, non-blank line should be a valid glob pattern."""
        content = (EXAMPLES_DIR / "claudeignore-template").read_text()
        for i, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Basic validation: gitignore patterns should not contain certain characters
            # They can contain *, ?, /, !, [, ], but not tabs or control chars
            assert "\t" not in stripped, f"Line {i}: Tab in pattern: {stripped}"
            # Patterns should not be excessively long
            assert len(stripped) < 200, f"Line {i}: Pattern too long: {stripped}"

    def test_has_security_patterns(self):
        """Should block common sensitive files."""
        content = (EXAMPLES_DIR / "claudeignore-template").read_text()
        assert ".env" in content, "Should block .env files"
        assert "credentials" in content.lower(), "Should block credentials"
        assert "node_modules" in content, "Should block node_modules"

    def test_has_comments(self):
        """Template should be well-commented for users."""
        content = (EXAMPLES_DIR / "claudeignore-template").read_text()
        comment_lines = [l for l in content.split("\n") if l.strip().startswith("#")]
        assert len(comment_lines) >= 5, "Template should have helpful comments"


class TestHooksStarterJson:
    """hooks-starter.json should be valid JSON with correct structure."""

    def test_file_exists(self):
        assert (EXAMPLES_DIR / "hooks-starter.json").exists()

    def test_valid_json(self):
        content = (EXAMPLES_DIR / "hooks-starter.json").read_text()
        data = json.loads(content)  # Raises JSONDecodeError if invalid
        assert isinstance(data, dict)

    def test_has_hooks_key(self):
        content = (EXAMPLES_DIR / "hooks-starter.json").read_text()
        data = json.loads(content)
        assert "hooks" in data, "Should have 'hooks' key"

    def test_hooks_have_valid_events(self):
        content = (EXAMPLES_DIR / "hooks-starter.json").read_text()
        data = json.loads(content)
        valid_events = {
            "PreCompact", "PostToolUse", "SessionStart", "SessionEnd",
            "Stop", "UserPromptSubmit",
        }
        for event in data["hooks"]:
            assert event in valid_events, f"Unknown hook event: {event}"

    def test_hooks_have_command_type(self):
        content = (EXAMPLES_DIR / "hooks-starter.json").read_text()
        data = json.loads(content)
        for event, hooks in data["hooks"].items():
            assert isinstance(hooks, list), f"{event}: hooks should be a list"
            for hook in hooks:
                assert "type" in hook, f"{event}: hook missing 'type'"
                assert "command" in hook, f"{event}: hook missing 'command'"


class TestClaudeMdOptimized:
    """claude-md-optimized.md should be under 800 tokens."""

    CHARS_PER_TOKEN = 4.0

    def test_file_exists(self):
        assert (EXAMPLES_DIR / "claude-md-optimized.md").exists()

    def test_under_800_tokens(self):
        """The optimized CLAUDE.md example should demonstrate the <800 token target."""
        content = (EXAMPLES_DIR / "claude-md-optimized.md").read_text()
        # Exclude comment lines (starting with #) from token count
        # as they're instructional, not part of the actual template
        non_comment_lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped.startswith("#") or stripped.startswith("##"):
                non_comment_lines.append(line)
        effective_content = "\n".join(non_comment_lines)
        estimated_tokens = int(len(effective_content) / self.CHARS_PER_TOKEN)
        assert estimated_tokens < 800, (
            f"Optimized CLAUDE.md example is ~{estimated_tokens} tokens, should be <800"
        )

    def test_has_static_section(self):
        content = (EXAMPLES_DIR / "claude-md-optimized.md").read_text()
        assert "static" in content.lower() or "STATIC" in content

    def test_has_volatile_section(self):
        content = (EXAMPLES_DIR / "claude-md-optimized.md").read_text()
        assert "volatile" in content.lower() or "VOLATILE" in content

    def test_static_before_volatile(self):
        """Static content should come before volatile content (for caching)."""
        content = (EXAMPLES_DIR / "claude-md-optimized.md").read_text()
        static_pos = content.lower().find("static")
        volatile_pos = content.lower().find("volatile")
        if static_pos >= 0 and volatile_pos >= 0:
            assert static_pos < volatile_pos, "Static section should come before volatile"
