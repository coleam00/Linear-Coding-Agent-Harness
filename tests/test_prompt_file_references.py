"""
Test: Prompt File References
============================

This test reproduces a bug where the initializer prompt references `app_spec.txt`
ambiguously, causing the agent to look in the wrong directory.

The Bug:
--------
1. The prompt says: "Start by reading `app_spec.txt` in your working directory"
2. The file is copied to `generations/my_project/app_spec.txt`
3. The agent's cwd is set to `generations/my_project`
4. BUT the agent tried to read `/path/to/Linear-Coding-Agent-Harness/app_spec.txt`
   (the harness root, not the project directory)

This happens because:
- The prompt doesn't explicitly state where the working directory is
- The agent may infer context from where it was invoked, not from the cwd setting
- "Your working directory" is ambiguous without explicit path context

The Fix:
--------
The prompt should either:
1. Use explicit relative paths: "./app_spec.txt"
2. Or state the full context: "in your project directory (the cwd)"
3. Or include the path in the prompt dynamically
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from prompts import PROMPTS_DIR, load_prompt, copy_spec_to_project


class TestPromptFileReferences:
    """Tests for file reference consistency in prompts."""

    def test_app_spec_exists_in_prompts_dir(self):
        """Verify app_spec.txt exists in prompts directory."""
        spec_path = PROMPTS_DIR / "app_spec.txt"
        assert spec_path.exists(), f"app_spec.txt not found at {spec_path}"

    def test_initializer_prompt_references_app_spec(self):
        """Verify initializer prompt references app_spec.txt."""
        prompt = load_prompt("initializer_prompt")
        assert "app_spec.txt" in prompt, "Prompt should reference app_spec.txt"

    def test_copy_spec_to_project_creates_file(self):
        """Verify copy_spec_to_project copies the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()

            copy_spec_to_project(project_dir)

            dest_file = project_dir / "app_spec.txt"
            assert dest_file.exists(), f"app_spec.txt not copied to {dest_file}"

    def test_prompt_uses_explicit_path(self):
        """
        FIXED: The prompt now uses explicit relative path.

        Previously the prompt said "in your working directory" which was
        ambiguous. Now it uses `./app_spec.txt` which is explicit.
        """
        prompt = load_prompt("initializer_prompt")

        # The fix: should use explicit relative path
        assert "./app_spec.txt" in prompt, (
            "Prompt should use explicit './app_spec.txt' path"
        )

        # Should NOT have the ambiguous phrase anymore
        assert "in your working directory" not in prompt, (
            "Prompt should not use ambiguous 'in your working directory' phrase"
        )

    def test_prompt_has_explicit_relative_path(self):
        """
        FIXED: Prompt uses explicit relative path for the first reference.

        The first reference to app_spec.txt (where agent reads the file)
        now uses `./app_spec.txt`. Other references in documentation
        context don't need the prefix.
        """
        prompt = load_prompt("initializer_prompt")

        # Count references to app_spec.txt
        references = prompt.count("app_spec.txt")
        assert references > 0, "Prompt should reference app_spec.txt"

        # The critical first reference should use explicit path
        explicit_relative = prompt.count("./app_spec.txt")
        assert explicit_relative >= 1, (
            f"Found {references} references to 'app_spec.txt' but "
            f"none use explicit './app_spec.txt' notation for the read instruction."
        )

    def test_file_exists_in_correct_location_after_copy(self):
        """
        Verify the file exists where the agent SHOULD look.

        This confirms the infrastructure is correct - the bug is in
        how the prompt communicates the file location.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "my_project"
            project_dir.mkdir()

            # This is what the harness does
            copy_spec_to_project(project_dir)

            # File should exist in project_dir (the agent's cwd)
            correct_path = project_dir / "app_spec.txt"
            assert correct_path.exists(), f"File should exist at {correct_path}"

            # File should NOT exist in parent (simulating harness root)
            wrong_path = Path(tmpdir) / "app_spec.txt"
            assert (
                not wrong_path.exists()
            ), f"File should NOT exist at {wrong_path} (harness root equivalent)"


class TestPromptPathClarity:
    """Tests for path clarity in all prompts."""

    def test_all_file_references_are_explicit(self):
        """
        Check that file references in prompts use explicit paths.

        Ambiguous references like "in your working directory" or
        "in the current directory" can confuse the agent about
        which directory is being referenced.
        """
        ambiguous_phrases = [
            "in your working directory",
            "in the current directory",
            "in this directory",
            "your directory",
        ]

        prompts_to_check = ["initializer_prompt", "coding_prompt"]
        issues = []

        for prompt_name in prompts_to_check:
            try:
                prompt = load_prompt(prompt_name)
                for phrase in ambiguous_phrases:
                    if phrase in prompt.lower():
                        issues.append(f"{prompt_name}: contains '{phrase}'")
            except FileNotFoundError:
                pass  # Skip missing prompts

        if issues:
            pytest.fail(
                "Found ambiguous directory references in prompts:\n"
                + "\n".join(f"  - {issue}" for issue in issues)
                + "\n\nThese should be replaced with explicit paths like './filename' "
                "or include context like 'in the project directory (your cwd)'"
            )
