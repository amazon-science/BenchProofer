# properties.py — G-PBT falsification battery for django__django-15022 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a soundness positive that reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject" case
# carries a refutation `witness`: a self-contained snippet that ELABORATES against
# the rival and FAILS on the frozen solution, so the rejection is attributable to
# the spec and not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   searchFilter (terms : List Nat) (parents : List Parent) : List Parent
#     problem_spec pins   result = parents.filter (fun p => combinedMatch terms p)
#   where combinedMatch keeps a record with an empty query unconditionally, and
#   otherwise keeps it exactly when a SINGLE related row matches EVERY query word
#   (rowMatchesAll = every word matched by that one row). The load-bearing content
#   is the QUANTIFIER NESTING: the existential over related rows sits INSIDE the
#   universal over words (∃row ∀word), together with the empty-query no-op and the
#   order-preserving filter shape.
#
# CARRIER NOTE: nagini modeled the same behaviour over `PSeq[int]` value sequences
# with an @Pure grounded oracle `some_row_matches_all`. This backend models the
# result list directly over a transparent `Parent`/`Row` carrier, so the rivals
# port cheaply and every reject case is refuted by a `decide`-able concrete input
# — no opaque callee blocks refutation, no conditioning is needed.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's #1 class). In nagini both inputs were immutable
#     `PSeq[int]` values with no `Acc(...)` heap permission, so nagini itself
#     already scored this lane N/A. Lean is referentially transparent regardless —
#     no aliasing, no permissions — so a write-back-into-a-read-only-input rival is
#     not expressible and the lane is VACUOUS here. See 'assessment'.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them.
#
# LANES REPAIRED BY THE INDEPENDENT AUDIT (this file was ported, gated SOUND, then
# re-attacked by an auditor who did not write it; every claim below rests on a real
# build, exit codes recorded in the case comments):
#   * ADMISSIBILITY was dropped by the port with the reason "the lean obligation
#     carries NO precondition hypothesis, so nothing could be PRECOND-TOO-STRONG."
#     That reason is WRONG, and it is the specific one the audit lane rejects: on a
#     TOTAL carrier the analogue of PRECOND-TOO-STRONG is the obligation being
#     UNSATISFIABLE at exactly an F2P-shaped input, which a positive that discharges
#     the spec predicate at that concrete input — by evaluation, as a `have`, before
#     closing the frozen obligation verbatim — tests directly. `admiss-f2p-shape`
#     below does that at BOTH poles of the F2P scenario. Landed, verified (exit 0).
#   * DIVERGENCE (F′) is a genuine KNOWN HOLE here, not a vacuous class, and the
#     distinction is recorded rather than glossed. See the note above SPEC_TESTS.
#   * Two rivals ADDED (`weak-duplicate-per-row`, `weak-order-reversed`): the ported
#     battery attacked only the kept/dropped PREDICATE, leaving the two other
#     clauses of `result = parents.filter …` — multiplicity and ORDER — unprobed.
#   * One refinement CORRECTED (`weak-empty-query-drops`): the ported text cited
#     P2P tests "that submit an empty or all-whitespace term", which do not exist
#     in this instance's P2P list. The real P2P evidence is 10 changelist tests
#     that build a changelist with NO search parameter at all.
from pathlib import Path

