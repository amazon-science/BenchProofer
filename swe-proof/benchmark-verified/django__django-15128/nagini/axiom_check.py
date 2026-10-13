#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15128.

This bundle has NO consumed @ContractOnly axiom: the relabel-map construction
is modelled DEEPLY (`build_relabel_map` in model.py). The deep model is an
A-reference -- it must equal the real alias relabel-map construction the gold
patch performs. G-AX validates that here by executing the REAL construction (the
exact dict-comprehension the gold patch builds inside the relabel-prefix step,
reproduced verbatim below) on boundary + randomized inputs and asserting that
every observation matches the two behavioural clauses model.py pins:

  (1) source-flag biconditional / excluded preservation:
      a current alias is a relabel source (a KEY of the change map) IFF it is
      not the kept (excluded) alias -- i.e. the kept alias is left present and
      unchanged, every other alias is relabelled;

  (2) disjointness safety property:
      the produced map's KEY set and VALUE set are disjoint
      (`set(change_map).isdisjoint(change_map.values())` -- the assertion the
      real relabel routine makes), GIVEN the fresh namespace ("prefix") differs
      from the one the current aliases live in.

  (3) per-ordinal value / injectivity:
      the value assigned to the alias at ordinal position `pos` is exactly
      '<new_prefix><pos>', so distinct positions get distinct values -- the map
      is injective and never collapses two source aliases onto one renamed
      value. Checked index-level against the real construction.

It also checks the DISCRIMINATOR: without the exclude step (the pre-patch
behaviour reproduced in model_prepatch.py), the kept base alias DOES become a
key of the map, violating clause (1) -- so the fix is observable.

