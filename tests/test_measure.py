"""Unit tests for scripts/measure.py."""

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add scripts directory to path for importing measure
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "token-optimizer" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import measure


class TestEstimateTokensFromFile:
    def test_known_content(self, tmp_path):
        """Known content should produce expected token range."""
        f = tmp_path / "test.md"
        # 400 characters -> ~100 tokens at 4 chars/token
        content = "a" * 400
        f.write_text(content)
        tokens = measure.estimate_tokens_from_file(f)
        assert tokens == 100

    def test_missing_file(self):
        tokens = measure.estimate_tokens_from_file(Path("/nonexistent/file.md"))
        assert tokens == 0

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        tokens = measure.estimate_tokens_from_file(f)
        assert tokens == 0

    def test_unicode_content(self, tmp_path):
        f = tmp_path / "unicode.md"
        f.write_text("Hello World! 🌍 This has unicode.")
        tokens = measure.estimate_tokens_from_file(f)
        assert tokens > 0


class TestEstimateTokensFromFrontmatter:
    def test_yaml_frontmatter(self, tmp_path):
        f = tmp_path / "skill.md"
        f.write_text("---\nname: test\ndescription: A test skill\n---\n\n# Body\nContent here.\n")
        tokens = measure.estimate_tokens_from_frontmatter(f)
        # Frontmatter is "name: test\ndescription: A test skill\n" = ~40 chars = ~10 tokens, min 20
        assert tokens >= 20

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "no-front.md"
        f.write_text("# Just a heading\nNo frontmatter here.\n")
        tokens = measure.estimate_tokens_from_frontmatter(f)
        assert tokens == measure.TOKENS_PER_SKILL_APPROX

    def test_missing_file(self):
        tokens = measure.estimate_tokens_from_frontmatter(Path("/nonexistent.md"))
        assert tokens == measure.TOKENS_PER_SKILL_APPROX


class TestCountLines:
    def test_basic(self, tmp_path):
        f = tmp_path / "lines.txt"
        f.write_text("line1\nline2\nline3\n")
        assert measure.count_lines(f) == 3

    def test_missing_file(self):
        assert measure.count_lines(Path("/nonexistent")) == 0

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert measure.count_lines(f) == 0


