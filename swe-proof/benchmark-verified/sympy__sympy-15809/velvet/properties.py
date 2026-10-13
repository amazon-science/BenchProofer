"""properties.py — G-PBT falsification battery for sympy__sympy-15809 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, the elided
``prove_correct`` tactic body — is changed, both regions the consumer spec view
elides, so ``markers.same_spec`` holds and the ``prove_correct constructMinMax``
obligation survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND the file elaborates with every obligation closed);
``expect:"reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

================================  DEFENDED SURFACE  ==========================

ONE contracted method over two read-only inputs:

  constructMinMax (idv : Int) (rawArgs : List Int)
      return (out : Except MinMaxErr MinMaxResult)
    ensures out = minMaxResult idv rawArgs                                 -- (E1)
    ensures rawArgs = [] → out = Except.ok (MinMaxResult.identityResult idv) -- (E2)

The method models a lattice-extremum constructor. It normalises its raw
arguments through an unchanged normalisation pipeline (modeled ``opaque`` as
``processArgs``, carrying only the one consumed fact ``processArgs_nil :
processArgs [] = []``) and then decides the result PURELY by how many members
survive:

  * none survive  ⇒ the identity element ``idv`` (``identityResult idv``);
  * one survives  ⇒ that member verbatim (``single a``);
  * two or more   ⇒ the extremum object over the survivors (``combined ms``).

Crucially, the empty argument list is NOT rejected: its extremum is the identity
element. The two ``ensures`` pin two things:

  * (E1) the whole outcome as ``minMaxResult idv rawArgs`` — the count-driven
    dispatch over the normalised members, on EVERY input;
  * (E2) the load-bearing fix, singled out: an empty raw-argument list yields
    the identity element (never a failure, never a wrong element). This is the
    exact behaviour the change introduces (the public issue reports that empty
    calls currently fail).

TWO input binders, both free (the ``pre-conditions`` region is EMPTY, so the
domain is total): ``idv`` — the lattice identity element, observed only by
equality with the empty-collection result; and ``rawArgs`` — the raw arguments,
whose normalised cardinality (0 / 1 / ≥2) selects the branch.

CARRIER — the decisive fact of this port. ``processArgs`` is an OPAQUE axiom; the
only property the kernel knows about it is ``processArgs_nil`` (empty in ⇒ empty
out). Its value at any NON-EMPTY input is unknown — which is exactly what keeps
the surface faithful (the normalisation pipeline is unchanged by the fix and
deliberately left abstract, directive 7). This governs HOW each reject clause is
witnessed:

  * (E2) the empty leg is TRANSPARENT: ``processArgs_nil`` rewrites
    ``processArgs []`` to ``[]``, so the empty branch reduces to a ground term
    and a rival that returns anything but ``Except.ok (identityResult idv)`` on
    ``[]`` is refuted by a literal ``.run`` statement closed with ``simp
    [..., processArgs_nil]`` — no conditioning needed.
  * (E1) the single / combined legs reference the OPAQUE ``processArgs rawArgs``
    and cannot be decided at a literal. They are attacked by CONDITIONING ON THE
    CARRIER: at ``rawArgs = [5]`` under the hypothesis ``processArgs [5] = [5]``
    (a single survivor) the spec demands ``single 5``; at ``rawArgs = [5,6]``
    under ``processArgs [5,6] = [5,6]`` (two survivors) it demands ``combined
    [5,6]``. Each hypothesis is a SINGLE assumption about ONE opaque term, so it
    is weak and self-satisfiable (``processArgs`` is opaque — no ``False`` is
    derivable from one equation about it), and the refuting input genuinely
    exists. The witness holds of the rival (whose output differs from the
    dictated one) and fails on gold (whose output IS ``minMaxResult idv rawArgs``).

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case in the
footer):
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries a MANDATORY
    frame-mutation rival (write ``operands[0] = zero`` through a read-only
    ``Acc(list_pred(operands),1/2)`` reference) because its input is held at a
    fractional heap permission an impl can illegally overwrite. Lean and Velvet
    are referentially transparent: ``idv`` and ``rawArgs`` are immutable values,
    this bundle declares NO ``mut`` binder, there is no heap and no aliasing — so
    there is no read-only input to mutate and no substitute probe to build. Not
    fabricated (per the porting map, this class is vacuous here).
  * DIVERGENCE / NON-TERMINATION — NOT shippable here, but NOT for the reason
    the first two passes recorded. This bundle runs under
    ``loom.semantics.termination "total"``: a postcondition is claimed of ALL runs,
    not only terminating ones, the verifier discharges a termination obligation, and a
    measure-less loop is genuinely REJECTED. So is the sharper shape that CARRIES a
    measure which does not decrease (``while q > 0 / invariant 0 ≤ q /
    done_with q = 0 / decreasing q``, body ``q := q``), which is REJECTED on the
    measure's own goal - ``case «decreasing_1: q»``, residual ``⊢ q < q``. (An earlier
    pass contrasted this with a ``partial``-semantics known spec hole in an internal
    findings doc; that cohort is withdrawn, since all 500 velvet bundles set
    ``"total"``.) An earlier pass claimed "a
    diverging implementation cannot be written at all"; a later audit re-ran
    the class and MEASURED that claim FALSE. A ``while`` loop with no
    ``decreasing`` clause IS writable in the impl region (velvet's loop form
    takes ``invariant`` / ``done_with`` / ``decreasing`` clauses) and the file
    is rejected with ``error: Decreasing annotations are required in total
    correctness semantics`` (exit 1) — so the class is neither vacuous nor a
    known hole; the rival exists and the spec rejects it.
    What blocks SHIPPING it is the WITNESS requirement, and that was measured
    too rather than argued. The termination diagnostic is emitted at the
    ``method`` declaration, not in the elided ``prove_correct`` body that
    ``witness_file`` strips, so the witness file inherits a hard elaboration
    error and NOTHING appended to it can elaborate: the weakest conceivable
    witness, ``example : True := trivial``, FAILS against the diverging rival
    (exit 1) with that same termination diagnostic. The gate would therefore
    record ``witness-unproven`` — an inconclusive outcome, not a pass — so a
    diverge case cannot be shipped green on this carrier. The rejection here is
    carried by the termination checker rather than by either ``ensures``, which
    is precisely what the witness requirement exists to refuse to credit.
    Recorded as a CARRIER/TOOLING limit on the reject lane, not as vacuity: the
    honest reading is that this bundle's spec does constrain divergence and the
    battery simply cannot attest to it in the witness-carrying form this gate
    demands. The nagini sibling carries no ``diverge-*`` case either, so nothing
    is dropped relative to it.
  * UNGROUNDED-ORACLE ECHO — N/A, as the nagini note itself frames it. The three
    nagini ``@Pure`` classifier axioms are predicates over the INPUT, not an
    answer-key for the result. Here (E1) pins ``out`` to ``minMaxResult idv
    rawArgs`` — a concrete ``def`` over the method's own inputs composed with the
    G-AX-validated ``processArgs`` (whose only asserted property is
    ``processArgs_nil``), not an opaque expected-result the impl could echo. The
    only satisfier is the honest count-dispatch; the positive control does it
    faithfully.
  * PARTIAL-DOMAIN / VALUE — the heart of this port: each reject rival is correct
    on part of the input domain and wrong on a sub-domain, refuted at a concrete
    input that pins one leg of the dispatch (empty / single / combined).

WITNESS MECHANICS. The frozen impl is a total function whose ``.run`` reduces to
``DivM.res (minMaxResult idv rawArgs)`` once the method ``def`` and
``NonDetT.run``/``pure`` are unfolded (no tester derivation is needed — and the
opaque ``processArgs`` would in any case stall ``decide`` on a derived tester, so
each witness states the postcondition DIRECTLY over ``.run``). Both halves of
every reject witness were checked out-of-band with ``scripts/lean_verify.sh``:
each ELABORATES against its rival (exit 0) and FAILS against the frozen solution
(exit 1, leaving the residual goal open), so each rejection is a genuine spec
refutation, not mechanical tactic breakage.

An INDEPENDENT audit re-derived all five reject cases from scratch with the real
verifier and confirmed the gold-side failure is SEMANTIC in every one: after
`simp` reduces both sides the residual is literally `⊢ False` (for the
conditioned witnesses, `⊢ False` under the single carrier hypothesis) — not a
missing identifier, not a type error, not a stuck `decide`, and not a timeout.
Three controls back that reading, each a real build:
  * the OPPOSITE claim (`.run = DivM.res (...)`, i.e. that the frozen impl is
    CORRECT at the same point, empty and conditioned alike) ELABORATES against
    the frozen solution (exit 0) — so the gold-side exit code carries
    information here, and the shipped witnesses are not passing on a
    reduction that never happened;
  * that same true-direction claim FAILS against a rival (exit 1), so the
    direction of the refutation is what decides the build;
  * a merely RESHAPED but CORRECT impl (the positive control) also FAILS the
    ≠-witness (exit 1), which is the test that separates a real refutation from
    a tactic mismatch: the witness discriminates WRONGNESS, not shape.

AXIOM lane: DROPPED. The ``axioms`` region declares ``processArgs`` /
``processArgs_nil``, G-AX-validated (axiom_check.py runs the real normalisation
pipeline against ``processArgs_nil`` on the base repo); that is not this gate's
concern, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15809"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the frozen impl body, verbatim: the executable statements strictly
# ---- BETWEEN the method's `-- impl-start` / `-- impl-end` markers. Every rival
# ---- and reshape edits ONLY this block (and, for the reshape, the elided
# ---- `prove_correct` tactic body), so the spec view is untouched and same_spec
# ---- holds by construction, leaving the frozen `prove_correct constructMinMax`
# ---- statement intact. Unique in the file (asserted at load by _swap).
_IMPL = (
    "    let result : Except MinMaxErr MinMaxResult :=\n"
    "      match processArgs rawArgs with\n"
    "      | []           => Except.ok (MinMaxResult.identityResult idv)\n"
    "      | [a]          => Except.ok (MinMaxResult.single a)\n"
    "      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "constructMinMax impl region drifted from expected text"

# ---- the frozen proof, verbatim. A reshape that changes the impl's syntactic
# ---- form may retune THIS block (elided from the spec view); rivals leave it as
# ---- is (the rejection is carried by the witness, not the tactic script).
_PROOF = (
    "prove_correct constructMinMax by\n"
    "  loom_solve <;> simp_all [minMaxResult, processArgs_nil]"
)
assert _BASE.count(_PROOF) == 1, "prove_correct region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the elided proof retuned (for correct reshapes)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness closers. The empty-leg witnesses state the (E2)-shaped goal at a
# ---- literal `[]` and reduce it with `processArgs_nil` folded into `simp`; the
# ---- single/combined-leg witnesses state the (E1)-shaped goal `.run ≠ DivM.res
# ---- (minMaxResult idv rawArgs)` under a hypothesis about the one opaque term.
def _w_empty(idv):
    return (
        f"example : (constructMinMax {idv} ([] : List Int)).run\n"
        f"    ≠ DivM.res (Except.ok (MinMaxResult.identityResult {idv})) := by\n"
        "  simp [constructMinMax, NonDetT.run, pure, processArgs_nil]\n"
    )


def _w_cond(idv, raw, hyp):
    return (
        f"example (h : {hyp}) :\n"
        f"    (constructMinMax {idv} ({raw} : List Int)).run\n"
        f"      ≠ DivM.res (minMaxResult {idv} ({raw} : List Int)) := by\n"
        "  simp [constructMinMax, minMaxResult, NonDetT.run, pure, h]\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally DIFFERENT but CORRECT impl
    # that MUST verify, else SPEC-TOO-STRONG. Ports the nagini
    # `pos-control-branch-reorder` ARGUMENT: bind the normalised members to a
    # local and dispatch with the branch order REVERSED (≥2 first, then one, then
    # empty). Observationally identical on every input (the same value is
    # produced), so both (E1) and (E2) still hold; the elided proof is retuned to
    # discharge the reordered `match` (a `rcases` over the three list shapes).
    # Verified out-of-band with a real build (exit 0). If a faithful reshape
    # cannot verify, the postcondition is over-fit to the branch ORDER
    # (SPEC-TOO-STRONG).
    #
    # The reshape is NOT definitionally equal to the frozen impl, so this case
    # tests something: the audit rebuilt this same impl body against the FROZEN
    # proof script and it FAILS (exit 1) with `unsolved goals` whose residual is
    # the two `match` expressions in opposite branch order, i.e. `simp_all` does
    # not close it and the retune is load-bearing. Reordering the arms genuinely
    # changes the elaborated term; only its VALUE is preserved, which is exactly
    # the distinction a soundness control should probe.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_reproved(
            "    let members := processArgs rawArgs\n"
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      match members with\n"
            "      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))\n"
            "      | [a]          => Except.ok (MinMaxResult.single a)\n"
            "      | []           => Except.ok (MinMaxResult.identityResult idv)\n"
            "    return result",
            "prove_correct constructMinMax by\n"
            "  loom_solve <;>\n"
            "    simp_all [minMaxResult, processArgs_nil] <;>\n"
            "    (rcases h : processArgs rawArgs with _ | ⟨a, _ | ⟨b, rest⟩⟩ <;> simp_all)"),
        "rationale": (
            "PASS SOURCE = (E1) ∧ (E2). Binding the normalised members to a local "
            "and dispatching with the branch order reversed (≥2, then one, then "
            "empty) produces the SAME `Except.ok` value on every input, so "
            "`out = minMaxResult idv rawArgs` and the empty-leg clause both still "
            "discharge; only the elided proof is retuned to the reordered `match`. "
            "A structurally different faithful reshape MUST verify; if it cannot, "
            "the spec is over-fit to the branch ORDER (SPEC-TOO-STRONG). Ports the "
            "sibling's branch-reorder positive control."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the method declares NO precondition (the pre-conditions
    # region is EMPTY), so the sibling's "an F2P-shaped input satisfies the
    # precondition" probe is degenerate: every input is in-domain. The residual
    # admissibility risk on a total domain is that the post-image is DEGENERATE at
    # the interesting point — an empty-collection result that came out the same
    # regardless of `idv` would read like a live one. This case discharges an
    # in-region assert pinning that at the F2P-shaped empty input the modeled
    # result depends on `idv` (it is EXACTLY `identityResult idv`, not a constant)
    # — so the empty case genuinely returns the supplied identity element. The
    # impl is kept verbatim so the method's own obligation still discharges; the
    # frozen proof closes it unchanged (the assert is definitional). Verified out
    # of band: the mirror assert claiming the empty result is `single 0` fails to
    # elaborate (an unsolved `False`), so the assert is live.
    #
    # The audit re-ran both halves and added the check the "non-degenerate" claim
    # actually needs. The mirror (`single 0`) fails (exit 1, residual
    # `⊢ False` under the `admiss_1` case) and a TAUTOLOGOUS assert (`(1:Int)=1`)
    # passes (exit 0), so the assert machinery reports the assert's own truth
    # rather than being inert. But neither of those shows idv-DEPENDENCE, which is
    # what the rationale claims — a mirror can fail merely for naming the wrong
    # constructor. So the audit also asserted the empty result equals
    # `identityResult 0`, a CONSTANT of the same shape: it FAILS (exit 1) for a
    # free `idv`, which is the direct evidence that the empty leg tracks the
    # SUPPLIED identity and is not a pinned constant.
    # =====================================================================
    {
        "id": "admiss-empty-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (minMaxResult idv ([] : List Int) = Except.ok (MinMaxResult.identityResult idv)))\n"
            + _IMPL),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "empty input: the modeled result there is exactly "
            "`Except.ok (identityResult idv)` — the supplied identity element, not "
            "a pinned constant — so the empty case genuinely depends on `idv`. The "
            "in-region assert must discharge (else the empty-leg obligation would "
            "be degenerate); the impl is kept verbatim so the method's own "
            "`ensures` still discharges. Re-aims the sibling's admissibility case "
            "(no precondition surface exists on this carrier)."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line, refuted at a concrete input by
    # a witness that FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P. The
    # five rivals attack the three legs of the count-dispatch — the empty leg
    # (twice: the pre-patch failure and a wrong identity value), the single leg,
    # and the combined leg (twice: a lone member instead of the extremum object,
    # and a short-circuit that collapses a surviving distinguished member to the
    # identity element) — moving `rawArgs` across empty / single / two and `idv`
    # across 7 / 3.
    # =====================================================================
    {
        "id": "prepatch-empty-failure",
        "kind": "uniqueness",
        "expect": "reject",
        # PRE-PATCH SHAPE: on the empty argument list, surface the FAILURE leg
        # instead of the identity element. This is the modeled image of the exact
        # bug the change removes — an empty call raises rather than returning a
        # well-defined extremum.
        "module": _impl(
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      match processArgs rawArgs with\n"
            "      | []           => Except.error MinMaxErr.noArguments\n"
            "      | [a]          => Except.ok (MinMaxResult.single a)\n"
            "      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))\n"
            "    return result"),
        "refinement": (
            "this IS the pre-patch behaviour: a call with no arguments surfaces a "
            "failure rather than the identity element. The F2P tests assert the "
            "empty call SUCCEEDS with the identity element (the minimum of no "
            "arguments is the top element, the maximum of no arguments is the "
            "bottom element); with the failure leg on the empty path those "
            "assertions error instead of producing the identity element — it does "
            "NOT resolve. It is the exact bug the change fixes, the discriminator "
            "G-DIFF senses."
        ),
        "rationale": (
            "REJECT from (E2) `rawArgs = [] → out = Except.ok (identityResult "
            "idv)`: on the empty list the post-image demands the success leg "
            "carrying the identity element, but the rival produces "
            "`Except.error .noArguments`. Refuted at the EMPTY list (idv=7) — the "
            "sub-domain the fix targets, where `processArgs_nil` makes the branch "
            "transparent. If it verified, the empty→identity fix would be unpinned "
            "(SPEC-TOO-WEAK / the prepatch family)."
        ),
        "witness": _w_empty(7),
    },
    {
        "id": "weak-empty-wrong-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # EMPTY LEG, WRONG VALUE: on the empty list return `identityResult 0`
        # (a fixed element) instead of the SUPPLIED identity `idv`. Succeeds — so
        # (E2)'s leg is right — but carries the wrong element; correct only when
        # the caller's identity happens to be 0.
        "module": _impl(
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      match processArgs rawArgs with\n"
            "      | []           => Except.ok (MinMaxResult.identityResult 0)\n"
            "      | [a]          => Except.ok (MinMaxResult.single a)\n"
            "      | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))\n"
            "    return result"),
        "refinement": (
            "returning a fixed element for the empty collection instead of the "
            "supplied identity makes the empty minimum and the empty maximum come "
            "out the SAME wrong value regardless of which extremum was requested. "
            "The F2P tests assert the empty minimum is the top element and the "
            "empty maximum is the bottom element (two DIFFERENT elements); a single "
            "hard-coded element cannot equal both, so at least one assertion stays "
            "red — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (E2)/(E1): on the empty list the post-image demands "
            "`Except.ok (identityResult idv)` for the SUPPLIED `idv`, but the "
            "rival returns `identityResult 0`, which disagrees for every idv ≠ 0. "
            "Refuted at the EMPTY list with idv=3 (so `identityResult 3` ≠ "
            "`identityResult 0`), moving the `idv` binder off the prepatch rival's "
            "value and demonstrating the empty result's dependence on `idv`. If it "
            "verified, the empty leg would not be pinned to the supplied identity "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _w_empty(3),
    },
    {
        "id": "weak-single-to-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # SINGLE LEG: return the identity element on EVERY input, collapsing the
        # count-dispatch. Correct on the empty leg, but on a single survivor it
        # returns `identityResult idv` where the spec demands the survivor itself.
        "module": _impl(
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      Except.ok (MinMaxResult.identityResult idv)\n"
            "    return result"),
        "refinement": (
            "collapsing every case to the identity element means a single-argument "
            "call no longer returns that argument. The F2P tests assert a "
            "one-argument extremum returns the argument verbatim (the minimum or "
            "maximum of a single value is that value); with the identity element "
            "returned instead the assertion stays red — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (E1) `out = minMaxResult idv rawArgs` on the SINGLE leg: "
            "when one member survives, the post-image demands `single a`, but the "
            "rival returns `identityResult idv`. The single leg references the "
            "OPAQUE `processArgs`, so the refutation is stated by CONDITIONING on "
            "the carrier — under `processArgs [5] = [5]` (one survivor) the spec "
            "dictates `single 5` and the rival yields `identityResult idv`. The "
            "hypothesis is a single weak equation about one opaque term "
            "(self-satisfiable — no `False` follows from it), so the refuting "
            "input genuinely exists. Refuted at rawArgs=[5], idv=7. If it "
            "verified, the single-survivor leg would be unpinned (SPEC-TOO-WEAK)."
        ),
        "witness": _w_cond(7, "[5]", "processArgs [5] = [5]"),
    },
    {
        "id": "weak-combined-to-single",
        "kind": "uniqueness",
        "expect": "reject",
        # COMBINED LEG: swap the two survivor branches — one survivor builds a
        # `combined [a]` and two-or-more returns `single a` (dropping the rest).
        # On a ≥2-survivor input it returns a lone member where the spec demands
        # the extremum object over all survivors.
        "module": _impl(
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      match processArgs rawArgs with\n"
            "      | []           => Except.ok (MinMaxResult.identityResult idv)\n"
            "      | [a]          => Except.ok (MinMaxResult.combined [a])\n"
            "      | a :: b :: rest => Except.ok (MinMaxResult.single a)\n"
            "    return result"),
        "refinement": (
            "swapping the survivor branches makes a two-or-more-argument call "
            "return a single lone member instead of the extremum object over all "
            "survivors. The F2P/P2P tests assert a multi-argument extremum is the "
            "combined object whose arguments are the survivors (e.g. an extremum "
            "of two distinct arguments is the two-argument object, order-"
            "insensitive); returning one member instead breaks those assertions — "
            "it does NOT resolve."
        ),
        "rationale": (
            "REJECT from (E1) `out = minMaxResult idv rawArgs` on the COMBINED "
            "leg: when two or more members survive, the post-image demands "
            "`combined (a :: b :: rest)`, but the rival returns `single a`. The "
            "combined leg references the OPAQUE `processArgs`, so the refutation "
            "CONDITIONS on the carrier — under `processArgs [5,6] = [5,6]` (two "
            "survivors) the spec dictates `combined [5,6]` and the rival yields "
            "`single 5`. The hypothesis is one weak equation about one opaque term "
            "(self-satisfiable), so the refuting input exists. Refuted at "
            "rawArgs=[5,6], idv=7 — the ≥2 sub-domain, distinct from the single-"
            "leg rival's point. If it verified, the many-survivor leg would be "
            "unpinned (SPEC-TOO-WEAK). Ports the sibling's swap-single-aggregate "
            "rival."
        ),
        "witness": _w_cond(7, "[5, 6]", "processArgs [5, 6] = [5, 6]"),
    },
    {
        "id": "weak-short-circuit-to-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # SHORT-CIRCUIT ON A SURVIVING MEMBER: before the count-dispatch, if a
        # distinguished member value survives normalisation, collapse the whole
        # result to the identity element. This keeps ALL THREE count legs
        # verbatim, so it is correct on every input whose survivors avoid that
        # value — the violation lives on a sub-domain the count-dispatch alone
        # does not separate, and (E1) has to catch it there.
        "module": _impl(
            "    let members := processArgs rawArgs\n"
            "    let result : Except MinMaxErr MinMaxResult :=\n"
            "      if members.contains 0 then Except.ok (MinMaxResult.identityResult idv)\n"
            "      else match members with\n"
            "        | []           => Except.ok (MinMaxResult.identityResult idv)\n"
            "        | [a]          => Except.ok (MinMaxResult.single a)\n"
            "        | a :: b :: rest => Except.ok (MinMaxResult.combined (a :: b :: rest))\n"
            "    return result"),
        "refinement": (
            "adding a short-circuit that returns the identity element whenever a "
            "distinguished member survives makes a multi-argument extremum "
            "collapse to the identity element instead of building the extremum "
            "object over its survivors. The F2P/P2P tests assert a multi-argument "
            "extremum whose members include such a value is still the combined "
            "object over the survivors (the identity element is the extremum of "
            "the EMPTY collection only); collapsing it returns the wrong element "
            "on every such call, so those assertions stay red — it does NOT "
            "resolve. Its real counterpart would also re-shape a normalisation "
            "behaviour the change leaves alone."
        ),
        "rationale": (
            "REJECT from (E1) `out = minMaxResult idv rawArgs` on a sub-domain "
            "NO count leg separates: all three count branches are kept verbatim, "
            "so the rival agrees with the spec on every input whose survivors "
            "avoid the distinguished value and disagrees only when one survives — "
            "exactly the sibling's absorbing/annihilator short-circuit class, "
            "which the first port recorded as inexpressible. It IS expressible: "
            "the survivors are an ordinary `List Int` the impl may inspect, and "
            "(E1) pins the result to the count-dispatch over them, so any "
            "value-triggered collapse contradicts it. Refuted by CONDITIONING on "
            "the carrier at rawArgs=[0,6] under `processArgs [0, 6] = [0, 6]` "
            "(two survivors, one distinguished): the spec dictates "
            "`combined [0, 6]` and the rival yields `identityResult 7`. The "
            "hypothesis is one weak equation about one opaque term "
            "(self-satisfiable), so the refuting input exists. This is a NEW "
            "input point (a two-survivor list whose members differ from the other "
            "combined rival's) probing whether (E1) constrains the impl OUTSIDE "
            "the branch structure it happens to be written with. If it verified, "
            "the dispatch would be pinned only up to an arbitrary "
            "value-triggered override (SPEC-TOO-WEAK). Re-derives the sibling's "
            "weak-absorbing-to-identity rival."
        ),
        "witness": _w_cond(7, "[0, 6]", "processArgs [0, 6] = [0, 6]"),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 9 SPEC cases (1 soundness
# positive, 1 admissibility, 1 frame-mutation, 6 uniqueness rivals) plus a
# 4-case AXIOM lane. It models `lattice_reduce(operands, identity, zero, single,
# aggregate)` over FIVE inputs, with THREE `@Pure @ContractOnly` classifier
# axioms over the input (`has_noncomparable_operand` / `has_absorbing_operand` /
# `canonical_count`) and a postcondition with SEVEN load-bearing clauses pinning
# each branch of a 5-way dispatch (empty / empty-set / absorbing / single /
# aggregate / totality / the non-comparable raise obligation).
#
# This velvet bundle models a NARROWER surface — the purely-functional
# count-driven core the Lean carrier can express: a single method
# `constructMinMax (idv, rawArgs)` whose result is `minMaxResult idv rawArgs`, a
# THREE-way dispatch (empty / single / ≥2) over the normalised-member count. The
# nagini `identity`/`zero`/`single`/`aggregate` sentinels and the comparability /
# absorbing classification collapse: `identity` ↦ `idv` (the empty-collection
# result); `single`/`aggregate` ↦ the `single a` / `combined ms` legs; and the
# `zero` (absorbing) and non-comparable logic live INSIDE the unchanged
# normalisation pipeline, modeled `opaque` as `processArgs` with only
# `processArgs_nil` asserted — so they are deliberately NOT separately modeled
# (directive 7; mapping.md §2-3). Every sibling case is accounted for below.
#
#   sibling case (nagini)              kind          -> here                       disposition
#   ------------------------------------------------------------------------------------------------
#   pos-control-branch-reorder         soundness     -> pos-branch-reorder         PORTED
#   admiss-f2p-shaped                  admissibility -> admiss-empty-nondegenerate  RE-AIMED
#   frame-mutate-readonly-operands     uniqueness    -> (none)                      VACUOUS (no heap)
#   weak-drop-noncomparable-raise      uniqueness    -> (none)                      OMITTED (carrier)
#   weak-empty-to-zero                 uniqueness    -> weak-empty-wrong-identity    RE-EXPRESSED
#   weak-empty-to-single               uniqueness    -> (folded)                     FOLDED (E2 empty leg)
#   weak-absorbing-to-identity         uniqueness    -> weak-short-circuit-to-identity  RE-EXPRESSED (audit)
#   weak-swap-single-aggregate         uniqueness    -> weak-combined-to-single      PORTED
#   weak-over-raise-on-comparable      uniqueness    -> prepatch-empty-failure       RE-EXPRESSED
#   AXIOM_TESTS (x4)                   axiom         -> (none)                        DROPPED (G-AX)
#
# Plus one carrier-specific rival with no single nagini source, defending a leg
# nagini splits across sentinels:
#   weak-single-to-identity  (uniqueness) — the single-survivor leg (E1), refuted
#     by conditioning at a one-survivor input. Nagini pins the single-survivor
#     branch via (P-single); on this carrier the analogous attack is "return the
#     identity element where the survivor is demanded", which no single nagini
#     rival matches one-for-one but which defends the same branch.
#
# PORTED (pos-control-branch-reorder -> pos-branch-reorder): the sibling reorders
#   the count cascade (≥2 first, then ==1, else identity) keeping the mandatory
#   raise and short-circuit. Here there is no raise / absorbing short-circuit to
#   keep (they are inside opaque `processArgs`); the reshape is the SAME idea —
#   bind the normalised members and dispatch with the branch order reversed
#   (≥2 / one / empty) — an observationally identical straight-line impl whose
#   elided proof is retuned to the reordered `match`.
# RE-AIMED (admissibility): the sibling asserts a half-permission input is
#   readable and the four sentinels are pairwise-distinct. There is no
#   precondition and no permission here, so that probe is vacuous. It is re-aimed
#   at the residual total-domain risk — a DEGENERATE post-image — by asserting the
#   empty-collection result is exactly `identityResult idv` (depends on the
#   supplied identity, not a constant).
# RE-EXPRESSED (weak-empty-to-zero -> weak-empty-wrong-identity): the sibling
#   returns the annihilator `zero` on the empty branch. The `zero` sentinel is not
#   modeled on this carrier (absorbing/annihilator logic is inside opaque
#   `processArgs`); the SAME argument — "the empty collection must yield the
#   identity element, not some other element" — is re-expressed as returning a
#   fixed WRONG identity element (`identityResult 0`) on the empty branch, refuted
#   because it disagrees with the supplied `idv`.
# RE-EXPRESSED (weak-over-raise-on-comparable -> prepatch-empty-failure): the
#   sibling raises unconditionally, a superset of the pre-patch empty-args bug.
#   The load-bearing part on this carrier is the EMPTY-collection totality — the
#   exact case the fix introduces — so it is re-expressed as its minimal image:
#   surface the failure leg on the empty argument list (the pre-patch shape). This
#   is also the G-DIFF discriminator (the modeled pre-patch bug).
# FOLDED (weak-empty-to-single): the sibling's empty->single rival attacks the
#   SAME empty-leg clause as empty-to-zero. On this carrier every empty-leg
#   violation ("empty returns anything but `identityResult idv`") is one clause
#   (E2); it is doubly attacked already — by prepatch-empty-failure (empty->error)
#   and weak-empty-wrong-identity (empty->wrong element). A third empty-leg rival
#   returning `single idv` would be refuted at the SAME input `[]` for the same
#   clause, adding no binder/clause coverage, so it is folded rather than shipped
#   redundantly. Folded for REDUNDANCY, not for inexpressibility: the audit built
#   it (empty leg -> `Except.ok (single idv)`, i.e. the right value under the
#   wrong constructor) and confirmed it lands — rival does not verify, the
#   `_w_empty(7)` witness elaborates against it (exit 0) and fails on the frozen
#   solution (exit 1). It is left out because it duplicates an attacked clause at
#   an attacked point, and that judgement is the reader's to disagree with.
# RE-EXPRESSED (weak-absorbing-to-identity -> weak-short-circuit-to-identity),
#   ADDED BY AUDIT. The first port recorded this OMITTED as inexpressible, on the
#   argument that the absorbing/annihilator short-circuit lives inside opaque
#   `processArgs` so no clause could be violated and "no discriminating witness
#   could exist". That argument is WRONG and the audit overturned it with real
#   builds. The rival does not need the spec to name an absorbing sentinel: it
#   only needs to deviate from `minMaxResult idv rawArgs`, and (E1) pins that on
#   EVERY input. A short-circuit keyed on a surviving member value is a deviation
#   the count-dispatch does not authorise, and although the survivors are opaque,
#   the refutation is stated at a point described by HYPOTHESIS exactly as the
#   single/combined rivals already do (`processArgs [0, 6] = [0, 6]`), which is
#   what makes an opaque carrier attackable at all. Measured out-of-band: the
#   rival does NOT verify (`unsolved goals`, the residual being the collapse
#   implication), its witness ELABORATES against the rival (exit 0) and FAILS on
#   the frozen solution with a semantic `⊢ False` (exit 1), and the consistency
#   probe cannot derive `False` from the hypothesis (exit 1). So the clause was
#   expressible all along and the case now ships. It also carries real coverage:
#   it is the ONLY rival that keeps all three count legs verbatim, so it is the
#   only one testing that (E1) constrains the impl outside the branch structure
#   the frozen impl is written with.
# OMITTED (weak-drop-noncomparable-raise): attacks behaviour that is NOT modeled
#   on this carrier. The non-comparable rejection (nagini (P-oblig)) obligates a
#   RAISE on a classified sub-domain, and the classification predicate has no
#   image here: the spec's only failure constructor is `MinMaxErr.noArguments`,
#   `MinMaxResult` carries no non-comparable case, and there is no
#   `has_noncomparable_operand` over which an obligation to fail could be
#   stated — the pipeline's own `ValueError` is an UNCHANGED-callee behaviour
#   deliberately left inside opaque `processArgs` (directive 7 / mapping.md §3),
#   so (E1) demands `Except.ok (...)` on every input and a rival that raises more
#   is rejected as a plain (E1) deviation rather than as the missing-raise
#   defect nagini pins. Note this is a narrower claim than the audit refuted
#   above: what is inexpressible is the OBLIGATION TO FAIL, not merely a rival
#   whose behaviour differs on an opaque-classified sub-domain. Genuine carrier
#   narrowing, NOT difficulty.
# VACUOUS (frame-mutate-readonly-operands): the sibling writes to a read-only
#   input held at `Acc(list_pred(operands),1/2)` and is rejected for insufficient
#   permission. This backend is referentially transparent — `idv` and `rawArgs`
#   are immutable values, this bundle declares no `mut` binder, there is no heap
#   or aliasing — so there is no read-only input to overwrite and no permission
#   system to trip. No substitute is fabricated.
# NOT-SHIPPABLE / TOOLING (divergence) — REASON CORRECTED BY THE SECOND AUDIT.
#   The earlier note called this class VACUOUS on the argument that "a diverging
#   reject rival cannot be written at all". That argument is FALSE and was
#   overturned with real builds. This bundle is `total`, so per the F' lane the
#   diverging rival is the shippable direction, and it does exist: a `while` loop
#   with no `decreasing` clause is writable in the impl region and the variant is
#   REJECTED, `error: Decreasing annotations are required in total correctness
#   semantics` (exit 1). Adding a bogus `decreasing 1` does not even typecheck
#   (`failed to synthesize OfNat (Option Nat) 1`), confirming the measure slot is
#   real and checked. So the spec DOES constrain divergence here.
#   What stops it shipping is the witness half, also measured, not argued: the
#   termination diagnostic is raised at the `method` declaration, OUTSIDE the
#   `prove_correct` body that `witness_file` strips, so the witness file carries
#   a hard elaboration error before the witness is even reached. Measured: the
#   `_w_empty(7)`-shaped witness fails against the diverging rival (exit 1), and
#   so does the weakest conceivable witness `example : True := trivial` (exit 1,
#   same termination diagnostic). Since half 1 of the discrimination check
#   ("the witness ELABORATES against the rival") is unsatisfiable for ANY witness,
#   the gate can only record `witness-unproven` — inconclusive, never a pass.
#   Disposition therefore: the class is REAL and REJECTED but NOT witness-
#   expressible on this carrier, which is a tooling limit on the reject lane
#   rather than vacuity or a spec hole. A rival whose rejection comes from the
#   termination checker rather than from either `ensures` is exactly what the
#   witness requirement declines to credit. The sibling carries no diverge-* case
#   either, so nothing is dropped relative to it.
# DROPPED (AXIOM_TESTS x4): the axiom lane is G-AX's job (axiom_check.py validates
#   `processArgs_nil` against the real normalisation pipeline on the base repo,
#   plus the single/combined reference legs); this gate ignores AXIOM_TESTS
#   regardless.
#
# COVERAGE. The sole obligation (`prove_correct constructMinMax`) is DEFENDED
# (pos-branch-reorder + admiss-empty-nondegenerate) and ATTACKED (all five
# reject rivals). BOTH independent postcondition clauses are attacked: (E2) the
# empty-leg fix — by prepatch-empty-failure (failure leg) and
# weak-empty-wrong-identity (wrong element) — and (E1) the full count-dispatch —
# on its single leg (weak-single-to-identity), its combined leg
# (weak-combined-to-single), and OUTSIDE the branch structure entirely
# (weak-short-circuit-to-identity, which keeps all three count legs verbatim and
# deviates only on a value-triggered sub-domain). Every input binder of the spec
# predicates is varied by the reject witnesses: `rawArgs` moves across `[]` /
# `[5]` / `[5,6]` / `[0,6]` (empty / single / two survivors — each of the three
# dispatch legs, plus a second two-survivor list with different members) and
# `idv` moves across 7 and 3 (so the empty result's dependence on the supplied
# identity is demonstrated, not pinned). Five DISTINCT input points: `[]`@idv7,
# `[]`@idv3, `[5]`@idv7, `[5,6]`@idv7, `[0,6]`@idv7. The two empty rivals fail at
# `[]` for DIFFERENT reasons (failure leg vs wrong element) and are separated by
# the `idv` they abuse; the single and combined rivals sit at disjoint cardinality
# regimes, so each carries its own discriminating input.
#
# The `idv` variation is MEANINGFUL, not two spellings of one point: measured
# out-of-band, the wrong-identity rival's witness re-stated at `idv=0` FAILS to
# elaborate against that very rival (exit 1, residual `⊢ False`) — at idv=0 the
# rival's hard-coded element coincides with the supplied one and it is
# observationally identical to the frozen impl there. So 7/3 versus 0 separates
# an agreement point from a disagreement point, which is what makes the binder's
# variation carry information.
#
# No frame/permission or divergence rival is fabricated (both classes vacuous on
# this carrier).
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT — spec-strength probes beyond the shipped cases. Every claim
# below is a real `lean_verify.sh` build; nothing here is argued.
#
# SPEC-TOO-WEAK probes (new wrong impls the battery did not contain; each MUST
# fail to verify, and one that verified would be a hole in the FROZEN spec).
# Six written, six rejected — NO spec hole found:
#   * dispatch on the RAW arguments instead of the normalised members (so
#     normalisation is skipped entirely) — rejected; residual is the raw `match`
#     against the `processArgs` one. Also landed as a witness (rival exit 0, gold
#     exit 1 with `⊢ False`, probe exit 1), i.e. (E1) really does force the impl
#     through the normalisation pipeline.
#   * empty leg -> `single idv`: right value, wrong constructor — rejected on
#     BOTH clauses (residual `¬rawArgs = []` for (E2) and the constructor
#     mismatch for (E1)).
#   * combined leg -> survivors REVERSED — rejected; witness landed (exit 0).
#   * combined leg -> only the first two survivors (`rest` dropped) — rejected;
#     witness landed at a THREE-survivor point (rival 0, gold 1, probe 1).
#   * single leg -> `combined [a]` (a one-member extremum object instead of the
#     member verbatim) — rejected; witness landed (exit 0).
#   * every non-empty raw list -> the failure leg, keeping the empty leg correct
#     (satisfies (E2) alone) — rejected by (E1), which confirms (E2) is not
#     carrying the spec by itself.
#
# SPEC-TOO-STRONG probes (new faithful CORRECT reshapes; one the spec could not
# admit would be a soundness hole). Four written, all four provable — no hole:
#   * a redundant `if rawArgs = [] then identity` guard ahead of the dispatch:
#     verifies under the FROZEN proof, unchanged (exit 0).
#   * `return` out of each match arm instead of binding `let result`: does NOT
#     close under the frozen script (the residual is `¬rawArgs = []` in the two
#     non-empty arms — the early `return` splits (E2) across branches), but it
#     IS provable — three independent retunes each verify (exit 0), e.g.
#     `rcases rawArgs` before `simp_all [minMaxResult, processArgs_nil]`. A
#     retune of the elided proof is admissible for a correct reshape, so this is
#     tactic-shape sensitivity, NOT a spec that rejects the impl.
#   * dispatch via `members.length = 0` before destructuring: same story —
#     needs the reordered-branch retune, then verifies (exit 0).
#   * `return minMaxResult idv rawArgs` (the cheapest correct impl): verifies
#     (exit 0), as an honest spec must allow — recorded as a control, not shipped,
#     since an impl that echoes the spec `def` tests nothing.
#
# So the frozen spec came out of both probes intact: nothing wrong verified, and
# nothing faithful was rejected once its elided proof was allowed to be retuned.
#
# ---------------------------------------------------------------------------
# SECOND INDEPENDENT AUDIT — every case re-derived from scratch with the real
# verifier (no claim below is inherited from the first audit's record; each is a
# build this pass ran itself).
#
# The five reject cases each reproduce the FULL discrimination matrix:
#   rival module exit 1 / witness-vs-rival exit 0 / witness-vs-gold exit 1 /
#   consistency probe exit 1 (for the three that bind a hypothesis).
# Every gold-side residual is a plain evaluation — `⊢ False` bare for the two
# empty-leg cases, `h : processArgs [..] = [..] ⊢ False` for the three
# conditioned ones. No stuck `decide`, no missing identifier, no type error, no
# timeout anywhere in the cell.
#
# FORGERY CONTROL (attack B′), run on ALL FIVE cases rather than a sample: each
# witness was rebuilt with its claim FLIPPED (`≠` -> `=`, i.e. asserting the impl
# is CORRECT at that same point) and built against both subjects.
#   flipped-vs-GOLD    exit 0  (all five) — gold's exit code tracks the CLAIM,
#                              so the shipped `≠` failures are real refutations
#                              and not a reduction that never happened;
#   flipped-vs-RIVAL   exit 1  (all five, residual `⊢ False`) — the DIRECTION of
#                              the claim is what decides each build.
# That pair is the evidence; nothing here rests on reading an error as "semantic".
#
# SHAPE-vs-WRONGNESS (the control that separates a refutation from a tactic
# mismatch): both witness shapes were rebuilt against the CORRECT positive-control
# reshape — `_w_empty(7)` exit 1 and `_w_cond(7,"[5, 6]",...)` exit 1. The
# witnesses discriminate WRONGNESS, not shape.
#
# NEITHER POSITIVE IS NEUTERED. The soundness reshape's own impl body was rebuilt
# against the FROZEN proof script: exit 1, `unsolved goals` whose residual is the
# two `match` exprs in opposite branch order — so the reshape is NOT definitionally
# equal to the frozen impl and its retune is load-bearing. The admissibility
# assert's machinery was probed four ways: the shipped claim passes (exit 0), a
# TAUTOLOGY `(1:Int)=1` passes (exit 0), an outright FALSE `(1:Int)=2` fails
# (exit 1), a wrong-constructor mirror (`single 0`) fails (exit 1), and — the
# probe the non-degeneracy claim actually needs — `identityResult 0`, a CONSTANT
# of the SAME shape, FAILS (exit 1) for a free `idv`. So the assert reports its
# own truth and the empty leg demonstrably tracks the SUPPLIED identity.
#
# SPEC-TOO-WEAK, seven FURTHER wrong impls this pass wrote (disjoint from both the
# shipped rivals and the first audit's six). All seven REJECTED (exit 1), so still
# no hole:
#   * combined leg duplicates the head (`a :: a :: rest`) — survivors reshaped;
#   * single leg returns `single 0` (a fixed literal, not the survivor);
#   * dispatch on `rawArgs.length` while taking values from the members;
#   * combined leg returns the survivors `mergeSort`ed (order perturbed);
#   * the ECHO attack: `if rawArgs = [] then identityResult idv else
#     minMaxResult 0 rawArgs` — right on (E2), echoes the spec `def` on the
#     non-empty leg but at the WRONG identity; (E1) still catches it;
#   * a measure-less `while` loop (see the divergence note) — rejected by the
#     termination obligation;
#   * the same loop with a bogus `decreasing 1` — does not even typecheck.
# SPEC-TOO-STRONG, three FURTHER correct reshapes, all VERIFYING under the FROZEN
# proof unchanged (exit 0): an if-ladder binding `members` first; a two-step
# `let base := ... ; let result := base`; and a redundant `members.isEmpty` guard
# ahead of the dispatch. One more (`return` out of each match arm) fails the
# frozen script (exit 1, residual `⊢ ¬rawArgs = []` in the two non-empty arms)
# and verifies once the elided proof is retuned with `rcases rawArgs` (exit 0) —
# admissible for a reshape, so tactic-shape sensitivity, not a spec that rejects
# a faithful impl. No soundness hole in either direction.
#
# STATEMENT INTEGRITY (attack A) re-checked by byte-diffing all seven case modules
# against Solution.lean: every diff is confined to the impl region, plus the
# elided `prove_correct` body for the soundness case alone. Both `ensures` lines
# and the `prove_correct constructMinMax` header are byte-identical in all seven.
#
# AXIOM_TESTS: empty. The axiom lane is G-AX's job; this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