INSTANCE = "django__django-15022"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- FROZEN impl region, verbatim (unique in the file, lies ENTIRELY inside
# impl-start/impl-end). Every variant replaces exactly this block. ----------------
_GOLD_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  -- Accumulate the per-word queries, then apply ONE combined filter (a single\n"
    "  -- join), so the surviving records are those a single related row satisfies\n"
    "  -- across the whole query.\n"
    "  let mut termQueries : List Nat := []\n"
    "  for t in terms do\n"
    "    termQueries := termQueries ++ [t]\n"
    "  return parents.filter (fun p => combinedMatch termQueries p)"
)
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl region drifted from Solution.lean"

# --- FROZEN proof tactic body, verbatim (unique; lies inside proof-start/end).
# For a soundness positive that reshapes the impl we also swap this for a proof
# that closes over the NEW shape, keeping the `theorem correct_searchFilter`
# STATEMENT byte-identical (only the tactic body changes). ------------------------
_GOLD_PROOF = (
    "  intro terms parents\n"
    "  have helper : ∀ (xs : List Nat) (init : List Nat),\n"
    "      (forIn (m := Id) xs init\n"
    "        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [bind, pure] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp\n"
    "  unfold problem_spec_searchFilter implementation_searchFilter\n"
    "  simp only [Id.run, bind]\n"
    "  rw [helper, List.nil_append]\n"
    "  rfl"
)
assert _BASE.count(_GOLD_PROOF) == 1, "gold proof body drifted from Solution.lean"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------

# pos-oracle-echo: the cheapest correct impl. The postcondition is grounded in the
# inputs (a filter over `combinedMatch`), so returning that filter directly is
# correct; the reshaped proof closes by `rfl`.
_POS_ECHO_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  -- The kept-record predicate is grounded in the inputs, so applying it as a\n"
    "  -- single filter directly is correct.\n"
    "  return parents.filter (fun p => combinedMatch terms p)"
)
_POS_ECHO_PROOF = (
    "  intro terms parents\n"
    "  unfold problem_spec_searchFilter implementation_searchFilter\n"
    "  rfl"
)

# pos-reshape-accumulate: structurally different but CORRECT. Instead of one
# `List.filter`, it walks the records with a mutable accumulator, appending each
# kept record in order — the shape a faithful patch could equally take. The proof
# reproves the loop equals `List.filter` by Route-B induction on the accumulator.
_POS_RESHAPE_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  -- Structurally different but correct: walk the records, keeping each one\n"
    "  -- (in order) exactly when a single related row matches every query word.\n"
    "  let mut acc : List Parent := []\n"
    "  for p in parents do\n"
    "    acc := acc ++ (if combinedMatch terms p then [p] else [])\n"
    "  return acc"
)
_POS_RESHAPE_PROOF = (
    "  intro terms parents\n"
    "  have helper : ∀ (xs : List Parent) (init : List Parent),\n"
    "      (forIn (m := Id) xs init\n"
    "        (fun p r => pure (ForInStep.yield\n"
    "          (r ++ (if combinedMatch terms p then [p] else []))))) "
    "= init ++ xs.filter (fun p => combinedMatch terms p) := by\n"
    "    intro xs\n"
    "    induction xs with\n"
    "    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]\n"
    "    | cons a as ih =>\n"
    "      intro init\n"
    "      rw [List.forIn_cons]\n"
    "      simp only [bind, pure] at ih ⊢\n"
    "      rw [ih]\n"
    "      simp [List.filter_cons]\n"
    "      by_cases h : combinedMatch terms a <;> simp [h]\n"
    "  unfold problem_spec_searchFilter implementation_searchFilter\n"
    "  simp only [Id.run, bind]\n"
    "  rw [helper, List.nil_append]\n"
    "  rfl"
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits only the impl region, keeps the frozen proof body
# (which cannot close over the reshaped impl), and carries a discriminating
# witness stated at a concrete `decide`-able input.
# ---------------------------------------------------------------------------

# weak-per-word-chain: the PRE-PATCH semantics — apply the query one word at a
# time, each word narrowing to records where SOME related row matches that word.
# Different words may be satisfied by different rows (∀word ∃row), never requiring
# a single row to clear the whole query.
_REJ_CHAIN_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  let mut qs := parents\n"
    "  for t in terms do\n"
    "    qs := qs.filter (fun p => p.rows.any (fun r => r.matched.contains t))\n"
    "  return qs"
)

