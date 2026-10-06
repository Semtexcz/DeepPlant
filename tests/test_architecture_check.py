"""Deterministic regression tests for the Python architecture guardrails (#108).

The size and import-boundary checks live in a small, standard-library,
repository-owned module (``tools/architecture_check.py``) that is run by
``make architecture-check``. These tests pin the counting semantics the canonical
contract defines — against small synthetic sources and temporary repository
trees — so the checker's own behaviour is verified rather than assumed:

- logical LOC excludes blank and comment-only lines but counts code lines,
  multi-line expressions, multi-line string content, and decorators;
- the module-level docstring is excluded while every other docstring counts;
- nested scopes are measured independently and overlap intentionally;
- soft violations warn, hard violations fail, and the boundaries are exact;
- the import-boundary rules catch forbidden Core dependencies, including nested
  and relative imports, without flagging allowed dependencies.

Tests build their own fixtures: no test writes into the source tree.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tools import architecture_check
from tools.architecture_check import Finding, Severity, SizeException

ROOT = Path(__file__).resolve().parents[1]


def _scope_locs(source: str) -> dict[str, int]:
    """Map every definition qualname to its complete-content logical LOC."""
    _, definitions = architecture_check.measure_source(source)
    return {definition.qualname: definition.loc for definition in definitions}


def _scope_kind(source: str, qualname: str) -> str:
    _, definitions = architecture_check.measure_source(source)
    for definition in definitions:
        if definition.qualname == qualname:
            return definition.kind
    raise AssertionError(f"no definition named {qualname!r}")


def _module_source(lines: int) -> str:
    """A production-shaped module whose logical LOC is exactly ``lines``."""
    return "".join(f"x{index} = {index}\n" for index in range(lines))


def _function_source(body_lines: int, name: str = "f") -> str:
    body = "".join(f"    x{index} = {index}\n" for index in range(body_lines))
    return f"def {name}():\n{body}"


def _class_source(body_lines: int) -> str:
    body = "".join(f"    x{index} = {index}\n" for index in range(body_lines))
    return f"class C:\n{body}"


def _size_findings(source: str, path: str = "src/deepplant/sample.py") -> tuple[Finding, ...]:
    return architecture_check.size_findings(path, source)


def _scope_findings(
    source: str, scope: str, path: str = "src/deepplant/sample.py"
) -> tuple[Finding, ...]:
    return tuple(finding for finding in _size_findings(source, path) if finding.scope == scope)


def _architecture(source: str, path: str = "src/deepplant/model/sample.py") -> tuple[Finding, ...]:
    return architecture_check.architecture_findings(
        path, source, architecture_check.module_path_for(path)
    )


def _write(root: Path, relative: str, source: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Logical LOC counting
# ---------------------------------------------------------------------------


def test_blank_lines_are_excluded() -> None:
    assert architecture_check.logical_lines("x = 1\n\n\ny = 2\n") == (1, 4)


def test_comment_only_lines_are_excluded() -> None:
    source = "x = 1\n# a genuine comment\n    # an indented comment\ny = 2\n"
    assert architecture_check.logical_lines(source) == (1, 4)


def test_inline_comment_keeps_its_code_line() -> None:
    assert architecture_check.logical_lines("x = 1  # trailing comment\n") == (1,)


def test_multiline_expression_counts_every_occupied_line() -> None:
    source = "x = (\n    1\n    + 2\n)\n"
    assert architecture_check.logical_lines(source) == (1, 2, 3, 4)


def test_multiline_string_content_is_counted() -> None:
    source = 'text = """line one\nline two\nline three"""\n'
    assert architecture_check.logical_lines(source) == (1, 2, 3)


def test_hash_inside_a_string_is_not_a_comment() -> None:
    source = 'def f():\n    """# not a comment"""\n    return 1\n'
    assert architecture_check.logical_lines(source) == (1, 2, 3)
    assert _scope_locs(source)["f"] == 3


def test_module_level_docstring_is_excluded() -> None:
    source = '"""Module doc.\n\nSecond paragraph.\n"""\nimport os\n\nx = 1\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert module_loc == 2


def test_standalone_one_line_module_docstring_is_excluded() -> None:
    module_loc, _ = architecture_check.measure_source('"""Module documentation."""\n')
    assert module_loc == 0


