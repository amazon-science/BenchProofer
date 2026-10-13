#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15368 (nagini).

SHADOW: the impl region of `model.py`'s `build_wrap_flags`, copied verbatim
below with the contract calls stripped (the two `Assert(...)` proof hints are
contract calls and are removed; nothing else in the impl region is). The impl
region uses only plain Python lists — no PSeq shim is needed. The @Pure
helpers (`empty_flags`, `wrap_flags`) exist only for the specification and are
not called by the impl, so they are not carried over. There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo logic the model models per mapping.md —
`django.db.models.query.QuerySet.bulk_update`'s inner per-object
classification loop for one column. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable. Because the classification is embedded in a method that goes on
to issue database UPDATEs, the oracle observes the per-object decision
through the real method's own output structure:

  * `QuerySet.update` is stubbed to capture its keyword arguments instead of
    touching the database (per mapping.md the machinery downstream of the
    per-object decision is identity for the observed behaviour);
  * each captured per-batch argument is the `Case` object the real loop
    built; its `cases` list holds, in object order, one `When` per object,
    and `When.result` is exactly the `then=` value the loop chose — the
    object's original attribute value if it was carried through, or a fresh
    wrapper object if it was wrapped as a literal. Object identity
    (`result is not attr`) therefore reads off the real wrap flag: the
    wrapper is always a newly constructed object, never the attribute
    itself, while a carried-through value is passed along unchanged
    (values that reach `When` unwrapped satisfy the capability test that
    `When`'s own argument normalisation applies, so it keeps them as-is);
  * flags are concatenated across the captured batches in call order, which
    preserves object order even when the input crosses the backend's
    batch-size limit.

Type bridge (mapping.md "Type abstraction"): each real attribute value is
abstracted to the two booleans the model carries —
`in_family = isinstance(attr, Expression)` and
`resolvable = hasattr(attr, 'resolve_expression')` — aligned per object.
The model's Requires (equal lengths; in_family[i] ==> resolvable[i]) holds
by construction: both bits derive from the same real value and the class
hierarchy guarantees the implication (audited by axiom_check.py / G-AX).
Outputs compare with == on List[bool].

Input domain: batches of real attribute values drawn from all three
reachable (in_family, resolvable) cells —
  (F, F) plain Python data (str, int, None, float, bool, bytes),
  (F, T) capability-carrying non-members (F, plus a minimal duck object),
  (T, T) family members (Value, CombinedExpression).
Boundary cases: the empty batch, every cell-pattern batch of length 1..3
exhaustively (39 batches), homogeneous batches, and one 700-object batch
that crosses the sqlite backend batch-size limit (multi-batch order check).
Fuzz: random batches of length 0..12 over the full pool.

>= 1e5 Requires-satisfying per-object inputs: 40 boundary batches +
25000 fuzz batches with total object count >= 100000 (padded if the draw
falls short). Pinned fuzz seed: 15368.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the repo under test) only.
"""
import random
import json
import sys

SEED = 15368
N_FUZZ_BATCHES = 25_000
MIN_OBJECTS = 100_000


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def build_wrap_flags(in_family, resolvable):
    result = []  # type: list
    i = len(resolvable)
    while i > 0:
        attr_resolvable = resolvable[i - 1]
        if not attr_resolvable:
            result = [True] + result
        else:
            result = [False] + result
        i = i - 1
    return result


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
        )
        django.setup()
    from django.contrib.auth.models import User
    from django.db.models.query import QuerySet
    from django.db.models.expressions import Expression, F, Value

    # --- oracle plumbing ------------------------------------------------------

    captured = []
    orig_update = QuerySet.update

    def capture_update(self, **kwargs):
        captured.append(kwargs)
        return 0

    class Duck:
        """A capability-carrying value that is NOT a family member — the
        model's (in_family=False, resolvable=True) cell witnessed by a value
        outside the one concrete family F also occupies."""
        def resolve_expression(self, *args, **kwargs):
            return self

        def __repr__(self):
            return "Duck()"

    def real_flags(attrs):
        """Run the REAL patched bulk_update over objects carrying `attrs` on
        one column; read back, in object order, whether each value was
        wrapped (True) or carried through (False)."""
        del captured[:]
        objs = []
        for i, a in enumerate(attrs):
            u = User(pk=i + 1, username="u%d" % i)
            u.first_name = a
            objs.append(u)
        User.objects.bulk_update(objs, ["first_name"])
        flags = []
        idx = 0
        for kwargs in captured:
            case = kwargs["first_name"]
            for w in case.cases:
                # identity: carried-through iff the then= value IS the
                # original attribute object
                flags.append(w.result is not attrs[idx])
                idx += 1
        if idx != len(attrs):
            return None  # object-count mismatch: itself a disagreement signal
        return flags

    def shadow_flags(attrs):
        """Bridge each real value to the model's two booleans, then run the
        contract-stripped impl region."""
        in_family = [isinstance(a, Expression) for a in attrs]
        resolvable = [hasattr(a, 'resolve_expression') for a in attrs]
        # the model's Requires must hold of the bridged input
        assert len(in_family) == len(resolvable)
        for f_bit, r_bit in zip(in_family, resolvable):
            assert (not f_bit) or r_bit, "hierarchy precondition violated"
        return build_wrap_flags(in_family, resolvable)

    def check_case(attrs):
        shadow_out = shadow_flags(attrs)
        real_out = real_flags(attrs)
        if shadow_out != real_out:
            return ("DISAGREEMENT\n  attrs=%r\n  shadow=%r\n  real=%r"
                    % (attrs, shadow_out, real_out))
        return None

    # --- input pools (all three reachable cells) ------------------------------

    def plain_pool():
        return ["test_note", "", "some text", 0, 1, 42, -7, None, 3.14, True,
                False, b"x"]

    def nonfam_pool():
        return [F('last_name'), F('username'), F('email'), Duck()]

    def family_pool():
        return [Value('x'), Value(1), Value(None),
                F('last_name') + 1, F('username') * 2]

    full_pool = plain_pool() + nonfam_pool() + family_pool()
    # one representative per cell, for the exhaustive small-batch patterns
    cell_reps = ["plain", F('last_name'), Value('x')]

    QuerySet.update = capture_update
    checked_batches = 0
    checked_objects = 0
    try:
        # --- boundary batches -------------------------------------------------
        boundary = [[]]                                     # empty batch
        for a in cell_reps:                                 # length 1: 3
            boundary.append([a])
        for a in cell_reps:                                 # length 2: 9
            for b in cell_reps:
                boundary.append([a, b])
        for a in cell_reps:                                 # length 3: 27
            for b in cell_reps:
                for c in cell_reps:
                    boundary.append([a, b, c])

        rng = random.Random(SEED)
        for attrs in boundary:
            err = check_case(attrs)
            if err:
                print(err)
                return 1
            checked_batches += 1
            checked_objects += len(attrs)

        # homogeneous + limit-crossing batches (700 objects on one column
        # exceeds the sqlite variable limit, forcing multiple real batches)
        extra = [
            [x for x in plain_pool()],
            [F('last_name')] * 10,
            [Duck() for _ in range(10)],
            [Value(i) for i in range(10)],
            [rng.choice(full_pool) for _ in range(700)],
        ]
        for attrs in extra:
            err = check_case(attrs)
            if err:
                print(err)
                return 1
            checked_batches += 1
            checked_objects += len(attrs)

        # --- fuzz -------------------------------------------------------------
        for _ in range(N_FUZZ_BATCHES):
            length = rng.randint(0, 12)
            attrs = [rng.choice(full_pool) for _ in range(length)]
            err = check_case(attrs)
            if err:
                print(err)
                return 1
            checked_batches += 1
            checked_objects += len(attrs)

        # pad with mid-size batches until >= 1e5 per-object inputs
        while checked_objects < MIN_OBJECTS:
            attrs = [rng.choice(full_pool) for _ in range(20)]
            err = check_case(attrs)
            if err:
                print(err)
                return 1
            checked_batches += 1
            checked_objects += len(attrs)
    finally:
        QuerySet.update = orig_update

    print("G-CONF OK: shadow impl == real per-object wrap decision on %d "
          "batches / %d objects (seed %d)."
          % (checked_batches, checked_objects, SEED))
    print(json.dumps({"checked_batches": checked_batches,
                      "checked_objects": checked_objects,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