# weak-first-row-only: consult ONLY the first related row (∃-over-rows collapsed
# to rows[0]). Keeps a record iff its first row matches every word; wrong whenever
# the only clearing row is a later one.
_REJ_FIRST_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  return parents.filter (fun p => match terms with\n"
    "    | [] => true\n"
    "    | _ :: _ => match p.rows with\n"
    "      | [] => false\n"
    "      | r :: _ => rowMatchesAll terms r)"
)

# weak-any-word: collapse the per-word AND (rowMatchesAll) into a per-word OR —
# keep a record when SOME row matches SOME single word (∃row ∃word). Far too
# permissive: multi-word searches widen instead of narrowing.
_REJ_ANY_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  return parents.filter (fun p => match terms with\n"
    "    | [] => true\n"
    "    | _ :: _ => p.rows.any (fun r => terms.any (fun t => r.matched.contains t)))"
)

# weak-duplicate-per-row: ADDED BY THE AUDIT. Emits one copy of a record PER
# clearing related row instead of one copy per record. The kept/dropped predicate
# is exactly right on every input — this rival agrees with gold about WHICH records
# survive — so it is invisible to every other rival in the battery; it diverges
# only in MULTIPLICITY, the "each record kept at most once" clause of
# `result = parents.filter …`. This is the shape a faithful patch takes when the
# combined filter re-introduces a row-multiplying join without collapsing it.
_REJ_DUP_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  let mut acc : List Parent := []\n"
    "  for p in parents do\n"
    "    if terms.isEmpty then\n"
    "      acc := acc ++ [p]\n"
    "    else\n"
    "      for r in p.rows do\n"
    "        if rowMatchesAll terms r then\n"
    "          acc := acc ++ [p]\n"
    "  return acc"
)

# weak-order-reversed: ADDED BY THE AUDIT. Keeps EXACTLY the right set of records,
# each exactly once, and reverses their order. Attacks the last unprobed clause of
# the postcondition — `List.filter` is order-PRESERVING — which no other case in
# the battery can see, since all of them differ from gold on membership.
_REJ_ORDER_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  return (parents.filter (fun p => combinedMatch terms p)).reverse"
)

# weak-empty-query-drops: flip the empty-query no-op — an empty query drops every
# record instead of keeping the collection unchanged.
_REJ_EMPTY_IMPL = (
    "def implementation_searchFilter (terms : List Nat) (parents : List Parent) :\n"
    "    List Parent := Id.run do\n"
    "  return parents.filter (fun p => match terms with\n"
    "    | [] => false\n"
    "    | _ :: _ => p.rows.any (fun r => rowMatchesAll terms r))"
)


# --- ADMISSIBILITY (added by the audit) -------------------------------------
# The frozen proof's `intro` line, unique in the file and wholly inside
# proof-start/proof-end, so a ground `have` can be prepended without touching the
# `correct_searchFilter` STATEMENT or the spec view.
_P_INTRO = "  intro terms parents\n"
assert _BASE.count(_P_INTRO) == 1, "frozen proof intro line drifted"

# Discharge the spec predicate BY EVALUATION at both poles of the F2P scenario,
# then close the frozen obligation verbatim. Nothing is assumed: no new
# declaration, no new axiom, statement byte-identical, `decide` computes.
_ADMISS_PROOF = (
    "  -- ADMISSIBILITY: the modeled behaviour must be SATISFIABLE at exactly an\n"
    "  -- F2P-shaped input, discharged by evaluation before the general proof.\n"
    "  -- Pole 1 (the record is DROPPED): a two-word query where each word is\n"
    "  -- matched by a DIFFERENT related row, so no single row clears the query.\n"
    "  have _ground_dropped : problem_spec_searchFilter [0, 1] [⟨0, [⟨[0]⟩, ⟨[1]⟩]⟩]\n"
    "      (implementation_searchFilter [0, 1] [⟨0, [⟨[0]⟩, ⟨[1]⟩]⟩]) := by\n"
    "    unfold problem_spec_searchFilter implementation_searchFilter\n"
    "    decide\n"
    "  -- Pole 2 (the record is KEPT): the same query, where ONE related row now\n"
    "  -- matches both words. A spec satisfiable only at one pole would be\n"
    "  -- vacuous on the scenario that separates the two behaviours.\n"
    "  have _ground_kept : problem_spec_searchFilter [0, 1] [⟨0, [⟨[0]⟩, ⟨[0, 1]⟩]⟩]\n"
    "      (implementation_searchFilter [0, 1] [⟨0, [⟨[0]⟩, ⟨[0, 1]⟩]⟩]) := by\n"
    "    unfold problem_spec_searchFilter implementation_searchFilter\n"
    "    decide\n"
) + _P_INTRO


