#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12039 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (`List Char` ↔ `str`, `''` ↔ `[]`, `idx ≥ length` ↔ IndexError).
              The modeled method `renderColumn` renders ONE column; the
              unchanged surrounding glue `', '.join(...)` is applied to build
              the full `Columns.__str__` output, so the shadow is the whole
              `Columns` string render. `quote_name = identity` (mapping.md §2):
              the unchanged name-quoting callee is the input carrier, so it is
              held to the identity, isolating the changed rendering op.
              There are NO A-tagged callees in this bundle (mapping.md §3), so
              the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.db.backends.ddl_references.Columns.__str__`, applied at
              base_commit (the real correctness oracle, G-RESOLVE), constructed
              with the SAME `quote_name = identity`.

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 12039
N_FUZZ = 100_000


def identity_quote(name):
    """mapping.md §2: G-CONF holds the unchanged name-quoting callee to the
    identity, so the rendered token equals the raw column string."""
    return name


# --- the R/I shadow: Solution.lean columnText, transliterated ----------------
def shadow_column_text(name, suffixes, idx):
    """columnText (name : List Char) (suffixes) (idx) transliterated to str.

    A4/A5: append the qualifier only when it is supplied for this position AND
    non-empty, with exactly one separating space; otherwise the bare name."""
    col = identity_quote(name)
    if idx < len(suffixes):           # A3: in range  ⇔  no IndexError
        suffix = suffixes[idx]
        if suffix:                    # A4: '' is falsy  ⇔  suffixes[idx] = []
            col = '{} {}'.format(col, suffix)
    return col                        # A5


def shadow_columns_str(columns, suffixes):
    """The full Columns.__str__ render (A6 glue: ', '.join over enumerate)."""
    return ', '.join(
        shadow_column_text(column, suffixes, idx)
        for idx, column in enumerate(columns)
    )


def oracle_columns_str(columns, suffixes):
    """patch.diff's behaviour: the patched django Columns.__str__. The harness
    applies patch.diff before this runs; quote_name = identity to match the
    shadow's carrier (mapping.md §2)."""
    from django.db.backends.ddl_references import Columns
    cols = Columns('t', list(columns), identity_quote, col_suffixes=tuple(suffixes))
    return str(cols)


def fuzz_cases(n, rng):
    # Column-name and qualifier alphabets. Qualifiers in the real code are
    # '' (ascending) or 'DESC' (descending); we fuzz a broader set incl. the
    # empty string, ordinary tokens, and ones with embedded spaces.
    names = ['name', 'headline', 'a', 'col_1', 'x', 'some_long_column_name', '']
    quals = ['', 'DESC', 'ASC', 'text_pattern_ops', ' ', 'DESC ', 'a b']

    # --- boundary cases (plan §4.1 step 4) ---
    # the two F2P/P2P-shaped single-column cases:
    yield (['headline'], ['DESC'])     # descending  -> 'headline DESC'  (F2P)
    yield (['headline'], [''])         # ascending   -> 'headline'       (P2P)
    yield (['headline'], [])           # no suffixes -> 'headline'       (IndexError path)
    yield ([], [])                     # no columns  -> ''
    yield (['a'], ['DESC', 'ASC'])     # more suffixes than columns
    yield (['a', 'b'], ['DESC'])       # fewer suffixes than columns (b -> IndexError path)
    yield (['a', 'b'], ['', 'DESC'])   # mixed empty/non-empty
    yield (['a', 'b', 'c'], ['DESC', '', 'ASC'])

    # --- randomized fuzz ---
    for _ in range(n):
        ncols = rng.randint(0, 5)
        columns = [rng.choice(names) for _ in range(ncols)]
        nsuf = rng.randint(0, ncols + 1)   # sometimes fewer/more than columns
        suffixes = [rng.choice(quals) for _ in range(nsuf)]
        yield (columns, suffixes)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for columns, suffixes in fuzz_cases(N_FUZZ, rng):
        count += 1
        shadow = shadow_columns_str(columns, suffixes)
        oracle = oracle_columns_str(columns, suffixes)
        if shadow != oracle:
            disagreements.append((columns, suffixes, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for cols, suf, sh, orc in disagreements:
            print("  columns=%r suffixes=%r shadow=%r oracle=%r"
                  % (cols, suf, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of renderColumn (full Columns.__str__ render) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
