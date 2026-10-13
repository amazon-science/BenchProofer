#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15572.

Two kind-A obligations are validated against the REAL callees by executing them
in the eval interpreter (stdlib `pathlib` + a faithful copy of Django's tiny
`to_path`; the unchanged predicate `is_django_path` reproduced from
`django/utils/autoreload.py` modulo the `django.__file__` constant):

  (A-consumed, structural) `beneath_framework` <-> `is_django_path`. The model's
      axiom declares it @Pure @ContractOnly with NO value Ensures, so the only
      property the proof consumes is that it is a DETERMINISTIC Boolean function
      of its entry. We assert exactly that on the real predicate: every
      observation is a `bool`, and repeated calls on the same input agree.

  (deep model, validated) the empty-entry collapse encoded by `join_base` /
      `is_present`:
        - LOAD-BEARING UNIVERSAL: joining the EMPTY entry onto the base yields
          the base itself (`Path.cwd() / to_path("") == Path.cwd()`), i.e. an
          empty entry would contribute the base location  -> modeled as
          join_base(0) == 0 (the reserved base token), is_present("") is False.
          This is the property the F2P test turns on and is checked on every
          entry the fuzz emits;
        - SCOPED (NOT a universal): on the configured/tested entries the F2P/P2P
          tests use, a PRESENT entry joins to a DISTINCT, non-base location
          (`Path.cwd() / to_path(s) != Path.cwd()`)  -> join_base(d)==d, d != 0.
          This is checked on the configured/tested corpus, NOT asserted of
          arbitrary truthy strings: truthiness (`bool(entry)`) is NOT equivalent
          to "joins to a distinct location". The dot-path family
          (`"."`, `"./."`, `Path(".")`) is TRUTHY yet collapses onto cwd
          (`cwd / Path(".") == cwd`); it is exercised explicitly below as the
          boundary where the two diverge, so this evidence is non-vacuous and the
          published claim is faithful (no false universal). No tested F2P/P2P
          input is a bare dot, so the soundness chain (verify => resolved) is
          unaffected;
        - truthiness of the raw entry (`bool(entry)`) is exactly is_present:
          "" is falsy; every non-empty str and every Path is truthy.