def _wit(terms, parents):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    input, closed by `decide`. Elaborates against a rival that diverges from the
    frozen result there, and fails on gold (which satisfies the spec everywhere).
    Binds nothing — the carrier is transparent, so the input is a literal."""
    return (
        f"example : ¬ problem_spec_searchFilter {terms}\n"
        f"    {parents}\n"
        f"    (implementation_searchFilter {terms} {parents}) := by\n"
        f"  unfold problem_spec_searchFilter implementation_searchFilter\n"
        f"  decide"
    )


SPEC_TESTS = [
    {
        "id": "pos-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_ECHO_IMPL),
                        _GOLD_PROOF, _POS_ECHO_PROOF),
        "rationale": (
            "the postcondition is GROUNDED in the inputs (result = the filter of "
            "the kept-record predicate over the records), so applying that filter "
            "directly is the cheapest correct impl and MUST verify; the proof "
            "closes by `rfl`. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-reshape-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _GOLD_IMPL, _POS_RESHAPE_IMPL),
                        _GOLD_PROOF, _POS_RESHAPE_PROOF),
        "rationale": (
            "structurally-different but CORRECT impl: instead of one library "
            "filter it walks the records with a mutable accumulator, appending each "
            "kept record in order — an equally faithful patch shape producing the "
            "identical result on every input. The frozen `theorem "
            "correct_searchFilter` STATEMENT is kept byte-identical; the proof "
            "reproves the loop equals the filter by induction on the accumulator. "
            "If it FAILS => SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        # ADDED BY THE INDEPENDENT AUDIT. The port dropped the admissibility lane
        # with the reason "the obligation has no precondition hypothesis, so
        # nothing could be PRECOND-TOO-STRONG" — which is not a demonstration of
        # vacuity. On a total carrier the analogue is the obligation being
        # UNSATISFIABLE at exactly an F2P-shaped input, and that is what this case
        # tests: it discharges the spec predicate BY EVALUATION at both poles of
        # the F2P scenario (the same two-word query, once where two different rows
        # each cover one word => record dropped, once where a single row covers
        # both => record kept) as `have`s, then closes the frozen obligation
        # verbatim. Verified: real build, exit 0.
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_PROOF),
        "rationale": (
            "the modeled behaviour is discharged BY EVALUATION at both poles of "
            "the F2P scenario — a two-word query over one record with two related "
            "rows, once where each word is matched by a DIFFERENT row (the record "
            "is dropped) and once where a SINGLE row matches both (the record is "
            "kept) — as ground `have`s, before the frozen obligation is closed "
            "verbatim. This is the total-carrier analogue of PRECOND-TOO-STRONG: "
            "if the obligation were unsatisfiable at exactly a normal F2P-shaped "
            "input, or satisfiable at only one pole (so the spec could not tell "
            "the two behaviours apart at all), this would FAIL. Nothing is "
            "assumed: no new declaration, no new axiom, the `correct_searchFilter` "
            "STATEMENT is byte-identical, and the ground instances are `have`s "
            "inside the existing tactic body. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "weak-per-word-chain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_CHAIN_IMPL),
        "refinement": (
            "this IS the pre-change behaviour: the query is applied one word at a "
            "time, each application keeping a record when SOME related row matches "
            "that word — so different words may be satisfied by different rows. Its "
            "faithful real counterpart is the unchanged repo, which over a "
            "multi-valued relation keeps a record whenever every word is matched by "
            "some (possibly different) related row. On the FAIL_TO_PASS scenario — "
            "children {Danielle/18, Daniel/19}, query 'danielle 19' — it KEEPS the "
            "parent (danielle matched by one child, 19 by the other) whereas the fix "
            "DROPS it (no single child matches both). It does NOT resolve, so a "
            "verifying rival here would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition: the spec pins result to the filter of "
            "combinedMatch, whose nonempty branch requires a SINGLE row to match "
            "every word (∃row ∀word). The per-word chain computes ∀word ∃row and "
            "diverges on any input where two words are matched only by different "
            "rows. Attacks the quantifier nesting. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # terms [0,1]; one parent, two rows each matching a DIFFERENT word:
        # gold drops (no row matches both), rival keeps (each word matched by a row).
        "witness": _wit("[0, 1]", "[⟨0, [⟨[0]⟩, ⟨[1]⟩]⟩]"),
    },
    {
        "id": "weak-first-row-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_FIRST_IMPL),
        "refinement": (
            "a real patch that inspected only the FIRST related row (e.g. limiting "
            "the join to one row) drops a record whose only all-words-clearing "
            "related row is not the first reachable one — diverging from 'Searches "
            "over multi-valued relationships return rows from related models only "
            "when all searched fields match that row' whenever the matching row is "
            "not first. Not behaviourally the gold patch; does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: combinedMatch's nonempty branch is an "
            "existential over ALL of a record's rows (`p.rows.any`), which a "
            "first-row-only check cannot match once a record has >1 row and only a "
            "later row clears the query. Attacks the exists-over-all-rows quantifier "
            "(the `rows` binder). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # terms [0]; one parent, first row matches nothing, second row matches word 0:
        # gold keeps (some row matches), rival drops (checks only the first row).
        "witness": _wit("[0]", "[⟨0, [⟨[]⟩, ⟨[0]⟩]⟩]"),
    },
    {
        "id": "weak-any-word",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ANY_IMPL),
        "refinement": (
            "collapsing the per-word AND (a row must match EVERY word) into a "
            "per-word OR (a row need match ANY one word) is what a faithful patch "
            "that OR-combined all term queries into one big disjunction would do: it "
            "keeps far too many records. On a two-word search where a related row "
            "matches only one word it wrongly keeps the record, so it widens rather "
            "than narrows the collection and fails test_many_search_terms / the "
            "multi-word assertions. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: rowMatchesAll requires a row to match "
            "EVERY word (`terms.all`); the rival's `terms.any` keeps a record on a "
            "single-word match. Attacks the for-all-over-words quantifier (the "
            "`terms` binder inside a matched row). If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # terms [0,1]; one parent, one row matching only word 0:
        # gold drops (row does not match word 1), rival keeps (matches word 0).
        "witness": _wit("[0, 1]", "[⟨0, [⟨[0]⟩]⟩]"),
    },
    {
        "id": "weak-empty-query-drops",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_EMPTY_IMPL),
        "refinement": (
            "a real patch that treated a word-less search as 'retain nothing' "
            "diverges from the observed behaviour: with no search words the "
            "collection is returned unchanged (the word loop is guarded and never "
            "entered). REFINEMENT CORRECTED BY THE AUDIT — the ported text claimed "
            "this would fail 'the PASS_TO_PASS search tests that submit an empty or "
            "all-whitespace term', and NO such test exists in this instance's "
            "PASS_TO_PASS list (checked against the repo at base_commit: every "
            "changelist test that submits a search parameter submits a non-empty "
            "one). The real P2P evidence is the other direction and is stronger: 10 "
            "PASS_TO_PASS changelist tests build a changelist with NO search "
            "parameter at all — the word list is empty and they assert on the "
            "UNFILTERED collection (row counts, ordering, pagination, "
            "select_related). A patch that dropped every record on a word-less "
            "query would return nothing to all 10. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: combinedMatch's empty-query branch "
            "returns true (keep every record), so on `terms = []` the spec pins "
            "result = parents; the rival returns the empty list. Attacks the "
            "empty-query no-op clause (the `terms = []` sub-domain). If it VERIFIES "
            "=> SPEC-TOO-WEAK."
        ),
        # empty query; one record (rows irrelevant):
        # gold keeps the record (no-op), rival drops it.
        "witness": _wit("[]", "[⟨0, []⟩]"),
    },
    {
        # ADDED BY THE INDEPENDENT AUDIT. Every rival above diverges from gold on
        # the kept/dropped PREDICATE, so all four attack the same clause of
        # `result = parents.filter …` from different angles and none of them can see
        # the other two clauses. This rival gets the predicate exactly RIGHT on every
        # input and diverges only in MULTIPLICITY.
        # Builds: witness vs rival exit 0; witness vs gold exit 1
        # (`decide` proved the proposition ... false); forgery (claim flipped) vs
        # gold exit 0, vs rival exit 1 — the exit codes invert with the claim.
        "id": "weak-duplicate-per-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_DUP_IMPL),
        "refinement": (
            "emits one copy of a record per CLEARING related row instead of one "
            "copy per record. This is what a faithful patch produces when the "
            "combined query is applied over a row-multiplying multi-valued join "
            "without collapsing the duplicates it spawns — the narrowed collection "
            "then reports a record once per matching related row. It agrees with "
            "the fix about exactly WHICH records survive, so it passes the "
            "membership assertions, and still fails the F2P scenario whose "
            "assertion is a COUNT: the record whose single related row clears an "
            "80-word repeated query is reported once by the fix and once per "
            "clearing row here, so a record reachable through two clearing rows "
            "returns a count of 2 where 1 is demanded. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: `result = parents.filter …` pins the "
            "result to a FILTER of the input collection, which keeps each record at "
            "most once and cannot duplicate. Attacks the multiplicity clause — the "
            "only case in the battery that does, since every other rival differs "
            "from the frozen impl on membership and so never reaches it. If it "
            "VERIFIES => SPEC-TOO-WEAK."
        ),
        # one word; one record with TWO rows that BOTH match it: gold keeps the
        # record once, the rival emits it twice. Same membership, different count.
        "witness": _wit("[0]", "[⟨0, [⟨[0]⟩, ⟨[0]⟩]⟩]"),
    },
    {
        # ADDED BY THE INDEPENDENT AUDIT. Keeps exactly the right records, each
        # exactly once, in the wrong ORDER — the last clause of the postcondition,
        # and the last one no other case in the battery can observe.
        # Builds: witness vs rival exit 0; witness vs gold exit 1
        # (`decide` proved the proposition ... false); forgery (claim flipped) vs
        # gold exit 0, vs rival exit 1 — the exit codes invert with the claim.
        "id": "weak-order-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJ_ORDER_IMPL),
        "refinement": (
            "returns the surviving records in REVERSED order. A faithful patch that "
            "rebuilt the narrowed collection by accumulating survivors onto the "
            "front of a fresh collection (rather than filtering in place) produces "
            "exactly this: the same records, each once, in the opposite order. The "
            "narrowed collection is required to preserve the ordering it was handed "
            "— the changelist renders rows in that order and the PASS_TO_PASS "
            "ordering tests assert the rendered sequence — so the faithful patch "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition: `result = parents.filter …` pins the "
            "result to an ORDER-PRESERVING filter of the input, not to the SET of "
            "surviving records. Attacks the order clause, which the four rivals "
            "above cannot reach because each of them already differs from the "
            "frozen impl on membership. If it VERIFIES => SPEC-TOO-WEAK."
        ),
        # one word; TWO records that BOTH survive it: gold returns them in input
        # order, the rival returns them reversed. Identical membership and counts.
        "witness": _wit("[0]", "[⟨0, [⟨[0]⟩]⟩, ⟨1, [⟨[0]⟩]⟩]"),
    },
]

# ---------------------------------------------------------------------------
# DIVERGENCE (F′) — a KNOWN HOLE on this bundle, not a vacuous class, and the
# audit records the difference deliberately: a vacuous class claims the battery is
# complete, a hole says the spec is not.
#
# This is vanilla Lean 4 + Mathlib: there is no `loom.semantics.termination` line
# in the frozen solution (grep: 0 hits), so the "total" vs "partial" reading of
# that option does not apply directly. What the carrier does instead is refuse to
# ADMIT a diverging impl at all, and the audit measured both spellings:
#
#   * plain `def` self-call — the file does not compile:
#       `fail to show termination for implementation_searchFilter ... no
#        parameters suitable for structural recursion ... well-founded recursion
#        cannot be used` (exit 1)
#     and the witness file built against it fails with the SAME error, i.e. the
#     failure is the definition, not the claim. That is the tooling failure mode
#     the audit lane says to report rather than ship: the rejection would attest
#     to an uncompilable file, not to the spec.
#   * `partial def` self-call — compiles, but the impl is then irreducible:
#       `Tactic `unfold` failed to unfold `implementation_searchFilter`` (exit 1)
#     on BOTH the module and the witness build, so no `decide`-able witness can
#     discriminate it. `partial` is not on variant_scope's banned-token list, so
#     the case would be scope-admissible — and it would be exactly the hollow
#     rejection this gate exists to refuse, since its gold-side error carries no
#     information about the claim.
#
# So the class is UNSHIPPABLE here for a demonstrated carrier reason, and the
# honest disposition is a recorded hole: the frozen spec is an input->output
# relation that says nothing about termination, and a diverging impl of it is
# neither refutable by a witness nor expressible as a compiling variant.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AUDIT PROBES THAT FOUND NOTHING (recorded so the next reader does not re-run
# them). All exit codes from real builds.
#
# SPEC-TOO-WEAK probes (new wrong impls, none verified => no spec hole):
#   * subset-reversed — keep a record when a row's matched set is a SUBSET of the
#     query, instead of the query being covered by the row. Rejected; refuted at
#     one word / one row matching nothing (exit 0 rival, 1 gold).
#   * norows-kept — treat a record with NO related rows as surviving any query
#     (the vacuous-existential trap). Rejected; refuted (exit 0 rival, 1 gold).
#   Both are subsumed by the shipped rivals' clauses, so neither was landed;
#   `weak-duplicate-per-row` and `weak-order-reversed` WERE landed because they hit
#   clauses nothing else in the battery reaches.
#
# SPEC-TOO-STRONG probes (new correct reshapes, both VERIFIED => no soundness
# hole; the spec admits faithful impls of genuinely different shape):
#   * prepend-then-reverse — accumulate survivors onto the FRONT of the
#     accumulator and reverse at the end (exit 0, re-proved in-region).
#   * structural recursion — abandon `Id.run do`/`for` entirely for a recursive
#     `def` over the record list (exit 0, re-proved in-region). This is the
#     sharpest of the two: it changes the impl's whole elaboration rather than
#     rearranging the frozen loop, and the frozen spec still admits it.
#
# No @ContractOnly axioms and no opaque callees: the per-(row, word) match matrix
# and the quantifier structure are modeled DEEPLY over the transparent
# Parent/Row carrier, so the axiom lane is vacuous here and belongs to G-AX
# regardless.
AXIOM_TESTS = []
