# Copyright (C) 2026 DeepPlant contributors
# SPDX-License-Identifier: AGPL-3.0-only

"""Deterministic Python architecture and size guardrails (Issue #108).

The canonical Python engineering contract (``docs/dev/python/index.md``) defines
logical-LOC size limits and keeps the semantic Core independent of presentation,
application, transport, CLI, GUI, and serialization layers. This module turns the
mechanically checkable subset of that contract into a deterministic,
repository-owned gate, run by ``make architecture-check``.

It is deliberately small and standard-library only (``ast`` and ``tokenize``):
it is not a general-purpose static-analysis framework, and it deliberately does
not claim to enforce every statement of the contract. It verifies two things:

Size rules
----------

Logical LOC is counted from Python lexical tokens, never from raw text:

- blank lines and genuine comment-only lines are excluded;
- a line that carries any non-comment token counts, including decorator lines
  and every source line a multi-line expression or multi-line string occupies;
- the module-level docstring is excluded; every other docstring counts as
  content of the scope that defines it;
- a module (or a test module) counts the whole file's logical content; a class
  counts its complete body including methods and nested classes; a
  function/method counts its complete body including nested definitions. A
  definition's scope begins at its first decorator, so scopes intentionally
  overlap: a method counts toward its own size, its class, and the module.

The enforced scopes and thresholds (soft notices never fail; hard limits do):

======================== =============== ===============
Scope                    Soft            Hard
======================== =============== ===============
Production module        250             500
Test module              400             800
Function/method          40              80
Class                    150             300
======================== =============== ===============

Discovered files are ``src/deepplant/**/*.py`` and ``tests/**/*.py``. The module
limit depends on the file kind (production vs ``tests/``); the function/method
and class limits apply to every discovered file. ``tools/**/*.py`` is outside
this size policy (it stays covered by Ruff, Pyright, and pytest).

Import-boundary rules
---------------------

The semantic Core and the other framework-free layers must not import transport,
CLI, GUI, or presentation layers. Only direct import statements are inspected
(including relative imports and ``from``-imported submodules); this is a
structural dependency check, not a proof about runtime or transitive behavior.

Exceptions
----------

Size exceptions are centralized in :data:`SIZE_EXCEPTIONS` (never inline
suppression comments). Each names its exact ``path`` and ``scope`` plus a written
justification. The list is intentionally empty: ordinary production code passes
every hard limit without grandfathering.
"""

from __future__ import annotations

import argparse
import ast
import io
import sys
import tokenize
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import cast

#: Repository root, derived from this file's location so the checker is
#: independent of the current working directory.
REPO_ROOT = Path(__file__).resolve().parents[1]

#: Modules whose size is guarded, as repository-relative globs.
SIZE_GLOBS: tuple[str, ...] = ("src/deepplant/**/*.py", "tests/**/*.py")

#: Repository-relative prefixes that distinguish file kinds and rule scope.
PRODUCTION_PREFIX = "src/deepplant/"
TEST_PREFIX = "tests/"

#: Scope labels that render as ``file: scope`` (module-level diagnostics).
MODULE_SCOPE_LABELS = frozenset({"module", "test module"})


class Severity(Enum):
    """Whether a finding is advisory (soft) or fails the gate (hard)."""

    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SizeLimits:
    """The soft and hard logical-LOC thresholds for one scope."""

    soft: int
    hard: int


PRODUCTION_MODULE_LIMITS = SizeLimits(soft=250, hard=500)
TEST_MODULE_LIMITS = SizeLimits(soft=400, hard=800)
FUNCTION_LIMITS = SizeLimits(soft=40, hard=80)
CLASS_LIMITS = SizeLimits(soft=150, hard=300)


@dataclass(frozen=True)
class SizeException:
    """One explicitly justified exemption from a single size finding.

    ``path`` is the repository-relative POSIX path and ``scope`` is the exact
    label the checker reports (``"module"``, ``"test module"``, or a definition
    qualname such as ``"EditorServer.start"``).
    """

    path: str
    scope: str
    justification: str


#: The size exceptions in force. Empty by design: the production tree passes
#: every hard limit, and the canonical policy is never weakened per file. Add an
#: entry only for generated, vendored, or schema material, with a written
#: justification and the narrowest possible scope.
SIZE_EXCEPTIONS: tuple[SizeException, ...] = ()