def test_standalone_multiline_module_docstring_is_excluded() -> None:
    source = '"""Line one.\nLine two.\nLine three."""\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert module_loc == 0


def test_module_docstring_sharing_a_line_with_code_counts_that_line() -> None:
    # The line carries an assignment as well as the docstring, so it is code.
    source = '"""Module documentation."""; answer = 42\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert module_loc == 1


def test_module_docstring_closing_line_with_code_counts_only_that_line() -> None:
    # Line one is pure docstring content (excluded); line two also carries code.
    source = '"""Line one.\nLine two."""; answer = 42\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert module_loc == 1


def test_module_docstring_containing_hash_is_not_a_comment() -> None:
    source = '"""Heading\n# not a comment\n"""\nvalue = 1\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert module_loc == 1


def test_function_docstring_is_counted() -> None:
    source = 'def f():\n    """Doc line one.\n    line two."""\n    return 1\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert _scope_locs(source)["f"] == 4
    assert module_loc == 4


def test_class_docstring_is_counted() -> None:
    source = 'class C:\n    """Doc line one.\n    line two."""\n    value = 1\n'
    module_loc, _ = architecture_check.measure_source(source)
    assert _scope_locs(source)["C"] == 4
    assert module_loc == 4


# ---------------------------------------------------------------------------
# Scope shapes: decorators, nesting, methods, overlap
# ---------------------------------------------------------------------------


def test_decorator_lines_belong_to_the_decorated_definition() -> None:
    source = "import functools\n\n\n@functools.cache\ndef f():\n    return 1\n"
    assert _scope_locs(source)["f"] == 3


def test_nested_function_is_measured_independently() -> None:
    source = "def outer():\n    def inner():\n        return 1\n    return inner\n"
    assert _scope_locs(source)["outer"] == 4
    assert _scope_locs(source)["outer.inner"] == 2


def test_nested_class_is_measured_independently() -> None:
    source = "class Outer:\n    class Inner:\n        value = 1\n"
    assert _scope_locs(source)["Outer"] == 3
    assert _scope_locs(source)["Outer.Inner"] == 2
    assert _scope_kind(source, "Outer.Inner") == "class"


def test_methods_count_inside_their_class() -> None:
    source = (
        "class C:\n    def one(self):\n        return 1\n    def two(self):\n        return 2\n"
    )
    locs = _scope_locs(source)
    assert _scope_kind(source, "C.one") == "method"
    assert locs["C.one"] == 2
    assert locs["C.two"] == 2
    assert locs["C"] == 5


def test_overlapping_scopes_are_intentional() -> None:
    source = "class C:\n    def method(self):\n        return 1\n"
    module_loc, _ = architecture_check.measure_source(source)
    locs = _scope_locs(source)
    # The method counts toward its own size, its class, and the module.
    assert locs["C.method"] == 2
    assert locs["C"] == 3
    assert module_loc == 3


# ---------------------------------------------------------------------------
# Thresholds and boundaries
# ---------------------------------------------------------------------------


def test_function_soft_boundary_is_inclusive() -> None:
    assert _scope_findings(_function_source(body_lines=39), "f") == ()
    warnings = _scope_findings(_function_source(body_lines=40), "f")
    assert [finding.severity for finding in warnings] == [Severity.WARNING]
    assert warnings[0].message == "41 LOC (soft limit 40)"


def test_function_hard_boundary_is_inclusive() -> None:
    # At exactly the hard limit the finding is still only a soft notice.
    assert _scope_findings(_function_source(body_lines=79), "f")[0].severity is Severity.WARNING
    error = _scope_findings(_function_source(body_lines=80), "f")[0]
    assert error.severity is Severity.ERROR
    assert error.message == "81 LOC (hard limit 80)"


def test_class_boundaries() -> None:
    assert _scope_findings(_class_source(body_lines=149), "C") == ()
    assert _scope_findings(_class_source(body_lines=150), "C")[0].severity is Severity.WARNING
    assert _scope_findings(_class_source(body_lines=299), "C")[0].severity is Severity.WARNING
    assert _scope_findings(_class_source(body_lines=300), "C")[0].severity is Severity.ERROR


