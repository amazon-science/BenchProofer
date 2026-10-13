"""properties.py — G-PBT falsification battery for django__django-12262 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct bindTagArguments`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE. One contracted method that decides the binding OUTCOME of a
custom template tag's already-classified argument list:

  bindTagArguments
      (bits : List Bit)
      (positionalParams keywordOnlyParams keywordOnlyDefaults : List Name)
      (acceptsExtraKeywords acceptsExtraPositional hasDefaults : Bool)
      (numDefaults : Nat) return (out : Option Err)
    ensures out = parseBits bits positionalParams keywordOnlyParams
                            keywordOnlyDefaults acceptsExtraKeywords
                            acceptsExtraPositional hasDefaults numDefaults

``parseBits`` is a total, fully-unfolded pure function of the method's own eight
inputs (``axioms`` region declares nothing — no opaque answer key): it seeds the
scan state, folds ``stepBit`` left-to-right over ``bits`` (inert once an error is
recorded — the real scan stops at the first malformation), then ``finalize``s the
leftover requirements. The single ``ensures`` pins the result to that fold, so
the unique satisfier IS the grounded decision — evaluating ``parseBits`` is the
correct answer, and there is no wrong echo to build (the honest cheapest-reshape
positive controls stand in for a positive).

The load-bearing discriminations ``stepBit`` / ``finalize`` compose, each
independently attackable:
  * a keyword names NO declared parameter (positional or keyword-only) AND the
    tag accepts no extra keywords => UNEXPECTED. The admissibility test is against
    the FULL declared keyword-only set, INDEPENDENT of which names are still
    pending (a keyword-only parameter carrying a default, or already supplied, is
    still recognised as accepted) — this is the fixed behaviour;
  * an already-recorded keyword => DUPLICATE (checked AFTER unexpected; on the
    first problematic keyword the two are mutually exclusive);
  * a positional after any keyword was bound => ordering error;
  * a positional with no pending positional left and no extra-positional
    acceptance => too-many;
  * at finalize, when the callable carries positional defaults its last
    ``numDefaults`` positional parameters are considered satisfied and dropped
    before the leftover-requirement check;
  * otherwise the list bound successfully (``none``).

The EIGHT input binders are all free and the post-image must hold for EVERY value
of each; every reject witness below varies them (see the footer's coverage
table): ``bits`` (shape/content), the three name lists, and the four flag/count
scalars.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival keeps the gold body verbatim then WRITES into a
    read-only sequence input granted only at half heap permission, and must be
    rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder on any input, there is no heap and no aliasing. There is no
    read-only input to overwrite and no permission system to trip, so the class
    is vacuous. No substitute is fabricated (per the porting map).
  * NON-TERMINATION - CLOSED BY THE SEMANTICS, not a vacuous class and not a
    hole. This entry has now been corrected twice, and the second correction is
    what is withdrawn here.
    (i) The first version said "vacuous because the bundle is
    partial-correctness". False: this bundle sets
    ``loom.semantics.termination "total"``, and its only correctness ``open`` is
    ``open TotalCorrectness DemonicChoice``. The ``set_option`` elaborator itself
    runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the
    ``open`` cannot disagree.
    (ii) The second version accepted that but claimed the ``decreasing`` clause is
    still not enforced as a descent obligation, citing two exit-0 builds. BOTH
    ARE FALSE, re-measured against the frozen file:
      - frozen loop with the body reduced to ``st := st`` (never advances ``i``)
        and the frozen ``decreasing bits.length - i`` kept verbatim, proofs
        reduced to a bare ``loom_solve``: REJECTED, exit 1, ``unsolved goals`` at
        the loop, on ``case «decreasing_1: bits.length - i»`` (and ``ensures_1``);
      - the same impl with the measure replaced by the constant ``(1 : Nat)``:
        REJECTED as well, on ``case «decreasing_1: (1 : Nat)»``.
    So the descent obligation IS emitted and IS live: the measure-carrying rival,
    which cannot be dismissed as merely missing an annotation, fails on the
    measure's own case. A loop with no measure at all is refused even earlier, at
    elaboration (``Decreasing annotations are required in total correctness
    semantics``). Under total semantics a postcondition is claimed of ALL runs, so
    a never-answering impl does NOT satisfy this spec, and the fact that
    ``done_with i = bits.length`` is assumed at loop exit cannot launder anything:
    the descent goal fires before that exit argument is reached. Nothing is
    escalated; the frozen spec needs no change.
    No reject case is shipped even so, and the reason is the WITNESS CONTRACT: a
    reject case needs a witness that ELABORATES against the rival, and a rejected
    diverging rival's module does not compile at all (the obligation fails at the
    ``method`` itself, ahead of any appended tester), so the gate would return
    ``witness-unproven`` -> INCONCLUSIVE rather than a rejection.
    That is the shape with NO measure. A rival that CARRIES a measure which
    does not decrease is refused at the ``prove_correct`` site instead, which
    the witness file strips, so that module does elaborate; but its post-image
    is then an unreduced ``forIn Lean.Loop.mk`` term carrying
    ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
    kernel will not normalise to a value a concrete-input tester can decide.
    Both shapes therefore land ``witness-unproven``.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``parseBits`` of the method's own inputs, computed entirely by a
    concrete ``def`` chain in the ``pure`` region. There is no value an echo could
    carry that satisfies the ensures yet is behaviourally wrong.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The decision surface has many
    sub-domains a rival can get right on most inputs yet diverge on one: the
    full-vs-pending keyword-only admissibility test (the F2P scenario), the
    duplicate-vs-unexpected error kind, the catch-all acceptance, the
    positional-ordering / too-many / defaults-truncation sub-behaviours.

WITNESS MECHANICS on this carrier — and WHICH IMPL the refutations are actually
checked against. The frozen impl is a ``while`` loop, which elaborates to a term
the kernel cannot reduce, so the frozen method's tester never ``decide``s: it is
STUCK, not false. That is the whole subtlety here, and the earlier note claiming
each witness "FAILS against the frozen solution" as the discrimination half was
misleading — gold's exit code carries NO information about the claim. Measured
per reject case, for all seven, with ``scripts/lean_verify.sh``:

  * witness vs its RIVAL                          -> exit 0 (elaborates)
  * witness vs the FROZEN solution                -> exit 1, but the error is
      ``Tactic `decide` failed for proposition … because its `Decidable`
      instance … did not reduce to `isTrue` or `isFalse` … reduction got stuck
      at the `Decidable` instance``
  * the FORGERY — the same witness with the claim FLIPPED to ``= true``, i.e.
      asserting the rival's wrong answer is the spec's answer — vs the frozen
      solution -> exit 1 with the BYTE-IDENTICAL stuck-reduction error.

So gold cannot serve as the discriminating subject on this carrier: a forged
witness would fail there exactly as the honest one does. What makes these cases
genuine is the subject the gate actually uses. G-PBT screens that stuck
reduction (``gold_stuck_screen: "reduction"`` in the record) and re-refutes each
witness against a VERIFYING positive of this same spec — here ``pos-direct-fold``,
which is loop-free and therefore kernel-reducible. Against that subject the pair
SEPARATES, which is the real evidence:

  * witness vs the verifying positive   -> exit 1, and the error is a genuine
      evaluation: ``Tactic `decide` proved that the proposition
      bindTagArgumentsTester <args> = false is false``
  * FORGERY (``= true``) vs the same positive -> exit 0.

That is a decided refutation whose exit code TRACKS the claim, in both
directions. An impl the verifier accepts cannot violate its own spec, so a
witness that fails there is a real counterexample to the rival. Each reject rival
is written STRAIGHT-LINE (an inline ``bits.foldl`` or a constant) so ITS OWN
tester reduces and ``decide`` settles it. No ``sorry`` / ``admit`` /
``native_decide`` / ``axiom``.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no A-reference
deep model (the binding decision is modeled deeply in the ``pure`` region; the
two unchanged callees are folded into the free input ``bits``). Nothing in the
proof rests on an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12262"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole executable body (the scan loop + finalize).
# ---- Lies wholly inside the one impl region and is unique in Solution.lean;
# ---- both facts are asserted by _swap. Every variant replaces this block, so
# ---- any drift of the frozen impl breaks the manifest loudly. ----
_IMPL = """    -- impl-start
    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults
    let mut i := 0
    while i < bits.length
      invariant i ≤ bits.length
      invariant st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)
      done_with i = bits.length
      decreasing bits.length - i
    do
      let b := bits[i]!
      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b
      i := i + 1
    return finalize st hasDefaults numDefaults
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The single loop-body update line (a substring of _IMPL, unique in the file).
# Anchor for the loop-preserving positive control, which retunes only this line.
_STEP_LINE = ("      let b := bits[i]!\n"
              "      st := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b\n"
              "      i := i + 1\n")
