#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-9658.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types (`str`). `renderReference`
              selects among the renderer's FOUR rules on the module path and
              places the reported simple name in the trailing position; the
              reported simple name IS the creation name (A3).
  * ORACLE  — `patch.diff`'s behaviour: the patched repo's real
              `sphinx.util.typing.restify` applied to a real stand-in placeholder
              object built exactly as the mock machinery builds it — a
              `_MockObject` subclass instance produced by `_make_subclass`, which
              is literally the call `_MockModule.__getattr__` /
              `_MockObject.__getattr__` make when an attribute is walked under
              `mock([...])`, the same path the F2P test `test_restify_mock`
              exercises. The harness applies patch.diff before this runs, so the
              imported `restify`/mock reflect the gold fix.

The check runs TWO oracle constructors and cross-validates them:

  * `oracle_by_walk`  — `mock([root])` + attribute access, the literal F2P path.
    It can only produce module paths *prefixed by an importable-as-mock root*, so
    it cannot reach a module path that names an already-imported real module.
  * `oracle_direct`   — `_make_subclass(created_name, module_path)()`, the same
    constructor the walk reaches internally, which can realise ANY module path
    including the ones the renderer reserves (`__builtin__`, `builtins`,
    `typing`). Every input the walk *can* realise is checked against the direct
    constructor too, so the direct constructor is not taken on trust.

Reaching the reserved module paths matters: the renderer dispatches on the module
path BEFORE it reads the trailing name, so a shadow fuzzed only over fresh
unique roots exercises exactly one of the four rules and is blind to the other
three. The fuzz distribution below draws the reserved paths and the reserved
simple name with real weight, and the run prints its per-rule hit counts so a
zero-coverage rule is visible rather than silent.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import importlib
import random
import string
import sys

SEED = 9658
N_FUZZ = 100_000

# Identifier alphabets for fuzzing module paths / names. Python attribute names
# (the way mock subobjects are reached, `unknown.secret.Class`) are valid
# identifiers, so restrict to identifier characters.
_FIRST = string.ascii_letters + "_"
_REST = string.ascii_letters + string.digits + "_"

# --- the module paths and the simple name the renderer reserves ---------------
# These mirror Solution.lean's `coreNamespaceA`, `coreNamespaceB`,
# `abbreviatedNamespace` and `aliasFactoryName`.
_CORE_A = "__builtin__"
_CORE_B = "builtins"
_ABBREV = "typing"
_ALIAS_NAME = "NewType.<locals>.new_type"

_OPEN = ":py:class:`"
_CLOSE = "`"
_ELEMENT_LIST_TAIL = "\\ []"
_ABBREV_MARK = "~"


def _ident(rng):
    n = rng.randint(1, 8)
    return rng.choice(_FIRST) + "".join(rng.choice(_REST) for _ in range(n - 1))


# --- the R/I shadow: Solution.lean renderReference, transliterated -----------

def shadow_reference(module_path, created_name):
    """`renderedReference (module_path, created_name)` transliterated to str.

    Four rules, tried in Solution.lean's order — the module path is consulted
    FIRST and the general dotted rule is reached only when the path is none of
    the reserved ones. The reported simple name IS the creation name (A3), and it
    is the trailing segment in every rule."""
    reported_name = created_name                       # reportedName c = c (A3)
    if module_path == _ABBREV and reported_name == _ALIAS_NAME:
        return _OPEN + reported_name + _CLOSE
    elif module_path in (_CORE_A, _CORE_B):
        return _OPEN + reported_name + _CLOSE + _ELEMENT_LIST_TAIL
    elif module_path == _ABBREV:
        return _OPEN + _ABBREV_MARK + module_path + "." + reported_name + _CLOSE
    else:
        return _OPEN + module_path + "." + reported_name + _CLOSE


def shadow_rule(module_path, created_name):
    """Which of the four rules the shadow took, for coverage reporting."""
    if module_path == _ABBREV and created_name == _ALIAS_NAME:
        return "rule1-alias"
    elif module_path in (_CORE_A, _CORE_B):
        return "rule2-core"
    elif module_path == _ABBREV:
        return "rule3-abbrev"
    else:
        return "rule4-general"


# --- the oracles: patched real restify on a real placeholder ------------------

