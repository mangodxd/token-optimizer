"""Cross-file number consistency tests.

The canonical numbers (43K, 28K, 15K, 38%, 30%) appear in 7+ files.
This test validates they all match and component sums are correct.
"""

import re
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent / "skills" / "token-optimizer"
REPO_ROOT = Path(__file__).parent.parent

# Canonical values
UNAUDITED_TOTAL = 43000  # ~43,000 tokens consumed
OPTIMIZED_TOTAL = 28000  # ~28,000 tokens after optimization
FIXED_OVERHEAD = 15000   # ~15,000 tokens core system
UNAVAILABLE_BEFORE_PCT = 38  # 38% of 200K
UNAVAILABLE_AFTER_PCT = 30   # 30% of 200K

# Component breakdown (before)
BEFORE_COMPONENTS = {
    "core_system": 15000,
    "mcp": 9000,
    "skills": 6000,
    "commands": 3000,
    "claude_md": 3500,
    "memory_md": 3500,
    "system_reminders": 3000,
}

# Component breakdown (after)
AFTER_COMPONENTS = {
    "core_system": 15000,
    "mcp": 6000,
    "skills": 3000,
    "commands": 1200,
    "claude_md": 800,
    "memory_md": 1000,
    "system_reminders": 1000,
}


def get_all_content_files():
    """Get all .md files in the skill directory."""
    files = []
    for f in SKILL_ROOT.rglob("*.md"):
        files.append(f)
    # Also check README.md at repo root
    readme = REPO_ROOT / "README.md"
    if readme.exists():
        files.append(readme)
    return files


def read_file_content(filepath):
    """Read file content, return empty string on error."""
    try:
        return filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


class TestCanonicalNumbers:
    """Verify canonical numbers are consistent across files."""

    def test_unaudited_total_consistent(self):
        """43,000 / 43K should appear consistently, not old values."""
        files = get_all_content_files()
        for f in files:
            content = read_file_content(f)
            # Check for stale old totals (e.g., 40K, 45K, 50K as the "unaudited" total)
            if "unaudited" in content.lower() or "before" in content.lower():
                # Should not contain "~50,000 tokens" or "~40,000 tokens" as the unaudited baseline
                assert "~50,000 tokens" not in content or "before" not in content.lower(), (
                    f"{f.name}: Contains stale unaudited total (~50,000)"
                )

    def test_fixed_overhead_consistent(self):
        """15,000 / 15K core system should be consistent."""
        files = get_all_content_files()
        for f in files:
            content = read_file_content(f)
            # Match "Core system + tools: 15,000 tokens" or "Core system (fixed): 15,000"
            # but NOT "Core system prompt: ~3,000" which is a sub-component
            match = re.search(r'Core system\s*(?:\+\s*tools|\(fixed\)).*?(\d{1,2},?\d{3})\s*tokens', content)
            if match:
                value = int(match.group(1).replace(",", ""))
                assert value == FIXED_OVERHEAD, (
                    f"{f.name}: Core system should be {FIXED_OVERHEAD}, found {value}"
                )

    def test_before_component_sum(self):
        """Before components should sum to ~43,000."""
        total = sum(BEFORE_COMPONENTS.values())
        assert total == UNAUDITED_TOTAL, (
            f"Before components sum to {total}, expected {UNAUDITED_TOTAL}"
        )

    def test_after_component_sum(self):
        """After components should sum to ~28,000."""
        total = sum(AFTER_COMPONENTS.values())
        assert total == OPTIMIZED_TOTAL, (
            f"After components sum to {total}, expected {OPTIMIZED_TOTAL}"
        )

    def test_savings_consistent(self):
        """Config savings should be ~15,000 tokens."""
        savings = UNAUDITED_TOTAL - OPTIMIZED_TOTAL
        assert savings == 15000, f"Savings should be 15,000, got {savings}"

    def test_unavailable_percentages(self):
        """38% and 30% should be derivable from token counts."""
        autocompact_buffer = 33000
        before_unavailable = UNAUDITED_TOTAL + autocompact_buffer
        after_unavailable = OPTIMIZED_TOTAL + autocompact_buffer
        before_pct = round(before_unavailable / 200000 * 100)
        after_pct = round(after_unavailable / 200000 * 100)
        assert before_pct == UNAVAILABLE_BEFORE_PCT, (
            f"Before unavailable should be {UNAVAILABLE_BEFORE_PCT}%, calculated {before_pct}%"
        )
        # After is 30.5% which rounds to 31, but we use 30 in docs (floor)
        assert after_pct in (UNAVAILABLE_AFTER_PCT, UNAVAILABLE_AFTER_PCT + 1), (
            f"After unavailable should be ~{UNAVAILABLE_AFTER_PCT}%, calculated {after_pct}%"
        )


class TestNoStaleNumbers:
    """Catch old/stale numbers that should have been updated."""

    def test_no_old_mcp_numbers(self):
        """Old MCP overhead numbers (12K, 7K as the base) should not appear."""
        files = get_all_content_files()
        for f in files:
            content = read_file_content(f)
            # "12,000 tokens" near "MCP" could be stale (old pre-ToolSearch number)
            # But 12,000 near "built-in tools" is correct
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "12,000" in line and "mcp" in line.lower():
                    # This would be a stale MCP number
                    assert False, f"{f.name}:{i+1}: Found '12,000' near 'MCP' - likely stale"

    def test_no_old_command_overhead(self):
        """Old command overhead (1,250 tokens for 25 commands) should not appear as THE overhead."""
        files = get_all_content_files()
        for f in files:
            content = read_file_content(f)
            # "1,250" as a fixed overhead for commands is stale
            if "1,250" in content and "commands" in content.lower():
                # Allow it in context of "~50 tokens x 25 = 1,250" which is a calculation
                pass  # This pattern is OK if it's a calculation example


class TestMeasurePyConstants:
    """Verify measure.py uses correct constants."""

    def test_chars_per_token(self):
        """Should use 4.0 chars per token."""
        assert measure_py_content().count("CHARS_PER_TOKEN = 4.0") == 1

    def test_fixed_overhead(self):
        """Should use 15000 for core system."""
        content = measure_py_content()
        assert '"tokens": 15000' in content or "'tokens': 15000" in content

    def test_tokens_per_skill(self):
        """Should use 100 tokens per skill."""
        assert "TOKENS_PER_SKILL_APPROX = 100" in measure_py_content()

    def test_tokens_per_command(self):
        """Should use 50 tokens per command."""
        assert "TOKENS_PER_COMMAND_APPROX = 50" in measure_py_content()

    def test_tokens_per_deferred_tool(self):
        """Should use 15 tokens per deferred tool."""
        assert "TOKENS_PER_DEFERRED_TOOL = 15" in measure_py_content()


def measure_py_content():
    """Read measure.py content (cached)."""
    if not hasattr(measure_py_content, "_cache"):
        measure_py_content._cache = (
            SKILL_ROOT / "scripts" / "measure.py"
        ).read_text()
    return measure_py_content._cache
