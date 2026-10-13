#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15037 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region
              (`qualifyReference` / the pure `targetQualifier` decision)
              transliterated to Python over the real repo carriers, via the
              mapping.md bijection (`List Char` ↔ `str`, `Option` ↔ `str|None`,
              `rel_type` ↔ `Bool`). The A-reference input `idKey` is the value of
              the unchanged callee `get_primary_key_column`; it is supplied as a
              fuzzed input here (G-CONF isolates the R/I decision legs — the
              branch + equality — while G-AX carries the callee itself, see
              axiom_check.py).
  * ORACLE  — `patch.diff`'s behaviour: the gold hunk's LITERAL decision
              expression (`inspectdb.py:120-125` post-patch):
                  if rel_type == 'ForeignKey':
                      if ref_pk_column and ref_pk_column != ref_db_column:
                          extra_params['to_field'] = ref_db_column
              i.e. the to_field value attached to the generated reference field
              (or None if no to_field key is set).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Self-contained: stdlib only (the decision is a pure function of the three
introspected values; no live DB needed for the R/I leg — the live callee is
G-AX's job). The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 15037
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean's targetQualifier, transliterated ---------

def shadow_qualifier(is_unique_ref, ref_column, id_key):
    """`targetQualifier (isUniqueRef) (refColumn) (idKey)` (Solution.lean pure
    region) over str/None carriers (mapping.md §2)."""
    if is_unique_ref:
        return None
    if id_key is None:
        return None
    if id_key != "" and id_key != ref_column:
        return ref_column
    return None


# --- the oracle: patch.diff's literal decision expression --------------------

def oracle_qualifier(is_unique_ref, ref_column, id_key):
    """patch.diff behaviour (inspectdb.py:120-125 post-patch). `is_unique_ref`
    selects rel_type ('OneToOneField' vs 'ForeignKey'); `id_key` is the real
    ref_pk_column; `ref_column` is ref_db_column. Returns the to_field value, or
    None when no to_field key is assigned."""
    rel_type = 'OneToOneField' if is_unique_ref else 'ForeignKey'
    to_field = None
    if rel_type == 'ForeignKey':
        ref_pk_column = id_key
        ref_db_column = ref_column
        if ref_pk_column and ref_pk_column != ref_db_column:
            to_field = ref_db_column
    return to_field


def fuzz_inputs(n, rng):
    names = ['id', 'pk', 'people_unique_id', 'other_id', 'code', 'uid', '', 'k0']
    key_choices = names + [None]
    # boundary cases first (plan §4.1 step 4)
    # F2P shape: plain FK, ref col 'people_unique_id', PK 'id' (present, distinct)
    yield (False, 'people_unique_id', 'id')
    yield (False, 'id', 'id')                  # FK to the PK column -> no to_field
    yield (False, 'other_id', None)            # target has no PK -> no to_field
    yield (False, 'other_id', '')              # empty PK name -> no to_field
    yield (True, 'people_unique_id', 'id')     # OneToOne -> never to_field
    yield (True, 'other_id', 'pk')             # OneToOne, distinct -> never
    yield (False, 'code', 'pk')                # plain FK, distinct -> to_field
    yield (False, '', 'id')                    # empty ref col, distinct PK
    for _ in range(n):
        is_unique = rng.random() < 0.5
        ref_col = rng.choice(names)
        id_key = rng.choice(key_choices)
        yield (is_unique, ref_col, id_key)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (is_unique, ref_col, id_key) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_qualifier(is_unique, ref_col, id_key)
        oracle = oracle_qualifier(is_unique, ref_col, id_key)
        if shadow != oracle:
            disagreements.append(((is_unique, ref_col, id_key), shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for inp, sh, orc in disagreements:
            print("  input=%r shadow=%r oracle=%r" % (inp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of qualifyReference agrees with patch.diff's "
          "to_field decision on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
