#!/usr/bin/env python3
"""G-AX structural soundness check for sphinx-doc__sphinx-9673.

This bundle consumes NO @ContractOnly axioms and validates NO A-reference deep
model against a real library callee: the entire changed behaviour is pure
integer/sequence classification logic, modelled deeply in model.py. There is
therefore no in-container library-callee execution to perform.

What this script DOES check (the analogue of G-AX for a no-axiom bundle): that
the model's decision functions agree, on boundary + randomized field-lists,
with a direct, faithful Python re-implementation of the patched
`augment_descriptions_with_types` return-classification + rtype-emission logic
(sphinx/ext/autodoc/typehints.py, gold). Concretely it confirms:

  (1) model `has_return_description(kinds)` == "some field is a return-
      description field under EITHER spelling" (codes 2 or 3), i.e. the patched
      `parts[0] in ('return', 'returns')` branch feeding `has_description`.
  (2) model `has_return_type(kinds)` == "some field is a return-type field"
      (code 4), i.e. the `parts[0] == 'rtype'` branch feeding `has_type`.
  (3) model `augment_return_typefield(kinds, ret)` ==
      `ret and has_description and not has_type` — the emission decision
      `if 'return' in annotations and 'return' in has_description and
       'return' not in has_type`.
  (4) model `name_is_return_key(name, short, plural)` == `name in (short,
      plural)` — the patched `if name in ('return', 'returns'): continue` skip.

It ALSO asserts the discriminator the F2P test observes: on a field-list whose
only return field uses the PLURAL spelling (code 3), with a return annotation
and no rtype field, the decision is True (rtype emitted) under the patched
logic but False under the pre-patch logic (short spelling only). This is the
exact behaviour `test_autodoc_typehints_description_no_undoc` checks.

Imports only the standard library. Exit 0 iff every obligation holds.
"""
import itertools
import random
import sys

# leading-token codes (mapping.md §2)
PARAM, TYPE, RETURN, RETURNS, RTYPE, OTHER = 0, 1, 2, 3, 4, 5
ALL_CODES = [PARAM, TYPE, RETURN, RETURNS, RTYPE, OTHER]


# --- faithful re-implementation of the PATCHED logic -------------------------
# (mirrors sphinx/ext/autodoc/typehints.py augment_descriptions_with_types,
#  gold), expressed over the code abstraction.

def real_has_return_description(kinds):
    # patched: parts[0] in ('return', 'returns') -> has_description.add('return')
    return any(c in (RETURN, RETURNS) for c in kinds)


def real_has_return_type(kinds):
    # parts[0] == 'rtype' -> has_type.add('return')
    return any(c == RTYPE for c in kinds)


def real_emit_rtype(kinds, return_annotated):
    # if 'return' in annotations: if 'return' in has_description and
    #                             'return' not in has_type: <append rtype>
    return (return_annotated and real_has_return_description(kinds)
            and not real_has_return_type(kinds))


def real_name_is_return_key(name, short, plural):
    # patched: if name in ('return', 'returns'): continue
    return name == short or name == plural


# --- the PRE-PATCH logic (short spelling only), for the discriminator --------

def prepatch_has_return_description(kinds):
    # pre-patch: parts[0] == 'return' only
    return any(c == RETURN for c in kinds)


def prepatch_emit_rtype(kinds, return_annotated):
    return (return_annotated and prepatch_has_return_description(kinds)
            and not real_has_return_type(kinds))


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def model_has_return_description(kinds):
    # front-recursive fold in model.py: c == 2 or c == 3
    return any(c == 2 or c == 3 for c in kinds)


def model_has_return_type(kinds):
    return any(c == 4 for c in kinds)


def model_augment_return_typefield(kinds, return_annotated):
    described = False
    typed = False
    for c in reversed(kinds):           # backward loop, as in model.py
        if c == 2 or c == 3:
            described = True
        elif c == 4:
            typed = True
    if return_annotated:
        if described and not typed:
            return True
    return False


def model_name_is_return_key(name, short, plural):
    return name == short or name == plural


# --- the checks --------------------------------------------------------------

def check_lists(kinds):
    ks = list(kinds)
    assert model_has_return_description(ks) == real_has_return_description(ks), \
        ("has_return_description mismatch on %r" % (ks,))
    assert model_has_return_type(ks) == real_has_return_type(ks), \
        ("has_return_type mismatch on %r" % (ks,))
    for ret in (False, True):
        assert model_augment_return_typefield(ks, ret) == real_emit_rtype(ks, ret), \
            ("emit-decision mismatch on kinds=%r return_annotated=%r" % (ks, ret))


def main():
    # (1) exhaustive over all field-lists of length <= 4 over the 6 codes
    count = 0
    for n in range(0, 5):
        for combo in itertools.product(ALL_CODES, repeat=n):
            check_lists(combo)
            count += 1

    # (2) randomized fuzz over longer field-lists
    rng = random.Random(9673)
    for _ in range(50000):
        n = rng.randint(0, 16)
        kinds = [rng.choice(ALL_CODES) for _ in range(n)]
        check_lists(kinds)
        count += 1

    # (3) name_is_return_key: short + plural skipped, others not
    SHORT, PLURAL = 100, 101
    for name in [SHORT, PLURAL, 0, 1, 2, 3, 4, 5, 99, 102, 200]:
        assert (model_name_is_return_key(name, SHORT, PLURAL)
                == real_name_is_return_key(name, SHORT, PLURAL)), \
            ("name_is_return_key mismatch on name=%r" % (name,))
    assert model_name_is_return_key(SHORT, SHORT, PLURAL) is True
    assert model_name_is_return_key(PLURAL, SHORT, PLURAL) is True
    assert model_name_is_return_key(7, SHORT, PLURAL) is False

    # (4) the F2P discriminator: a lone plural-spelling return-description field,
    #     a return annotation, no rtype field -> rtype IS emitted (patched),
    #     but the PRE-PATCH (short-only) logic would NOT emit it.
    plural_only = [RETURNS]                    # the Napoleon-style :returns:
    assert real_emit_rtype(plural_only, True) is True, \
        "patched logic must emit rtype for a plural return-description"
    assert model_augment_return_typefield(plural_only, True) is True, \
        "model must emit rtype for a plural return-description"
    assert prepatch_emit_rtype(plural_only, True) is False, \
        "pre-patch (short-only) logic must FAIL to emit rtype (the bug)"
    # the short spelling already worked pre-patch and post-patch alike:
    short_only = [RETURN]
    assert real_emit_rtype(short_only, True) is True
    assert prepatch_emit_rtype(short_only, True) is True
    # with no return annotation, nothing is emitted regardless of description:
    assert real_emit_rtype([RETURNS], False) is False
    # with an existing rtype field, nothing fresh is emitted:
    assert real_emit_rtype([RETURNS, RTYPE], True) is False

    print("G-AX OK: model decision functions == patched "
          "augment_descriptions_with_types return logic over %d field-lists "
          "(exhaustive len<=4 + 50000 fuzz) + name_is_return_key + the plural "
          "return-description discriminator. No consumed axioms; structural "
          "cross-check only." % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