@dataclass(frozen=True)
class Finding:
    """One deterministic size or import-boundary diagnostic."""

    severity: Severity
    path: str
    scope: str
    message: str
    line: int = 0

    def render(self) -> str:
        """Render the diagnostic in the stable, documented one-line shape."""
        separator = ": " if self.scope in MODULE_SCOPE_LABELS else ":"
        return f"{self.severity.value:<7} {self.path}{separator}{self.scope} {self.message}"


# ---------------------------------------------------------------------------
# Size measurement (token-aware logical LOC)
# ---------------------------------------------------------------------------

#: Token types that never make a line a code line: line structure, layout
#: indentation, the end marker, and genuine comments.
_IGNORED_TOKEN_TYPES: frozenset[int] = frozenset(
    {
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENDMARKER,
        tokenize.COMMENT,
        tokenize.ENCODING,
    }
)

#: Definition kinds the checker reports separately (one of
#: ``"function"``, ``"method"``, or ``"class"``).


@dataclass(frozen=True)
class Definition:
    """One function, method, or class with its complete-content logical LOC."""

    kind: str
    qualname: str
    lineno: int
    loc: int


def logical_lines(source: str) -> tuple[int, ...]:
    """Return the 1-based lines that carry a Python lexical token.

    Blank lines (only ``NEWLINE``/``NL``), structural indentation, and genuine
    comment-only lines (only ``COMMENT``) are excluded. A multi-line string token
    marks every source line it spans, so the interior lines of a docstring or
    string literal count. The decision is made from tokens, never from text such
    as ``line.strip().startswith("#")`` (``#`` inside a string is content).
    """
    lines: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in _IGNORED_TOKEN_TYPES:
            continue
        start = token.start[0]
        lines.update(range(start, max(token.end[0], start) + 1))
    return tuple(sorted(lines))


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    """Return a child -> parent map for the whole tree."""
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _qualname(node: ast.AST, parents: dict[ast.AST, ast.AST], name: str) -> str:
    """Return the dotted definition name, qualified by nested scopes."""
    names: list[str] = []
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(parent.name)
        current = parent
    names.reverse()
    names.append(name)
    return ".".join(names)


