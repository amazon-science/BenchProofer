#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16263.

Validates the one kind-A obligation of this bundle — the **A-reference** deep
model `referencedNames` (Solution.lean `pure` region) against the REAL callee
added by the patch: `BaseExpression.get_refs` / `Ref.get_refs` (and, by the same
union pattern, `WhereNode.get_refs`).

The patch adds:

    # Ref.get_refs:             return {self.refs}
    # BaseExpression.get_refs:  refs = set()
    #                           for expr in self.get_source_expressions():
    #                               refs |= expr.get_refs()
    #                           return refs

The model encodes:

    referencedNames (reference s)   = [s]
    referencedNames (composite es)  = ⋃ referencedNames eᵢ      (concat; set-eq)

We build real Django expression trees mirroring the model's `Expr`
(reference ↦ Ref(alias, source); composite ↦ a Func combining the children),
run the REAL `get_refs`, and assert `set(referencedNames(model)) ==
real_expr.get_refs()` over boundary trees + randomized fuzz trees.

`get_refs` is a method ADDED by the gold patch (it does not exist at
base_commit), so the real callee only exists once the patch is applied. The
G-AX harness does NOT apply the gold patch for us (unlike G-CONF), so this
script applies the gold patch (mounted read-only at /work/patch.diff) to
/testbed itself before importing Django. The deep model `referencedNames` is
then validated against the genuine patched `get_refs`. (This is the one place
the deep model is actually exercised: G-CONF shares the real `get_refs` result
between its shadow and oracle, so the model↔callee equality is G-AX's job.)

Runs in-container against /testbed (PYTHONPATH=/testbed, non-editable repo).
Imports only Django (the same package the gold patch lives in) + stdlib. Exit 0
iff every obligation holds.
"""
import os
import random
import subprocess
import sys

SEED = 16263
N_FUZZ = 20_000
MAX_DEPTH = 4
MAX_CHILDREN = 4
NAME_POOL = ["a", "b", "c", "authors_count", "name_lower", "__count", "x1", "y2"]

GOLD_PATCH = "/work/patch.diff"


def _apply_gold_patch():
    """Apply the gold patch to /testbed so the patch-added `get_refs` exists.
    Idempotent-tolerant: if the tree is already patched (the harness changed
    behaviour), `git apply --check` short-circuits without erroring."""
    if not os.path.exists(GOLD_PATCH):
        print(f"G-AX ERROR: gold patch not found at {GOLD_PATCH}")
        sys.exit(2)
    # Skip if already applied (reverse-applies cleanly => already present).
    already = subprocess.run(
        ["git", "apply", "--reverse", "--check", GOLD_PATCH],
        cwd="/testbed", capture_output=True, text=True,
    )
    if already.returncode == 0:
        return  # patch already in place
    r = subprocess.run(
        ["git", "apply", GOLD_PATCH],
        cwd="/testbed", capture_output=True, text=True,
    )
    if r.returncode != 0:
        print(f"G-AX ERROR: could not apply gold patch:\n{r.stderr}")
        sys.exit(2)


def _setup_django():
    """Minimal settings so expression objects can be constructed. get_refs is a
    pure tree walk; no database connection is needed."""
    sys.path.insert(0, "/testbed")
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


# ---- model.py reference (kept in lock-step with Solution.lean) --------------

def model_referenced_names(node):
    """referencedNames / referencedNamesList transliterated. `node` is
    ('ref', name) or ('comp', [children]). Returns a list (compared as a set)."""
    kind = node[0]
    if kind == "ref":
        return [node[1]]
    out = []
    for ch in node[1]:
        out.extend(model_referenced_names(ch))
    return out


# ---- real Django expression construction ------------------------------------

def build_real(node, Ref, Value, Func):
    """Build a real Django Expression tree isomorphic to `node`."""
    kind = node[0]
    if kind == "ref":
        # Ref(refs, source): the only node get_refs reports a name for.
        return Ref(node[1], Value(1))
    children = [build_real(ch, Ref, Value, Func) for ch in node[1]]
    if not children:
        # A composite with no children: a leaf expression with no refs
        # (BaseExpression.get_refs over empty source expressions => set()).
        return Value(1)
    # Func is a generic Expression whose source expressions are exactly
    # `children` (any arity ≥ 1, unlike Coalesce which demands ≥ 2), so
    # BaseExpression.get_refs unions over them — the composite case.
    return Func(*children, function="F")


def rand_tree(rng, depth):
    if depth <= 0 or rng.random() < 0.5:
        return ("ref", rng.choice(NAME_POOL))
    k = rng.randint(0, MAX_CHILDREN)
    return ("comp", [rand_tree(rng, depth - 1) for _ in range(k)])


def boundary_trees():
    return [
        ("ref", "authors_count"),
        ("ref", "__count"),
        ("comp", []),                                   # no refs
        ("comp", [("ref", "a")]),                       # single ref
        ("comp", [("ref", "a"), ("ref", "b")]),         # two refs
        ("comp", [("ref", "a"), ("ref", "a")]),         # duplicate (set-eq)
        ("comp", [("comp", [("ref", "a")]), ("ref", "b")]),  # nested
        ("comp", [("comp", []), ("comp", [])]),         # nested empties
        ("comp", [("ref", "x1"), ("comp", [("ref", "y2"), ("ref", "a")])]),
    ]


def main():
    _apply_gold_patch()
    _setup_django()
    from django.db.models.expressions import Ref, Value, Func

    # The real get_refs must exist (it is what the patch adds). After applying
    # the gold patch above it must be present; if not, the patch did not take
    # effect => fail loudly rather than silently validate nothing.
    if not hasattr(Ref, "get_refs") or not hasattr(Value, "get_refs"):
        print("G-AX FAIL: real get_refs not present after applying gold patch")
        return 1

    rng = random.Random(SEED)
    checks = 0
    trees = boundary_trees() + [rand_tree(rng, MAX_DEPTH) for _ in range(N_FUZZ)]
    for node in trees:
        expected = set(model_referenced_names(node))
        real_expr = build_real(node, Ref, Value, Func)
        got = set(real_expr.get_refs())
        if got != expected:
            print(f"G-AX FAIL: referencedNames mismatch on {node!r}: "
                  f"model={sorted(expected)} real={sorted(got)}")
            return 1
        checks += 1

    print(f"G-AX OK: referencedNames deep model == real get_refs on "
          f"{len(boundary_trees())} boundary + {N_FUZZ} fuzz trees "
          f"({checks} checks, seed={SEED}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
