"""properties.py — G-PBT falsification battery for django__django-14559 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_bulkUpdate`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``
and no new ``axiom``/``theorem`` beyond the frozen set). ``expect:"reject"``
passes iff (in scope AND it does NOT verify AND the case's refutation ``witness``
holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one modeled behavior; a single spec predicate over two input
binders). A batched modification over a sequence of stored-row identifiers
reports how many rows it matched across all fixed-size batches:

  problem_spec_bulkUpdate (keys : List Int) (batchSize : Nat)
                          (result : Option Nat) : Prop
    result = some (batchedMatchCount batchSize keys)     -- the load-bearing pin

with the precondition ``1 ≤ batchSize`` living in the ``correct_bulkUpdate``
binder. ``batchedMatchCount`` is a GROUNDED total function of the two inputs (it
splits ``keys`` into consecutive ``batchSize``-sized chunks and sums each chunk's
DISTINCT-identifier count, ``batch.dedup.length``), NOT an opaque answer key — so
there is no ungrounded oracle to echo. Every callee is transparent: the whole
carrier is decidable, so each reject witness is a plain ``decide`` at a concrete
input (no conditioning on opaque terms is needed).

BINDER STRUCTURE (read this before judging binder coverage). The pin depends on
BOTH input binders and both are exercised by the reject witnesses:

  * ``keys`` — the identifier sequence. Varied across empty ([]), a distinct
    singleton, and sequences containing a WITHIN-batch duplicate ([1,1]).
  * ``batchSize`` — the chunk width. Varied across {1, 2}. The duplicate
    semantics hinges on it: a repeated identifier in ONE batch collapses (counted
    once) while the SAME repeat SPLIT across two size-1 batches sums (counted
    once per batch). A rival that mishandles only one of these regimes verifies
    unless a witness lands in that regime, so the battery probes both: the
    within-batch collapse at ``batchSize = 2`` (no-dedup rival) and the
    cross-batch split at ``batchSize = 1`` (whole-sequence rival).

Every independent top-level clause of the spec is attacked. The pin has two
observable components — PRESENCE (``result`` is ``some _``, never ``none``) and
VALUE (the count equals ``batchedMatchCount``). The ``result-none`` rival attacks
presence; the remaining five attack the value along distinct axes (constant echo,
lost within-batch dedup, ignored batching, dropped tail batches, overlapping
windows).

The battery carries all three directions this gate exists to test: SPEC-TOO-WEAK
(the six ``expect="reject"`` rivals), SPEC-TOO-STRONG (the two ``soundness``
positives), and PRECOND-TOO-STRONG (``admissibility-f2p-shaped-inputs``, which
discharges the ``1 ≤ batchSize`` guard together with the pin, by evaluation, at
four ground inputs, then closes the frozen obligation verbatim).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds ``keys`` at a
    half-permission (``Acc(list_pred(keys), 1/2)``) and ships a MANDATORY
    frame-mutation rival that WRITES to it (``keys.append(0)``), rejected for
    insufficient permission. Lean is referentially transparent: ``keys`` is an
    immutable value with no heap footprint, no aliasing and no ``mut`` binder —
    there is no read-only input to overwrite and no permission to violate. NOT
    fabricated (per the porting map this class is vacuous here); see the
    accounting block and ``assessment``.

  * UNGROUNDED-ORACLE ECHO — N/A: the post-image is ``batchedMatchCount`` fully
    unfolded from the two inputs, not an axiomatized oracle; the ``axioms`` region
    declares no ``opaque``/``axiom``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof script is tuned to the frozen
``for``/``mut`` loop — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet proving the rival
CONTRADICTS the spec at one concrete input. Each was checked (two real
``lake env lean`` builds) to ELABORATE against its rival and to FAIL against the
frozen solution (so it discriminates rather than asserting a tautology). The
carrier is fully decidable — ``List Int``, ``Nat``, ``Option Nat`` all derive
``DecidableEq`` and ``List.toChunks`` / ``List.dedup`` compute on ground literals
— so each witness ``unfold``s the spec + rival and ``decide``s a concrete
(in)equality of ``Option Nat``; against gold the same ``decide`` faces
``some (batchedMatchCount ..) = some (batchedMatchCount ..)`` and reports the
proposition false, i.e. the build FAILS.

AXIOM lane: EMPTY. ``meta.json`` declares no axiom and no ``deep_model_reference``
that G-PBT would probe here — the per-batch matched tally is modeled DEEPLY as
``batch.dedup.length`` (a total operation over the identifier sequence), not as an
opaque callee. The nagini sibling's ``matched_rows`` @ContractOnly axiom and its
two AXIOM_TESTS belong to the G-AX lane, which this gate ignores. ``AXIOM_TESTS``
is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-14559"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (each unique inside Solution.lean; verified at load).
# The full impl body is the load-bearing shape of the impl region; every impl
# reshape lands entirely inside `-- impl-start`/`-- impl-end`. The full frozen
# tactic body lies wholly inside `-- proof-start`/`-- proof-end`; only the
# soundness positives (which legitimately re-prove) touch it. The reject rivals
# leave it frozen — they are judged by their witness, not by whether the frozen
# script happens to break against their reshaped impl.
# ---------------------------------------------------------------------------
_IMPL = (
    "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
    "  if keys.isEmpty then\n"
    "    return some 0\n"
    "  let batches := List.toChunks batchSize keys\n"
    "  let mut rowsUpdated := 0\n"
    "  for batch in batches do\n"
    "    rowsUpdated := rowsUpdated + batch.dedup.length\n"
    "  return some rowsUpdated"
)

_PROOF = (
    "  intro keys batchSize hb\n"
    "  unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched\n"
    "  by_cases h : keys.isEmpty\n"
    "  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`\n"
    "    have hk : keys = [] := List.isEmpty_iff.mp h\n"
    "    have hc : List.toChunks batchSize ([] : List Int) = [] := by\n"
    "      cases batchSize with\n"
    "      | zero => omega\n"
    "      | succ m => rfl\n"
    "    subst hk\n"
    "    simp only [Id.run, h, if_true, hc, List.foldl_nil]\n"
    "    rfl\n"
    "  · -- non-empty input: bridge the desugared loop to the helper, then close\n"
    "    simp only [Id.run, h, if_false, Bool.false_eq_true]\n"
    "    show some (Id.run (forIn (List.toChunks batchSize keys) 0\n"
    "        (fun batch r => ForInStep.yield (r + batch.dedup.length))))\n"
    "      = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))\n"
    "    rw [forIn_sum_bulkUpdate]"
)

assert _BASE.count(_IMPL) == 1, "impl anchor drift"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec + proof view intact)."""
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_proof(new_impl: str, new_proof: str) -> str:
    """Solution.lean with the impl AND the proof body replaced (spec view intact,
    theorem STATEMENT byte-identical). For soundness positives that must re-prove
    a structurally different impl."""
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


