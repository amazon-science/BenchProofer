"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-15100 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct stripDiacritics`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over a single read-only input):

  stripDiacritics (s : List Char) return (out : List Char)
    ensures out = markFreeSeq (canonicalDecompose s)                       (C1)

The operation maps a code-point sequence to its mark-free canonical form: first
decompose it canonically (``canonicalDecompose``), then keep every non-combining
code point and drop every combining mark (``markFreeSeq``). The single top-level
``ensures`` clause pins the composition of those two steps. The method has NO
``require`` clause, so the admitted domain is total; the sole input binder is
``s``.

C1 folds two facets a rival can violate independently:
  * facet (D) — the DECOMPOSITION step runs (the classifier is applied to
    ``canonicalDecompose s``, not to the raw ``s``); this is the behavioural
    delta the fix introduces (the pre-fix code short-circuits and returns the
    input untouched whenever it already equals its own decomposition — the exact
    already-decomposed input the issue reports);
  * facet (F) — the mark-FILTER keeps exactly the non-combining code points and
    drops exactly the combining marks (``markFreeSeq``'s keep/drop rule).

CARRIER NOTE — the decisive fact of this port. BOTH callees are ``opaque`` free
functions with no constraining axiom (mapping.md §3): ``canonicalDecompose :
List Char → List Char`` and ``isCombiningMark : Char → Bool`` (``markFreeSeq`` is
a transparent ``def`` written over ``isCombiningMark``). The post-image
``markFreeSeq (canonicalDecompose s)`` therefore has NO value the kernel can
compute at any concrete ``s`` — the decomposition of a literal is unknowable, and
the keep/drop rule turns on an unknowable combining class. Two consequences:

  * ``derive_tester_for`` / a ``…Tester s = false`` route cannot ``decide``
    anything (both the guard and the result live behind opaque terms), and the
    frozen impl is a ``while`` loop whose extracted ``…Exec`` does not reduce
    under a plain script. So witnesses reach the postcondition DIRECTLY, via the
    extracted ``stripDiacriticsExec`` program and the spec's own
    ``markFreeSeq``/``canonicalDecompose`` image — never a tester.
  * every attack must be stated against a term the elaborator cannot compute, so
    each reject witness CONDITIONS ON THE CARRIER (the prompt's technique): it
    quantifies over the code points ``canonicalDecompose`` produces at a chosen
    literal and over their combining class, states that equation and class as
    weak, jointly-satisfiable hypotheses, and refutes the rival at that
    described point. Each witness binds one ``canonicalDecompose`` equation plus
    one/two ``isCombiningMark`` class facts; the consistency probe cannot derive
    ``False`` from them (distinct opaque terms), so no witness is a forgery from
    an inconsistent premise.

WITNESS SUBJECT — why every reject case carries a ``witness_reference``. The
frozen impl CANNOT serve as the discrimination subject on this carrier, and the
reason is measured, not argued. Its ``while`` loop extracts to an
``NonDetT.run (forIn Lean.Loop.mk …)`` term that no plain script normalises, so
against the frozen impl the witness's hypothesis ``h`` stays that unreduced
loop term and the goal ``⊢ False`` is simply left unsolved — for EVERY claim,
regardless of truth. Three builds establish that gold's exit code carries no
information about what is being claimed:

  * the witness (``…Exec lit ≠ DivM.res (markFreeSeq (canonicalDecompose lit))``)
    fails on the frozen impl — ``unsolved goals … h : (NonDetT.run do let r ←
    forIn Lean.Loop.mk …) = DivM.res … ⊢ False``;
  * the FLIPPED claim (the same binders and the same tactic script with ``≠``
    replaced by ``=``, i.e. asserting the frozen impl is CORRECT there) fails on
    the frozen impl with the same unreduced-loop ``unsolved goals``;
  * even a trivially TRUE claim at the empty input fails there the same way.

So a witness asserting gold is correct would also have been recorded as a
refutation. The repair the harness provides is ``witness_reference``: a
loop-free impl of the SAME frozen spec that the gate independently checks
shares the spec and VERIFIES, for the witness to be refuted against instead.
An impl the verifier accepts cannot violate its own spec, so a genuine witness
must still fail there — and against this reference the claim DOES reduce, which
is what makes the exit code mean something. Measured per rival: the witness
ELABORATES against the rival (exit 0); against the reference it reduces to
``h : True ⊢ False`` (exit 1) — ``simp`` PROVED the postcondition equation for
that impl and could not for the rival, the strongest refutation signature
available; the FLIPPED claim VERIFIES against the reference (exit 0), so the
exit code tracks the claim rather than the carrier; and the consistency probe
cannot derive ``False`` from the hypotheses (exit 1).

ADVERSARIAL READ of the nagini classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    makes this class MANDATORY (the input carries ``Acc(list_pred(s), 1/2)`` and
    its sharpest rival WRITES into the read-only input — a store / an append — to
    trip INSUFFICIENT PERMISSION). Lean and Velvet are referentially transparent:
    ``s`` is an immutable value, this bundle declares NO ``mut`` parameter, and
    there is no heap, no aliasing, no permission system. There is no read-only
    input to overwrite and no substitute probe to build, so the class is vacuous
    (per the porting map, legitimately dropped, not fabricated). This accounts
    for BOTH nagini frame rivals (frame-mut-store, frame-mut-append).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. C1 pins the
    result to ``markFreeSeq (canonicalDecompose s)`` — ``markFreeSeq`` is a
    concrete ``def`` and the two callees are the SAME opaque terms the result is
    stated over, not a separate answer-key a wrong impl could echo (directive 8:
    the result is grounded in the sole input ``s`` through those callees). There
    is no wrong echo to build; the positive controls are honest reshapes.
  * DIVERGENCE / non-termination: CLOSED BY THE SEMANTICS on this backend, not
    vacuous. ``loom.semantics.termination`` is ``total`` here (the frozen spec
    carries a ``decreasing i`` measure and the impl is a terminating backward
    loop), and the option cannot drift from the file's
    ``open TotalCorrectness DemonicChoice`` because the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``). Under ``total`` a
    postcondition is claimed of ALL runs, not only terminating ones, so the
    verifier demands a decreasing measure on every loop AND discharges its descent.
    "A non-terminating rival cannot even be written" is withdrawn: a rival owns the
    whole impl region and the frozen body is already a loop, so the rival is
    writable, and it is REJECTED when written. Measured here with the proof reduced
    to a bare ``loom_solve``: a spliced loop with NO measure is refused at the
    ``method`` declaration
    (``Decreasing annotations are required in total correctness semantics``), and a
    loop CARRYING a non-decreasing measure
    (``while z > 0 / invariant z > 0 / done_with z = 0 / decreasing z``, body
    ``z := z + 1``) is refused on the measure's own goal:
    ``case «decreasing_1: z»``, residual ``⊢ z + 1 < z``. There is no
    partial-correctness hole to exploit (no velvet bundle sets ``partial``; all
    500 velvet ``Solution.lean`` set ``total``). (The sibling carries no
    divergence rival either.)

    NOT SHIPPED as a reject case, and the reason is the WITNESS half, not the
    verifier half — measured, not argued. A reject case must carry a witness
    that ELABORATES against its rival; a diverging rival's extracted
    ``stripDiacriticsExec`` is precisely the irreducible term this carrier
    cannot normalise, so the witness fails on the RIVAL side (exit 1,
    ``unsolved goals … h : (NonDetT.run do let _ ← forIn Lean.Loop.mk 1 …) =
    DivM.res [] ⊢ False``), and a direct ``… = DivM.div`` claim fails the same
    way (exit 1, the same unreduced ``forIn`` term). The ``witness_reference``
    repair cannot help here: it substitutes the GOLD subject, whereas this is
    the rival subject — the half that must SUCCEED. So the case would be
    recorded ``witness-unproven`` => MALFORMED-TESTS => gate ERROR, i.e.
    shipping it would fail this battery rather than strengthen it. The class is
    therefore genuinely CLOSED (the verifier does reject a diverging rival, so
    it is not a spec hole) but NOT EXPRESSIBLE as a G-PBT case on this carrier.
  * PARTIAL-DOMAIN / VALUE / CONTROL-FLOW — APPLIES, and is the whole reject
    surface. Each rival gets the shape right (a ``List Char``) and is correct on
    part of the domain, but violates facet (D) or facet (F) on the sub-domain the
    fix concerns (a code point whose decomposition carries a combining mark).

WITNESS PLACEMENT. The four reject witnesses sit at FOUR DISTINCT literal inputs
— ``['x']``, ``['y']``, ``['w']``, ``['z']`` — each conditioned on a DIFFERENT
opaque-carrier point (a decomposition to one combining mark, to one non-combining
base, again to a combining mark, and to two non-combining bases). So the sole
binder ``s`` moves across the battery, and each rival is refuted at a point that
exercises the specific keep/drop / decompose behaviour it mishandles rather than
at one pinned input. Facet (D) is attacked by the skip-decompose and
return-input rivals; facet (F) by the no-filter and inverted-filter rivals.

AXIOM lane: DROPPED. The axiom lane is G-AX's job; this bundle declares NO
``axiom`` (both callees are ``opaque`` free functions with nothing asserted about
their values — mapping.md §3 records the G-AX skip), so there is nothing here for
this gate to probe, and it ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-15100"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single
# ---- `-- impl-start`/`-- impl-end` region and is unique in Solution.lean (both
# ---- facts asserted at load by _swap), so every edit leaves the spec regions
# ---- (axioms/pure/pre/post + the method signature and the `ensures`) untouched.
# The ENTIRE frozen backward-fold loop body (used for the reject rivals and the
# direct-return positive control).
_GOLD_IMPL = """    -- impl-start
    let mut result : List Char := []
    let mut i := (canonicalDecompose s).length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ (canonicalDecompose s).length
      invariant result = markFreeSeq ((canonicalDecompose s).drop i)
      done_with i = 0
      decreasing i
    do
      let c := (canonicalDecompose s)[i - 1]!
      result := (if isCombiningMark c then [] else [c]) ++ result
      i := i - 1
    return result
    -- impl-end"""
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# The loop guard alone (unique inside the impl region) — for the guard-reshape
# positive control that keeps the whole loop scaffold + framing invariants.
_GOLD_GUARD = "    while i > 0\n"
assert _BASE.count(_GOLD_GUARD) == 1, "loop-guard anchor drifted"

# The first line of the impl body — for prepending the admissibility assert.
_GOLD_IMPL_HEAD = "    -- impl-start\n    let mut result : List Char := []"
assert _BASE.count(_GOLD_IMPL_HEAD) == 1, "impl-head anchor drifted"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-fold loop (it discharges the loop-body goal via the drop-step
# ---- lemma). A positive control that reshapes the impl away from that loop must
# ---- retune the tactic body; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct stripDiacritics` obligation survives with an identical
# ---- statement. Unique in the file.
_GOLD_PROOF = """prove_correct stripDiacritics by
  loom_solve
  rw [markFreeSeq_drop_step (canonicalDecompose s) i (by omega) (by omega)]
  simp_all"""
assert _BASE.count(_GOLD_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body drop-step lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct stripDiacritics by\n  loom_solve"

# ---- the WITNESS SUBJECT (see "WITNESS SUBJECT" in the module docstring).
# The frozen `while` loop extracts to an `NonDetT.run (forIn Lean.Loop.mk …)`
# term that no plain script normalises, so a witness built against the frozen
# impl leaves `⊢ False` unsolved for EVERY claim — the flipped claim and a
# trivially true claim fail identically. Its exit code therefore discriminates
# nothing. This loop-free impl of the SAME frozen spec is the subject the
# witnesses are refuted against instead: `same_spec` holds (only the elided impl
# region and `prove_correct` body differ), it VERIFIES (the gate re-checks both
# before using it), and its `…Exec` DOES reduce — so `simp` either proves the
# postcondition equation at the described point (`h : True`, the refutation) or
# leaves a concrete list equation (no refutation). Identical text to
# pos-direct-model's module, which the battery independently asserts verifies.
_WITNESS_REFERENCE = _swap(
    _swap(_BASE, _GOLD_IMPL,
          "    -- impl-start\n"
          "    return markFreeSeq (canonicalDecompose s)\n"
          "    -- impl-end"),
    _GOLD_PROOF, _PROOF_STRAIGHT)


def _reject(impl_body):
    """Full Solution.lean variant with ONLY the impl region body replaced by a
    straight-line rival (frozen tactic script kept — expected NOT to verify; the
    witness, not the module build, is what attributes the rejection to the
    spec)."""
    return _swap(_BASE, _GOLD_IMPL,
                 "    -- impl-start\n" + impl_body + "\n    -- impl-end")


# ---- witness preamble. `extract_program_for` names the rival's executable
# ---- `stripDiacriticsExec` (extraction needs no decidability); the witness then
# ---- states, at a concrete literal input CONDITIONED on the opaque carrier
# ---- (a `canonicalDecompose <lit> = <cps>` equation plus the `isCombiningMark`
# ---- class of those code points), that the rival's extracted output differs
# ---- from the spec's own `markFreeSeq (canonicalDecompose <lit>)` image. Under
# ---- those hypotheses the rival's straight-line body reduces (`simp [markFreeSeq,
# ---- …, NonDetT.run, pure]`) to a false list equation, while the frozen loop's
# ---- `…Exec` stays stuck — so the witness elaborates against the rival and
# ---- FAILS on gold. Checked in a file whose `prove_correct` block is stripped;
# ---- no `axiom`/`sorry`/`native_decide`.
def _witness(binders, lit, close):
    return (
        "extract_program_for stripDiacritics\n\n"
        f"example {binders} :\n"
        f"    stripDiacriticsExec {lit}\n"
        f"      ≠ DivM.res (markFreeSeq (canonicalDecompose {lit})) := by\n"
        "  unfold stripDiacriticsExec stripDiacritics\n"
        "  intro h\n"
        f"  rw [{close['rw']}] at h\n"
        f"  simp [markFreeSeq, {close['simp']}, NonDetT.run, pure] at h\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the explicit backward-fold loop and return the modeled
        # form directly. This is the honest cheapest-correct impl (markFreeSeq ∘
        # canonicalDecompose IS the desired transform); the loop only existed to
        # establish `result = markFreeSeq ((canonicalDecompose s).drop 0)`.
        # Retunes the tactic body to bare `loom_solve` (the loop-body drop-step
        # lemma is no longer needed); the obligation statement is untouched.
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    -- impl-start\n"
                  "    return markFreeSeq (canonicalDecompose s)\n"
                  "    -- impl-end"),
            _GOLD_PROOF, _PROOF_STRAIGHT),
        "rationale": "a straight-line `return markFreeSeq (canonicalDecompose s)` "
                     "is the simplest correct impl; it meets C1 (`out = markFreeSeq "
                     "(canonicalDecompose s)`) by definition. If it fails to verify "
                     "the postcondition is over-fit to the loop form => "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-guard-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the ENTIRE backward-fold scaffold and both framing
        # invariants VERBATIM, but rewrite the loop guard `i > 0` as the
        # logically-equivalent `¬ (i = 0)`. Same behaviour, different executable
        # shape; the frozen loop invariant is discharged exactly as before, so the
        # frozen proof is kept unchanged.
        "module": _swap(_BASE, _GOLD_GUARD, "    while ¬ (i = 0)\n"),
        "rationale": "the loop guard `i > 0` rewritten as the equivalent "
                     "`¬ (i = 0)`; the entire backward-fold scaffold, both framing "
                     "invariants, and the front-recursive drop-step proof are kept "
                     "verbatim. Must verify, else the spec is over-fit to the `>` "
                     "spelling of the guard => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY (expect=verify). The method has NO `require` clause, so the
    # nagini "a self-call on an F2P-shaped input satisfies the precondition"
    # probe is vacuous on the total domain — nothing could exclude any input.
    # Re-aimed at the residual admissibility risk: that the post-image is
    # DEGENERATE (e.g. constant) so no rival could be distinguished. This case
    # discharges an in-region `assert`, over fresh opaque code points, that the
    # keep/drop rule genuinely DISCRIMINATES — a single non-combining code point
    # is retained (`markFreeSeq [a] = [a]`) while the empty sequence maps to the
    # empty result — so the modeled behaviour is not constant. The frozen loop
    # and obligation are kept verbatim so C1 still discharges; the assert is live
    # (a false claim leaves an unsolved goal — confirmed empirically) and is
    # discharged by the frozen proof's `simp_all`.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _GOLD_IMPL_HEAD,
            "    -- impl-start\n"
            "    assert (with_name_prefix `adm\n"
            "      ((∀ base mark : Char, isCombiningMark base = false →\n"
            "          isCombiningMark mark = true →\n"
            "          markFreeSeq [base, mark] = [base])\n"
            "        ∧ markFreeSeq ([] : List Char) = []))\n"
            "    let mut result : List Char := []"),
        "rationale": "the obligation is SATISFIABLE at exactly an F2P-shaped input "
                     "— a base code point followed by a combining mark, the very "
                     "shape the failing example turns on — and the in-region assert "
                     "discharges the post-image THERE, by evaluation, before the "
                     "frozen obligation closes verbatim: `markFreeSeq [base, mark] = "
                     "[base]` for a non-combining `base` and a combining `mark`. "
                     "That is the total-carrier analogue of the sibling's "
                     "precondition probe (no `require` clause exists to satisfy, so "
                     "the residual risk is the obligation being unsatisfiable at an "
                     "F2P-shaped point, not an input being excluded). The second "
                     "conjunct pins the empty sequence, so the post-image is also "
                     "non-degenerate rather than constant. The assert is LIVE: "
                     "replacing `= [base]` with `= [base, mark]` (the mark NOT "
                     "dropped) leaves unsolved goals and does not verify, checked "
                     "with a real build. If it FAILS => PRECOND-TOO-STRONG.",
    },
    {
        "id": "pos-filter-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: express the keep/drop rule as a `List.filter` over the
        # complement predicate instead of the front-recursive `markFreeSeq` fold.
        # Observationally the same transform, but a genuinely different shape: the
        # impl no longer mentions `markFreeSeq` at all, so the obligation is closed
        # through an in-proof bridging `have` (impl/proof regions only — the spec
        # regions and the `ensures` are untouched) rather than by definitional
        # unfolding. This is the reshape most likely to expose the postcondition as
        # over-fit to `markFreeSeq`'s recursive spelling.
        "module": _swap(
            _swap(_BASE, _GOLD_IMPL,
                  "    -- impl-start\n"
                  "    return (canonicalDecompose s).filter "
                  "(fun c => ! isCombiningMark c)\n"
                  "    -- impl-end"),
            _GOLD_PROOF,
            "prove_correct stripDiacritics by\n"
            "  have bridge : ∀ xs : List Char, markFreeSeq xs "
            "= xs.filter (fun c => ! isCombiningMark c) := by\n"
            "    intro xs\n"
            "    induction xs with\n"
            "    | nil => simp [markFreeSeq]\n"
            "    | cons c cs ih =>\n"
            "      simp [markFreeSeq, List.filter_cons, ih]\n"
            "      by_cases hc : isCombiningMark c <;> simp [hc]\n"
            "  loom_solve"),
        "rationale": "`(canonicalDecompose s).filter (fun c => ! isCombiningMark c)` "
                     "is the same keep/drop transform written as a filter over the "
                     "complement predicate rather than as `markFreeSeq`'s front "
                     "recursion — a faithful correct impl whose shape shares no "
                     "syntax with the frozen fold. It meets C1 via the "
                     "`markFreeSeq xs = xs.filter (! isCombiningMark ·)` bridge "
                     "proven inductively in the elided proof body. Must verify, else "
                     "the postcondition is over-fit to `markFreeSeq`'s recursive "
                     "spelling and admits only impls that name it => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a straight-line impl carrying a machine-checked
    # refutation witness at a DISTINCT literal input CONDITIONED on the opaque
    # carrier, and the refinement argument that its faithful real counterpart
    # would NOT resolve the failing test `test_strip_accents`. Every witness was
    # verified out-of-band: it ELABORATES against its rival (exit 0), FAILS
    # against the frozen solution (exit 1), and its hypotheses are jointly
    # satisfiable (the consistency probe cannot derive `False`).
    # =====================================================================
    {
        "id": "weak-no-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # facet (F): decompose but KEEP every code point — never apply the
        # combining-mark filter. Correct on inputs whose decomposition has no
        # combining mark; wrong on every input that carries one.
        "module": _reject("    return canonicalDecompose s"),
        "refinement": "a faithful counterpart that decomposes but keeps every code "
                      "point (no `not combining(c)` test) returns the full "
                      "decomposition with combining marks intact. On the F2P input "
                      "that decomposes to a base plus a combining mark it yields the "
                      "base-plus-mark sequence (and on the marks-only input it "
                      "yields the marks) rather than the mark-free residue the "
                      "failing example asserts (`'o'`, resp. the empty string), so "
                      "it stays RED. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (F): `markFreeSeq` DROPS combining "
                     "marks, but the rival keeps them, so the result differs "
                     "wherever the decomposition carries a mark. Refuted at "
                     "`s = ['x']` conditioned on `canonicalDecompose ['x'] = [m]` "
                     "with `isCombiningMark m = true` (a satisfiable pair of "
                     "hypotheses about distinct opaque terms): gold drops `m` to "
                     "`[]`, the rival returns `[m]`. Discrimination comes from the "
                     "combining code point the filter must remove. If it VERIFIES "
                     "=> SPEC-TOO-WEAK (the filter is unpinned).",
        "witness": _witness(
            "(m : Char) (hm : isCombiningMark m = true)\n"
            "    (hd : canonicalDecompose ['x'] = [m])",
            "['x']", {"rw": "hd", "simp": "hm"}),
        # Gold's loop cannot decide this (or any) claim — see _WITNESS_REFERENCE.
        # Against the reference the witness reduces to `h : True ⊢ False` (exit 1)
        # while the flipped claim VERIFIES (exit 0), so the exit code tracks the
        # claim; against the rival the witness elaborates (exit 0).
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "weak-inverted-filter",
        "kind": "uniqueness",
        "expect": "reject",
        # facet (F), inverted: keep the COMBINING marks and drop the bases — the
        # complementary predicate. Correct only on the all-combining edge; wrong
        # on every input carrying a non-combining code point.
        "module": _reject(
            "    return (canonicalDecompose s).filter (fun c => isCombiningMark c)"),
        "refinement": "inverting the keep predicate (keep marks, drop bases) "
                      "returns the marks-only subsequence. On any real word the "
                      "base letters — exactly what the failing example expects to "
                      "survive — are dropped, so the result is empty (or the "
                      "stray marks) instead of the stripped letters, and the test "
                      "stays RED. It would NOT resolve.",
        "rationale": "REJECT from C1 facet (F): `markFreeSeq` KEEPS non-combining "
                     "code points; the rival keeps the complement, contradicting "
                     "the keep/drop rule. Refuted at `s = ['y']` conditioned on "
                     "`canonicalDecompose ['y'] = [b]` with `isCombiningMark b = "
                     "false` (a satisfiable pair about distinct opaque terms): gold "
                     "keeps the non-combining `b` as `[b]`, the rival filters it "
                     "out to `[]`. Discrimination comes from a non-combining code "
                     "point the rival wrongly drops. If it VERIFIES => "
                     "SPEC-TOO-WEAK.",
        "witness": _witness(
            "(b : Char) (hb : isCombiningMark b = false)\n"
            "    (hd : canonicalDecompose ['y'] = [b])",
            "['y']", {"rw": "hd", "simp": "hb"}),
        # Gold's loop cannot decide this (or any) claim — see _WITNESS_REFERENCE.
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "weak-return-input",
        "kind": "uniqueness",
        "expect": "reject",
        # facet (D): the pre-fix no-op — return the input untouched, skipping BOTH
        # the decomposition and the filter. Correct only when the input is already
        # its own mark-free canonical form; wrong on any accented / combining
        # input.
        "module": _reject("    return s"),
        "refinement": "returning the input unchanged is the reported pre-fix bug: "
                      "an already-decomposed accented input is returned with its "
                      "combining mark intact instead of stripped. The failing "
                      "example asserts the accent is removed (`'o'` for the "
                      "base-plus-diaeresis input), so it stays RED. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 facet (D): returning `s` gives `out = s`, "
                     "which equals `markFreeSeq (canonicalDecompose s)` only when "
                     "`s` is already its own mark-free canonical form. Refuted at "
                     "`s = ['w']` conditioned on `canonicalDecompose ['w'] = [m]` "
                     "with `isCombiningMark m = true` (a satisfiable pair about "
                     "distinct opaque terms): gold decomposes and drops the mark to "
                     "`[]`, the rival returns `['w']`. Discrimination comes from an "
                     "input whose decomposition differs from itself and carries a "
                     "mark. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _witness(
            "(m : Char) (hm : isCombiningMark m = true)\n"
            "    (hd : canonicalDecompose ['w'] = [m])",
            "['w']", {"rw": "hd", "simp": "hm"}),
        # Gold's loop cannot decide this (or any) claim — see _WITNESS_REFERENCE.
        "witness_reference": _WITNESS_REFERENCE,
    },
    {
        "id": "weak-skip-decompose",
        "kind": "uniqueness",
        "expect": "reject",
        # facet (D): apply the mark-filter to the RAW input instead of to its
        # decomposition — markFreeSeq s rather than markFreeSeq (canonicalDecompose
        # s). Correct whenever s already equals its decomposition; wrong on a
        # precomposed glyph, where the single non-combining code point is never
        # split so its accent is never separated and dropped.
        "module": _reject("    return markFreeSeq s"),
        "refinement": "omitting the decomposition and filtering the raw input "
                      "leaves a PRECOMPOSED accented code point untouched: it is a "
                      "single non-combining code point, so the filter keeps it and "
                      "the accent is never separated. The failing test expects the "
                      "accent stripped (the precomposed and the already-decomposed "
                      "spellings must reduce alike), so it stays RED. It would NOT "
                      "resolve.",
        "rationale": "REJECT from C1 facet (D): the result is pinned to "
                     "`markFreeSeq (canonicalDecompose s)`; filtering `s` directly "
                     "drops the decomposition step and diverges wherever "
                     "`canonicalDecompose s ≠ s`. Refuted at `s = ['z']` "
                     "conditioned on `canonicalDecompose ['z'] = [a, b]` (a "
                     "precomposed glyph decomposing to two non-combining code "
                     "points) with `isCombiningMark 'z' = false`, "
                     "`isCombiningMark a = false`, `isCombiningMark b = false` (all "
                     "about distinct opaque terms, jointly satisfiable): gold keeps "
                     "both decomposed points `[a, b]`, the rival keeps the raw "
                     "`['z']`. Discrimination comes from an input whose "
                     "decomposition lengthens it. If it VERIFIES => SPEC-TOO-WEAK.",
        "witness": _witness(
            "(a b : Char) (ha : isCombiningMark a = false)\n"
            "    (hb : isCombiningMark b = false) (hz : isCombiningMark 'z' = false)\n"
            "    (hd : canonicalDecompose ['z'] = [a, b])",
            "['z']", {"rw": "hd", "simp": "ha, hb, hz"}),
        # Gold's loop cannot decide this (or any) claim — see _WITNESS_REFERENCE.
        "witness_reference": _WITNESS_REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 2 MANDATORY frame-mutation rivals, 4 uniqueness
# rivals) plus a 5-case AXIOM lane. The sibling contracts `strip_marks(s:
# List[int])` over a PSeq[int] carrier with a half-permission read-only input, an
# ASCII fast-path guard, and grounded @Pure `nfkd`/`strip_combining` models. This
# bundle narrows the carrier to ONE contracted method `stripDiacritics` over
# `List Char`, models the SAME transform as `markFreeSeq (canonicalDecompose s)`
# for TWO opaque callees (no fast-path guard is modeled — it is a pure
# performance short-circuit with no value footprint, folded into the single
# general path), and has NO permission surface. Every sibling case is accounted
# for below.
#
#   sibling case (nagini)          -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-control-reorder            -> pos-guard-reshape             PORTED (re-aimed)
#   (added)                        -> pos-direct-model              ADDED
#   (added)                        -> pos-filter-reshape            ADDED (audit)
#   admiss-f2p-input               -> admiss-nondegenerate          PORTED (re-aimed)
#   frame-mut-store                -> (none)                        VACUOUS
#   frame-mut-append               -> (none)                        VACUOUS
#   (no sibling case)              -> (none)                        DIVERGENCE:
#                                     closed by `total` semantics, but
#                                     INEXPRESSIBLE as a case (the witness fails
#                                     on the RIVAL side; see the docstring)
#   partial-no-filter              -> weak-no-filter                PORTED
#   partial-inverted-filter        -> weak-inverted-filter          PORTED
#   partial-skip-decompose         -> weak-skip-decompose           PORTED
#   cf-always-return-input         -> weak-return-input             PORTED
#   AXIOM_TESTS (5)                -> (none)                        DROPPED (G-AX)
#
# 4 behavioural rivals PORTED; 1 positive PORTED (re-aimed) + 2 ADDED; the
# admissibility case PORTED (re-aimed); both mandatory frame rivals VACUOUS; the
# axiom lane DROPPED.
#
# AUDIT REVISION. An independent audit re-derived every reject case's two builds
# and found the discrimination half resting on a carrier limit rather than on the
# spec: against the frozen impl the witness's hypothesis stays an unreduced
# `NonDetT.run (forIn Lean.Loop.mk …)` term and `⊢ False` is left unsolved for
# EVERY claim. Measured: the FLIPPED claim (same binders, same tactics, `≠` ->
# `=`, i.e. asserting the frozen impl is CORRECT at that point) fails on gold
# with the same unreduced-loop `unsolved goals`, and so does a trivially true
# claim at the empty input — so gold's exit code carried no information about
# what was claimed, and a witness asserting gold correct would have been recorded
# as a refutation. All four rivals now carry `witness_reference`
# (= _WITNESS_REFERENCE, the loop-free verifying impl of the same spec), against
# which each witness reduces to `h : True ⊢ False` (exit 1) while its flipped
# twin VERIFIES (exit 0) — the exit code now tracks the claim. The audit also
# re-aimed the admissibility case from a degeneracy assert onto the F2P-shaped
# base+mark point (`markFreeSeq [base, mark] = [base]`, LIVE: the mark-kept twin
# does not verify), and ADDED pos-filter-reshape after confirming the spec admits
# a `List.filter`-shaped correct impl that never names `markFreeSeq`.
#
# AUDIT REVISION 2 (independent re-derivation). Every claim above was re-measured
# with real builds rather than re-read. Confirmed, per rival, all four:
#   * the witness ELABORATES against its rival (EXIT 0);
#   * against the `witness_reference` it FAILS (EXIT 1) with `h : True ⊢ False`;
#   * the FORGERY test (prompt attack B'), both directions, on all four:
#     - FLIP (`≠` -> `=`, i.e. asserting the reference is CORRECT at that point)
#       VERIFIES against the reference (EXIT 0). So the exit code TRACKS the claim
#       — this is what makes the reference a discriminator and not a carrier limit.
#     - REVEAL (`exact (h : Nat)` in place of the closing step) prints, against
#       the reference, `Type mismatch h has type True … but is expected to have
#       type ℕ` — `simp` PROVED the postcondition equation there; against each
#       RIVAL the same probe prints `No goals to be solved`, i.e. `simp` closed
#       `False` from the rival's own equation. That pair is a genuine refutation.
#   * the consistency probe cannot derive `False` (EXIT 1, `simp_all made no
#     progress`), so no witness is forged from an inconsistent premise.
# Independently re-confirmed that GOLD cannot be the subject: the witness and its
# FLIPPED twin both fail against the frozen impl (EXIT 1) with the same unreduced
# `forIn Lean.Loop.mk` hypothesis, so gold's exit code carries no information
# about the claim. `witness_reference` is load-bearing, not decorative.
# Statement integrity (attack A): all 8 case modules + the reference diff to the
# frozen file ONLY inside the impl region and/or the `prove_correct` body; lines
# 1-55 (imports, options, axioms, `pure`, pre/post regions, method signature and
# the `ensures`) are byte-identical in every one.
# SPEC-TOO-WEAK probe (attack D), 6 NEW wrong rivals beyond the shipped four, all
# correctly REJECTED (EXIT 1), so no spec hole: double decomposition; output
# `.drop 1`; `.eraseDups`; the loop guard weakened to `i > 1` (refused on
# `done_1: i = 0`); the body index moved from `i - 1` to `i` (refused on the
# framing invariant); and an `if s = [] then return []` short-circuit (refused on
# `ensures_1`, residual `⊢ [] = markFreeSeq (canonicalDecompose s)` — note the
# spec does NOT let an impl assume the decomposition of `[]` is `[]`, since
# `canonicalDecompose` is opaque; that is correct strength, not over-strength).
# SPEC-TOO-STRONG probe (attack E), 3 NEW correct reshapes: `List.flatMap` over
# the keep/drop function VERIFIES (EXIT 0); `List.foldr` VERIFIES (EXIT 0); and a
# FORWARD loop with a reversed accumulation invariant and an
# `(canonicalDecompose s).length - i` measure VERIFIES (EXIT 0) once its bridging
# step is written with `Nat.add_sub_cancel` (the first spelling failed on a
# rewrite pattern — a tactic gap, not a spec hole). So the spec admits impls that
# never name `markFreeSeq`, that fold the other way, and that traverse the other
# direction: it is not over-fit to the frozen fold's shape.
#
# PORTED (rivals): the four nagini partial-domain / control-flow rivals port
#   directly onto the two facets of C1. partial-no-filter -> weak-no-filter and
#   partial-inverted-filter -> weak-inverted-filter attack facet (F) (the mark
#   filter's keep/drop rule); cf-always-return-input -> weak-return-input and
#   partial-skip-decompose -> weak-skip-decompose attack facet (D) (the
#   decomposition step). The nagini fast-path-materialisation subtlety of
#   cf-always-return-input collapses here (no fast-path is modeled), so it is the
#   plain "return the input untouched" no-op — the reported pre-fix bug, of which
#   Solution_prepatch.lean is a guarded variant (G-DIFF). Each carries a
#   machine-checked witness CONDITIONED on the opaque carrier that ELABORATES
#   against the rival (EXIT 0) and FAILS against the `witness_reference` — the
#   loop-free VERIFYING impl of the same spec, which the frozen loop cannot
#   substitute for because its extracted `…Exec` does not reduce for any claim
#   (see WITNESS SUBJECT in the docstring) — with a satisfiable hypothesis set
#   (the consistency probe cannot derive `False`).
# PORTED-RE-AIMED (positive): pos-control-reorder reordered the loop's classifier
#   branch (`== vs not`); the structural analog here reshapes the loop GUARD
#   `i > 0` as `¬ (i = 0)`, keeping the frozen scaffold, invariants and proof
#   (pos-guard-reshape). ADDED pos-direct-model so the reshape space also covers
#   dropping the loop entirely and returning the modeled form (retuning the
#   elided tactic body) — the honest cheapest-correct impl. ADDED (audit)
#   pos-filter-reshape, the furthest honest reshape: a `List.filter` over the
#   complement predicate that never names `markFreeSeq`, closed through an
#   in-proof inductive bridge. All three build against the verifier (EXIT 0), so
#   the spec is not over-fit to `markFreeSeq`'s recursive spelling.
# PORTED-RE-AIMED (admissibility): admiss-f2p-input built a fresh F2P-shaped input
#   and discharged the half-permission precondition via a self-call. This method
#   has NO `require` clause and no permission surface, so no input could be
#   excluded and the literal precondition probe is vacuous. The total-carrier
#   analogue is the obligation being UNSATISFIABLE at an F2P-shaped input, which
#   this case tests directly: an in-region assert discharges the post-image at
#   the base+mark point by evaluation (`markFreeSeq [base, mark] = [base]` for a
#   non-combining `base` and a combining `mark`) before the frozen obligation
#   closes verbatim, with `markFreeSeq [] = []` pinning non-degeneracy as well.
#   The assert is LIVE: the mark-KEPT twin (`= [base, mark]`) leaves unsolved
#   goals and does not verify (real build, EXIT 1).
# VACUOUS (frame-mut-store, frame-mut-append; MANDATORY on nagini): both reject an
#   illegal WRITE to the read-only input `s` (a store `s[0]=s[0]` / an append),
#   held at `Acc(list_pred(s), 1/2)`, tripping INSUFFICIENT PERMISSION before any
#   postcondition is considered. This backend is referentially transparent, has
#   no heap and no aliasing, and this bundle declares NO `mut` binder — every
#   input is an immutable value with no heap footprint. There is no read-only cell
#   to overwrite and no substitute probe to build. Not fabricated (porting map:
#   this class is vacuous here). Its ARGUMENT (a patch mutating its input) has no
#   value footprint the spec can force here — the result is `out = markFreeSeq
#   (canonicalDecompose s)`, a fresh list, read-only by construction.
# DROPPED (AXIOM_TESTS, 5): the axiom lane is G-AX's job; this gate ignores it.
#   This bundle declares NO `axiom` — both callees are `opaque` free functions
#   with nothing asserted about their values to validate (mapping.md §3 records
#   the G-AX skip; the nagini sibling's @ContractOnly `nfkd`/`is_combining`/
#   `is_fixed_form_guard`/`strip_combining` axioms have no counterpart because
#   nothing is claimed about the opaque callees here). Nothing to probe.
#
# BINDER / CLAUSE COVERAGE. The sole input binder is `s`; the single top-level
#   clause C1 (`out = markFreeSeq (canonicalDecompose s)`) folds two facets
#   (decomposition runs; the mark filter keeps non-combining / drops combining).
#   C1 is DEFENDED by the three positive controls and the admissibility case, and
#   ATTACKED by all four rivals: facet (D) by weak-return-input and
#   weak-skip-decompose, facet (F) by weak-no-filter and weak-inverted-filter.
#   `s` is varied across FOUR DISTINCT witness inputs (['x'], ['y'], ['w'], ['z'])
#   each conditioned on a DIFFERENT opaque-carrier point (a decomposition to one
#   combining mark; to one non-combining base; to a combining mark; to two
#   non-combining bases), so no rival is refuted at a pinned input and both facets
#   are demonstrated. The reject lane is NON-EMPTY, so SPEC-TOO-WEAK is detectable.
#
# WITNESS FORM. Both callees are opaque, so no `…Tester s` can `decide` and the
#   frozen `while`-loop `…Exec` does not reduce; each witness therefore CONDITIONS
#   ON THE CARRIER (quantifies over the code points `canonicalDecompose` produces
#   at a literal and over their combining class, as weak jointly-satisfiable
#   hypotheses) and states that the rival's extracted `stripDiacriticsExec` output
#   differs from the spec's `markFreeSeq (canonicalDecompose …)` image at that
#   described point. The SUBJECT of the discrimination half is the
#   `witness_reference`, not the frozen impl: gold's `…Exec` is an unreduced
#   `forIn Lean.Loop.mk` term for which every claim fails alike (the flipped claim
#   and a trivially true claim were both measured failing identically), so its
#   exit code discriminates nothing. Confirmed empirically per rival, with real
#   builds: the witness ELABORATES against its rival (EXIT 0); against the
#   reference it reduces to `h : True ⊢ False` and FAILS (EXIT 1) — `simp` proved
#   the postcondition equation for that impl and could not for the rival; the
#   FLIPPED claim VERIFIES against the reference (EXIT 0), so the exit code tracks
#   the claim rather than the carrier; and the hypotheses are jointly satisfiable
#   (the consistency probe cannot derive `False`, EXIT 1).
AXIOM_TESTS = []