def test_production_module_boundaries() -> None:
    assert _scope_findings(_module_source(250), "module") == ()
    assert _scope_findings(_module_source(251), "module")[0].severity is Severity.WARNING
    assert _scope_findings(_module_source(500), "module")[0].severity is Severity.WARNING
    assert _scope_findings(_module_source(501), "module")[0].severity is Severity.ERROR


def test_test_module_uses_its_own_limits() -> None:
    path = "tests/test_sample.py"
    assert _scope_findings(_module_source(400), "test module", path) == ()
    soft = _scope_findings(_module_source(401), "test module", path)
    assert soft[0].severity is Severity.WARNING
    assert soft[0].message == "401 LOC (soft limit 400)"
    assert _scope_findings(_module_source(800), "test module", path)[0].severity is Severity.WARNING
    hard = _scope_findings(_module_source(801), "test module", path)
    assert hard[0].severity is Severity.ERROR
    assert hard[0].message == "801 LOC (hard limit 800)"


def test_function_limits_apply_to_test_files_too() -> None:
    findings = _size_findings(_function_source(body_lines=80), "tests/test_sample.py")
    assert [finding.severity for finding in findings] == [Severity.ERROR]
    assert findings[0].scope == "f"


# ---------------------------------------------------------------------------
# Diagnostics: severity, ordering, formatting, attribution, exclusions
# ---------------------------------------------------------------------------


def test_multiple_violations_are_all_reported() -> None:
    source = _function_source(body_lines=80, name="first") + _function_source(
        body_lines=80, name="second"
    )
    findings = _size_findings(source)
    assert {finding.scope for finding in findings} == {"first", "second"}


def test_hard_violation_fails_and_soft_does_not() -> None:
    assert architecture_check.has_errors(_size_findings(_function_source(40))) is False
    assert architecture_check.has_errors(_size_findings(_function_source(80))) is True


def test_diagnostic_rendering_is_stable_and_attributed() -> None:
    errors = _size_findings(_function_source(body_lines=80))
    assert errors[0].path == "src/deepplant/sample.py"
    assert errors[0].scope == "f"
    assert errors[0].render() == ("ERROR   src/deepplant/sample.py:f 81 LOC (hard limit 80)")
    module_warning = _size_findings(_module_source(251))
    assert module_warning[0].render() == (
        "WARNING src/deepplant/sample.py: module 251 LOC (soft limit 250)"
    )


# ---------------------------------------------------------------------------
# Centralized exceptions
# ---------------------------------------------------------------------------


def test_centralized_exception_suppresses_exactly_its_scope() -> None:
    path = "src/deepplant/sample.py"
    source = _function_source(body_lines=80)
    matching = SizeException(path=path, scope="f", justification="generated by a code generator")
    assert architecture_check.size_findings(path, source, exceptions=(matching,)) == ()
    other = SizeException(path=path, scope="g", justification="a different scope")
    assert architecture_check.size_findings(path, source, exceptions=(other,)) != ()


def test_valid_exception_suppresses_only_its_exact_scope() -> None:
    path = "src/deepplant/sample.py"
    source = _function_source(body_lines=80, name="f") + _function_source(body_lines=80, name="g")
    exception = SizeException(path=path, scope="f", justification="generated by a code generator")
    findings = architecture_check.size_findings(path, source, exceptions=(exception,))
    assert [finding.scope for finding in findings] == ["g"]


def test_mismatched_exception_never_suppresses_a_violation() -> None:
    path = "src/deepplant/sample.py"
    source = _function_source(body_lines=80)
    wrong_scope = SizeException(path=path, scope="other", justification="a different scope")
    wrong_path = SizeException(path="src/deepplant/other.py", scope="f", justification="a path")
    findings = architecture_check.size_findings(path, source, exceptions=(wrong_scope, wrong_path))
    assert [finding.severity for finding in findings] == [Severity.ERROR]


def test_default_exception_list_is_empty() -> None:
    assert architecture_check.SIZE_EXCEPTIONS == ()


def test_default_exception_configuration_is_valid() -> None:
    assert architecture_check.size_exception_problems(architecture_check.SIZE_EXCEPTIONS) == ()


