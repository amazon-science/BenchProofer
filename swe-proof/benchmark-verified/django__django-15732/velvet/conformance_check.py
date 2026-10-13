#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15732 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`narrowed` +
              `selectedTarget`, pure region) transliterated to Python over the
              real repo types via the mapping.md bijection (`List String` ↔
              `list[str]`, `Bool` ↔ `bool`, `Option String` ↔ act-on-name /
              raise). There are NO A-tagged callees in the impl region (the
              three helpers are taken as opaque method inputs), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the constraint-selection block of the
              PATCHED `_delete_composed_index` (`django/db/backends/base/
              schema.py:574-590` post-image) transliterated VERBATIM. We
              transliterate rather than drive the real method end-to-end because
              `_delete_composed_index` requires a live `connection`, a built
              `Model._meta`, DB introspection (`_constraint_names`), and the
              name machinery (`_unique_constraint_name`) purely to recover this
              one decision; building that context in-container would not isolate
              the modeled behaviour (same rationale as the astropy-13236
              bundle). The oracle below is the post-image selection logic, with
              the three helper results supplied as the fuzzed inputs — exactly
              the values mapping.md binds them to.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container, stdlib only. Fuzz seed pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 15732
N_FUZZ = 100_000

# A small identifier pool so `canonical ∈ names` collisions occur often.
_IDS = ["t_id_uniq", "t_name_key", "t_id_1c3b_uniq", "t_pkey",
        "t_name_694f_uniq", "a", "b", "c", "d", "default"]


# --- the R/I shadow: Solution.lean narrowed/selectedTarget, transliterated ---
def shadow(names, unique_sel, allow_multiple, canonical):
    """selectedTarget(names, uniqueSel, allowMultiple, canonical) — the impl.

    Returns the chosen identifier (str) when a unique target exists, else None
    (the `none` arm, i.e. the ValueError path). Mirrors the nested `if` of
    `narrowed` followed by the singleton decision of `selectedTarget`."""
    ns = names
    if unique_sel is True and ns != [] and allow_multiple is True:
        if canonical in ns:
            ns = [canonical]
    return ns[0] if len(ns) == 1 else None


# --- the oracle: gold patch.diff selection block, transliterated verbatim -----
def oracle(names, unique_sel, allow_multiple, canonical):
    """The PATCHED `_delete_composed_index` selection logic (schema.py post-image).

        constraint_names = self._constraint_names(...)          # = names
        if (constraint_kwargs.get("unique") is True              # = unique_sel
                and constraint_names                              # truthiness
                and ...allows_multiple_constraints_on_same_fields):  # = allow_multiple
            default_name = str(self._unique_constraint_name(...)) # = canonical
            if default_name in constraint_names:
                constraint_names = [default_name]
        if len(constraint_names) != 1:
            raise ValueError(...)            # -> None (no unique target)
        ...delete constraint_names[0]        # -> constraint_names[0]
    """
    constraint_names = list(names)
    if (unique_sel is True
            and constraint_names
            and allow_multiple is True):
        default_name = canonical
        if default_name in constraint_names:
            constraint_names = [default_name]
    if len(constraint_names) != 1:
        return None
    return constraint_names[0]


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # (names, unique_sel, allow_multiple, canonical)
    yield ([], True, True, "x")                       # empty candidates
    yield (["only"], True, True, "only")              # already singleton, present
    yield (["only"], True, True, "other")             # already singleton, absent
    yield (["a", "b"], True, True, "a")               # two candidates, canonical present -> narrow
    yield (["a", "b"], True, True, "z")               # two candidates, canonical absent -> raise
    yield (["a", "b"], False, True, "a")              # not unique selection -> no narrowing
    yield (["a", "b"], True, False, "a")              # backend disallows multiple -> no narrowing
    yield (["pk", "uniq"], True, True, "uniq")        # the F2P scenario: 2 -> 1
    yield (["a", "a"], True, True, "a")               # dup candidates, canonical present
    yield (["a", "b", "c"], True, True, "b")          # three -> 1
    for _ in range(n):
        k = rng.randint(0, 4)
        names = [rng.choice(_IDS) for _ in range(k)]
        unique_sel = rng.choice([True, False])
        allow_multiple = rng.choice([True, False])
        canonical = rng.choice(_IDS)
        yield (names, unique_sel, allow_multiple, canonical)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for names, u, a, c in fuzz_inputs(N_FUZZ, rng):
        count += 1
        sh = shadow(names, u, a, c)
        orc = oracle(names, u, a, c)
        if sh != orc:
            disagreements.append((names, u, a, c, sh, orc))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for names, u, a, c, sh, orc in disagreements:
            print("  names=%r unique=%r multi=%r canonical=%r shadow=%r oracle=%r"
                  % (names, u, a, c, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of chooseTarget agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
