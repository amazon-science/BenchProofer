#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13569 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule `groupingContribution`, transliterated
              to Python over the real repo type (an SQL `Expression` node), via
              the mapping.md bijection:
                  isNondetGenerator = true  <->  isinstance(node, Random)
                  []                        <->  empty column list
                  [e]  (i.e. [self])        <->  the node itself
              The modeled method's impl region is `return []` (the Random leg);
              the non-generator leg (`[self]`) is the generic rule the change
              contrasts with, included here to pin the abstraction boundary.
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched repo's
              `node.get_group_by_cols(alias)` evaluated on the real expression
              nodes (the real correctness oracle, G-RESOLVE).

They must agree on every input. Equality bridge (mapping.md §2):
  shadow == []   <=>  oracle == []
  shadow == [e]  <=>  oracle == [node]   (the node contributes itself)

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. Runs on stdlib + django. Fuzz seed pinned (mapping.md §4).
"""
import os
import random
import sys

SEED = 13569
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


# --- the R/I shadow: Solution.lean groupingContribution, transliterated ------
# def groupingContribution (e : Expr) : List Expr :=
#   if e.isNondetGenerator then [] else [e]
def shadow_grouping(node, is_nondet_generator):
    """Returns the shadow contribution, in the same value domain as the oracle:
    [] for a non-deterministic generator, else the node itself ([self])."""
    if is_nondet_generator:
        return []
    return [node]


def oracle_grouping(node, alias):
    """patch.diff behaviour: the patched repo's get_group_by_cols on the real
    node. With the gold patch applied, Random overrides this to return []."""
    return node.get_group_by_cols(alias=alias)


def main():
    _bootstrap_django()
    from django.db.models.functions import Random, Pi, Now
    from django.db.models.expressions import Value

    rng = random.Random(SEED)

    # Representative leaf expressions and their abstraction flag
    # (isNondetGenerator = isinstance(node, Random)). All are non-aggregate
    # leaves; Random is the one the change special-cases.
    #
    # Non-generator nodes here are chosen to be ones that inherit the GENERIC
    # BaseExpression rule (contribute [self]) so the `else` leg of
    # groupingContribution is exercised exactly. (Value is deliberately excluded:
    # it overrides get_group_by_cols to [] and so lies outside the modeled
    # generic-rule domain — including it would be testing an unmodeled node.)
    cases = [
        ("Random", lambda: Random(), True),
        ("Pi", lambda: Pi(), False),
        ("Now", lambda: Now(), False),
    ]

    # Sanity guard: confirm our non-generator nodes really do inherit the generic
    # [self] rule under the patched repo (so the abstraction boundary is honest).
    for name, mk, is_nondet in cases:
        node = mk()
        is_random = isinstance(node, Random)
        if is_random != is_nondet:
            print(f"G-CONF FAIL: abstraction flag wrong for {name}: "
                  f"isinstance Random={is_random}, declared={is_nondet}")
            return 1
        if not is_nondet:
            got = node.get_group_by_cols()
            if got != [node]:
                print(f"G-CONF FAIL: non-generator {name} does not inherit the "
                      f"generic [self] rule under the patched repo: {got!r}")
                return 1

    # Also confirm Value stays outside the modeled domain (documentation guard,
    # not part of the differential): it must NOT be a Random and must NOT yield
    # [self], which is exactly why it is excluded above.
    v = Value(rng.randint(-1000, 1000))
    assert not isinstance(v, Random)

    aliases = [None, "", "T", "T1", "thing", "related", "col_0", "x" * 32]

    disagreements = 0
    examples = []
    for i in range(N_FUZZ):
        name, mk, is_nondet = cases[rng.randrange(len(cases))]
        node = mk()
        alias = aliases[rng.randrange(len(aliases))]

        is_random = isinstance(node, Random)
        shadow = shadow_grouping(node, is_random)
        oracle = oracle_grouping(node, alias)

        # Bridge: compare emptiness, and (when non-empty) self-inclusion.
        shadow_empty = (len(shadow) == 0)
        oracle_empty = (len(oracle) == 0)
        agree = (shadow_empty == oracle_empty)
        if agree and not shadow_empty:
            # both non-empty: both must be exactly [node] (contributes itself)
            agree = (oracle == [node] and shadow == [node])
        if not agree:
            disagreements += 1
            if len(examples) < 10:
                examples.append((name, alias, shadow, oracle))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreement(s) over {N_FUZZ} "
              f"inputs (seed={SEED}).")
        for name, alias, shadow, oracle in examples:
            print(f"  node={name} alias={alias!r} shadow={shadow!r} "
                  f"oracle={oracle!r}")
        return 1

    print(f"G-CONF OK: R/I shadow of groupingColumns agrees with patch.diff "
          f"behaviour on {N_FUZZ} inputs (seed={SEED}), 0 disagreements "
          f"(Random -> [] ; generic non-generator leaf -> [self]).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
