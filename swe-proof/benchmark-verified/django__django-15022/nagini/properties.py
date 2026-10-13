# properties.py — PBT falsification battery for django__django-15022.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a FULL model.py source that shares the frozen spec
# (markers.same_spec) and edits ONLY inside the `# impl-start` / `# impl-end`
# region (region surgery via _swap GUARANTEES same_spec). The runner runs Nagini
# verify on each and checks the outcome against `expect`.
#
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py):
#
#   search_retains_object(rows: PSeq[int], terms: PSeq[int]) -> bool
#     Ensures(Result() == some_row_matches_all(rows, terms))
#
#   The load-bearing clause is the GROUNDED postcondition pinning the result to
#   `some_row_matches_all` — the EXISTS-row, FOR-ALL-terms retention predicate
#   (a single related row must clear EVERY term). The behavioural delta the spec
#   defends is the QUANTIFIER SWAP:
#       fix (single .filter(Q(*term_queries)))  =  exists-row, for-all-terms
#       bug (chained qs.filter(or_queries) per bit) = for-all-terms, exists-row
#   The F2P scenario "danielle 19" over children {Danielle@18, Daniel@19} is the
#   concrete witness: every term is individually covered (Danielle->"danielle",
#   Daniel->"19") so the pre-patch keeps the parent (count 1), but no single
#   child clears both, so the fix drops it (count 0).
#
# Why several standard lanes are N/A here (justified in the return assessment):
#   * FRAME-MUTATION: N/A. Both inputs are `PSeq[int]` value sequences (immutable
#     pure values, NO `Acc(...)` heap permission). There is no full-permission
#     read-only reference to overwrite, so the project's #1 weakness class cannot
#     arise. has_readonly_input = False.
#   * UNGROUNDED-ORACLE ECHO: N/A as a WRONG echo. The postcondition oracle
#     `some_row_matches_all(rows, terms)` is GROUNDED — a @Pure fold fully
#     unfolded over the two inputs, not an opaque answer-key. Echoing it
#     (`return some_row_matches_all(rows, terms)`) is the CORRECT cheapest impl,
#     so it is included as a positive control, not a reject.
#   * AXIOM lane: empty. meta.json `axioms: []`. The only @ContractOnly symbol,
#     `matches`, is an UNINTERPRETED relation (tautology contract `Implies(R,R)`)
#     — the proof relies on NO property of it; there is no consumed library axiom
#     and no real Docker callee to probe. The deep model is an A-reference
#     validated host-side by axiom_check.py (G-AX), not a Docker axiom probe.
from pathlib import Path

INSTANCE = "django__django-15022"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl region body (between `# impl-start` and `# impl-end`),
# captured verbatim so each variant replaces ONLY executable/proof text inside
# the impl region. The frozen spec (axioms/pure/pre/post) is never touched.
_GOLD_IMPL = """    # Skeleton of the patch: every per-term query is accumulated and the object
    # is retained only if a single related row clears the whole conjunction.
    retained = False
    i = len(rows)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(rows))
        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
        # invariants-end
        row = rows[i - 1]
        Assert(rows.drop(i - 1)[0] == row)
        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
        # all_clear: does this single related row satisfy every term?
        all_clear = True
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
            # invariants-end
            term = terms[j - 1]
            Assert(terms.drop(j - 1)[0] == term)
            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
            if not matches(row, term):
                all_clear = False
            j = j - 1
        Assert(all_clear == row_matches_all(row, terms))
        if all_clear:
            retained = True
        i = i - 1
    return retained"""

assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


# ---------------------------------------------------------------------------
# POSITIVE CONTROL 1 — honest grounded-oracle echo (cheapest correct impl).
# The postcondition oracle is grounded in the inputs, so returning it directly
# IS correct and MUST verify. If it fails => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_ORACLE = """    # Honest cheapest correct impl: the postcondition oracle is GROUNDED in the
    # inputs (a @Pure fold over rows/terms), so returning it directly is correct.
    return some_row_matches_all(rows, terms)"""

# ---------------------------------------------------------------------------
# POSITIVE CONTROL 2 — structurally different but CORRECT.
# Keeps the gold backward-loop shape and EVERY gold invariant/framing assert
# verbatim (per pilot bug #2 / caution: do not drop framing asserts; do not flip
# to a forward-append that needs an f(a+b) lemma). The only executable change is
# the inner all_clear computation shape: `all_clear = all_clear and matches(...)`
# instead of `if not matches(...): all_clear = False`. Same invariant holds.
# ---------------------------------------------------------------------------
_POS_RESHAPE = """    # Structurally different but correct: inner all_clear folded via a boolean
    # AND-accumulation instead of the if/clear shape. Gold invariants + framing
    # asserts kept verbatim so the proof obligations are unchanged.
    retained = False
    i = len(rows)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(rows))
        Invariant(retained == some_row_matches_all(rows.drop(i), terms))
        # invariants-end
        row = rows[i - 1]
        Assert(rows.drop(i - 1)[0] == row)
        Assert(rows.drop(i - 1).drop(1) == rows.drop(i))
        all_clear = True
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
            # invariants-end
            term = terms[j - 1]
            Assert(terms.drop(j - 1)[0] == term)
            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
            all_clear = all_clear and matches(row, term)
            j = j - 1
        Assert(all_clear == row_matches_all(row, terms))
        if all_clear:
            retained = True
        i = i - 1
    return retained"""

# ---------------------------------------------------------------------------
# ADMISSIBILITY — a self-call caller on an F2P-shaped input. There is no
# precondition (pre-conditions region empty), so a normal input must be
# admitted. Builds the "danielle 19" 2-row x 2-term shape (opaque ids), calls
# the modeled function, and asserts the result agrees with the grounded oracle.
# If this fails => PRECOND-TOO-STRONG. We keep the gold impl verbatim and append
# the admissibility caller AFTER `return retained` (dead-after-return code still
# type/contract-checks the call site in Nagini).
# ---------------------------------------------------------------------------
_ADMISS = _GOLD_IMPL + """