def oracle_direct(module_path, created_name):
    """patch.diff's behaviour: the patched real restify applied to the placeholder
    `_make_subclass(created_name, module_path)()` — the very constructor
    `_MockObject.__getattr__`/`_MockModule.__getattr__` invoke. Realises ANY
    module path, including the reserved ones."""
    from sphinx.ext.autodoc.mock import _make_subclass
    from sphinx.util.typing import restify
    return str(restify(_make_subclass(created_name, module_path)()))


def _build_mock_chain(mod, segments):
    """Reproduce the F2P access pattern: under mock([mod]), import the mocked
    root module and walk `segments` by attribute access, returning the leaf
    placeholder object (a `_MockObject` subclass instance). e.g.
    segments=['secret','Class'] mirrors `unknown.secret.Class`."""
    from sphinx.ext.autodoc.mock import mock
    with mock([mod]):
        obj = importlib.import_module(mod)
        for seg in segments:
            obj = getattr(obj, seg)
        return obj


def oracle_by_walk(mod, segments):
    """patch.diff's behaviour on the leaf placeholder reached by `mod` + the
    attribute walk `segments` — the literal F2P access path."""
    from sphinx.util.typing import restify
    return str(restify(_build_mock_chain(mod, segments)))


def _expected_module_and_name(mod, segments):
    """Derive the (module_path, created_name) the leaf placeholder carries, from
    the access path, matching the mock machinery (mapping.md §1):

      - The root mocked module's __name__ is `mod`.
      - module.__getattr__(s) -> _make_subclass(s, module.__name__) instance, whose
        __display_name__ = mod + '.' + s and __module__ = mod.
      - object.__getattr__(s) -> _make_subclass(s, obj.__display_name__) instance,
        whose __module__ = previous __display_name__ and creation name = s.

    So the leaf's __module__ is the dotted path of all segments EXCEPT the last,
    prefixed by mod; its creation name is the LAST segment."""
    assert segments, "need at least one attribute segment"
    if len(segments) == 1:
        module_path = mod
    else:
        module_path = mod + "." + ".".join(segments[:-1])
    created_name = segments[-1]
    return module_path, created_name


# A fixed, unique root prefix for the walk-reachable inputs. The mock machinery
# only intercepts an import when the requested module is (a descendant of) a name
# passed to `mock([...])`; `importlib.import_module(mod)` for a *bare* random
# identifier that happens to name a real, already-imported stdlib module (e.g.
# `os`, `string`, `time`) returns the REAL module instead of a mock placeholder,
# and the attribute walk then fails on a non-existent attribute. That is a fuzzer
# artifact, NOT a behavioral disagreement: the modeled behavior is restify on
# genuine mock placeholders. We make every random walk root collision-free by
# construction with a prefix that is not a real importable module, so
# `mock([mod])` always installs a fresh placeholder root and the walk yields only
# mock subobjects.
#
# The same property is what makes the walk alone INSUFFICIENT coverage: a leaf's
# module path always begins with its root, so a prefixed root can never produce
# the reserved module paths. Those are fuzzed through `oracle_direct` below.
_ROOT_PREFIX = "mockroot9658_"


def walk_inputs(n, rng):
    """(mod, segments) pairs for the attribute-walk oracle. Always rule 4 by
    construction (the root prefix is not a reserved path), plus the canonical
    boundary cases."""
    yield ("unknown", ["secret", "Class"])     # the F2P test case
    yield ("unknown", ["Class"])               # single segment
    yield ("torch", ["nn", "Module"])          # the issue's example
    yield ("a", ["b", "c", "d", "e"])          # deep chain
    yield ("pkg", ["Sub", "Inner", "Leaf"])
    for _ in range(n):
        mod = _ROOT_PREFIX + _ident(rng)
        depth = rng.randint(1, 5)
        segments = [_ident(rng) for _ in range(depth)]
        yield (mod, segments)