Imports nothing repo-specific beyond a faithful inline copy of the unchanged
`to_path` / `is_django_path` (both are 3-line helpers; reproduced verbatim with
provenance). Exit 0 iff every obligation holds.
"""
import random
import sys
from pathlib import Path


# --- faithful copies of the unchanged repo helpers (provenance in mapping.md) -

def to_path(value):
    """Verbatim from django/utils/_os.py:56-62 (unchanged by the gold patch)."""
    if isinstance(value, Path):
        return value
    elif not isinstance(value, str):
        raise TypeError("Invalid path type: %s" % type(value).__name__)
    return Path(value)


# A stand-in framework root for is_django_path. The real callee uses
# Path(django.__file__).parent; the contract the proof consumes is only
# determinism + Boolean-ness, so any fixed root exercises that faithfully.
_FRAMEWORK_ROOT = Path("/usr/lib/python3/dist-packages/django")


def is_django_path(path):
    """Faithful copy of django/utils/autoreload.py:54-56 (unchanged callee),
    with the framework root pinned to a constant for the determinism check."""
    return _FRAMEWORK_ROOT in Path(path).parents


# --- the checks --------------------------------------------------------------

# The dot-path family: TRUTHY entries that nonetheless normalize onto cwd. These
# are the documented boundary where truthiness and "joins to a distinct location"
# DIVERGE. We assert they collapse onto the base (so we do NOT publish the false
# universal "every truthy entry is distinct from the base"). NONE of the F2P/P2P
# tested inputs is a bare dot, so the soundness chain is unaffected; this corpus
# entry only keeps the published evidence faithful and non-vacuous.
DOT_PATHS = [".", "./.", "././.", "./"]


def check_empty_entry_collapse(entry_str):
    """LOAD-BEARING UNIVERSAL: the empty entry collapses onto the base, and is
    falsy (modeled as token 0). Checked on every empty entry the corpus emits."""
    cwd = Path.cwd()
    joined = cwd / to_path(entry_str)
    assert entry_str == "", "check_empty_entry_collapse expects the empty entry"
    assert joined == cwd, (
        "empty-entry collapse broken: cwd / to_path('') = %r != cwd %r"
        % (joined, cwd))
    # model: is_present("") is False  <->  bool("") is False
    assert not bool(entry_str), "empty entry must be falsy"


def check_present_distinct_on_tested(entry_str):
    """SCOPED (NOT a universal): on the configured/tested entries, a present
    (non-empty, non-dot) entry joins to a distinct, non-base location. Asserted
    ONLY on the configured/tested corpus, never of arbitrary truthy strings."""
    cwd = Path.cwd()
    joined = cwd / to_path(entry_str)
    assert bool(entry_str), "a configured present entry must be truthy"
    assert joined != cwd, (
        "configured present entry %r should be distinct from base: "
        "joined=%r cwd=%r" % (entry_str, joined, cwd))


def check_dot_path_truthy_but_collapses(entry):
    """BOUNDARY: a dot-path entry is TRUTHY yet collapses onto cwd, so
    truthiness != "joins to a distinct location". This is exactly the case the
    false universal would over-claim; we assert the real behaviour so the
    published claim stays faithful (and the evidence is non-vacuous)."""
    cwd = Path.cwd()
    joined = cwd / to_path(entry)
    assert bool(entry), "a dot-path entry must be truthy (truthiness diverges)"
    assert joined == cwd, (
        "dot-path %r expected to collapse onto base but did not: joined=%r "
        "cwd=%r" % (entry, joined, cwd))


def check_path_entry_present(rel):
    """A non-dot Path entry (always truthy) is a present, distinct location.
    Scoped to the tested Path inputs, not asserted of arbitrary Path values."""
    cwd = Path.cwd()
    p = Path(rel)
    joined = cwd / to_path(p)
    assert bool(p), "a Path entry must be truthy"
    assert joined != cwd, (
        "Path entry %r should be distinct from base: %r" % (p, joined))


def check_predicate_axiom(path_str):
    """beneath_framework <-> is_django_path: deterministic Boolean of the entry
    (the ONLY property the proof consumes; the axiom carries no value Ensures)."""
    o1 = is_django_path(path_str)
    o2 = is_django_path(path_str)
    assert isinstance(o1, bool), (
        "is_django_path must return bool, got %r on %r" % (type(o1), path_str))
    assert o1 == o2, (
        "is_django_path nondeterministic on %r: %r vs %r" % (path_str, o1, o2))


def main():
    # --- empty-entry collapse (LOAD-BEARING universal) -----------------------
    check_empty_entry_collapse("")

    # --- present-entry distinctness on the configured/tested entries ---------
    # (the F2P/P2P inputs: relative/absolute path strings; none a bare dot)
    boundary_present = [
        "templates",
        "template_tests/relative_str",
        "/absolute/templates_dir",
        "a",
        "x/y/z",
        "dir with spaces",
        "templates_extra",
        "./already_dotted",
        "../up_one",
    ]
    for s in boundary_present:
        check_present_distinct_on_tested(s)

    # --- BOUNDARY: dot-path family is TRUTHY yet collapses onto cwd -----------
    # Exercises exactly where truthiness != "joins to a distinct location", so
    # the published evidence is non-vacuous and asserts no false universal.
    # (Path('.') as a Path-typed entry is covered too.)
    for d in DOT_PATHS:
        check_dot_path_truthy_but_collapses(d)
    assert Path.cwd() / to_path(Path(".")) == Path.cwd(), (
        "Path('.') entry expected to collapse onto base")
    assert bool(Path(".")), "Path('.') is truthy"

    # Path-typed entries (non-dot, always truthy -> present, distinct)
    for rel in ["template_tests/relative_path", "p", "deep/nested/dir"]:
        check_path_entry_present(rel)

    # --- randomized fuzz: empty entry collapses; non-dot present is distinct -
    rng = random.Random(15572)
    parts = ["a", "b", "templates", "x", "y", "z", "dir", "tpl", "sub", "9"]
    for _ in range(20000):
        if rng.random() < 0.15:
            check_empty_entry_collapse("")           # the empty entry
        else:
            n = rng.randint(1, 4)
            s = "/".join(rng.choice(parts) for _ in range(n))
            check_present_distinct_on_tested(s)

    # --- is_django_path predicate axiom: deterministic Boolean ---------------
    pred_inputs = [
        "/usr/lib/python3/dist-packages/django/forms/templates",
        "/home/user/project/templates",
        "templates", "", "/", "a/b/c",
        str(_FRAMEWORK_ROOT / "contrib" / "admin"),
    ]
    for _ in range(2000):
        n = rng.randint(0, 4)
        pred_inputs.append("/".join(rng.choice(parts) for _ in range(n)))
    for p in pred_inputs:
        check_predicate_axiom(p)

    print("G-AX OK: empty-entry collapse (cwd/to_path('')==cwd) validated "
          "universally (1 boundary + ~3000 fuzz empties); present-entry "
          "distinctness validated on %d configured/tested + ~17000 fuzz "
          "non-dot entries (scoped, NOT a universal); dot-path family "
          "(%d str + Path('.')) confirmed TRUTHY-yet-collapsing (boundary where "
          "truthiness != distinctness, so no false universal is published); "
          "is_django_path deterministic Boolean on %d inputs"
          % (len(boundary_present), len(DOT_PATHS), len(pred_inputs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
