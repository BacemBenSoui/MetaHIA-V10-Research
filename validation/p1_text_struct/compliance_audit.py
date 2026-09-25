"""System-compliance audit of the P1-TEXT-STRUCT gateway (convention section 4), separate from the scorer.

The scorer cannot observe a hidden semantic resource from (prediction, reference); this audit inspects
the gateway itself:
  1. dependency manifest: every import must be on the standard-library allowlist (no local modules,
     no third-party package, no model);
  2. declared resources: every module-level collection literal of strings must be declared in the
     gateway's RESOURCES dict under a permitted closed-class/morphology category;
  3. forbidden names: no resource or name that looks like semantic knowledge;
  4. no I/O at runtime: no open(), network, subprocess or dynamic import (no resource loaded from disk);
  5. file allowlist: the gateway is a single declared file.
Negative tests (tests/test_p1_text_struct_*): deliberately non-compliant gateways must fail the audit.
"""
from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORTS = {"__future__", "re", "dataclasses", "typing", "collections", "functools", "itertools",
                   "string", "unicodedata", "json"}
ALLOWED_RESOURCE_CATEGORIES = {"determiners", "pronouns", "prepositions", "auxiliaries", "negators",
                               "conjunctions", "quantifiers", "number_words", "suffix_rules", "irregular_forms",
                               "adverb_classes_by_suffix"}
FORBIDDEN_HINTS = ("synonym", "antonym", "hypernym", "hyponym", "gazetteer", "entity", "entities", "sentiment",
                   "embedding", "wordnet", "colour", "color", "city", "cities", "profession", "idiom", "meaning",
                   "semantic", "opposite", "incompatib")
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "__import__", "input"}
FORBIDDEN_MODULE_PREFIXES = ("urllib", "socket", "http", "subprocess", "requests", "importlib", "os", "pathlib",
                             "pickle", "shelve", "sqlite3")


def _is_string_collection(node: ast.AST) -> bool:
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return bool(node.elts) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in node.elts)
    if isinstance(node, ast.Dict):
        return bool(node.keys) and all(isinstance(k, ast.Constant) and isinstance(k.value, str) for k in node.keys)
    if isinstance(node, ast.Call) and getattr(node.func, "id", "") in {"frozenset", "set", "dict", "tuple"}:
        return any(_is_string_collection(a) for a in node.args)
    return False


def audit_source(source: str, filename: str = "<gateway>") -> list[str]:
    tree = ast.parse(source, filename=filename)
    problems: list[str] = []
    declared: dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "RESOURCES" for t in node.targets):
            try:
                declared = ast.literal_eval(node.value)
            except ValueError:
                problems.append("RESOURCES must be a literal dict {name: category}")
    if not declared:
        problems.append("gateway must declare RESOURCES = {resource_name: category}")
    for name, category in declared.items():
        if category not in ALLOWED_RESOURCE_CATEGORIES:
            problems.append(f"resource {name!r}: category {category!r} is not permitted")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for m in modules:
                root = m.split(".")[0]
                if root not in ALLOWED_IMPORTS or m.startswith(FORBIDDEN_MODULE_PREFIXES):
                    problems.append(f"import {m!r} is outside the dependency allowlist")
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if fname in FORBIDDEN_CALLS:
                problems.append(f"call {fname}() is forbidden (no runtime I/O or dynamic code)")
        if isinstance(node, ast.Name) and any(h in node.id.lower() for h in FORBIDDEN_HINTS):
            problems.append(f"name {node.id!r} looks like semantic knowledge")
    for node in tree.body:
        if isinstance(node, ast.Assign) and _is_string_collection(node.value):
            for target in node.targets:
                name = getattr(target, "id", None)
                if name and name != "RESOURCES" and name not in declared:
                    problems.append(f"undeclared module-level word collection {name!r}")
    return sorted(set(problems))


def audit_gateway(path: Path, allowed_files: set[str]) -> list[str]:
    problems = [] if path.name in allowed_files else [f"gateway file {path.name!r} not in the allowlist"]
    return problems + audit_source(path.read_text(encoding="utf-8"), str(path))