def direct_inputs(n, rng):
    """(module_path, created_name) pairs for the direct-constructor oracle. This
    is the generator that reaches the reserved module paths and the reserved
    simple name, so all four rules are exercised. Boundary cases first."""
    # one canonical input per rule, plus the interesting crossings
    yield (_ABBREV, _ALIAS_NAME)          # rule 1
    yield (_CORE_A, "Class")              # rule 2  (the reviewer's witness)
    yield (_CORE_B, "Class")              # rule 2
    yield (_ABBREV, "Foo")                # rule 3
    yield ("unknown.secret", "Class")     # rule 4
    yield (_CORE_A, _ALIAS_NAME)          # rule 2 wins over the reserved name
    yield (_CORE_B, _ALIAS_NAME)          # rule 2 wins over the reserved name
    yield (_ABBREV, "")                   # rule 3, empty trailing name
    yield (_CORE_B, "")                   # rule 2, empty trailing name
    yield ("", "X")                       # rule 4, empty module path
    yield ("typings", "Class")            # near-miss on the abbreviated path
    yield ("builtin", "Class")            # near-miss on a core path
    yield ("__builtins__", "Class")       # near-miss on a core path
    yield ("a.typing", "Class")           # reserved name only as a SEGMENT
    yield ("a.builtins", "Class")         # reserved name only as a SEGMENT
    yield (_ABBREV, "NewType.<locals>.new_typ")   # near-miss on reserved name
    yield (_ABBREV, "NewType.<locals>.new_types")  # near-miss on reserved name

    reserved_paths = [_CORE_A, _CORE_B, _ABBREV]
    for _ in range(n):
        r = rng.random()
        if r < 0.30:
            # reserved module path: rules 1-3
            module_path = rng.choice(reserved_paths)
        elif r < 0.40:
            # a near-miss on a reserved path, to pin the guards' exact extent
            base = rng.choice(reserved_paths)
            module_path = rng.choice([base + _ident(rng), _ident(rng) + base,
                                      base[:-1], base.upper(),
                                      _ident(rng) + "." + base])
        else:
            module_path = ".".join(_ident(rng) for _ in range(rng.randint(1, 5)))
        if rng.random() < 0.25:
            created_name = _ALIAS_NAME
        elif rng.random() < 0.10:
            created_name = rng.choice([_ALIAS_NAME[:-1], _ALIAS_NAME + "x", ""])
        else:
            created_name = _ident(rng)
        yield (module_path, created_name)


def main():
    rng = random.Random(SEED)
    disagreements = []
    coverage = {"rule1-alias": 0, "rule2-core": 0, "rule3-abbrev": 0,
                "rule4-general": 0}
    count = 0

    # --- leg A: the direct constructor, over all four rules ------------------
    for module_path, created_name in direct_inputs(N_FUZZ, rng):
        count += 1
        coverage[shadow_rule(module_path, created_name)] += 1
        shadow = shadow_reference(module_path, created_name)
        oracle = oracle_direct(module_path, created_name)
        if shadow != oracle:
            disagreements.append(("direct", module_path, created_name,
                                  shadow, oracle))
            if len(disagreements) >= 5:
                break

    # --- leg B: the literal F2P attribute walk, cross-validated -------------
    # Every walk input is checked against BOTH the shadow and the direct
    # constructor, so leg A's constructor is never taken on trust.
    if not disagreements:
        for mod, segments in walk_inputs(N_FUZZ, rng):
            count += 1
            module_path, created_name = _expected_module_and_name(mod, segments)
            coverage[shadow_rule(module_path, created_name)] += 1
            shadow = shadow_reference(module_path, created_name)
            oracle = oracle_by_walk(mod, segments)
            direct = oracle_direct(module_path, created_name)
            if shadow != oracle or direct != oracle:
                disagreements.append(("walk %r %r" % (mod, segments),
                                      module_path, created_name,
                                      "%s / direct=%s" % (shadow, direct),
                                      oracle))
                if len(disagreements) >= 5:
                    break

    print("rule coverage: " + ", ".join("%s=%d" % (k, coverage[k])
                                        for k in sorted(coverage)))
    unhit = [k for k, v in coverage.items() if v == 0]
    if unhit:
        print("G-CONF FAIL: %d rule(s) of the modeled dispatch were never "
              "exercised, so the shadow is untested on them: %s"
              % (len(unhit), ", ".join(sorted(unhit))))
        return 1
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for how, mp, cn, sh, orc in disagreements:
            print("  via=%s module_path=%r created_name=%r shadow=%r oracle=%r"
                  % (how, mp, cn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderReference agrees with patch.diff "
          "behaviour (real restify on mock placeholders) on %d inputs "
          "(seed=%d), 0 disagreements; all four modeled rules exercised."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
