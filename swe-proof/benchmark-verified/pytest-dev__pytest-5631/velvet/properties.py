"""properties.py — G-PBT falsification battery for pytest-dev__pytest-5631 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct countSentinelArgs`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a single scanned sequence):

  countSentinelArgs (entries : List ArgEntry) return (out : CountResult)
    ensures out.err = false                    -- (E1) the scan never aborts
    ensures out.n = sentinelCount entries      -- (E2) the exact count

``ArgEntry`` carries three fields — ``isAttribute`` (the entry is bound to a
named attribute, so it is skipped), ``valueId`` (the OPAQUE object identity of
the replacement value; identity is total and never aborts), and ``eqTotal``
(whether the replacement value's equality test is TOTAL, i.e. always returns a
boolean; a value whose equality is non-total is the array-like value from the
problem statement). ``sentinelCount`` is a total, fully-unfolded fold over the
list: an entry contributes 1 exactly when it is not attribute-bound AND its
value identity is one of the two markers (``hitsMarker``, decided by identity —
so it inspects no value contents and can never abort). The ``axioms`` region is
empty; the post-image is grounded in the method's own input (no opaque answer
key to echo).

The two independent ``ensures`` clauses pin, respectively:
  * (E1) out.err = false — the scan is TOTAL: it returns a count for every
    admissible input, INCLUDING one whose replacement value has a non-total
    equality test. This is the discriminator vs the reported defect (the abort);
  * (E2) out.n = sentinelCount entries — the count is EXACT: an entry counts iff
    it is a non-attribute marker-by-identity, so neither a non-marker value nor
    an attribute-bound entry may be counted, and every marker must be.

The sole INPUT BINDER is ``entries``; its per-element fields ``isAttribute`` /
``valueId`` / ``eqTotal`` are the sub-inputs the reject witnesses vary. E2
depends on ``isAttribute`` and ``valueId``; E1 exists precisely to forbid the
result depending on ``eqTotal`` by ABORTING on a non-total value.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The sibling carries this as a
    MANDATORY rival (a store into the read-only ``kinds`` held at half
    permission). Lean and Velvet are referentially transparent: ``entries`` is
    an immutable value, this bundle declares NO ``mut`` binder over any input
    (only the local accumulator ``cnt`` and index ``i`` are ``mut``), there is
    no heap and no aliasing — so there is no read-only input to overwrite and no
    substitute probe. Not fabricated (per the porting map: vacuous here).
  * TOTALITY (control-flow-effect) — APPLIES; the headline discriminator. A
    rival that ABORTS (returns ``err = true``) on a non-total-equality value is
    refuted by E1. This is the pre-fix behaviour ported onto ``err``.
  * PARTIAL-DOMAIN / VALUE — APPLIES: over-counting a non-total value as a
    marker; counting every entry; dropping the first entry. Each is right on a
    sub-domain and diverges from ``sentinelCount`` elsewhere. Refuted by E2.
  * UNGROUNDED-ORACLE ECHO — N/A. ``sentinelCount`` / ``hitsMarker`` / ``contrib``
    are concrete ``def``s over the method's own input (empty ``axioms`` region);
    the cheapest correct impl simply evaluates the fold, covered honestly by the
    positive controls.

WITNESS PLACEMENT. The frozen impl is a backward ``while`` loop whose extracted
tester does NOT reduce under ``decide`` (the fixpoint stays stuck), so each
reject rival is a straight-line loop-free CLOSED FORM whose extracted tester DOES
reduce to a literal. Each reject rival therefore carries a machine-checked
refutation ``witness`` — a Velvet tester statement
``countSentinelArgsTester <entries> = false`` at ONE concrete input, checked in a
file whose ``prove_correct`` block is stripped so no tactic script can mask the
verdict. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its loop-free rival (the tester ``decide``s to
``false`` — the rival's output violates the postcondition there) and FAILS
against the frozen loop-solution (whose extracted fixpoint stays stuck under
``decide``), so each rejection is a genuine spec refutation and not mechanical
tactic breakage. No witness binds a hypothesis (the carrier is fully
transparent — ``valueId`` is a concrete ``Nat``), so there is no
joint-satisfiability obligation.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(mapping.md §3: the scan calls no unchanged external operation; every step is R
or I). Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-5631"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (the WHOLE `do` body; lies wholly inside the single
# ---- impl region and is unique in Solution.lean). ---------------------------
_IMPL = (
    "    -- impl-start\n"
    "    let mut cnt : Nat := 0\n"
    "    let mut i := entries.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
    "      invariant cnt = sentinelCount (entries.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let e := entries[i - 1]!\n"
    "      if hitsMarker e then\n"
    "        cnt := cnt + 1\n"
    "      else\n"
    "        cnt := cnt\n"
    "      i := i - 1\n"
    "    return ⟨false, cnt⟩\n"
    "    -- impl-end"
)

# ---- proof-body anchor. A `prove_correct` tactic body is elided from the
# ---- consumer spec view, so a variant may retune it without touching the spec
# ---- or dropping the obligation. Unique in the file.
_PROOF = (
    "prove_correct countSentinelArgs by\n"
    "  loom_solve\n"
    "  all_goals\n"
    "    rw [sentinelCount_drop_step entries i (by omega) (by omega)]\n"
    "    simp only [contrib]\n"
    "    split <;> simp_all <;> omega"
)

# The reshaped/loop-free variants own no loop index `i`, so the frozen tactic
# script (which names `i`) does not apply. For loop-free soundness positives we
# retune to the bare solver; for reject rivals we also reduce to the bare solver
# (they must NOT verify regardless — the proof body is elided from the spec
# view, and the rejection is attributed to the postcondition by the witness).
_SOLVE = "prove_correct countSentinelArgs by\n  loom_solve"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl, proof=_SOLVE):
    """Reshape the whole impl body AND retune the tactic script."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, proof)