class TestResolveRealPath:
    def test_regular_file(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("content")
        resolved = measure.resolve_real_path(f)
        assert resolved == f.resolve()

    def test_symlink(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("content")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        resolved = measure.resolve_real_path(link)
        assert resolved == target.resolve()


class TestSanitizeLabel:
    def test_valid_labels(self):
        assert measure.sanitize_label("before") == "before"
        assert measure.sanitize_label("after") == "after"
        assert measure.sanitize_label("snap-2026") == "snap-2026"
        assert measure.sanitize_label("test_1") == "test_1"

    def test_invalid_label_exits(self):
        with pytest.raises(SystemExit):
            measure.sanitize_label("../../../etc/passwd")

    def test_path_traversal_blocked(self):
        with pytest.raises(SystemExit):
            measure.sanitize_label("../../bad")

    def test_spaces_blocked(self):
        with pytest.raises(SystemExit):
            measure.sanitize_label("has spaces")


class TestCountMcpToolsAndServers:
    def test_with_mock_config(self, tmp_path):
        config_path = tmp_path / "settings.json"
        config_path.write_text(json.dumps({
            "mcpServers": {
                "server-a": {"command": "test"},
                "server-b": {"command": "test"},
                "server-c": {"command": "test"},
            }
        }))
        with mock.patch.object(measure, "get_mcp_config_paths", return_value=[config_path]):
            result = measure.count_mcp_tools_and_servers()
        assert result["server_count"] == 3
        assert result["tool_count_estimate"] == 3 * measure.AVG_TOOLS_PER_SERVER
        assert result["tokens"] == 3 * measure.AVG_TOOLS_PER_SERVER * measure.TOKENS_PER_DEFERRED_TOOL

    def test_missing_config(self, tmp_path):
        with mock.patch.object(measure, "get_mcp_config_paths", return_value=[tmp_path / "missing.json"]):
            result = measure.count_mcp_tools_and_servers()
        assert result["server_count"] == 0
        assert result["tokens"] == 0

    def test_invalid_json(self, tmp_path):
        config_path = tmp_path / "settings.json"
        config_path.write_text("not valid json")
        with mock.patch.object(measure, "get_mcp_config_paths", return_value=[config_path]):
            result = measure.count_mcp_tools_and_servers()
        assert result["server_count"] == 0


class TestHasPathsFrontmatter:
    def test_with_paths(self, tmp_path):
        f = tmp_path / "rule.md"
        f.write_text("---\npaths:\n  - src/**\n---\n# Rule\n")
        assert measure._has_paths_frontmatter(f) is True

    def test_without_paths(self, tmp_path):
        f = tmp_path / "rule.md"
        f.write_text("---\nname: general\n---\n# Rule\n")
        assert measure._has_paths_frontmatter(f) is False

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "rule.md"
        f.write_text("# Just content\nNo frontmatter.\n")
        assert measure._has_paths_frontmatter(f) is False

    def test_missing_file(self):
        assert measure._has_paths_frontmatter(Path("/nonexistent.md")) is False


class TestDetectImports:
    def test_finds_imports(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        doc = tmp_path / "docs" / "standards.md"
        doc.parent.mkdir()
        doc.write_text("# Coding Standards\n" * 50)
        claude_md.write_text("## My Config\n@docs/standards.md\n## More\n")
        imports = measure._detect_imports(claude_md)
        assert len(imports) == 1
        assert imports[0]["pattern"] == "@docs/standards.md"
        assert imports[0]["exists"] is True
        assert imports[0]["tokens"] > 0

    def test_no_imports(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("## Config\nNo imports here.\n")
        imports = measure._detect_imports(claude_md)
        assert len(imports) == 0

    def test_missing_import_target(self, tmp_path):
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@nonexistent/file.md\n")
        imports = measure._detect_imports(claude_md)
        assert len(imports) == 1
        assert imports[0]["exists"] is False
        assert imports[0]["tokens"] == 0

    def test_path_traversal_blocked(self, tmp_path):
        """@imports pointing outside project root should be skipped."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("@../../etc/passwd.md\n")
        imports = measure._detect_imports(claude_md)
        assert len(imports) == 0


class TestCheckSettingsEnv:
    def test_finds_vars(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({
            "env": {
                "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "70",
                "UNRELATED_VAR": "value",
            }
        }))
        result = measure._check_settings_env(settings)
        assert result["settings_exists"] is True
        assert "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE" in result["found"]
        assert "UNRELATED_VAR" not in result["found"]

    def test_missing_file(self, tmp_path):
        result = measure._check_settings_env(tmp_path / "nope.json")
        assert result["settings_exists"] is False
        assert result["found"] == {}

    def test_no_env_block(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({"mcpServers": {}}))
        result = measure._check_settings_env(settings)
        assert result["found"] == {}


class TestGetFrontmatterDescriptionLength:
    def test_single_line(self, tmp_path):
        f = tmp_path / "SKILL.md"
        f.write_text('---\nname: test\ndescription: "A short desc"\n---\n')
        length = measure._get_frontmatter_description_length(f)
        assert length == len("A short desc")

    def test_multiline(self, tmp_path):
        f = tmp_path / "SKILL.md"
        f.write_text('---\nname: test\ndescription: |\n  Line one\n  Line two\n---\n')
        length = measure._get_frontmatter_description_length(f)
        assert length > 0

    def test_no_description(self, tmp_path):
        f = tmp_path / "SKILL.md"
        f.write_text("---\nname: test\n---\n")
        length = measure._get_frontmatter_description_length(f)
        assert length == 0


class TestMeasureComponents:
    """Integration test using the tmp_claude_dir fixture."""

    def test_basic_components(self, tmp_claude_dir, monkeypatch):
        monkeypatch.setattr(measure, "CLAUDE_DIR", tmp_claude_dir)
        monkeypatch.setattr(measure, "HOME", tmp_claude_dir.parent)

        # Mock find_projects_dir to return our test projects dir
        projects_dir = tmp_claude_dir / "projects" / "-tmp-test"
        monkeypatch.setattr(measure, "find_projects_dir", lambda: projects_dir)

        # Mock get_mcp_config_paths
        monkeypatch.setattr(
            measure, "get_mcp_config_paths",
            lambda: [tmp_claude_dir / "settings.json"],
        )

        components = measure.measure_components()

        # CLAUDE.md exists
        assert components["claude_md_global"]["exists"] is True
        assert components["claude_md_global"]["tokens"] > 0

        # Skills counted
        assert components["skills"]["count"] == 3

        # Commands counted
        assert components["commands"]["count"] == 3

        # MCP servers counted
        assert components["mcp_tools"]["server_count"] == 2

        # MEMORY.md found
        assert components["memory_md"]["exists"] is True

        # .claudeignore exists
        assert components["claudeignore"]["global_exists"] is True

        # Hooks configured
        assert components["hooks"]["configured"] is True

        # Rules found
        assert components["rules"]["count"] == 2
        assert components["rules"]["always_loaded"] == 1  # general.md has no paths:

        # Settings env found
        assert "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE" in components["settings_env"]["found"]

        # Core system present
        assert components["core_system"]["tokens"] == 15000


class TestSnapshotAndCompare:
    def test_snapshot_cycle(self, tmp_path, monkeypatch):
        monkeypatch.setattr(measure, "SNAPSHOT_DIR", tmp_path / "snapshots")
        monkeypatch.setattr(measure, "CLAUDE_DIR", tmp_path / ".claude")
        monkeypatch.setattr(measure, "HOME", tmp_path)
        monkeypatch.setattr(measure, "find_projects_dir", lambda: None)
        monkeypatch.setattr(measure, "get_mcp_config_paths", lambda: [])
        monkeypatch.setattr(measure, "get_session_baselines", lambda n: [])

        # Create minimal CLAUDE.md
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "CLAUDE.md").write_text("# Test\n")

        snapshot = measure.take_snapshot("before")
        assert snapshot["label"] == "before"
        assert (tmp_path / "snapshots" / "snapshot_before.json").exists()

        # Take "after" snapshot
        snapshot2 = measure.take_snapshot("after")
        assert snapshot2["label"] == "after"
        assert (tmp_path / "snapshots" / "snapshot_after.json").exists()