def _is_method(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    """Whether the nearest enclosing definition is a class."""
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return isinstance(parent, ast.ClassDef)
        current = parent
    return False


def _definition_start(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> int:
    """First source line of a definition, including its decorators."""
    if node.decorator_list:
        return min(decorator.lineno for decorator in node.decorator_list)
    return node.lineno


def _module_docstring_lines(tree: ast.Module) -> frozenset[int]:
    """Lines of the module-level docstring, which is attributed to no scope."""
    if not tree.body:
        return frozenset()
    first = tree.body[0]
    if not isinstance(first, ast.Expr):
        return frozenset()
    value = first.value
    if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
        return frozenset()
    return frozenset(range(value.lineno, (value.end_lineno or value.lineno) + 1))


def measure_source(source: str) -> tuple[int, tuple[Definition, ...]]:
    """Measure one module's logical LOC and every definition it contains.

    Returns the module logical LOC (excluding the module-level docstring) and
    every function, method, and class defined anywhere in the file, each with its
    own complete-content logical LOC. Scopes intentionally overlap.
    """
    code_lines = frozenset(logical_lines(source))
    tree = ast.parse(source)
    parents = _parents(tree)
    module_loc = len(code_lines - _module_docstring_lines(tree))

    definitions: list[Definition] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = _definition_start(node)
        end = node.end_lineno or node.lineno
        if isinstance(node, ast.ClassDef):
            kind = "class"
        elif _is_method(node, parents):
            kind = "method"
        else:
            kind = "function"
        definitions.append(
            Definition(
                kind=kind,
                qualname=_qualname(node, parents, node.name),
                lineno=start,
                loc=sum(1 for line in code_lines if start <= line <= end),
            )
        )
    definitions.sort(key=lambda definition: (definition.lineno, definition.qualname))
    return module_loc, tuple(definitions)


# ---------------------------------------------------------------------------
# Size findings
# ---------------------------------------------------------------------------


def _is_excepted(path: str, scope: str, exceptions: Sequence[SizeException]) -> bool:
    """Whether a centralized exception covers this exact path and scope."""
    return any(exception.path == path and exception.scope == scope for exception in exceptions)


def _one_size_finding(
    path: str,
    scope: str,
    loc: int,
    limits: SizeLimits,
    line: int,
    exceptions: Sequence[SizeException],
) -> tuple[Finding, ...]:
    """Classify one measured scope into a soft notice, a hard error, or nothing."""
    if _is_excepted(path, scope, exceptions):
        return ()
    if loc > limits.hard:
        severity, level, limit = Severity.ERROR, "hard", limits.hard
    elif loc > limits.soft:
        severity, level, limit = Severity.WARNING, "soft", limits.soft
    else:
        return ()
    message = f"{loc} LOC ({level} limit {limit})"
    return (Finding(severity=severity, path=path, scope=scope, message=message, line=line),)


def size_findings(
    path: str,
    source: str,
    *,
    exceptions: Sequence[SizeException] = SIZE_EXCEPTIONS,
) -> tuple[Finding, ...]:
    """Return the size findings for one module's source text.

    The module limit depends on the file kind; the function/method and class
    limits apply to every discovered file.
    """
    is_test = path.startswith(TEST_PREFIX)
    module_loc, definitions = measure_source(source)
    module_scope = "test module" if is_test else "module"
    module_limits = TEST_MODULE_LIMITS if is_test else PRODUCTION_MODULE_LIMITS

    findings = list(_one_size_finding(path, module_scope, module_loc, module_limits, 1, exceptions))
    for definition in definitions:
        limits = CLASS_LIMITS if definition.kind == "class" else FUNCTION_LIMITS
        findings.extend(
            _one_size_finding(
                path, definition.qualname, definition.loc, limits, definition.lineno, exceptions
            )
        )
    return tuple(findings)


# ---------------------------------------------------------------------------
# Import-boundary findings
# ---------------------------------------------------------------------------

#: Third-party roots that must never appear in the framework-free layers:
#: web framework/transport (FastAPI, Starlette, Uvicorn), CLI (Typer, Click), and
#: GUI toolkits (PySide6, PyQt, shiboken). The semantic Core is deliberately
#: independent of all of them (ADR-0002).
FRAMEWORK_ROOTS: tuple[str, ...] = (
    "fastapi",
    "starlette",
    "uvicorn",
    "typer",
    "click",
    "PySide6",
    "PySide2",
    "PyQt5",
    "PyQt6",
    "shiboken6",
)


@dataclass(frozen=True)
class LayerRule:
    """Forbidden import targets for one layer, with the reason it exists."""

    scope: str
    forbidden: tuple[str, ...]
    reason: str

    def matches(self, path: str) -> bool:
        """Whether this rule governs the given repository-relative path."""
        if self.scope.endswith("/"):
            return path.startswith(self.scope)
        return path == self.scope


#: The authoritative import-boundary rules. Each ``scope`` is a repository path
#: (a directory prefix or one file); each ``forbidden`` entry is a module that
#: scope must not import, directly or through a submodule.
_LAYER_RULES: tuple[LayerRule, ...] = (
    LayerRule(
        scope="src/deepplant/model/",
        forbidden=FRAMEWORK_ROOTS
        + ("deepplant.editor", "deepplant.render", "deepplant.io", "deepplant.adapters"),
        reason=(
            "the semantic Core must stay independent of presentation, application, "
            "transport, CLI, GUI, and serialization layers (ADR-0002, ADR-0004)"
        ),
    ),
    LayerRule(
        scope="src/deepplant/render/",
        forbidden=FRAMEWORK_ROOTS + ("deepplant.editor",),
        reason=(
            "the headless renderer must not depend on the editor application, "
            "transport, or GUI layers (ADR-0002, ADR-0003)"
        ),
    ),
    LayerRule(
        scope="src/deepplant/adapters/",
        forbidden=FRAMEWORK_ROOTS + ("deepplant.editor", "deepplant.render"),
        reason=(
            "external-format adapters must not depend on presentation or application "
            "layers (ADR-0002)"
        ),
    ),
    LayerRule(
        scope="src/deepplant/io.py",
        forbidden=FRAMEWORK_ROOTS + ("deepplant.editor", "deepplant.render", "deepplant.adapters"),
        reason=(
            "the YAML serialization boundary must not depend on presentation, "
            "application, transport, or external-format adapters (ADR-0004)"
        ),
    ),
)


def module_path_for(path: str) -> tuple[str, ...]:
    """Return the dotted package containing a repository-relative module path.

    Used to resolve relative imports (``from ..render import x``). A leading
    ``src/`` directory is dropped so ``src/deepplant/model/plant.py`` resolves
    inside the ``deepplant`` package.
    """
    parts = Path(path).with_suffix("").parts
    if parts and parts[0] == "src":
        parts = parts[1:]
    return tuple(parts[:-1])


def _resolve_import_from(node: ast.ImportFrom, module_path: tuple[str, ...]) -> str:
    """Resolve an ``ImportFrom`` node to a dotted module name."""
    if node.level == 0:
        return node.module or ""
    keep = len(module_path) - (node.level - 1)
    base = module_path[: max(keep, 0)]
    if node.module:
        base = base + tuple(node.module.split("."))
    return ".".join(base)


def _imported_modules(source: str, module_path: tuple[str, ...]) -> tuple[tuple[int, str], ...]:
    """Return ``(lineno, module)`` for every import performed in the source.

    Both ``import a.b`` and ``from a import b`` are covered; ``from a import b``
    also yields the ``a.b`` submodule so ``from deepplant import editor`` is
    visible. Relative imports and aliases are resolved to absolute module names.
    """
    tree = ast.parse(source)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_import_from(node, module_path)
            if base:
                found.append((node.lineno, base))
                found.extend(
                    (node.lineno, f"{base}.{alias.name}")
                    for alias in node.names
                    if alias.name != "*"
                )
    return tuple(found)


def _forbidden_target(module: str, forbidden: Sequence[str]) -> str | None:
    """Return the forbidden target a module equals or nests under, if any."""
    for target in forbidden:
        if module == target or module.startswith(target + "."):
            return target
    return None


def architecture_findings(
    path: str, source: str, module_path: tuple[str, ...], rules: Sequence[LayerRule] = _LAYER_RULES
) -> tuple[Finding, ...]:
    """Return the import-boundary findings for one module's source text."""
    rule = next((candidate for candidate in rules if candidate.matches(path)), None)
    if rule is None:
        return ()
    seen: set[tuple[int, str]] = set()
    findings: list[Finding] = []
    for lineno, imported in _imported_modules(source, module_path):
        target = _forbidden_target(imported, rule.forbidden)
        if target is None or (lineno, target) in seen:
            continue
        seen.add((lineno, target))
        findings.append(
            Finding(
                severity=Severity.ERROR,
                path=path,
                scope=f"line {lineno}",
                message=f"forbidden import '{target}' ({rule.reason})",
                line=lineno,
            )
        )
    return tuple(findings)


# ---------------------------------------------------------------------------
# Repository check, rendering, and CLI
# ---------------------------------------------------------------------------


def iter_python_files(root: Path, globs: Sequence[str]) -> Iterator[Path]:
    """Yield each in-scope file once, in a deterministic order."""
    seen: set[Path] = set()
    for pattern in globs:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def check_repository(
    root: Path, *, exceptions: Sequence[SizeException] = SIZE_EXCEPTIONS
) -> tuple[Finding, ...]:
    """Run every size and import-boundary check over ``root``.

    Findings are returned in a stable order (path, line, scope, message), so the
    same source tree always produces the same result.
    """
    findings: list[Finding] = []
    for path in iter_python_files(root, SIZE_GLOBS):
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        try:
            findings.extend(size_findings(relative, source, exceptions=exceptions))
            if relative.startswith(PRODUCTION_PREFIX):
                findings.extend(architecture_findings(relative, source, module_path_for(relative)))
        except (SyntaxError, tokenize.TokenError) as exc:
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    path=relative,
                    scope="module",
                    message=f"cannot parse Python source: {exc}",
                )
            )
    return tuple(
        sorted(
            findings,
            key=lambda finding: (finding.path, finding.line, finding.scope, finding.message),
        )
    )


def render_findings(findings: Sequence[Finding]) -> str:
    """Render the findings plus a stable summary line."""
    lines = [finding.render() for finding in findings]
    errors = sum(1 for finding in findings if finding.severity is Severity.ERROR)
    lines.append("")
    lines.append(f"architecture check: {errors} error(s), {len(findings) - errors} warning(s)")
    return "\n".join(lines)


def has_errors(findings: Sequence[Finding]) -> bool:
    """Whether any finding must fail the gate."""
    return any(finding.severity is Severity.ERROR for finding in findings)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the checker."""
    parser = argparse.ArgumentParser(
        prog="architecture_check",
        description="Deterministic Python size and import-boundary guardrails (Issue #108).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root to check (defaults to this checkout).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the checker and return a process exit code."""
    arguments = build_parser().parse_args(None if argv is None else list(argv))
    root_argument = cast("str | None", arguments.root)
    root = Path(root_argument).resolve() if root_argument else REPO_ROOT
    findings = check_repository(root)
    print(render_findings(findings), flush=True)
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    sys.exit(main())