def test_valid_exception_configuration_is_accepted() -> None:
    exception = SizeException(
        path="src/deepplant/sample.py", scope="f", justification="generated code"
    )
    assert architecture_check.size_exception_problems((exception,)) == ()


def test_exception_with_empty_justification_is_rejected() -> None:
    exception = SizeException(path="src/deepplant/sample.py", scope="f", justification="")
    problems = architecture_check.size_exception_problems((exception,))
    assert any("justification" in problem for problem in problems)


def test_exception_with_whitespace_only_justification_is_rejected() -> None:
    exception = SizeException(path="src/deepplant/sample.py", scope="f", justification="  \t ")
    problems = architecture_check.size_exception_problems((exception,))
    assert any("justification" in problem for problem in problems)


def test_exception_with_empty_path_or_scope_is_rejected() -> None:
    exception = SizeException(path="   ", scope="", justification="looks justified")
    problems = architecture_check.size_exception_problems((exception,))
    assert any("'path'" in problem for problem in problems)
    assert any("'scope'" in problem for problem in problems)


def test_duplicate_exception_entries_are_rejected() -> None:
    first = SizeException(path="src/deepplant/sample.py", scope="f", justification="first reason")
    second = SizeException(path="src/deepplant/sample.py", scope="f", justification="second reason")
    problems = architecture_check.size_exception_problems((first, second))
    assert any("duplicate" in problem for problem in problems)


def test_wildcard_exceptions_are_rejected() -> None:
    wildcard_path = SizeException(path="src/deepplant/*.py", scope="f", justification="wildcard")
    wildcard_scope = SizeException(
        path="src/deepplant/sample.py", scope="EditorServer.*", justification="wildcard"
    )
    assert any(
        "wildcard" in problem
        for problem in architecture_check.size_exception_problems((wildcard_path,))
    )
    assert any(
        "wildcard" in problem
        for problem in architecture_check.size_exception_problems((wildcard_scope,))
    )


def test_invalid_exception_configuration_fails_the_repository_check(tmp_path: Path) -> None:
    # The tree itself is clean; only the configuration is invalid.
    _write(tmp_path, "src/deepplant/a.py", _module_source(10))
    exception = SizeException(path="src/deepplant/a.py", scope="module", justification="   ")

    findings = architecture_check.check_repository(tmp_path, exceptions=(exception,))

    assert findings
    assert all(finding.severity is Severity.ERROR for finding in findings)
    assert any("justification" in finding.message for finding in findings)
    assert architecture_check.has_errors(findings) is True


def test_valid_exception_configuration_does_not_fail_the_repository_check(tmp_path: Path) -> None:
    _write(tmp_path, "src/deepplant/a.py", _function_source(body_lines=80))
    exception = SizeException(path="src/deepplant/a.py", scope="f", justification="generated code")

    assert architecture_check.check_repository(tmp_path, exceptions=(exception,)) == ()


# ---------------------------------------------------------------------------
# Repository scan, ordering, and the command-line entry point
# ---------------------------------------------------------------------------


def test_check_repository_reports_in_stable_order(tmp_path: Path) -> None:
    _write(tmp_path, "src/deepplant/b.py", _module_source(501))
    _write(tmp_path, "src/deepplant/a.py", _module_source(501))
    _write(tmp_path, "tests/test_c.py", _module_source(801))

    findings = architecture_check.check_repository(tmp_path)

    assert [finding.path for finding in findings] == [
        "src/deepplant/a.py",
        "src/deepplant/b.py",
        "tests/test_c.py",
    ]
    assert all(finding.severity is Severity.ERROR for finding in findings)


def test_check_repository_excludes_tools_from_size_rules(tmp_path: Path) -> None:
    _write(tmp_path, "tools/big.py", _module_source(900))
    assert architecture_check.check_repository(tmp_path) == ()


def test_main_returns_nonzero_on_a_hard_violation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, "src/deepplant/a.py", _module_source(501))

    code = architecture_check.main(["--root", str(tmp_path)])

    output = capsys.readouterr().out
    assert code == 1
    assert output.startswith("ERROR   src/deepplant/a.py: module 501 LOC (hard limit 500)")
    assert "architecture check: 1 error(s), 0 warning(s)" in output