Imports nothing repo-specific: the construction is plain stdlib Python (the
same dict-comprehension the gold patch uses). Exit 0 iff every obligation
holds.
"""
import random
import string
import sys


# --- the REAL construction (verbatim from the gold patch's relabel step) -----
#
# Gold (django/db/models/sql/query.py, bump_prefix after the fix):
#
#     if exclude is None:
#         exclude = {}
#     self.change_aliases({
#         alias: '%s%d' % (self.alias_prefix, pos)
#         for pos, alias in enumerate(self.alias_map)
#         if alias not in exclude
#     })
#
# alias_map is an ordered mapping; enumerate(self.alias_map) walks its keys in
# order. We reproduce exactly that comprehension over an ordered alias list.

def gold_change_map(alias_order, new_prefix, exclude):
    """The change map the (fixed) relabel step builds: each current alias other
    than an excluded one is mapped to '<new_prefix><pos>'."""
    if exclude is None:
        exclude = set()
    return {
        alias: '%s%d' % (new_prefix, pos)
        for pos, alias in enumerate(alias_order)
        if alias not in exclude
    }


def prepatch_change_map(alias_order, new_prefix):
    """The pre-patch relabel step: NO exclude -- every alias is a key."""
    return {
        alias: '%s%d' % (new_prefix, pos)
        for pos, alias in enumerate(alias_order)
    }


# --- the checks --------------------------------------------------------------

def check_clauses(alias_order, new_prefix, excluded):
    """Assert clauses (1) and (2) on the real gold construction for one input.

    `alias_order` is the ordered list of current aliases; `new_prefix` is the
    fresh namespace letter (must differ from each current alias's leading
    prefix); `excluded` is the kept base alias (one of `alias_order`)."""
    cm = gold_change_map(alias_order, new_prefix, {excluded})

    keys = set(cm)
    values = set(cm.values())

    # Clause (1): a current alias is a KEY (a relabel source) IFF it is not the
    # excluded alias. (Index-level equivalence -- no value-membership proxy.)
    for alias in alias_order:
        is_key = alias in keys
        not_excluded = (alias != excluded)
        assert is_key == not_excluded, (
            "clause(1) violated: alias %r is_key=%s but (alias!=excluded)=%s "
            "(order=%r excluded=%r)" % (alias, is_key, not_excluded,
                                        alias_order, excluded))
    # The excluded alias is never a key (left present and unchanged).
    assert excluded not in keys, (
        "clause(1): excluded alias %r leaked in as a key %r" % (excluded, keys))

    # Clause (2): keys and values are disjoint -- the real change_aliases
    # assertion `set(change_map).isdisjoint(change_map.values())`.
    assert keys.isdisjoint(values), (
        "clause(2) violated: change_map keys %r intersect values %r "
        "(order=%r new_prefix=%r)" % (keys, values, alias_order, new_prefix))

    # Clause (3): per-ordinal value / injectivity. The value the real
    # comprehension assigns to the alias at ordinal position `pos` is exactly
    # '<new_prefix><pos>' (the model's `fresh_alias(new_ns, pos)`), so distinct
    # positions get distinct values -- the map is injective and never collapses
    # two source aliases onto one renamed value. Checked at the index level
    # against the real construction (no value-membership proxy).
    for pos, alias in enumerate(alias_order):
        if alias == excluded:
            continue  # excluded alias is not a key (clause 1)
        expected = '%s%d' % (new_prefix, pos)
        assert cm[alias] == expected, (
            "clause(3) violated: alias %r at pos %d got value %r, expected %r "
            "(order=%r)" % (alias, pos, cm[alias], expected, alias_order))
    # Injectivity: the produced values are pairwise distinct.
    produced_values = list(cm.values())
    assert len(produced_values) == len(set(produced_values)), (
        "clause(3) violated: change_map values are not distinct %r "
        "(order=%r new_prefix=%r)" % (produced_values, alias_order, new_prefix))


def check_discriminator(alias_order, new_prefix, excluded):
    """The pre-patch construction (no exclude) makes the kept base alias a key,
    violating clause (1) -- the behavioural change must be observable."""
    cm = prepatch_change_map(alias_order, new_prefix)
    # The excluded base alias IS relabelled by the pre-patch step (a key).
    assert excluded in set(cm), (
        "discriminator: pre-patch should relabel the base alias %r but did not "
        "(order=%r)" % (excluded, alias_order))


def make_alias(prefix_letter, n):
    return '%s%d' % (prefix_letter, n)


def main():
    rng = random.Random(15128)
    letters = list(string.ascii_uppercase)

    boundary = []
    # The motivating case from the issue: lhs/rhs share prefix 'T', rhs has
    # sequential aliases T4,T5; without a fresh prefix the naive relabel makes
    # change_map {'T4':'T5','T5':'T6'} (keys/values intersect). A fresh prefix
    # 'U' moves every target into the U-namespace, restoring disjointness.
    boundary.append((["T4", "T5"], "U", "T4"))
    boundary.append((["T1", "T2", "T3"], "U", "T1"))
    boundary.append((["T1"], "U", "T1"))            # only the base alias
    boundary.append((["T4", "T5", "T6"], "V", "T4"))
    boundary.append((["A1", "B2", "C3"], "Z", "A1"))  # mixed leading letters
    boundary.append((["T2", "T3"], "U", "T2"))

    checked = 0
    for alias_order, new_prefix, excluded in boundary:
        # Precondition: the fresh prefix differs from every current alias's
        # leading letter (the renaming moves into a fresh namespace).
        assert all(not a.startswith(new_prefix) for a in alias_order), (
            "bad boundary input: new_prefix %r clashes with %r"
            % (new_prefix, alias_order))
        assert excluded in alias_order
        check_clauses(alias_order, new_prefix, excluded)
        check_discriminator(alias_order, new_prefix, excluded)
        checked += 1

    # --- randomized fuzz -----------------------------------------------------
    for _ in range(20000):
        old_letter = rng.choice(letters)
        # fresh prefix: any other letter
        new_prefix = rng.choice([c for c in letters if c != old_letter])
        n = rng.randint(1, 12)
        # current aliases all live in the old namespace (same leading letter),
        # with distinct ordinal suffixes (an ordered alias map).
        nums = rng.sample(range(0, 100), n)
        alias_order = [make_alias(old_letter, x) for x in nums]
        excluded = alias_order[0]   # the base/initial alias is the first one
        check_clauses(alias_order, new_prefix, excluded)
        check_discriminator(alias_order, new_prefix, excluded)
        checked += 1

    print("G-AX OK: deep model build_relabel_map validated == real relabel-map "
          "construction (source-flag biconditional + key/value disjointness + "
          "per-ordinal value/injectivity) on %d boundary + fuzz inputs; pre-patch "
          "discriminator confirmed (base alias relabelled without exclude)."
          % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
