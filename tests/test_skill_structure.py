"""Structural validity tests for the Token Optimizer skill."""

import re
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent / "skills" / "token-optimizer"
REPO_ROOT = Path(__file__).parent.parent


class TestSkillMdStructure:
    """SKILL.md should have valid frontmatter and required sections."""

    def test_skill_md_exists(self):
        assert (SKILL_ROOT / "SKILL.md").exists()

    def test_has_frontmatter(self):
        content = (SKILL_ROOT / "SKILL.md").read_text()
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        end = content.find("---", 3)
        assert end > 0, "SKILL.md must have closing --- for frontmatter"

    def test_frontmatter_has_name(self):
        content = (SKILL_ROOT / "SKILL.md").read_text()
        frontmatter = content[3:content.find("---", 3)]
        assert "name:" in frontmatter, "Frontmatter must have 'name:' field"

    def test_frontmatter_has_description(self):
        content = (SKILL_ROOT / "SKILL.md").read_text()
        frontmatter = content[3:content.find("---", 3)]
        assert "description:" in frontmatter, "Frontmatter must have 'description:' field"

    def test_has_phase_sections(self):
        content = (SKILL_ROOT / "SKILL.md").read_text()
        for phase in ["Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]:
            assert phase in content, f"SKILL.md must contain '{phase}'"


class TestAgentPrompts:
    """Agent prompts should have required structure."""

    def test_agent_prompts_exists(self):
        assert (SKILL_ROOT / "references" / "agent-prompts.md").exists()

    def test_has_all_audit_agents(self):
        content = (SKILL_ROOT / "references" / "agent-prompts.md").read_text()
        expected_agents = [
            "CLAUDE.md Auditor",
            "MEMORY.md Auditor",
            "Skills Auditor",
            "MCP Auditor",
            "Commands Auditor",
            "Settings & Advanced Auditor",
        ]
        for agent in expected_agents:
            assert agent in content, f"Missing agent: {agent}"

    def test_has_synthesis_agent(self):
        content = (SKILL_ROOT / "references" / "agent-prompts.md").read_text()
        assert "Synthesis Agent" in content or "Synthesis" in content

    def test_has_verification_agent(self):
        content = (SKILL_ROOT / "references" / "agent-prompts.md").read_text()
        assert "Verification Agent" in content or "Verification" in content

    def test_all_agents_have_security_note(self):
        content = (SKILL_ROOT / "references" / "agent-prompts.md").read_text()
        # Each agent block should contain the security instruction
        agent_blocks = content.split("###")
        for block in agent_blocks[1:]:  # Skip header
            if "Auditor" in block or "Synthesis" in block or "Verification" in block:
                assert "SECURITY" in block or "security" in block.lower(), (
                    f"Agent block missing security note: {block[:100]}..."
                )

    def test_agents_have_model_assignments(self):
        content = (SKILL_ROOT / "references" / "agent-prompts.md").read_text()
        # Check for model= in Task() blocks
        model_assignments = re.findall(r'model="(\w+)"', content)
        assert len(model_assignments) >= 8, (
            f"Expected at least 8 model assignments, found {len(model_assignments)}"
        )
        # Valid models
        valid_models = {"haiku", "sonnet", "opus"}
        for model in model_assignments:
            assert model in valid_models, f"Invalid model: {model}"


class TestReferenceFiles:
    """All reference files should exist and be non-empty."""

    REFERENCE_FILES = [
        "references/agent-prompts.md",
        "references/implementation-playbook.md",
        "references/optimization-checklist.md",
        "references/token-flow-architecture.md",
    ]

    @pytest.mark.parametrize("filepath", REFERENCE_FILES)
    def test_reference_exists_and_nonempty(self, filepath):
        full_path = SKILL_ROOT / filepath
        assert full_path.exists(), f"Missing reference file: {filepath}"
        content = full_path.read_text()
        assert len(content) > 100, f"Reference file too small: {filepath} ({len(content)} chars)"


class TestExampleFiles:
    """Example files should exist."""

    EXAMPLE_FILES = [
        "examples/claude-md-optimized.md",
        "examples/claudeignore-template",
        "examples/hooks-starter.json",
    ]

    @pytest.mark.parametrize("filepath", EXAMPLE_FILES)
    def test_example_exists(self, filepath):
        full_path = SKILL_ROOT / filepath
        assert full_path.exists(), f"Missing example file: {filepath}"


class TestImplementationPlaybook:
    """Implementation playbook should have all actions."""

    def test_has_original_actions(self):
        content = (SKILL_ROOT / "references" / "implementation-playbook.md").read_text()
        for action in ["4A:", "4B:", "4C:", "4D:", "4E:", "4F:", "4G:"]:
            assert action in content, f"Missing action {action}"

    def test_has_new_actions(self):
        content = (SKILL_ROOT / "references" / "implementation-playbook.md").read_text()
        for action in ["4H:", "4I:", "4J:", "4K:"]:
            assert action in content, f"Missing new action {action}"


class TestReadmeFileTree:
    """README file tree should match actual directory structure."""

    def test_readme_exists(self):
        assert (REPO_ROOT / "README.md").exists()

    def test_listed_files_exist(self):
        """Files mentioned in the README file tree should actually exist."""
        readme = (REPO_ROOT / "README.md").read_text()

        # Extract file tree section
        tree_match = re.search(
            r"```\s*\nskills/token-optimizer/\s*\n(.*?)```",
            readme,
            re.DOTALL,
        )
        if not tree_match:
            pytest.skip("Could not find file tree in README")

        tree_content = tree_match.group(1)
        # Parse indented file names (skip directory-only lines)
        for line in tree_content.strip().split("\n"):
            # Strip tree drawing characters and whitespace
            clean = line.strip().lstrip("├─└│ ")
            # Skip empty lines and directory headers and descriptions
            if not clean or clean.endswith("/") or "  " in clean:
                continue
            # Extract just the filename (before any description)
            filename = clean.split()[0] if clean.split() else clean

            # Skip if it looks like a description rather than a filename
            if not ("." in filename or filename in ("install.sh",)):
                continue

            # Build expected path based on indentation
            # This is a simplified check: just verify the filename exists somewhere in the skill
            matches = list(SKILL_ROOT.rglob(filename))
            if not matches:
                # Also check repo root
                matches = list(REPO_ROOT.rglob(filename))
            assert len(matches) > 0, f"File from README tree not found: {filename}"


class TestScriptsDirectory:
    """Scripts should be present and valid Python."""

    def test_measure_py_exists(self):
        assert (SKILL_ROOT / "scripts" / "measure.py").exists()

    def test_measure_py_is_valid_python(self):
        """measure.py should be syntactically valid Python."""
        content = (SKILL_ROOT / "scripts" / "measure.py").read_text()
        compile(content, "measure.py", "exec")  # Raises SyntaxError if invalid

    def test_measure_py_has_main(self):
        content = (SKILL_ROOT / "scripts" / "measure.py").read_text()
        assert 'if __name__ == "__main__"' in content


class TestOptimizationChecklist:
    """Optimization checklist should have all numbered items."""

    def test_has_items_1_through_22(self):
        content = (SKILL_ROOT / "references" / "optimization-checklist.md").read_text()
        for i in range(1, 23):
            assert f"### {i}." in content, f"Missing checklist item {i}"

    def test_has_new_items_23_through_30(self):
        content = (SKILL_ROOT / "references" / "optimization-checklist.md").read_text()
        for i in range(23, 31):
            assert f"### {i}." in content, f"Missing new checklist item {i}"