def _rival(expr):
    """Solution.lean whose impl body is a single loop-free `return (<expr>)`,
    with the tactic script reduced to the bare solver."""
    return _impl(
        "    -- impl-start\n"
        f"    return ({expr})\n"
        "    -- impl-end")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `countSentinelArgsTester entries = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped, so no tactic
# ---- script can mask the verdict. `CountResult`/`ArgEntry` fields are `Bool`
# ---- and `Nat`, so the postcondition decidability derives and each witness
# ---- closes by `decide`.
def _tester(body):
    return ("extract_program_for countSentinelArgs\n"
            "prove_precondition_decidable_for countSentinelArgs\n"
            "prove_postcondition_decidable_for countSentinelArgs\n"
            "derive_tester_for countSentinelArgs\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — the cheapest HONEST impl, which MUST verify
    # (else SPEC-TOO-STRONG). `sentinelCount entries` is GROUNDED in the input (a
    # total fold, no opaque answer key), so returning it directly is a correct
    # fully-grounded implementation, not an ungrounded-oracle echo. The loop is
    # gone, so the frozen proof's loop reasoning is unneeded and the residual
    # goals close under the bare `loom_solve`.
    # =====================================================================
    {
        "id": "pos-control-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _rival("⟨false, sentinelCount entries⟩"),
        "rationale": "the post-image `sentinelCount entries` is GROUNDED in the "
                     "input (a total fold, no opaque answer key), so returning "
                     "`⟨false, sentinelCount entries⟩` is the honest cheapest "
                     "CORRECT impl. It MUST verify — the clauses are literally "
                     "`out.err = false` and `out.n = sentinelCount entries` — else "
                     "the postcondition is SPEC-TOO-STRONG. Also shows the spec is "
                     "not echo-vulnerable: any wrong constant/echo fails E2.",
    },
    {
        "id": "pos-control-arith-accumulate",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different but CORRECT: keep the frozen backward loop and
        # every invariant byte-identical, only reshape the per-entry step — the
        # `if hitsMarker then cnt+1 else cnt` branch becomes an arithmetic
        # accumulate `cnt + (if hitsMarker e then 1 else 0)` (= `cnt + contrib e`).
        # Observationally identical; the frozen loop proof closes it unchanged.
        "module": _impl(
            "    -- impl-start\n"
            "    let mut cnt : Nat := 0\n"
            "    let mut i := entries.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
            "      invariant cnt = sentinelCount (entries.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let e := entries[i - 1]!\n"
            "      cnt := cnt + (if hitsMarker e then 1 else 0)\n"
            "      i := i - 1\n"
            "    return ⟨false, cnt⟩\n"
            "    -- impl-end",
            proof=_PROOF),
        "rationale": "structurally different CORRECT reshape: the branch-increment "
                     "is replaced by an arithmetic accumulate "
                     "`cnt + (if hitsMarker e then 1 else 0)` (= `cnt + contrib e`), "
                     "keeping every loop invariant byte-identical. `out.n = "
                     "sentinelCount entries` still discharges under the frozen loop "
                     "proof. A faithful reshape MUST verify, else the clause is "
                     "over-fit to the if/else FORM => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — there is NO `require` clause, so the sibling's "a normal
    # input satisfies the precondition" probe is vacuous (nothing could exclude an
    # F2P-shaped input). Re-aimed at the residual admissibility risk on a total
    # domain: that the post-image is UNSATISFIABLE / degenerate at the interesting
    # point. This case discharges an in-region `assert` pinning the count at an
    # F2P-shaped input carrying ONE entry of every kind — an attribute-bound entry
    # (skipped), a marker (counted), a non-marker total-equality value (skipped),
    # and a non-marker NON-total-equality value (skipped, NOT aborting) — so the
    # post-image is non-degenerate (exactly one counted, and the non-total value
    # is scanned without abort). The impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live (a false claim leaves an
    # unsolved goal — checked during authoring).
    # =====================================================================
    {
        "id": "admiss-f2p-shape-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss\n"
            "      (sentinelCount [⟨true, 0, true⟩, ⟨false, 0, true⟩,\n"
            "                      ⟨false, 5, true⟩, ⟨false, 7, false⟩] = 1))\n"
            "    let mut cnt : Nat := 0\n"
            "    let mut i := entries.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ entries.length\n"
            "      invariant cnt = sentinelCount (entries.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let e := entries[i - 1]!\n"
            "      if hitsMarker e then\n"
            "        cnt := cnt + 1\n"
            "      else\n"
            "        cnt := cnt\n"
            "      i := i - 1\n"
            "    return ⟨false, cnt⟩\n"
            "    -- impl-end",
            proof=(
                "prove_correct countSentinelArgs by\n"
                "  loom_solve\n"
                "  all_goals first\n"
                "    | decide\n"
                "    | (rw [sentinelCount_drop_step entries i (by omega) (by omega)]\n"
                "       simp only [contrib]\n"
                "       split <;> simp_all <;> omega)")),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped input (one entry of every kind: attribute-bound, "
                     "marker, non-marker total-equality, non-marker NON-total-"
                     "equality): it counts exactly the single marker (= 1, neither "
                     "0 nor all), and the non-total-equality value is scanned "
                     "without abort. The in-region assert must discharge (else the "
                     "obligation is unsatisfiable / degenerate); the impl is kept "
                     "verbatim so the method's own `ensures` still discharges.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form with a machine-checked
    # refutation witness at a concrete input and the refinement argument for why
    # its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================

    # ---- TOTALITY clause (E1): abort on a non-total-equality value ----
    {
        "id": "weak-abort-on-nontotal",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour ported onto `err`: deciding membership by
        # value-equality aborts whenever a replacement value has a non-total
        # equality test, so the scan sets `err = true` on any such input. Correct
        # (err = false) exactly on the sub-domain where every value has a total
        # equality test; diverges on any non-total value.
        "module": _rival(
            "⟨entries.any (fun e => !e.eqTotal), sentinelCount entries⟩"),
        "refinement": "this IS the pre-fix behaviour: deciding sentinel membership "
                      "by value-equality evaluates the replacement value's equality "
                      "test in a truth context, which aborts for an array-like value "
                      "whose equality is non-total — surfacing as the reported "
                      "collection-time error. The failing test collects a decoration "
                      "whose replacement value has exactly that non-total equality; "
                      "the abort fires at collection so the test ERRORS instead of "
                      "passing — it does NOT resolve (it is the very defect the fix "
                      "removes).",
        "rationale": "REJECT from E1 (`out.err = false`): the rival returns "
                     "`err = true` whenever some entry has a non-total equality "
                     "test, but the scan must be TOTAL (identity never aborts). "
                     "Verifying would be SPEC-TOO-WEAK on the totality clause. "
                     "Refuted at a single non-attribute non-marker value with a "
                     "non-total equality test — the sub-domain no other witness "
                     "makes err-observable.",
        "witness": _tester(
            "example : countSentinelArgsTester [⟨false, 2, false⟩] = false := by\n"
            "  decide\n"),
    },

    # ---- COUNT clause (E2): over-count a non-total value as a marker ----
    {
        "id": "weak-count-nontotal-as-marker",
        "kind": "uniqueness",
        "expect": "reject",
        # A guarded value-equality membership (`try: in sentinels except: True`)
        # treats any un-comparable replacement value as a sentinel and counts it.
        # Correct on every input WITHOUT a non-total value; diverges by counting a
        # non-attribute non-total value the identity decision excludes.
        "module": _rival(
            "⟨false, (entries.filter "
            "(fun e => hitsMarker e || (!e.isAttribute && !e.eqTotal))).length⟩"),
        "refinement": "a faithful patch deciding membership by GUARDED "
                      "value-equality (treating an un-comparable replacement value "
                      "as a sentinel rather than aborting) would COUNT that "
                      "array-like value as a mock argument. The fixture machinery "
                      "would then expect the runner to supply an argument for a "
                      "value that is NOT a sentinel, breaking the failing "
                      "decoration — it would NOT resolve (a non-sentinel value must "
                      "not be counted).",
        "rationale": "REJECT from E2 (`out.n = sentinelCount entries`): "
                     "`sentinelCount` counts a non-attribute entry ONLY when its "
                     "identity is a marker, so counting a non-marker non-total value "
                     "over-counts. Verifying would be SPEC-TOO-WEAK. Refuted at a "
                     "non-total non-marker value paired with a genuine marker (a "
                     "length-2 input the other witnesses do not probe): gold counts "
                     "1, the rival 2.",
        "witness": _tester(
            "example : countSentinelArgsTester "
            "[⟨false, 5, false⟩, ⟨false, 0, true⟩] = false := by\n"
            "  decide\n"),
    },

    # ---- COUNT clause (E2): count every entry (the pre-fix len fallback) ----
    {
        "id": "weak-count-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix `return len(patchings)` fallback: count every entry
        # regardless of attribute binding or marker identity. Correct ONLY on the
        # all-marker non-attribute sub-domain; diverges on any attribute-bound or
        # non-marker entry.
        "module": _rival("⟨false, entries.length⟩"),
        "refinement": "this is the pre-fix length fallback: it counts "
                      "attribute-bound and non-marker entries as mock arguments, so "
                      "the fixture machinery would expect the runner to supply "
                      "arguments it must not — the argument-count tests would get "
                      "the wrong count and FAIL; it would NOT resolve.",
        "rationale": "REJECT from E2: `entries.length != sentinelCount entries` "
                     "whenever any entry is attribute-bound or a non-marker. Refuted "
                     "at a single attribute-bound entry (isAttribute = true — the "
                     "binder value no other witness exercises): gold counts 0, the "
                     "rival 1.",
        "witness": _tester(
            "example : countSentinelArgsTester [⟨true, 0, true⟩] = false := by\n"
            "  decide\n"),
    },

    # ---- COUNT clause (E2): drop the first entry ----
    {
        "id": "weak-skip-first-entry",
        "kind": "uniqueness",
        "expect": "reject",
        # Count the fold over the TAIL, dropping the first entry unconditionally.
        # Correct exactly when the first entry is not a counted marker; diverges
        # (undercounts by one) when the first entry is a marker.
        "module": _rival("⟨false, sentinelCount entries.tail⟩"),
        "refinement": "a faithful off-by-one patch dropping the first entry from "
                      "the count would omit a leading marker directive from the "
                      "argument count; a singly-decorated test would then report the "
                      "wrong count, so the fixture machinery mis-injects and the "
                      "test ERRORS — it would NOT resolve.",
        "rationale": "REJECT from E2: `sentinelCount entries.tail` omits the "
                     "index-0 contribution, differing from `sentinelCount entries` "
                     "whenever the first entry is a marker. Correct on the "
                     "complementary sub-domain (first entry not counted) — a genuine "
                     "partial-domain rival at the BOUNDARY element. Refuted at a "
                     "single marker entry: gold counts 1, the rival 0.",
        "witness": _tester(
            "example : countSentinelArgsTester [⟨false, 0, true⟩] = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals) plus a 1-case AXIOM lane. This
# bundle models the SAME purely-functional core — how many replacement directives
# stand in for a runner-supplied argument, decided by IDENTITY — over a
# `List ArgEntry` carrier (three touched fields per entry) instead of the
# sibling's permission-bearing `List[int]` of kind tags. The value surface
# carries across; the permission surface does not exist here.
#
#   sibling case                 -> here                              disposition
#   --------------------------------------------------------------------------
#   pos-cheap-grounded-oracle    -> pos-control-direct-fold           PORTED
#   pos-arith-accumulate         -> pos-control-arith-accumulate      PORTED
#   admiss-allkinds              -> admiss-f2p-shape-nondegenerate    RE-AIMED
#   frame-write-readonly-input   -> (none)                            VACUOUS
#   raise-on-kind3-totality      -> weak-abort-on-nontotal            PORTED
#   partial-kind3-counts         -> weak-count-nontotal-as-marker     PORTED
#   count-everything-fallback    -> weak-count-everything             PORTED
#   skip-first-directive         -> weak-skip-first-entry             PORTED
#   AXIOM_TESTS (1)              -> (none)                            DROPPED (G-AX)
#
# 6 ported, 1 re-aimed, 1 vacuous, 1 dropped = 7 SPEC cases (2 soundness,
# 1 admissibility, 4 uniqueness).
#
# PORTED (2 positive controls). pos-cheap-grounded-oracle returned the grounded
#   @Pure fold directly; on nagini that required an in-region ghost proof loop to
#   discharge the fold's intrinsic bound (P3). Velvet's `List.length`-based fold
#   has no such bound obligation in the `ensures`, so the port is the clean
#   one-liner `return ⟨false, sentinelCount entries⟩` with the loop removed and
#   the proof collapsed to the bare `loom_solve`. pos-arith-accumulate ports
#   1:1: keep the backward loop and all invariants byte-identical, replace the
#   branch-increment with the arithmetic accumulate `cnt + (if hitsMarker e then
#   1 else 0)`; the frozen loop proof closes it unchanged. Both verified to build.
# RE-AIMED (admissibility). The sibling builds a [0,1,2,3] one-of-every-kind
#   input and asserts the Requires predicate admits it. There is NO `require`
#   clause here, so that probe is vacuous. Re-aimed at the residual total-domain
#   risk: the post-image is non-degenerate at the analogous one-of-every-kind
#   input (attribute-bound / marker / non-marker total / non-marker non-total),
#   asserting the count is exactly 1 (and the non-total value is scanned without
#   abort). The in-region assert is live and the impl is kept verbatim.
# PORTED (4 rivals). raise-on-kind3-totality re-expresses onto E1: the rival
#   ABORTS (err = true) on a non-total-equality value, refuted by `out.err =
#   false`. partial-kind3-counts, count-everything-fallback, and
#   skip-first-directive re-express onto E2 (`out.n = sentinelCount entries`):
#   counting a non-marker non-total value, counting every entry (the pre-fix len
#   fallback), and dropping the first entry. Each refinement argument carries over
#   (a faithful counterpart with that defect still mis-counts / aborts on the
#   failing decoration, so it would NOT resolve). Each carries a machine-checked
#   witness that ELABORATES against the loop-free rival and FAILS against the
#   frozen loop-solution (two real builds per case).
# VACUOUS (frame-write-readonly-input). The sibling carries this MANDATORY
#   because `kinds` is held at Acc(list_pred(kinds), 1/2) and a store into it is
#   rejected for insufficient permission. This backend is referentially
#   transparent and declares no `mut` binder over any input — `entries` is an
#   immutable value with no heap footprint — so there is no read-only input to
#   overwrite and no permission system to trip. Not fabricated (porting map:
#   vacuous here).
# DROPPED (AXIOM_TESTS). The sibling's axiom lane validates its A-reference deep
#   model (counts_as_mock / count_sentinel_directives) against the real identity
#   semantics. This bundle declares no axioms and no deep-model references
#   (mapping.md §3: the scan calls no unchanged external operation; every step is
#   R or I), so there is nothing to probe — and this gate ignores AXIOM_TESTS
#   regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `entries : List ArgEntry` (per-element fields isAttribute / valueId /
#   eqTotal), and two independent clauses. Both are attacked:
#   * E1 (`out.err = false`) by weak-abort-on-nontotal;
#   * E2 (`out.n = sentinelCount entries`) by weak-count-nontotal-as-marker,
#     weak-count-everything, and weak-skip-first-entry, across three distinct
#     sub-domains (over-count a non-total value; count every entry; drop the
#     first).
#   The four reject witnesses probe four DISTINCT input points (pts = 4):
#     [⟨false,2,false⟩]                     — non-total non-marker (E1: err)
#     [⟨false,5,false⟩, ⟨false,0,true⟩]     — non-total non-marker + marker (E2)
#     [⟨true,0,true⟩]                       — attribute-bound (E2)
#     [⟨false,0,true⟩]                      — marker at the boundary (E2)
#   `isAttribute` is varied (true in weak-count-everything, false elsewhere),
#   `valueId` is varied (2, 5, 0, 0 — marker and non-marker), `eqTotal` is varied
#   (false in the two totality/over-count witnesses, true elsewhere) and is the
#   binder weak-abort-on-nontotal specifically abuses — so no field of the
#   element carrier is held constant across the witnesses. List length is varied
#   (1 and 2). No two rivals share an input tuple.
# WITNESS DISCRIMINATION (verified during authoring with two real builds per
#   reject case): each witness ELABORATES against its loop-free rival (the
#   extracted tester `decide`s to false — the rival's output violates the
#   postcondition at the probed input) and FAILS against the frozen loop-solution
#   (whose extracted fixpoint stays stuck under decide). No witness binds a
#   hypothesis (the carrier is fully transparent), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
AXIOM_TESTS = []
