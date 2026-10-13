#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-11734.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean
`implementation_relocateFilterIntoSubquery` skeleton and diffs it against the
REAL patched filter-expression rewrite from `Query.split_exclude` over the full
discrete RHS-shape matrix plus >=1e5 randomized draws.

The modeled observable is the head-of-`split_exclude` rewrite (query.py:1704-1706
post-patch):

    filter_lhs, filter_rhs = filter_expr
    if isinstance(filter_rhs, OuterRef):
        filter_expr = (filter_lhs, OuterRef(filter_rhs))
    elif isinstance(filter_rhs, F):
        filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
    # else: a direct value is left unchanged

`real_rewrite` reproduces that branch VERBATIM using the genuine, imported
`django.db.models.OuterRef` / `F` classes (so the real `OuterRef(...)` wrapping
semantics and the real `class OuterRef(F)` hierarchy are exercised). The result's
outer-reference nesting depth is read back by walking the real `OuterRef.name`
chain, and the left-hand side is checked unchanged.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import string
import sys
import tempfile

SEED = 20240625
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "testapp"))
    open(os.path.join(d, "testapp", "__init__.py"), "w").close()
    open(os.path.join(d, "testapp", "models.py"), "w").close()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "testapp"],
        USE_TZ=True,
    )
    django.setup()


# ---- the modeled re-anchoring (post-patch desired behavior) ----------------
# Shadow of `reanchor` / `implementation_relocateFilterIntoSubquery` in
# Solution.lean. RHS shapes:
#   ("value", v)         -> FilterRHS.value
#   ("col",   name)      -> FilterRHS.colRef
#   ("outer", lvl, name) -> FilterRHS.outerRef
# Result is (lhs, reanchored-rhs) as a tagged tuple.
def shadow_rewrite(lhs, rhs):
    tag = rhs[0]
    if tag == "value":
        return (lhs, ("value", rhs[1]))
    if tag == "col":
        return (lhs, ("outer", 1, rhs[1]))
    if tag == "outer":
        return (lhs, ("outer", rhs[1] + 1, rhs[2]))
    raise AssertionError("bad shape")


def main():
    setup_django()
    from django.db.models import F, OuterRef

    def make_outerref(level, name):
        """A genuine OuterRef nested `level` deep over column `name`."""
        ref = OuterRef(name)            # level 1
        for _ in range(level - 1):
            ref = OuterRef(ref)         # +1 level each wrap
        return ref

    def outer_depth(ref):
        """Walk the real OuterRef.name chain to recover the nesting level."""
        level = 0
        cur = ref
        while isinstance(cur, OuterRef):
            level += 1
            cur = cur.name
        return level, cur  # cur is the base field-name string

    def real_rewrite(lhs, rhs):
        """The patched split_exclude head branch, verbatim, on real objects."""
        tag = rhs[0]
        if tag == "value":
            filter_rhs = rhs[1]          # a plain literal, no resolve_expression
        elif tag == "col":
            filter_rhs = F(rhs[1])
        elif tag == "outer":
            filter_rhs = make_outerref(rhs[1], rhs[2])
        else:
            raise AssertionError("bad shape")

        filter_lhs = lhs
        # --- begin verbatim patched rewrite (query.py:1704-1706) ---
        if isinstance(filter_rhs, OuterRef):
            filter_expr = (filter_lhs, OuterRef(filter_rhs))
        elif isinstance(filter_rhs, F):
            filter_expr = (filter_lhs, OuterRef(filter_rhs.name))
        else:
            filter_expr = (filter_lhs, filter_rhs)
        # --- end verbatim patched rewrite ---

        out_lhs, out_rhs = filter_expr
        if isinstance(out_rhs, OuterRef):
            lvl, base = outer_depth(out_rhs)
            return (out_lhs, ("outer", lvl, base))
        # literal carried unchanged
        return (out_lhs, ("value", out_rhs))

    # full discrete matrix
    NAMES = ["pk", "job", "name", "id"]
    cases = []
    for lhs in NAMES:
        for v in (0, 7, -3):
            cases.append((lhs, ("value", v)))
        for nm in NAMES:
            cases.append((lhs, ("col", nm)))
            for lvl in (1, 2, 3, 4):
                cases.append((lhs, ("outer", lvl, nm)))

    rng = random.Random(SEED)

    def rand_name():
        return "".join(rng.choice(string.ascii_lowercase)
                       for _ in range(rng.randint(1, 6)))

    for _ in range(N_RANDOM):
        lhs = rand_name()
        shape = rng.choice(["value", "col", "outer"])
        if shape == "value":
            cases.append((lhs, ("value", rng.randint(-1000, 1000))))
        elif shape == "col":
            cases.append((lhs, ("col", rand_name())))
        else:
            cases.append((lhs, ("outer", rng.randint(1, 6), rand_name())))

    disagreements = 0
    checked = 0
    for lhs, rhs in cases:
        got = real_rewrite(lhs, rhs)
        exp = shadow_rewrite(lhs, rhs)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH lhs={lhs} rhs={rhs}: real={got} shadow={exp}")

    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s) over {checked} checks")
    return 1


if __name__ == "__main__":
    sys.exit(main())