def _with_proof_prefix(prefix: str) -> str:
    """Solution.lean with the FROZEN impl and the FROZEN tactic body both intact,
    and `prefix` inserted ahead of that tactic body. For the admissibility case:
    the extra `have`s must discharge on their own and the frozen obligation is
    then closed VERBATIM, so a failure is attributable to the added assertions
    rather than to a re-proof."""
    return _swap(_BASE, _PROOF, prefix + _PROOF)


# ---------------------------------------------------------------------------
# Witness scaffold. The spec is a bare decidable predicate, so a witness states
# its negation directly at a ground input: `¬ problem_spec_bulkUpdate keys bs
# (implementation_bulkUpdate keys bs)`. Checked in a file whose frozen obligation
# is elided by the gate, so no tactic script can mask the verdict. `decide`
# settles the `Option Nat` (in)equality after unfolding; against gold the same
# `decide` faces `some (batchedMatchCount ..) = some (batchedMatchCount ..)` and
# fails (the discriminator half).
# ---------------------------------------------------------------------------
def _witness(keys: str, bs: str) -> str:
    return (
        "example : ¬ problem_spec_bulkUpdate\n"
        f"    {keys} {bs}\n"
        "    (implementation_bulkUpdate\n"
        f"      {keys} {bs}) := by\n"
        "  unfold problem_spec_bulkUpdate implementation_bulkUpdate\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_bulkUpdate` statement byte-identical and re-proves its own
    # impl shape (no new axiom/lemma; no `sorry`/`admit`/`native_decide`).
    # =====================================================================
    {
        "id": "pos-drop-empty-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the early empty-input guard entirely and accumulate over
        # the chunks. `List.toChunks bs [] = []` for `bs ≥ 1`, so the loop yields 0
        # on the empty input too — the guard was redundant. The proof drops the
        # `by_cases` split and closes directly through the loop→fold helper
        # (verified with a real build).
        "module": _with_impl_proof(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  let batches := List.toChunks batchSize keys\n"
            "  let mut rowsUpdated := 0\n"
            "  for batch in batches do\n"
            "    rowsUpdated := rowsUpdated + batch.dedup.length\n"
            "  return some rowsUpdated",
            "  intro keys batchSize hb\n"
            "  unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched\n"
            "  show some (Id.run (forIn (List.toChunks batchSize keys) 0\n"
            "      (fun batch r => ForInStep.yield (r + batch.dedup.length))))\n"
            "    = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))\n"
            "  rw [forIn_sum_bulkUpdate]"),
        "rationale": "correct reshape that removes the redundant empty-input guard "
                     "(the batching already yields no batches on the empty sequence, "
                     "so the tally is 0 either way). It computes "
                     "batchedMatchCount on every input, so `result = some "
                     "(batchedMatchCount ..)` must hold — else SPEC-TOO-STRONG. "
                     "Proof: the loop→fold helper closes it without the case split; "
                     "no new axiom/lemma, statement unchanged. Measured caveat, so "
                     "the strength of this positive is not overstated: the FROZEN "
                     "tactic body also closes this impl (its `by_cases` split still "
                     "goes through, the empty arm just becomes redundant), so the "
                     "shortened script here is a convenience rather than a "
                     "necessity. `pos-foldl-no-loop` is the positive that genuinely "
                     "forces a re-proof — the frozen script FAILS on that impl.",
    },
    {
        "id": "pos-foldl-no-loop",
        "kind": "soundness",
        "expect": "verify",
        # Structurally different CORRECT reshape: keep the empty guard but replace
        # the mutable `for` accumulation with a direct `List.foldl` over the
        # chunks — definitionally the closed form `batchedMatchCount` computes. The
        # proof `simp`s the branch and closes each arm by `rfl` (verified with a
        # real build). Only impl + proof change; the theorem STATEMENT is identical.
        "module": _with_impl_proof(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  if keys.isEmpty then\n"
            "    return some 0\n"
            "  let batches := List.toChunks batchSize keys\n"
            "  return some (batches.foldl (fun acc batch => acc + batch.dedup.length) 0)",
            "  intro keys batchSize hb\n"
            "  unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched\n"
            "  by_cases h : keys.isEmpty\n"
            "  · have hk : keys = [] := List.isEmpty_iff.mp h\n"
            "    have hc : List.toChunks batchSize ([] : List Int) = [] := by\n"
            "      cases batchSize with\n"
            "      | zero => omega\n"
            "      | succ m => rfl\n"
            "    subst hk\n"
            "    simp only [Id.run, h, if_true, hc, List.foldl_nil]\n"
            "    rfl\n"
            "  · simp only [Id.run, h, if_false, Bool.false_eq_true]\n"
            "    rfl"),
        "rationale": "structurally different CORRECT reshape: the mutable loop is "
                     "replaced by the direct `List.foldl` over the chunks, which is "
                     "definitionally the closed form the spec pins to. A faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG. Proof: `rfl` closes "
                     "both branches after the `simp`; no loop→fold bridge needed, no "
                     "new axiom/lemma, statement unchanged. This is the load-bearing "
                     "positive: the FROZEN tactic body does NOT close this impl (its "
                     "`show` of the desugared `forIn` term no longer matches the "
                     "direct fold, measured), so the case really does exercise "
                     "re-provability of a different impl shape rather than riding "
                     "the frozen script.",
    },

    # =====================================================================
    # ADMISSIBILITY / PRECOND-TOO-STRONG — the obligation must be SATISFIABLE at
    # concrete inputs shaped like the ones the real behavior is read back at, not
    # merely provable in the abstract. On this total carrier that is the analogue
    # of the sibling's precondition-entry positive: each `have` discharges the
    # guard `1 ≤ batchSize` AND the whole spec predicate at a ground input BY
    # EVALUATION, and only then is the frozen obligation closed VERBATIM — so a
    # failure is attributable to the added assertions, not to a re-proof.
    # =====================================================================
    {
        "id": "admissibility-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_proof_prefix(
            "  -- ADMISSIBILITY. Four ground points, each carrying the guard\n"
            "  -- `1 ≤ batchSize` as a conjunct so an over-constrained precondition\n"
            "  -- would fail here, and each closed by `decide` on the fully unfolded\n"
            "  -- pin so an obligation the impl can never hit would fail too.\n"
            "  have adm_empty : 1 ≤ 1 ∧ problem_spec_bulkUpdate [] 1\n"
            "      (implementation_bulkUpdate [] 1) := by\n"
            "    refine ⟨by decide, ?_⟩\n"
            "    unfold problem_spec_bulkUpdate implementation_bulkUpdate\n"
            "    decide\n"
            "  have adm_repeat_one_batch : 1 ≤ 2 ∧ problem_spec_bulkUpdate [(7 : Int), 7] 2\n"
            "      (implementation_bulkUpdate [(7 : Int), 7] 2) := by\n"
            "    refine ⟨by decide, ?_⟩\n"
            "    unfold problem_spec_bulkUpdate implementation_bulkUpdate\n"
            "    decide\n"
            "  have adm_repeat_split : 1 ≤ 1 ∧ problem_spec_bulkUpdate [(7 : Int), 7] 1\n"
            "      (implementation_bulkUpdate [(7 : Int), 7] 1) := by\n"
            "    refine ⟨by decide, ?_⟩\n"
            "    unfold problem_spec_bulkUpdate implementation_bulkUpdate\n"
            "    decide\n"
            "  have adm_multi_batch : 1 ≤ 2 ∧ problem_spec_bulkUpdate [(1 : Int), 2, 3, 4, 5] 2\n"
            "      (implementation_bulkUpdate [(1 : Int), 2, 3, 4, 5] 2) := by\n"
            "    refine ⟨by decide, ?_⟩\n"
            "    unfold problem_spec_bulkUpdate implementation_bulkUpdate\n"
            "    decide\n"),
        "rationale": "PRECOND-TOO-STRONG probe. The frozen obligation carries one "
                     "precondition (`1 ≤ batchSize`) and pins the result to "
                     "`some (batchedMatchCount ..)`; neither is checked for "
                     "SATISFIABILITY by the other lanes, which only ask whether the "
                     "obligation is provable under the binder. This case discharges "
                     "the guard together with the full pin, by EVALUATION, at four "
                     "ground inputs spanning the observable regimes the modeled "
                     "behavior is read back at: the empty sequence (reports 0), a "
                     "repeat inside ONE batch (collapses to 1), the SAME repeat "
                     "split across two size-1 batches (sums to 2), and a "
                     "multi-batch distinct run (reports the full total). If the "
                     "guard were over-constrained, or the pinned count were a value "
                     "the operation can never report at such an input, the "
                     "corresponding `decide` would fail. The frozen tactic body then "
                     "closes the obligation verbatim, so the case adds assertions "
                     "rather than re-proving, and any failure is attributable to "
                     "them. Verified with a real build.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P tests. Across the six
    # witnesses, `keys` ranges over {[9],[5],[1,1],[1,2]} and `batchSize` over
    # {1,2}; the within-batch dedup regime (bs=2) and the cross-batch split
    # regime (bs=1) are both probed.
    # =====================================================================
    {
        "id": "result-none",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: the operation performs the modification but
        # reports nothing (returns `none` instead of a present count). Attacks the
        # PRESENCE component of the pin.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  return none"),
        "refinement": "returning no count at all is the literal pre-patch behaviour "
                      "(the operation used to report nothing). The faithful real "
                      "patch — leave the return value absent — is exactly what the "
                      "issue asks to change; the F2P tests that read back a numeric "
                      "matched count (an empty input expecting 0, a full run "
                      "expecting the total, the duplicate cases expecting 1 / 2) "
                      "would all FAIL against an absent return — it does NOT resolve.",
        "rationale": "REJECT from the pin `result = some (batchedMatchCount ..)`: the "
                     "rival returns `none`, which is never `some _`, so it violates "
                     "the PRESENCE half on every input. Refuted at a distinct "
                     "singleton [9], bs=1 (gold reports some 1, rival none).",
        "witness": _witness("[(9 : Int)]", "1"),
    },
    {
        "id": "const-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Always report a matched count of 0. Satisfies PRESENCE (it is `some _`)
        # and is correct on the empty input, but wrong for any non-empty sequence
        # whose batches match rows. Attacks the VALUE component.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  return some 0"),
        "refinement": "reporting a constant 0 reproduces the pre-patch effect for "
                      "non-empty inputs (no meaningful count). The faithful real "
                      "patch (return 0 always) would FAIL the full-run F2P test "
                      "(expects the total matched count, not 0) and both duplicate "
                      "cases (expect 1 / 2) — it does NOT resolve. Cheap supporting "
                      "case confirming the VALUE pin, not merely PRESENCE, carries "
                      "the discrimination.",
        "rationale": "REJECT from the pin: `some 0 ≠ some (batchedMatchCount ..)` "
                     "whenever the sequence matches ≥1 row. Refuted at [5], bs=1 "
                     "(gold some 1, rival some 0).",
        "witness": _witness("[(5 : Int)]", "1"),
    },
    {
        "id": "no-within-batch-dedup",
        "kind": "uniqueness",
        "expect": "reject",
        # Sum each batch's RAW length instead of its distinct-identifier count —
        # i.e. skip the within-batch collapse. Correct when every batch has no
        # repeats, WRONG when an identifier recurs inside one batch. Attacks the
        # `batch.dedup.length` (distinct-count) structure of the pin. Exercises the
        # bs=2 (within-batch) regime.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  if keys.isEmpty then\n"
            "    return some 0\n"
            "  let batches := List.toChunks batchSize keys\n"
            "  let mut rowsUpdated := 0\n"
            "  for batch in batches do\n"
            "    rowsUpdated := rowsUpdated + batch.length\n"
            "  return some rowsUpdated"),
        "refinement": "counting every identifier in a batch (raw length) rather than "
                      "the DISTINCT identifiers double-counts a repeat within a "
                      "single batch. The faithful real patch (sum each batch's key "
                      "count without accounting for the set-based match collapsing "
                      "duplicates) would FAIL the duplicate F2P case where a repeat "
                      "in ONE batch must report 1, not 2 — it does NOT resolve.",
        "rationale": "REJECT from the pin's per-batch distinct-count "
                     "(`batch.dedup.length`): the rival uses `batch.length`, which "
                     "exceeds it whenever a batch holds a repeat. Refuted at [1,1], "
                     "bs=2 (one batch [1,1]; gold some 1, rival some 2).",
        "witness": _witness("[(1 : Int), 1]", "2"),
    },
    {
        "id": "ignore-batching-whole-sequence",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore `batchSize`: dedup over the WHOLE sequence at once, as if it were a
        # single batch. Correct when the sequence fits in one batch, WRONG when a
        # repeat is SPLIT across batches (which must be counted once per batch).
        # Directly attacks the batching structure via the `batchSize` binder;
        # exercises the bs=1 (cross-batch split) regime.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  if keys.isEmpty then\n"
            "    return some 0\n"
            "  return some keys.dedup.length"),
        "refinement": "deduplicating the whole sequence in one shot collapses a "
                      "repeat that the real operation would match once PER batch. "
                      "The faithful real patch (count distinct identifiers globally "
                      "and return that) would FAIL the F2P case where the same "
                      "identifier split across size-1 batches must report 2, not 1 — "
                      "it does NOT resolve.",
        "rationale": "REJECT from the pin's per-BATCH tally: a global dedup drops the "
                     "batching entirely, so it disagrees with the sum-over-chunks "
                     "whenever a repeat spans two batches. Refuted at [1,1], bs=1 "
                     "(two singleton batches; gold some 2, rival some 1). This case "
                     "abuses the `batchSize` binder specifically.",
        "witness": _witness("[(1 : Int), 1]", "1"),
    },
    {
        "id": "first-batch-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Report only the FIRST batch's distinct count, dropping every later batch.
        # Correct on the single-batch sub-domain (len keys ≤ batchSize), WRONG for
        # multi-batch inputs. Attacks the sum-over-ALL-batches structure of the pin.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  if keys.isEmpty then\n"
            "    return some 0\n"
            "  let batches := List.toChunks batchSize keys\n"
            "  return some ((batches.headD []).dedup.length)"),
        "refinement": "reporting only the first batch's count is correct when "
                      "everything fits in one batch but drops every later batch. The "
                      "faithful real patch (return the first per-batch update() count "
                      "instead of the accumulated total) would FAIL the full-run F2P "
                      "test (many objects across batches expect the full total) and "
                      "the size-1 duplicate case (expects 2, this reports the first "
                      "batch's 1) — it does NOT resolve.",
        "rationale": "REJECT from the pin's SUM over all chunks: dropping the tail "
                     "batches understates the total whenever there is more than one "
                     "batch. Refuted at [1,2], bs=1 (two batches [1],[2]; gold "
                     "some 2, rival some 1).",
        "witness": _witness("[(1 : Int), 2]", "1"),
    },
    {
        "id": "overlapping-windows",
        "kind": "uniqueness",
        "expect": "reject",
        # Take a full-width window per element but advance the cursor by ONE, so
        # windows overlap and interior identifiers are counted repeatedly. Correct
        # only for batchSize = 1; grossly overcounts otherwise. Attacks the
        # DISJOINT-consecutive-chunk structure of the pin. `List.range` keeps the
        # loop decidable so the witness is a plain `decide`.
        "module": _with_impl(
            "def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do\n"
            "  if keys.isEmpty then\n"
            "    return some 0\n"
            "  let mut rowsUpdated := 0\n"
            "  for i in List.range keys.length do\n"
            "    rowsUpdated := rowsUpdated + ((keys.drop i).take batchSize).dedup.length\n"
            "  return some rowsUpdated"),
        "refinement": "summing over OVERLAPPING sliding windows (advance by one, take "
                      "a full batch each step) counts each interior identifier in up "
                      "to batchSize windows. The faithful real patch (issue an "
                      "update over each sliding window and sum) reports far more than "
                      "the true matched count, so the full-run F2P test (expects the "
                      "exact total) would FAIL — it does NOT resolve.",
        "rationale": "REJECT from the pin's DISJOINT consecutive chunking: the "
                     "overlapping walk revisits interior identifiers and overcounts "
                     "for any batchSize > 1. Refuted at [1,2], bs=2 (gold one batch "
                     "[1,2] → some 2; rival windows [1,2],[2] → some 3).",
        "witness": _witness("[(1 : Int), 2]", "2"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 1 MANDATORY frame-mutation, 4 uniqueness rivals)
# plus a 2-case AXIOM lane. This bundle models a NARROWER but IDENTICAL core
# behavior: the sibling contracts a heap-carrying `bulk_apply_count` with a
# half-permission read-only `keys` and a front-recursive `batched_total` oracle,
# whereas lean models the same per-batch matched-count fold as a pure total
# function `batchedMatchCount` over an immutable `List Int` + `Nat`. Every
# sibling case is recorded below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape             -> pos-drop-empty-guard        RE-EXPRESSED
#                                      (+ pos-foldl-no-loop)        ADDED positive
#   admissibility-entry             -> admissibility-f2p-shaped-inputs  PORTED
#                                      (guard conjunct only; the permission
#                                       conjunct is VACUOUS — no heap)
#   frame-mutation-keys-append      -> (none)                      VACUOUS (no heap)
#   const-zero-echo                 -> const-zero                  PORTED
#   partial-domain-first-group-only -> first-batch-only            PORTED
#   wrong-grouping-per-element      -> no-within-batch-dedup       RE-EXPRESSED
#                                      + ignore-batching-whole-seq  SPLIT
#   double-count-advance-by-one     -> overlapping-windows         PORTED
#   (pre-patch None return)         -> result-none                 ADDED (presence)
#   AXIOM_TESTS (2)                 -> (none)                      DROPPED (G-AX)
#
# RE-EXPRESSED (positive control): the sibling renames the cursor, reorders
#   commutative asserts, and rewrites the step-cap while keeping the gold
#   invariant set. Those framing asserts are nagini permission/invariant
#   machinery with no lean counterpart; the ARGUMENT ("a structurally different
#   but faithful impl must verify") is carried by two reshapes that ARE
#   expressible here: dropping the redundant empty guard (pos-drop-empty-guard,
#   proof loses the case split) and replacing the mutable loop by a direct
#   `List.foldl` (pos-foldl-no-loop, proof closes by `rfl`). Both re-prove the
#   byte-identical `correct_bulkUpdate` statement with a real `lake` build; no
#   new axiom/lemma, no sorry/native_decide.
# PORTED (admissibility) -> admissibility-f2p-shaped-inputs. An earlier revision
#   of this manifest recorded the lane as VACUOUS, on the argument that the only
#   precondition (`1 ≤ batchSize`) is a plain binder hypothesis the frozen proof
#   already uses (the empty-input `toChunks` case needs `batchSize ≠ 0`), so a
#   standalone positive would merely restate it. That reasoning was WRONG and the
#   omission is now repaired. "The frozen proof consumes the hypothesis" shows the
#   guard is USED, not that it is SATISFIABLE — and satisfiability is the whole
#   content of PRECOND-TOO-STRONG. The analogue on a total carrier is the
#   obligation being unsatisfiable at exactly the inputs the modeled behavior is
#   read back at, which a positive that discharges guard AND pin together at those
#   concrete inputs BY EVALUATION tests directly; the frozen obligation is then
#   closed verbatim, so nothing is re-proven and a failure is attributable to the
#   added assertions. Landed with a real build, so the lane is expressible here and
#   the earlier "vacuous" record was an effort gap, not a carrier fact. Only the
#   sibling's PERMISSION conjunct (`Acc(list_pred(keys), 1/2)`) has no counterpart
#   (see the frame-mutation entry below).
# VACUOUS (frame-mutation): the sibling carries this MANDATORY because `keys` is
#   held at `Acc(list_pred(keys), 1/2)` and its rival illegally writes to it
#   (`keys.append(0)`), rejected by the permission system. This backend is
#   referentially transparent and declares no `mut` input binder — `keys` is an
#   immutable value with no heap footprint and no aliasing — so there is no
#   read-only input to overwrite and no permission to violate. Not fabricated
#   (porting map: this class is vacuous on Lean-family carriers).
# PORTED / RE-EXPRESSED (value rivals): const-zero-echo ports directly
#   (return some 0). first-group-only ports as first-batch-only (report only the
#   head chunk). double-count-advance-by-one ports as overlapping-windows (full
#   window per element, advance by 1). wrong-grouping-per-element (nagini: sum
#   over single-key prefixes, which diverges from the per-group fold except when
#   group_size == 1) RE-EXPRESSES as TWO complementary rivals, because on this
#   carrier the "grouping is wrong" failure splits along the two regimes the
#   `batchSize` binder controls: no-within-batch-dedup uses raw `batch.length`
#   (wrong when a repeat sits in ONE batch, refuted at bs=2) and
#   ignore-batching-whole-sequence dedups globally (wrong when a repeat is SPLIT
#   across batches, refuted at bs=1). Splitting is what forces both `batchSize`
#   regimes into the witness set. result-none is ADDED to attack the PRESENCE
#   half of the pin (the literal pre-patch `None` return), which the nagini
#   surface expressed as `Result() is not None` — here `Option Nat`'s `none`.
#
#   The six reject witnesses probe SIX distinct input points: keys ∈
#   {[9],[5],[1,1],[1,1],[1,2],[1,2]} and batchSize ∈ {1,1,2,1,1,2}. Both spec
#   binders are varied: `keys` across empty-adjacent singletons, within-batch
#   duplicates, and multi-batch sequences; `batchSize` across {1,2} so the
#   within-batch collapse (bs=2) and the cross-batch split (bs=1) are each
#   exercised by a rival built to abuse exactly that regime. Both independent
#   observable clauses of the pin are attacked: PRESENCE (result-none) and VALUE
#   (the other five, along the constant / dedup / batching / tail / overlap axes).
#   Each witness was checked with two real `lake env lean` builds to ELABORATE
#   against its rival and FAIL against the frozen solution.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no `opaque` callee (the per-batch matched tally is modeled deeply as
# `batch.dedup.length`, a total operation over the identifier sequence, not an
# oracle), so there is nothing to probe and the gate ignores AXIOM_TESTS anyway.
AXIOM_TESTS = []