def _admiss_caller() -> None:
    # F2P-shaped: 2 related rows, 2 search terms (the "danielle 19" scenario).
    rows = PSeq(0, 1)    # type: PSeq[int]
    terms = PSeq(10, 11)  # type: PSeq[int]
    r = search_retains_object(rows, terms)
    Assert(r == some_row_matches_all(rows, terms))
    # also the empty-terms / empty-rows corners must be admissible
    empty = PSeq(0).take(0)  # type: PSeq[int]
    r2 = search_retains_object(empty, terms)
    Assert(r2 == some_row_matches_all(empty, terms))
    r3 = search_retains_object(rows, empty)
    Assert(r3 == some_row_matches_all(rows, empty))"""


# ---------------------------------------------------------------------------
# REJECT 1 — the pre-patch chained-filter bug (for-all-terms, exists-row).
# This is the literal removed code: retain iff EVERY term is matched by SOME
# (possibly different) related row. It is `model_prepatch.py`'s skeleton.
# ---------------------------------------------------------------------------
_REJ_CHAINED = """    # Pre-patch chained-filter semantics: retain iff every term is matched by
    # SOME related row (for-all-terms, exists-row) — even if no single row
    # clears all terms. Does NOT establish the exists-row, for-all-terms oracle.
    retained = True
    j = len(terms)
    while j > 0:
        # invariants-start
        Invariant(0 <= j and j <= len(terms))
        Invariant(retained == some_row_matches_all(rows, terms))
        # invariants-end
        term = terms[j - 1]
        term_seen = False
        i = len(rows)
        while i > 0:
            # invariants-start
            Invariant(0 <= i and i <= len(rows))
            # invariants-end
            row = rows[i - 1]
            if matches(row, term):
                term_seen = True
            i = i - 1
        if not term_seen:
            retained = False
        j = j - 1
    return retained"""

# ---------------------------------------------------------------------------
# REJECT 2 — first-row-only (partial-domain over the rows axis).
# Inspect ONLY the first related row: retain iff rows[0] clears all terms.
# Correct only on inputs where the clearing row is the first one (or no row
# clears); WRONG when only a LATER related row satisfies every term.
# ---------------------------------------------------------------------------
_REJ_FIRST_ROW = """    # Partial-domain (rows axis): check ONLY the first related row. Diverges
    # whenever the row that clears all terms is not rows[0].
    retained = False
    if len(rows) > 0:
        row = rows[0]
        all_clear = True
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            Invariant(all_clear == row_matches_all(row, terms.drop(j)))
            # invariants-end
            term = terms[j - 1]
            Assert(terms.drop(j - 1)[0] == term)
            Assert(terms.drop(j - 1).drop(1) == terms.drop(j))
            if not matches(row, term):
                all_clear = False
            j = j - 1
        if all_clear:
            retained = True
    return retained"""

# ---------------------------------------------------------------------------
# REJECT 3 — any-match (for the weakest quantifier order, exists-row exists-term).
# Retain iff ANY single (row, term) pair matches. Strictly weaker than the
# oracle: keeps a candidate whenever any related row matches any one term, even
# when no row clears ALL terms (multi-term searches collapse to a one-term OR).
# ---------------------------------------------------------------------------
_REJ_ANY = """    # exists-row, exists-term: retain if ANY (row, term) pair matches at all.
    # This collapses the per-term AND into a global OR — far too permissive.
    retained = False
    i = len(rows)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(rows))
        # invariants-end
        row = rows[i - 1]
        j = len(terms)
        while j > 0:
            # invariants-start
            Invariant(0 <= j and j <= len(terms))
            # invariants-end
            term = terms[j - 1]
            if matches(row, term):
                retained = True
            j = j - 1
        i = i - 1
    return retained"""

# ---------------------------------------------------------------------------
# REJECT 4 — empty-terms boundary flip (partial-domain over the terms axis).
# Identical to gold EXCEPT it initializes the inner all_clear to
# `len(terms) > 0`, so a row with ZERO terms is wrongly judged NOT to clear all
# terms. Diverges exactly on the empty-search subdomain: gold/oracle says a
# row clears the empty conjunction (row_matches_all(row, []) == True), this
# rival says it does not. The Invariant(all_clear == row_matches_all(...)) at
# j==0 with empty terms is then violated, so it must reject.
# ---------------------------------------------------------------------------
_REJ_EMPTY_TERMS = _swap(
    _GOLD_IMPL,
    "        all_clear = True\n        j = len(terms)",
    "        all_clear = len(terms) > 0\n        j = len(terms)",
)


SPEC_TESTS = [
    {
        "id": "pos-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_ORACLE),
        "rationale": "the postcondition oracle some_row_matches_all is GROUNDED "
                     "in the inputs, so returning it directly is the correct "
                     "cheapest impl and MUST verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-reshape-inner-and",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_RESHAPE),
        "rationale": "structurally different correct impl (inner all_clear folded "
                     "via boolean AND-accumulation, gold invariants + framing "
                     "asserts kept verbatim) MUST verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS),
        "rationale": "no precondition; a normal F2P-shaped input (2 rows x 2 "
                     "terms) plus the empty-rows / empty-terms corners must be "
                     "admitted and the call site verifies (else PRECOND-TOO-STRONG).",
    },
    {
        "id": "weak-chained-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_CHAINED),
        "refinement": "this is the literal PRE-PATCH chained `.filter()` skeleton "
                      "(for-all-terms, exists-row). Its faithful real patch keeps "
                      "`queryset = queryset.filter(or_queries)` per bit, which the "
                      "issue reports as the bug: on the F2P scenario children "
                      "{Danielle@18, Daniel@19} search 'danielle 19' it KEEPS the "
                      "parent (count 1) because each term is matched by some row, "
                      "whereas the fix drops it (count 0). It would NOT resolve "
                      "test_many_search_terms / the multi-valued-relationship F2P.",
        "rationale": "rejected by Invariant(retained == some_row_matches_all(rows, "
                     "terms)): the for-all-terms/exists-row computation cannot "
                     "establish the exists-row/for-all-terms retention predicate "
                     "(the quantifier swap the postcondition pins).",
    },
    {
        "id": "weak-first-row-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_FIRST_ROW),
        "refinement": "a faithful patch that inspects only the FIRST related row "
                      "(e.g. limiting the join to one row) drops candidates whose "
                      "only all-terms-clearing related row is not first. It would "
                      "fail 'Searches over multi-valued relationships return rows "
                      "from related ...' whenever the matching related row is not "
                      "the first reachable one — not behaviourally the gold patch.",
        "rationale": "rejected by Invariant(retained == some_row_matches_all("
                     "rows.drop(i), terms)) — a one-row check cannot match the "
                     "exists-over-ALL-rows oracle for inputs with >1 row.",
    },
    {
        "id": "weak-any-row-any-term",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ANY),
        "refinement": "exists-row/exists-term collapses the per-term AND into a "
                      "global OR: retain on ANY single field match. A faithful "
                      "patch that OR-combined every term query (one big "
                      "Q.OR(*all_terms)) keeps far too many candidates — it would "
                      "fail test_many_search_terms (multi-term searches must "
                      "narrow, not widen) and is not the AND-of-ORs gold combination.",
        "rationale": "rejected by Ensures(Result() == some_row_matches_all(rows, "
                     "terms)): the any-match accumulator returns True on inputs "
                     "where no single row clears every term, contradicting the "
                     "for-all-terms requirement inside the oracle.",
    },
    {
        "id": "weak-empty-terms-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_EMPTY_TERMS),
        "refinement": "supporting partial-domain case (terms axis): identical to "
                      "gold except a row with ZERO terms is judged NOT to clear "
                      "the (vacuous) conjunction. A faithful patch that treats an "
                      "empty search as 'retain nothing' diverges from Django, "
                      "which on an empty/whitespace search_term does not enter the "
                      "term loop at all and retains the unfiltered queryset; "
                      "dropping every candidate would not resolve the P2P search "
                      "tests with empty/short terms.",
        "rationale": "rejected by Invariant(all_clear == row_matches_all(row, "
                     "terms.drop(j))) at j==0 over empty terms: row_matches_all("
                     "row, []) == True but the rival initialises all_clear=False.",
    },
]

# No consumed @ContractOnly axioms and no real Docker callee to probe (meta.json
# axioms: []; `matches` is uninterpreted; the deep model is A-reference validated
# host-side by axiom_check.py / G-AX). The axiom lane is therefore empty.
AXIOM_TESTS = []