assert _BASE.count(_STEP_LINE) == 1, "loop-body step line drifted"

# The state initializer (unique). Anchor for the admissibility in-region assert.
_INIT = "    let mut st : PState := initState positionalParams keywordOnlyParams keywordOnlyDefaults\n"
assert _BASE.count(_INIT) == 1, "state initializer drifted"

# ---- proof-body anchors. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view, so a reshape may retune its script without touching
# ---- the spec or dropping the obligation. Rivals leave it as-is (their
# ---- rejection is carried by the witness, not the tactic script). ----
_PROOF = """prove_correct bindTagArguments by
  loom_solve
  case «invariant_2: st = (bits.take i).foldl (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional) (initState positionalParams keywordOnlyParams keywordOnlyDefaults)» =>
    have hi : i < bits.length := by omega
    rw [invariant_2,
        scan_take_step (stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional)
          (initState positionalParams keywordOnlyParams keywordOnlyDefaults) bits i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [parseBits]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# The final catch-all tactic line (unique; retuned by the admissibility case to
# also discharge its in-region assert's concrete goal).
_PROOF_TAIL = "  all_goals simp_all [parseBits]"
assert _BASE.count(_PROOF_TAIL) == 1, "proof tail drifted"


def _impl(body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(body), _PROOF, proof)


# ---- Straight-line rival helper. A rival re-expresses the whole scan as an
# ---- inline `bits.foldl` over a per-bit step lambda, so its tester reduces
# ---- under `decide`. The step lambda below is the gold `stepBit` spelled
# ---- inline; each rival is built by a single targeted edit of ITS OWN clause
# ---- (the drift guard is the _swap on _IMPL above, which replaces the whole
# ---- region and fails loudly if the frozen impl ever changes). ----
_GOLD_STEP = """        match st.error with
        | some _ => st
        | none =>
          match bit with
          | .keyword p =>
              if !positionalParams.contains p && !keywordOnlyParams.contains p && !acceptsExtraKeywords then
                { st with error := some (.unexpectedKeyword p) }
              else if st.recorded.contains p then
                { st with error := some (.duplicateKeyword p) }
              else
                let recorded' := st.recorded ++ [p]
                if st.pendingPositional.contains p then
                  { st with recorded := recorded', pendingPositional := st.pendingPositional.erase p }
                else if st.pendingKeywordOnly.contains p then
                  { st with recorded := recorded', pendingKeywordOnly := st.pendingKeywordOnly.erase p }
                else
                  { st with recorded := recorded' }
          | .positional =>
              if !st.recorded.isEmpty then
                { st with error := some .positionalAfterKeyword }
              else
                match st.pendingPositional with
                | [] =>
                    if acceptsExtraPositional then st
                    else { st with error := some .tooManyPositional }
                | _ :: rest => { st with pendingPositional := rest }"""


def _scan_body(step, final="hasDefaults numDefaults"):
    """A straight-line impl body: fold `step` over `bits`, then finalize."""
    return ("    return finalize\n"
            "      (bits.foldl (fun st bit =>\n" + step + "\n        )\n"
            "        (initState positionalParams keywordOnlyParams keywordOnlyDefaults))\n"
            "      " + final)


def _step_edit(old, new):
    """A rival step lambda differing from gold by one clause (asserted unique)."""
    if _GOLD_STEP.count(old) != 1:
        raise AssertionError(f"rival edit anchor not unique: {old!r}")
    return _GOLD_STEP.replace(old, new, 1)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `bindTagArgumentsTester <args> = false` says the extracted program's
# ---- result violates the postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped, so no tactic script
# ---- can mask the verdict. There is no `require` clause, so the precondition is
# ---- `True` and decides trivially. ----
_TESTER = ("extract_program_for bindTagArguments\n"
           "prove_precondition_decidable_for bindTagArguments\n"
           "prove_postcondition_decidable_for bindTagArguments\n"
           "derive_tester_for bindTagArguments\n\n")


def _witness(args):
    return _TESTER + f"example : bindTagArgumentsTester {args} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the identical obligation statement;
    # only the executable surface and (where needed) the tactic script move.
    # =====================================================================
    {
        "id": "pos-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the loop entirely and return the modeled decision
        # directly. Observationally identical (the loop's post-state fed to
        # finalize IS `parseBits`), so the ensures holds definitionally; the
        # tactic script is retuned to `loom_solve` alone because the no-loop
        # body leaves none of the loop-invariant goals the frozen script closes.
        "module": _impl_reproved(
            "    return parseBits bits positionalParams keywordOnlyParams keywordOnlyDefaults acceptsExtraKeywords acceptsExtraPositional hasDefaults numDefaults",
            "prove_correct bindTagArguments by\n  loom_solve"),
        "rationale": "returning the modeled decision directly satisfies "
                     "`out = parseBits …` definitionally; a correct loop-free "
                     "reshape must verify, else SPEC-TOO-STRONG on the loop form. "
                     "Proof retuned (`loom_solve` alone) since the no-loop body "
                     "emits none of the loop-invariant VCs.",
    },
    {
        "id": "pos-loop-body-let",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the stepped state to a local before assigning it, keeping
        # the SAME loop, SAME invariants and SAME accumulator. Definitionally
        # identical, so the frozen loop-invariant proof discharges unchanged.
        "module": _swap(
            _BASE, _STEP_LINE,
            "      let b := bits[i]!\n"
            "      let stepped := stepBit positionalParams keywordOnlyParams acceptsExtraKeywords acceptsExtraPositional st b\n"
            "      st := stepped\n"
            "      i := i + 1\n"),
        "rationale": "hoisting the per-bit step into a `let` before the mutation "
                     "computes the SAME accumulator on every iteration, so the "
                     "ensures still discharges with the frozen invariants and the "
                     "frozen tactic script; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on the loop body's exact form.",
    },

    # =====================================================================
    # ADMISSIBILITY. The method carries NO `require` clause, so the sibling's
    # "a normal input satisfies the precondition" probe is degenerate (every
    # input is in-domain). The residual admissibility risk on a total-domain
    # spec is that the post-image is DEGENERATE at the interesting points — a
    # spec no impl distinguishes reads exactly like one every impl meets. This
    # case discharges an in-region assert pinning that `parseBits` genuinely
    # distinguishes the three central outcomes: a keyword-only-with-default
    # supplied once BINDS (none); an unknown keyword with no catch-all is
    # UNEXPECTED; the same keyword-only name supplied twice is DUPLICATE (not
    # unexpected). The rest of the impl is kept verbatim so the method's own
    # obligation still discharges; the proof is retuned to also close the assert.
    # =====================================================================
    {
        "id": "admiss-outcome-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _INIT,
                "    assert (with_name_prefix `assert\n"
                "      (parseBits [Bit.keyword 1] [] [1] [1] false false false 0 = none ∧\n"
                "       parseBits [Bit.keyword 9] [] [] [] false false false 0 = some (Err.unexpectedKeyword 9) ∧\n"
                "       parseBits [Bit.keyword 1, Bit.keyword 1] [] [1] [] false false false 0 = some (Err.duplicateKeyword 1)))\n"
                + _INIT),
            _PROOF_TAIL,
            "  all_goals first | (refine ⟨by decide, by decide, by decide⟩) | simp_all [parseBits]"),
        "rationale": "the post-image is satisfiable AND non-degenerate: `parseBits` "
                     "genuinely distinguishes its three central outcomes — a "
                     "keyword-only parameter carrying a default supplied once BINDS "
                     "(`none`), an unknown keyword with no catch-all is UNEXPECTED, "
                     "and the same keyword-only name supplied twice is DUPLICATE "
                     "(not UNEXPECTED). The in-region assert must discharge (else "
                     "the decision would be constant / the obligation degenerate); "
                     "the impl is kept verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing tests. Each rival is written
    # straight-line so its tester reduces under `decide`.
    # =====================================================================
    {
        "id": "weak-prepatch-pending-kwonly",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch defect (the reverted edit): the unexpected-keyword test
        # consults the MUTATING pending-keyword-only set instead of the FULL
        # declared keyword-only set. A keyword-only parameter carrying a default
        # (absent from the pending set) supplied once is then wrongly UNEXPECTED.
        "module": _impl(_scan_body(_step_edit(
            "if !positionalParams.contains p && !keywordOnlyParams.contains p && !acceptsExtraKeywords then",
            "if !positionalParams.contains p && !st.pendingKeywordOnly.contains p && !acceptsExtraKeywords then"))),
        "refinement": "this IS the reverted pre-patch decision: the "
                      "unexpected-keyword admissibility test consults the "
                      "mutating pending-keyword-only set (keyword-only names "
                      "without a default, minus those already supplied) rather "
                      "than the full declared keyword-only set. Its faithful real "
                      "counterpart raises 'unexpected keyword argument' for a "
                      "keyword-only-with-default supplied once, so it FAILS the "
                      "F2P test_simple_tags / test_inclusion_tags expectations "
                      "(the value is accepted, not an error). It would NOT resolve.",
        "rationale": "REJECT from the ensures: on the discriminating sub-domain "
                     "(a keyword-only parameter carrying a default, supplied once) "
                     "`parseBits` binds successfully (`none`) because the "
                     "admissibility test is against the FULL declared set, but the "
                     "rival reports UNEXPECTED. Verifying would be SPEC-TOO-WEAK. "
                     "Refuted at bits=[keyword 1], keywordOnlyParams=[1], "
                     "keywordOnlyDefaults=[1] (moves the defaults binder to a "
                     "non-empty value).",
        "witness": _witness("[Bit.keyword 1] [] [1] [1] false true false 0"),
    },
    {
        "id": "weak-duplicate-as-unexpected",
        "kind": "uniqueness",
        "expect": "reject",
        # Collapses DUPLICATE into UNEXPECTED: a repeated acceptable keyword is
        # reported as an unexpected keyword instead of a duplicate.
        "module": _impl(_scan_body(_step_edit(
            "              else if st.recorded.contains p then\n"
            "                { st with error := some (.duplicateKeyword p) }",
            "              else if st.recorded.contains p then\n"
            "                { st with error := some (.unexpectedKeyword p) }"))),
        "refinement": "a counterpart that raised the 'unexpected keyword "
                      "argument' message (rather than 'received multiple values "
                      "for keyword argument') for a doubly-supplied keyword-only "
                      "parameter FAILS the F2P test_simple_tag_errors / "
                      "test_inclusion_tag_errors assertions that pin the "
                      "multiple-values message for `kwarg=42 kwarg=37`. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the ensures: on a repeated acceptable keyword "
                     "`parseBits` reports DUPLICATE (the spec pins the error KIND, "
                     "distinct from UNEXPECTED) but the rival reports UNEXPECTED. "
                     "Refuted at bits=[keyword 1, keyword 1], "
                     "keywordOnlyParams=[1].",
        "witness": _witness("[Bit.keyword 1, Bit.keyword 1] [] [1] [] false false false 0"),
    },
    {
        "id": "weak-ignore-catch-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the extra-keywords disjunct: a keyword unknown to a tag that
        # nonetheless accepts arbitrary extra keywords is wrongly UNEXPECTED.
        "module": _impl(_scan_body(_step_edit(
            "if !positionalParams.contains p && !keywordOnlyParams.contains p && !acceptsExtraKeywords then",
            "if !positionalParams.contains p && !keywordOnlyParams.contains p then"))),
        "refinement": "a counterpart that ignored the accepts-extra-keywords flag "
                      "would raise on a tag declaring an arbitrary-extra-keywords "
                      "catch-all that legitimately receives an unknown keyword, "
                      "breaking the unlimited-args-kwargs PASS_TO_PASS family that "
                      "relies on a catch-all accepting arbitrary keyword "
                      "arguments. It would NOT resolve.",
        "rationale": "REJECT from the ensures: the accepts-extra-keywords disjunct "
                     "is load-bearing — `parseBits` binds an otherwise-unknown "
                     "keyword when the flag is set (`none`), but the rival reports "
                     "UNEXPECTED. Refuted at bits=[keyword 9], acceptsExtraKeywords"
                     "=true (moves that flag binder to true, which no other reject "
                     "witness sets).",
        "witness": _witness("[Bit.keyword 9] [] [] [] true false false 0"),
    },
    {
        "id": "weak-never-raise",
        "kind": "uniqueness",
        "expect": "reject",
        # Always binds successfully: never reports any malformation.
        "module": _impl("    return none"),
        "refinement": "a real patch that never reported a malformation would "
                      "accept every malformed tag invocation, failing every error "
                      "F2P (test_simple_tag_errors / test_inclusion_tag_errors) "
                      "and the missing/unexpected assertions. It would NOT resolve.",
        "rationale": "REJECT from the ensures: on an unknown keyword with no "
                     "catch-all `parseBits` reports UNEXPECTED, but the rival "
                     "returns `none`. Verifying would be SPEC-TOO-WEAK (the report "
                     "obligation is unpinned). Refuted at bits=[keyword 9], all "
                     "flags false.",
        "witness": _witness("[Bit.keyword 9] [] [] [] false false false 0"),
    },
    {
        "id": "weak-ignore-too-many-positional",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the too-many-positional error: an extra positional bit with no
        # pending positional left is silently accepted regardless of the
        # accepts-extra-positional flag.
        "module": _impl(_scan_body(_step_edit(
            "                match st.pendingPositional with\n"
            "                | [] =>\n"
            "                    if acceptsExtraPositional then st\n"
            "                    else { st with error := some .tooManyPositional }\n"
            "                | _ :: rest => { st with pendingPositional := rest }",
            "                match st.pendingPositional with\n"
            "                | [] => st\n"
            "                | _ :: rest => { st with pendingPositional := rest }"))),
        "refinement": "a counterpart that never reported too-many-positional "
                      "would accept surplus positional arguments for a tag that "
                      "takes none extra, failing the too-many-positional error "
                      "assertions in the P2P error family. It would NOT resolve.",
        "rationale": "REJECT from the ensures: with no pending positional and "
                     "`acceptsExtraPositional = false`, `parseBits` reports "
                     "too-many, but the rival returns `none`. Refuted at "
                     "bits=[positional], all lists empty, acceptsExtraPositional"
                     "=false.",
        "witness": _witness("[Bit.positional] [] [] [] false false false 0"),
    },
    {
        "id": "weak-ignore-defaults-truncation",
        "kind": "uniqueness",
        "expect": "reject",
        # Finalizes as if the callable carried NO positional defaults: it never
        # drops the defaulted trailing positionals before the leftover-requirement
        # check, so an omitted defaulted positional is wrongly reported missing.
        "module": _impl(_scan_body(_GOLD_STEP, final="false 0")),
        "refinement": "a counterpart that ignored the positional defaults would "
                      "demand a value for a positional parameter that carries a "
                      "default, reporting it missing when it may legitimately be "
                      "omitted — breaking the one-default tag P2P family. It would "
                      "NOT resolve.",
        "rationale": "REJECT from the ensures via `finalize`'s defaults truncation: "
                     "with hasDefaults=true, numDefaults=1 and one pending "
                     "positional, `parseBits` drops the defaulted positional and "
                     "binds (`none`), but the rival (finalizing with `false 0`) "
                     "reports it missing. Refuted at bits=[], positionalParams=[1], "
                     "hasDefaults=true, numDefaults=1 (moves the defaults "
                     "flag/count binders).",
        "witness": _witness("[] [1] [] [] false false true 1"),
    },
    {
        "id": "weak-ignore-positional-after-keyword",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the ordering check: a positional bit after a keyword has been
        # bound is processed as an ordinary positional instead of an ordering
        # error.
        "module": _impl(_scan_body(_step_edit(
            "          | .positional =>\n"
            "              if !st.recorded.isEmpty then\n"
            "                { st with error := some .positionalAfterKeyword }\n"
            "              else\n"
            "                match st.pendingPositional with",
            "          | .positional =>\n"
            "                match st.pendingPositional with"))),
        "refinement": "a counterpart that dropped the ordering check would accept "
                      "a positional argument supplied after a keyword argument, "
                      "failing the 'positional argument(s) after some keyword "
                      "argument(s)' error assertion in the P2P error family. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the ensures: after a keyword binds, a following "
                     "positional makes `parseBits` report the ordering error, but "
                     "the rival consumes the pending positional instead (here "
                     "binding cleanly to `none`). Refuted at "
                     "bits=[keyword 1, positional], positionalParams=[5], "
                     "keywordOnlyParams=[1] (moves positionalParams off empty).",
        "witness": _witness("[Bit.keyword 1, Bit.positional] [5] [1] [] false false false 0"),
    },

    # ---- ADDED BY AUDIT. Two clauses of the frozen decision that no case above
    # ---- attacked: the FIRST-error-wins inertness of the scan, and the seed
    # ---- state's defaulted-keyword-only filter. Both rivals were built and
    # ---- their witnesses measured against the same subject the gate uses (a
    # ---- verifying loop-free positive of this spec, since gold's tester is
    # ---- stuck): rival exit 0, subject exit 1 with a decided
    # ---- "`decide` proved that the proposition … is false", and the
    # ---- claim-flipped FORGERY exit 0 against that subject. ----
    {
        "id": "weak-error-not-inert",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the `match st.error with | some _ => st` guard, so the scan keeps
        # stepping after a malformation is recorded and a LATER bit overwrites the
        # FIRST error. The spec pins the FIRST malformation (the real scan stops
        # there), so the reported error kind is wrong whenever two bits are both
        # problematic.
        "module": _impl(_scan_body(_step_edit(
            "        match st.error with\n"
            "        | some _ => st\n"
            "        | none =>\n",
            "        "))),
        "refinement": "a counterpart whose scan continued past the first "
                      "malformation would report the LAST problem rather than the "
                      "first, so an invocation that is both unexpected-keyword and "
                      "surplus-positional raises the wrong message — failing the "
                      "error-message assertions in the F2P error families, which "
                      "pin the FIRST error raised. It would NOT resolve.",
        "rationale": "REJECT from the ensures via the inertness of `stepBit` once "
                     "`error` is set: at bits=[keyword 9, positional] with all "
                     "lists empty and all flags false, `parseBits` reports "
                     "UNEXPECTED (the first malformation, and the fold is inert "
                     "thereafter) while the rival's second bit overwrites it with "
                     "too-many-positional. The only case attacking the "
                     "first-error-wins clause, and the only reject witness whose "
                     "`bits` carries TWO independently-problematic bits.",
        "witness": _witness("[Bit.keyword 9, Bit.positional] [] [] [] false false false 0"),
    },
    {
        "id": "weak-init-no-default-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # Seeds `pendingKeywordOnly` with the FULL declared keyword-only list
        # instead of filtering out the names carrying a default. Those names are
        # then still pending at finalize, so a keyword-only parameter that carries
        # a default and is simply omitted is wrongly reported missing.
        "module": _impl(
            "    return finalize\n"
            "      (bits.foldl (fun st bit =>\n" + _GOLD_STEP + "\n        )\n"
            "        { recorded := [], pendingPositional := positionalParams,\n"
            "          pendingKeywordOnly := keywordOnlyParams, error := none })\n"
            "      hasDefaults numDefaults"),
        "refinement": "a counterpart that seeded the pending keyword-only set with "
                      "every declared keyword-only name, rather than only those "
                      "lacking a default, would demand a value for a keyword-only "
                      "parameter that carries one — reporting it missing when it "
                      "may legitimately be omitted, which breaks the "
                      "keyword-only-with-default tag family. It would NOT resolve.",
        "rationale": "REJECT from the ensures via `initState`'s defaults filter: "
                     "with keywordOnlyParams=[1], keywordOnlyDefaults=[1] and NO "
                     "bits supplied, `parseBits` binds successfully (`none`) "
                     "because the defaulted name was never pending, but the rival "
                     "reports it missing. The only case attacking the seed "
                     "state's filter, and the only reject witness that moves "
                     "keywordOnlyDefaults to a non-empty value with EMPTY bits.",
        "witness": _witness("[] [] [1] [1] false false false 0"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 6 uniqueness — one mandatory frame-mutation, one
# non-termination). Every one is accounted for below. This battery carries 12
# cases (2 soundness, 1 admissibility, 9 uniqueness). The sibling contracts
# `bind_keywords` over THREE parallel READ-ONLY sequence inputs carrying
# fractional heap permissions plus a `catch_all` bool, returning a 3-valued code
# (0 OK / 1 UNEXPECTED / 2 DUPLICATE) via a @Pure `outcome` fold, under a
# MustTerminate obligation. This backend models the SAME per-bit binding decision
# but over a richer carrier: `bits : List Bit` with FIVE outcome kinds (it also
# models positional ordering, too-many-positional and the defaults-truncated
# missing-argument check that the sibling's 3-code abstraction elides), decided
# straight-line by the pure `parseBits`. The value surface carries across intact
# and is strictly RICHER; the permission surface, the loop-eagerness reshape and
# the termination obligation do not exist here.
#
#   sibling case                   -> here                              disposition
#   -----------------------------------------------------------------------------
#   pos-control-hoisted-guards     -> pos-loop-body-let                 PORTED (reshaped)
#   (no sibling / new positive)    -> pos-direct-fold                   ADDED
#   admiss-gold-baseline           -> admiss-outcome-nondegenerate      RE-AIMED
#   frame-mutation-append          -> (none)                            VACUOUS
#   diverge-before-answer          -> (none)                            SPEC-CLOSED
#   prepatch-default-unexpected    -> weak-prepatch-pending-kwonly      PORTED
#   duplicate-as-unexpected        -> weak-duplicate-as-unexpected      PORTED
#   ignore-catch-all               -> weak-ignore-catch-all             PORTED
#   always-ok-supporting           -> weak-never-raise                  PORTED
#   (no sibling / carrier-widening)-> weak-ignore-too-many-positional   ADDED
#   (no sibling / carrier-widening)-> weak-ignore-defaults-truncation   ADDED
#   (no sibling / carrier-widening)-> weak-ignore-positional-after-kw   ADDED
#   (no sibling / audit)           -> weak-error-not-inert              ADDED (audit)
#   (no sibling / audit)           -> weak-init-no-default-filter       ADDED (audit)
#
# 5 ported, 1 re-aimed, 1 vacuous, 1 closed by the semantics; 1 positive + 5 uniqueness
# rivals added (3 at port time, 2 by the audit).
#
# AUDIT PROBES that did NOT find a defect, recorded so the next reader does not
# re-spend the builds:
#   * SPEC-TOO-WEAK (attack D), four NEW wrong impls beyond the shipped set. All
#     four were correctly REJECTED, and each witness separated against the
#     verifying-positive subject (rival exit 0 / subject exit 1 "`decide` proved
#     … is false" / claim-flipped forgery exit 0):
#       - the scan not inert after the first error   -> SHIPPED as
#         weak-error-not-inert;
#       - the seed state's defaulted-keyword-only filter dropped -> SHIPPED as
#         weak-init-no-default-filter;
#       - `finalize`'s missing-argument list ORDER swapped (keyword-only names
#         before leftover positionals) -> rejected. Not shipped: the two shipped
#         additions already cover unattacked clauses, and this one attacks list
#         order rather than a decision;
#       - `finalize` dropping the defaulted positionals from the FRONT
#         (`drop numDefaults`) instead of the tail (`take (length - numDefaults)`)
#         -> rejected. Not shipped for the same reason; the defaults-truncation
#         clause already has a shipped rival.
#     No wrong impl VERIFIED, so no spec hole was found on the VALUE surface.
#   * SPEC-TOO-STRONG (attack E), three NEW correct reshapes. Two VERIFY, so the
#     spec is not over-tight on impl shape: `stepBit` unfolded by hand as a
#     top-level `bits.foldl` (verifies with the frozen script plus
#     `simp_all [parseBits]`), and `stepBit`'s body INLINED into the frozen loop
#     body (verifies once the loop-invariant case ends with `simp only [stepBit]`;
#     the frozen script alone leaves that goal open, which is a proof-script
#     tuning matter, not a spec one).
#     One reshape could NOT be closed and is recorded as UNCERTAIN, not as a
#     hole: swapping the guard ORDER so the duplicate test precedes the
#     admissibility test. That reshape is extensionally EQUAL to the frozen
#     decision — a name can only be in `recorded` if it already passed the
#     admissibility test, so on the first problematic keyword the two guards are
#     mutually exclusive (brute-forced over 34,560 inputs: 0 differences) — but
#     proving it needs exactly that "everything recorded is admissible" invariant,
#     which is not available as a lemma here and which four proof scripts failed
#     to derive (`simp_all [parseBits, stepBit]`, a `funext`/`congr` route, a
#     `simp only … ; rfl` route, and an `rfl` route; the first leaves the fold
#     equation unsolved, the second cannot unify `funext` against the goal). The
#     sibling battery reports the SAME reshape as needing that same unavailable
#     lemma, so this is a proof-engineering limit that both backends share, not
#     evidence the spec rejects a faithful impl. Flagged as uncertain.
#
# VACUOUS (frame-mutation-append): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body verbatim then appends to a read-only sequence input held
#   at half heap permission, and must be rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent: every parameter is an immutable
#   value, the method declares no `mut` binder, there is no heap and no aliasing.
#   There is no read-only input to overwrite and no permission system to trip, so
#   the class is vacuous. The sibling's "the input run must not be mutated"
#   obligation is structurally guaranteed by the ABSENCE of a `mut` binder, which
#   the frozen spec already encodes. No substitute fabricated.
# SPEC-CLOSED (diverge-before-answer) - corrected disposition, twice over, and
#   this text RETRACTS the "known spec hole" the previous revision recorded.
#   Revision 1 called the class VACUOUS on the ground that the bundle is
#   partial-correctness. That ground is false: Solution.lean line 4 sets
#   `loom.semantics.termination "total"` and line 7 opens `TotalCorrectness`;
#   the `set_option` itself runs `openScope `TotalCorrectness``
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`), so nothing later re-opens a
#   partial scope, and this file contains no `open PartialCorrectness` at all.
#   Revision 2 accepted that and then claimed the descent obligation is not
#   enforced anyway, on two exit-0 builds. RE-MEASURED against the frozen file,
#   both come out REJECTED:
#     * frozen loop, body replaced by `st := st` (never advances `i`), frozen
#       invariants and frozen `decreasing bits.length - i` kept verbatim, every
#       proof reduced to a bare `loom_solve` -> EXIT 1, `unsolved goals`, on
#       `case «decreasing_1: bits.length - i»` together with `ensures_1`.
#     * the same impl with `decreasing (1 : Nat)` -> EXIT 1 as well, on
#       `case «decreasing_1: (1 : Nat)»`. So the measure IS carrying a descent
#       obligation on this carrier, and the annotated rival is refused on the
#       measure's own goal rather than merely on a missing annotation.
#   That is the goal emitted by
#   `TotalCorrectness.DemonicChoice.WPGen.forWithInvariantLoop` (Loom
#   `MonadAlgebras/NonDetT/Basic.lean:544`), which takes `measure : β → Nat`; the
#   `PartialCorrectness` twin at :211 takes `measure : β → Option ℕ` and discards
#   it, and that is the rule this bundle does not use. It remains true that both
#   frozen invariants hold trivially for the no-op body (`i` stays 0 and
#   `initState … ` IS the `bits.take 0` fold) and that `done_with i = bits.length`
#   is assumed at loop exit rather than reached; under partial semantics that is
#   exactly what WOULD launder a never-answering impl. Under the total rule the
#   descent goal fires first, so it does not.
#   There is therefore no defect in the FROZEN spec to escalate. No reject case is
#   shipped, and the reason is the WITNESS CONTRACT: a reject case needs a witness
#   that ELABORATES against the rival, and the rejected rival's module does not
#   compile at all (the obligation fails at the `method` itself, ahead of any
#   appended tester), so the gate returns `witness-unproven` -> INCONCLUSIVE,
#   which fails the battery rather than recording a rejection. Disposition:
#   SPEC-CLOSED and unwitnessable, not a hole and not "vacuous".
# RE-AIMED (admissibility): the sibling ships the gold impl verbatim to confirm
#   the three half-permissions admit a normal binding run. This backend's method
#   has NO precondition and no permission surface, so that probe is degenerate
#   (every input is in-domain). It is re-aimed at the residual total-domain risk —
#   that the post-image is DEGENERATE at the interesting points — via an in-region
#   assert that `parseBits` genuinely distinguishes its three central outcomes
#   (keyword-only-with-default binds; unknown keyword is UNEXPECTED; repeated
#   keyword is DUPLICATE, not UNEXPECTED). The impl is kept verbatim so the
#   method's own obligation still discharges; the proof is retuned to also close
#   the assert VC.
#   AUDIT CHECK that this case is not self-satisfying: the assert has to be TRUE
#   for the case to verify, i.e. the retuned tactic tail does not close an
#   arbitrary goal. Measured by FALSIFYING the first conjunct — asserting the
#   keyword-only-with-default supplied once is `unexpectedKeyword 1` (the
#   pre-patch answer) instead of `none`, everything else identical — which FAILS,
#   exit 1, with `unsolved goals case «assert_1: …»` on exactly the falsified
#   conjunct. So the three concrete outcomes are genuinely discharged by
#   evaluation and the case is load-bearing, not decorative.
# PORTED-RESHAPED (pos-control-hoisted-guards): the sibling hoists each guard
#   condition into a typed boolean local, keeping the SAME forward loop and every
#   invariant. This backend's frozen impl folds the whole per-bit decision into
#   the pure `stepBit`, so the sibling's guard-hoist has no counterpart; the
#   reshape SPIRIT — "structurally different, behaviourally identical, frozen
#   invariants kept" — is carried by pos-loop-body-let (bind the stepped state to
#   a `let` before the mutation). pos-direct-fold adds a second, loop-free
#   positive (return `parseBits` directly), the shape most likely to expose a
#   loop-form-dependent SPEC-TOO-STRONG.
# ADDED (3 uniqueness): the sibling's 3-code `outcome` abstraction models only
#   UNEXPECTED / DUPLICATE / OK, so it has no case for the ordering, too-many-
#   positional or defaults-truncated-missing behaviours this carrier models. Each
#   of the three added rivals attacks one such transparent clause of `parseBits`
#   AND moves a binder the ported rivals hold fixed:
#     weak-ignore-too-many-positional  — attacks the too-many clause; moves
#       acceptsExtraPositional (implicitly, by attacking the branch it guards) and
#       exercises a `positional` bit.
#     weak-ignore-defaults-truncation  — attacks `finalize`'s defaults truncation;
#       the ONLY reject witness that moves hasDefaults=true / numDefaults=1.
#     weak-ignore-positional-after-kw  — attacks the ordering clause; the ONLY
#       reject witness that moves positionalParams off `[]` (to `[5]`).
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the EIGHT input binders of
#   the sole ensures (9 reject cases, 9 distinct input points):
#     bits                 — [keyword 1] / [keyword 1, keyword 1] / [keyword 9] /
#                            [positional] / [] / [keyword 1, positional] /
#                            [keyword 9, positional]: varied (single/double
#                            keyword, positional, empty, and two MIXED shapes —
#                            one keyword-then-positional, one where BOTH bits are
#                            independently problematic, which is what pins the
#                            first-error-wins clause).
#     positionalParams     — [] (8 rivals), [5] (positional-after-kw): both.
#     keywordOnlyParams    — [1] (prepatch, duplicate, positional-after-kw,
#                            init-no-default-filter), [] (others): both.
#     keywordOnlyDefaults  — [1] (prepatch, init-no-default-filter), [] (others):
#                            both, and now at two DIFFERENT bits shapes (a
#                            supplied defaulted keyword-only name, and an omitted
#                            one) — the two sides of the fixed behaviour.
#     acceptsExtraKeywords — true (catch-all), false (others): both.
#     acceptsExtraPositional — true (prepatch), false (others): both.
#     hasDefaults          — true (defaults-truncation), false (others): both.
#     numDefaults          — 1 (defaults-truncation), 0 (others): both.
#   Every independent top-level behavior `parseBits` composes is attacked: the
#   full-vs-pending keyword-only admissibility test (prepatch), the error KIND
#   split (duplicate-as-unexpected), the catch-all disjunct (catch-all), the
#   emit-vs-suppress guard (never-raise), the positional ordering clause
#   (positional-after-kw), the too-many-positional clause (too-many), the
#   defaults-truncated missing check (defaults-truncation), the FIRST-error-wins
#   inertness of the fold (error-not-inert), and the seed state's
#   defaulted-keyword-only filter (init-no-default-filter).
#   The one behaviour of the frozen impl NOT attackable as a reject case is loop
#   TERMINATION: a never-advancing loop VERIFIES here, which is the known spec
#   hole recorded above, not a coverage gap the battery can close.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no A-reference deep model (the binding decision is modeled deeply in
# the pure region; the two unchanged callees are folded into the free input
# `bits`), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