def test_main_returns_zero_on_a_clean_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(tmp_path, "src/deepplant/a.py", _module_source(10))

    code = architecture_check.main(["--root", str(tmp_path)])

    assert code == 0
    assert "architecture check: 0 error(s), 0 warning(s)" in capsys.readouterr().out


def test_command_line_entry_point_is_cwd_independent(tmp_path: Path) -> None:
    _write(tmp_path, "src/deepplant/a.py", _module_source(501))

    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "architecture_check.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(tmp_path),
    )

    assert completed.returncode == 1
    assert "module 501 LOC (hard limit 500)" in completed.stdout


# ---------------------------------------------------------------------------
# Import-boundary rules
# ---------------------------------------------------------------------------


def test_allowed_core_imports_pass() -> None:
    source = textwrap.dedent(
        """
        from collections.abc import Mapping

        import pydantic

        from deepplant.model import PlantModel
        from deepplant.model.process import ProcessStep
        """
    )
    assert _architecture(source) == ()


@pytest.mark.parametrize(
    "import_line",
    [
        "import fastapi",
        "from fastapi import FastAPI",
        "import starlette",
        "import uvicorn",
        "import typer",
        "from click import command",
        "from PySide6.QtCore import QTimer",
        "import PyQt5",
    ],
)
def test_framework_imports_in_the_core_are_forbidden(import_line: str) -> None:
    findings = _architecture(f"{import_line}\n")
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert findings[0].message.startswith("forbidden import")


@pytest.mark.parametrize(
    "import_line",
    [
        "import deepplant.editor",
        "import deepplant.editor.api",
        "from deepplant.editor import api",
        "from deepplant.editor.api import EditorServer",
        "from deepplant import editor",
    ],
)
def test_core_may_not_import_the_editor(import_line: str) -> None:
    findings = _architecture(f"{import_line}\n")
    assert len(findings) == 1
    assert findings[0].message.startswith("forbidden import 'deepplant.editor'")


def test_core_may_not_import_the_renderer() -> None:
    findings = _architecture("from deepplant.render import svg\n")
    assert len(findings) == 1
    assert findings[0].message.startswith("forbidden import 'deepplant.render'")


def test_relative_imports_are_resolved_and_checked() -> None:
    path = "src/deepplant/model/sample.py"
    findings = architecture_check.architecture_findings(
        path, "from ..render import svg\n", architecture_check.module_path_for(path)
    )
    assert len(findings) == 1
    assert findings[0].message.startswith("forbidden import 'deepplant.render'")


def test_module_path_for_resolves_the_containing_package() -> None:
    assert architecture_check.module_path_for("src/deepplant/model/plant.py") == (
        "deepplant",
        "model",
    )
    assert architecture_check.module_path_for("src/deepplant/io.py") == ("deepplant",)


def test_forbidden_import_in_a_nested_scope_is_detected() -> None:
    source = textwrap.dedent(
        """
        def helper() -> None:
            import fastapi
        """
    )
    findings = _architecture(source)
    assert len(findings) == 1
    assert "forbidden import 'fastapi'" in findings[0].message


def test_framework_imports_are_only_forbidden_inside_ruled_layers() -> None:
    # FastAPI belongs to the editor transport, so no layer rule governs it there.
    assert _architecture("from fastapi import FastAPI\n", "src/deepplant/editor/api.py") == ()
    # The headless renderer is framework-free, so the same import fails there.
    assert len(_architecture("from fastapi import FastAPI\n", "src/deepplant/render/svg.py")) == 1


def test_editor_may_depend_on_the_renderer() -> None:
    source = "from deepplant.render import compute_process_pfd_layout\n"
    assert _architecture(source, "src/deepplant/editor/projection.py") == ()


def test_serialization_boundary_may_import_yaml_but_not_the_editor() -> None:
    assert _architecture("import yaml\n", "src/deepplant/io.py") == ()
    assert len(_architecture("from deepplant.editor import api\n", "src/deepplant/io.py")) == 1


# ---------------------------------------------------------------------------
# Repository-wide guard: the delivered tree passes the new gate
# ---------------------------------------------------------------------------


def test_repository_has_no_hard_size_or_import_violations() -> None:
    findings = architecture_check.check_repository(ROOT)
    errors = [finding.render() for finding in findings if finding.severity is Severity.ERROR]
    assert errors == []
