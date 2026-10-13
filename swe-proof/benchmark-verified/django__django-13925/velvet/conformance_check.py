#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13925 (plan §4.1).

Refutes the R/I refinement legs of refinement.md by executing both sides on the
same fuzzed inputs and comparing observable outputs.

REFINEMENT STRUCTURE:
  The modeled routine `Model._check_default_pk` returns the single advisory
  `models.W042` iff a four-operand boolean guard holds, else `[]`. Each operand
  is a pure, independent boolean observation of the model / its environment
  (mapping.md §2):
      pk_auto_created            <- cls._meta.pk.auto_created
      pk_inherited_from_ancestor <- isinstance(cls._meta.pk, OneToOneField)
                                     and cls._meta.pk.remote_field.parent_link
      default_key_type           <- settings.is_overridden('DEFAULT_AUTO_FIELD')
      app_key_type               <- cls._meta.app_config
                                       ._is_default_auto_field_overridden
  None is a contracted callee, so each is a FREE boolean input here (fuzzed over
  {False, True}). All ops in the impl region are R (bool ↔ Bool, exact) / I (the
  boolean conjunction); there is no A leg. conf_skip=false.

  SHADOW — Solution.lean's `implicitPrimaryKeyAdvisory` post-image
           transliterated: the boolean
             pk_auto_created and (not pk_inherited_from_ancestor)
                             and (not default_key_type)
                             and (not app_key_type)
  ORACLE — the patched guard of `_check_default_pk` transliterated VERBATIM
           (the gold `if (... and not(...) and not ... and not ...)`), reduced
           to "does the guard fire?" i.e. is the returned list the one-element
           W042 advisory (True) or [] (False).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

stdlib only; the fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 13925
N_FUZZ = 100_000


def shadow(pk_auto_created, pk_inherited_from_ancestor,
           default_key_type, app_key_type):
    """implicitPrimaryKeyAdvisory post-image, transliterated to Python:
        pkAutoCreated && !pkInheritedFromAncestor
                      && !defaultKeyTypeConfigured && !appKeyTypeConfigured
    """
    return (pk_auto_created and (not pk_inherited_from_ancestor)
            and (not default_key_type) and (not app_key_type))


def oracle(pk_auto_created, pk_inherited_from_ancestor,
           default_key_type, app_key_type):
    """The patched `_check_default_pk` guard, transliterated VERBATIM from
    django/db/models/base.py (gold patch applied):

        if (
            cls._meta.pk.auto_created and
            not (isinstance(cls._meta.pk, OneToOneField) and
                 cls._meta.pk.remote_field.parent_link) and
            not settings.is_overridden('DEFAULT_AUTO_FIELD') and
            not cls._meta.app_config._is_default_auto_field_overridden
        ):
            return [Warning(... id='models.W042')]   # guard fires -> True
        return []                                    # else        -> False

    The whole `isinstance(...) and ...parent_link` sub-expression is the free
    boolean `pk_inherited_from_ancestor` (mapping.md §2 A2)."""
    if (pk_auto_created
            and not pk_inherited_from_ancestor
            and not default_key_type
            and not app_key_type):
        return True       # the one-element [W042] advisory
    return False          # []


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: all 2^4 = 16 boolean combinations of the four operands.
    combos = list(itertools.product([False, True], repeat=4))
    # Plus seeded fuzz over the same boolean cube.
    combos += [tuple(rng.random() < 0.5 for _ in range(4)) for _ in range(N_FUZZ)]

    for a, b, c, d in combos:
        count += 1
        s = bool(shadow(a, b, c, d))
        o = bool(oracle(a, b, c, d))
        if s != o:
            disagreements.append((a, b, c, d, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of implicitPrimaryKeyAdvisory agrees with the "
          "patched _check_default_pk guard on %d inputs (16 exhaustive + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
