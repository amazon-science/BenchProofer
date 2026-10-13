"""properties.py — G-PBT falsification battery for sympy__sympy-19495 (velvet).

NOT a Velvet module; a record of adversarially-reasoned falsification cases the
G-PBT gate executes. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region is changed — the consumer spec view
elides that region, so ``markers.same_spec`` holds and the
``prove_correct evalSubsFree`` obligation survives with a byte-identical
statement). ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must ELABORATE against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method over a purely-functional core):

  evalSubsFree (boundSym : Binder) (condition : Cond) (baseSet : SetObj)
               (old : Old) (new : New) return (out : BuiltSet)
    require CondSubDefined condition old new
    require BaseSubDefined baseSet old new
    require BuildsDefined boundSym condition baseSet old new
    require oldObj old ≠ binderObj boundSym
    ensures out = evalSubsSpec boundSym condition baseSet old new

  where the single load-bearing clause pins ``out`` to

    evalSubsSpec boundSym condition baseSet old new
      = mkSet boundSym (substCond condition old new) (substSet baseSet old new)

  The operation replaces a free symbol ``old`` (distinct from the set's own
  bound symbol) by ``new`` inside a membership-style set
  ``{ boundSym | condition, over baseSet }``. The intended result pushes the
  substitution through BOTH the condition and the base set and rebuilds the set
  keeping the set's ORIGINAL bound symbol. Three independent argument positions
  of the rebuilt set are pinned, and each is a load-bearing decision:

   (binder)  the rebuilt set is keyed on ``boundSym`` — the set's OWN internal
             binder — NEVER on the replacement value ``new`` (nor on the
             replaced free symbol ``old``). The bound symbol is internal to the
             set: substituting some OTHER, free symbol must leave it untouched.
             This is the discriminating behaviour the public issue reports (the
             bound variable being mistaken for the substituted symbol).
             AUDIT NOTE on where this position is observable, measured against
             the real callees rather than argued (and CORRECTING an earlier
             revision of this note, which claimed the binder is unobservable
             whenever the substituted condition collapses): the binder is
             discriminated on the ordinary, NON-collapsing sub-domain by every
             wrong binder choice, and ALSO on the collapse sub-domain once the
             rival is the real pre-fix rebuild rather than a binder-only
             near-miss. The pre-fix code does not merely rename the binder, it
             switches the constructor to its value-keyed invocation shape
             (``ConditionSet(new, Contains(new, base), base)``), and that shape's
             membership test can be FALSE — which is why keying on the
             replacement fails the very interval-collapse assertion this
             instance's test patch changed, and why keying on the replaced symbol
             fails both collapse assertions. Per-assertion measurements are in
             the reject block below. The (base) position is the one the collapse
             sub-domain discriminates most sharply (collapse returns the base, so
             a wrong base survives nothing there).
   (cond)    the condition slot carries ``substCond condition old new`` — the
             substitution actually applied to the condition, not the raw
             pre-substitution condition. (Its two arguments' ORDER is no longer
             one of the decisions the ``ensures`` makes: with the substitution's
             argument roles sorted (``Old``/``New``) the reversed call is a type
             error — see the retirement note below.)
   (base)    the base slot carries ``substSet baseSet old new`` — the
             substitution actually applied to the base set, not the raw base set.

WHAT THE MODEL'S DOMAIN DECIDES INSTEAD OF THE ``ensures``. BOTH callees are
PARTIAL — each raises on arguments outside its domain — so the model carries their
domains explicitly (mapping.md §3.3, §3.4, §3.5): the constructor's three slots
get three sorts (``Binder``, ``Cond``, ``SetObj``) with one axiom per real
invocation shape (``mkSet`` binder-keyed, ``mkSetOnValue`` value-keyed) and a
result sort ``BuiltSet`` distinct from the component sort; the substitution
callee's two argument roles get the sorts ``Old`` and ``New``; and NEITHER
callee's partiality is exhausted by its sorts, so the remainder is carried by
three ``require``s. The substitution callee refuses a replacement the component
cannot be compared against: ``CondSubDefined`` / ``BaseSubDefined``. The
CONSTRUCTOR refuses with every slot holding exactly the right kind of object,
because building the set tests the condition against the elements of a finite
base and an element the condition cannot be compared against makes that test
signal instead of answering: ``BuildsDefined``, which ranges over EVERY
set-building invocation the model can NAME at these arguments and not merely the
one the ``ensures`` returns. FIVE consequences shape this battery, and the FIRST
is the one an adversary should check first:

  * THE DISCRIMINATING DECISION IS STILL AN ``ensures`` DECISION, not a typing
    one. The sorts must not be allowed to answer the question the instance is
    about. They do not: the target behaviour is *rebuild keyed on the set's own
    binder* versus *rebuild keyed on the substituted value*, and BOTH are
    well-sorted and writable — ``mkSet boundSym …`` and
    ``mkSetOnValue (newObj new) …`` — because the value-keyed shape is a real
    invocation shape of the same real callee (it is the one the deleted code
    used). The wrong one is rejected by the postcondition and by nothing else; the
    ``weak-keyed-on-new`` rival IS that shape, and it is refuted with a
    discriminating witness. What typing removes is only the family of
    applications the REAL callees would refuse — never a behaviour the real code
    could exhibit. The check that this is so is mechanical and was re-run on this
    model: all FIVE reject rivals below ELABORATE and are rejected with
    ``unsolved goals`` on the postcondition, and so are 3 further wrong impls of
    the attack-D list (both components raw; the value-keyed shape over a raw base;
    a doubly-substituted condition) — 8 behavioural rejections, not one of them a
    sort mismatch. A ninth wrong impl (a diverging ``while true`` prefix) is
    rejected by the total-correctness termination requirement
    (``Decreasing annotations are required in total correctness semantics``).

  * ARGUMENT ROUTING AND SUBSTITUTION DIRECTION are no longer ``ensures``
    decisions but TYPING ones, and two rivals were retired for that reason
    (recorded, not silently dropped). ``weak-slots-exchanged`` (the two computed
    components exchanged between the constructor's condition and base slots) died
    with the first sorting: a ``SetObj`` cannot inhabit a ``Cond`` slot. Its
    replacement ``weak-subst-direction-reversed`` (both components computed by the
    right callee and routed to the right slot, but the substitution applied
    BACKWARDS) dies with this one: with the substitution's argument roles sorted,
    ``substCond condition new old`` is a type error
    (``Application type mismatch: The argument new has type New but is expected to
    have type Old``). A type-incorrect rival cannot be a reject case at all — the
    gate builds each witness in a file that RETAINS the rival's impl region, so a
    non-elaborating module reports ``witness-unproven`` (MALFORMED-TESTS) rather
    than a refutation. Every transposition of the gold impl's own arguments is now
    ill-typed, so what is left for the ``ensures`` to decide is WHICH handle lands
    in a slot and WHICH invocation shape is used — exactly what the five rivals
    attack.
  * A rival that returns exactly the spec's value but ALSO invokes a callee out of
    its domain and DISCARDS the result — the family a total-function callee model
    cannot observe, because a weakest-precondition calculus sees nothing of a
    discarded application of a total function — is excluded here by TWO mechanisms,
    one for each kind of partiality the real callees have, and NEITHER of them is
    the ``ensures`` (which constrains only the returned value, so it can never see
    a discarded call at all).
    Where the out-of-domain call is SORTALLY wrong it is a TYPE ERROR, hence
    unwritable rather than merely unproven. MEASURED on this model, NINE such
    probes: an extra constructor call with a plain object in the binder slot (the
    ORIGINAL defect this bundle was repaired for); the stored base set or the
    condition substituted AT THE SET'S OWN BINDER; a MANUFACTURED set (the result
    of a constructor call) substituted at its own binder, both directly and
    nested; the substitution reversed, discarded and returned; the replaced object
    supplied in the replacement role; and a built set fed back into a component
    slot. All nine are rejected before verification, e.g. ``error: Application
    type mismatch: The argument new has type New but is expected to have type
    Binder in the application mkSet new``. Two more (echoing a raw or substituted
    component where the operation must return a BUILT set) are rejected the same
    way, which is the ``SetObj``/``BuiltSet`` split showing up in the return
    position.
    Where it is NOT sortally wrong — every slot holding exactly the kind of object
    the constructor asks for, and the real constructor refusing anyway, because it
    tests the condition against the elements of a finite base — the call IS
    writable and well-typed, so the sorts cannot exclude it and the mechanism is
    the third precondition instead. ``BuildsDefined boundSym condition baseSet old
    new`` asserts the constructor's definedness at EVERY set-building invocation
    this model can NAME at these arguments — either shape, at the stored components
    and at their substituted forms, keyed on the binder or on either substitution
    argument (mapping.md §3.5). Under it, a discarded well-typed call denotes an
    invocation the real constructor accepts, which is precisely what licenses
    reading the two building axioms as total functions of their sorts. Without it a
    rival could make one extra, result-discarded, fully well-sorted rebuild that
    the real callee REFUSES — on this instance's own F2P-shaped input — and still
    verify while its Python counterpart raises; axiom_check.py obligation 16 is
    that input, measured on PRE-PATCH source, and obligations 17–18 measure the
    precondition's density and the completeness of its coverage.
  * The out-of-domain family is excluded WITHOUT penalising harmless extra work.
    MEASURED, six writable discarded-call probes — a doubly-substituted condition,
    a doubly-substituted base, a raw-component rebuild, and the value-keyed shape
    on each of the three objects in scope (the replaced object, the replacement,
    the set's own binder) — all VERIFY, each denoting an invocation the real
    constructor accepts on every input the three preconditions admit
    (axiom_check.py obligation 15 measures those same shapes on the boundary grids,
    and obligation 18 measures all 41904 nameable set-building invocations over the
    pool). So the domain model rejects the calls the real code would refuse and
    nothing else: what ``BuildsDefined`` costs is measured too — 19 of 2347
    admitted pool inputs, of which 13 are excluded only because a writable EXTRA
    shape is refused while the operation itself returns, i.e. 0.6% of the domain on
    which the contract is silent rather than wrong.
  * The three definedness ``require``s are OPAQUE ``Prop``s with no defining
    equation, so they cannot be exploited from inside the impl region and no rival
    can be built on them: nothing about a condition, a set or a built set follows
    from any of them. They are also not hypotheses in scope inside the impl
    (measured on each of the three: ``by assumption`` fails), so they neither
    strengthen nor weaken what the rivals below have to do.

CARRIER NOTE — THE OPAQUE BOUNDARY, and how a witness reaches the post-image.
The whole result flows through the opaque constructor ``mkSet`` over the opaque
substitution callees ``substCond``/``substSet``, so a ``decide`` on a literal
cannot COMPUTE it — all SEVEN sorts are opaque with NO closed term available (the
axioms region declares no constant of any of them, and the previous revision's
``objDefault``/``Inhabited`` pair is gone), so there is nothing to reduce. Two facts
make the reject lane expressible anyway (the documented "condition on the
carrier" route):

  * The gold impl is a straight-line ``let``/``return`` body (no loop), so
    ``NonDetT.run (evalSubsFree …)`` reduces under ``simp [NonDetT.run, pure]``
    to the impl's straight-line value — a ``Prop`` goal, never IR-compiled
    (``extract_program_for`` is unavailable: the method is ``noncomputable``
    over opaque callees, so the extractor's generated ``def`` would fail the
    IR-compile check).
  * Each rival is likewise straight-line, so ``NonDetT.run (rival …)`` reduces
    to the rival's wrong rebuild term. The witness then CONDITIONS on the
    opaque carrier: it hypothesises that the rival's rebuild differs from
    the spec's ``mkSet boundSym (substCond …) (substSet …)`` (a single ``≠``
    about opaque terms) and concludes the program's output differs from the spec's.
    Against the FROZEN impl the same reduction lands on ``mkSet boundSym … =
    mkSet boundSym …`` with the reduced goal ``False``, which the hypothesis
    cannot close — so the witness FAILS on gold. Both halves were verified with
    real builds during authoring, and the consistency probe (``example
    <binders> : False``) fails on each witness's single hypothesis, so no
    witness assumes its own conclusion.

Every reject witness carries exactly ONE hypothesis about a single opaque
composition and is jointly satisfiable. No ``sorry``/``admit``/
``native_decide``/``axiom``.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
models the change as TWO functions over an ``int``-tagged carrier
(``Result0(kind, sym, base, cond)`` with ``kind ∈ {EMPTY, BASE, SET}`` and a
``COND ∈ {FALSE, TRUE, OPEN}`` tag): a constructor deep-model ``build`` and the
patched branch ``replace_free_parameter``. THIS backend models the SAME change
but at the level the change actually lives — the uniform rebuild of the set from
its own binder together with the substituted condition and substituted base —
over OPAQUE SORTED carriers with no ``kind``/``COND`` tag machinery. The
per-branch reduction (false→empty, true→base, open→set) is a property of the
UNCHANGED constructor ``mkSet`` (an A-reference validated by G-AX, mapping.md
§3), NOT of the changed method, so the nagini rivals that attack the ``kind``
tags of ``build`` have no counterpart here; the rivals that attack the REBUILD's
binder/argument choice re-site onto ``mkSet``'s three argument positions. See
the accounting block for every sibling case.

  * PARTIAL-DOMAIN / value-mask (uniqueness) — APPLIES, and carries the reject
    lane. The three argument positions of the rebuild are transparent
    combinations of the opaque callees, so a rival wrong on one position while
    correct on the others is the natural falsifier.
  * FRAME-MUTATION / permission (nagini N/A here already) — VACUOUS. This
    backend is referentially transparent; ``boundSym``/``condition``/
    ``baseSet``/``old``/``new`` are immutable non-``mut`` values, there is no
    heap, no aliasing and no fractional-permission system to trip. (The nagini
    sibling itself declared this class N/A — no reference-typed inputs — so
    there is nothing even to re-express.)
  * DIVERGENCE / non-termination — the obligation IS enforced here, but the class
    is UNSHIPPABLE ON THIS CARRIER for a witness reason, not a vacuity one. This
    bundle is ``total`` (``loom.semantics.termination "total"``), so the verifier
    does discharge a termination obligation and a rival whose loop carries no
    decreasing measure is genuinely REJECTED. MEASURED, correcting an earlier
    draft of this paragraph that claimed "a diverging implementation cannot be
    written": two diverging rivals WERE written over this signature (``while true
    do i := i + 1`` before the correct rebuild; and a loop whose counter moves
    away from its bound) and both are rejected, each with
    ``error: Decreasing annotations are required in total correctness semantics``
    plus the residual ``Failed to prove assertion without names: WPGen (forIn
    Lean.Loop.mk …)``. Both also pass ``variant_problems`` (in scope: same_spec
    holds, the obligation survives, no new assumption), so the rejection is real
    and attributable to the termination clause.
    What blocks SHIPPING it is the witness half. CORRECTED BY A THIRD AUDIT,
    which re-measured this paragraph's mechanism and found it wrong in a way that
    mattered: the previous draft claimed "the diverging module does not elaborate
    AT ALL … there is nothing a better-authored witness can do here: the rival's
    rejection happens strictly before any witness is reachable". That is true of
    the two shapes it measured and FALSE in general, so it was resting the
    disposition on a reason that does not hold. There are FOUR distinguishable
    diverging shapes on this signature and they split into two mechanisms:

      (i) NO measure at all (``while true do i := i + 1``) and the two SELF-CALL
          shapes (re-entering ``evalSubsFree`` on the same arguments, bound or
          returned). These really do fail at the DECLARATION: the bare loop with
          ``error: Decreasing annotations are required in total correctness
          semantics``, and the self-call with ``error: fail to show termination
          for evalSubsFree … failed to infer structural recursion``. A
          trivially-true witness (``example : (1:Nat) + 1 = 2 := by decide``)
          appended to each fails at exit 1 for that same reason, so the gate would
          record ``witness-unproven``. For these three the old sentence holds.
      (ii) A measure CLAIMED BUT NOT KEPT — the shape the sibling's
          ``weak-rfp-measure-not-kept`` is about: a ``while i ≥ 0`` carrying
          ``invariant``/``done_with``/``decreasing i`` whose body does ``i := i +
          1``. This one ELABORATES (the appended trivial witness builds at exit
          0, measured, which is the control the previous draft never ran) and is
          rejected BEHAVIOURALLY on the termination clause itself:
          ``error: unsolved goals case «decreasing_1: i»``. So the obligation is
          checked rather than taken on trust, and the module is reachable by a
          witness. A second shape (``i := 1``, ``while i > 0``, counter moving
          away from its bound) behaves identically.

    What actually blocks (ii) is the KNOWN IRREDUCIBLE-LOOP-TERM class the gate
    itself screens for (``pbt.py _STUCK_UNIFICATION_TERM``), not module
    non-elaboration. MEASURED, three witness shapes against the (ii) rival, all
    exit 1 on the RIVAL side (the half that must succeed): the shipped
    ``≠ DivM.res`` shape leaves ``⊢ ¬(NonDetT.run do let _ ← forIn Lean.Loop.mk 0
    fun x r => … ) = …``; a ``= DivM.div`` shape leaves the same unreduced
    ``forIn Lean.Loop.mk`` term; and the conditioned shape fails with ``Type
    mismatch: After simplification, term heq has type (NonDetT.run do let _ ←
    forIn Lean.Loop.mk …) = DivM.res … but is expected to have type False``. The
    loop term does not normalise under ``simp [NonDetT.run, pure]``, so no claim
    about the program's output can be stated against it. ``witness_reference``
    does not help either: it substitutes the GOLD-side subject, and the failing
    half here is the rival's.
    Disposition: the termination clause is genuinely defended by the carrier — and
    (ii) shows it is defended by a CHECKED measure, not by the parser — but the
    class is NOT EXPRESSIBLE as a witnessed reject case, because a witness cannot
    reach the post-image of a loop-bearing rival on this carrier. A carrier limit
    with the exact error text, not a vacuous class and not a spec hole.
  * UNGROUNDED-ORACLE ECHO — N/A in the harmful sense. ``evalSubsSpec`` is a
    total ``def`` written directly over the transparent rebuild structure and
    the opaque callees; it is not an opaque answer-key the impl could echo
    without doing the work (the impl must forward the right binder and apply the
    right substitution to each component). The ``axioms`` region declares
    ``substCond``/``substSet``/``mkSet``/``mkSetOnValue`` as opaque with NO
    ``ensures`` — A-references validated by G-AX (mapping.md §3), not consumed
    contracts to attack. The sorts are not ``ensures`` clauses either: they are
    the callees' DOMAIN, discharged against the real callees by G-AX
    obligations 6–11 and 15 rather than assumed (mapping.md §3.3, §3.4). Nor are
    the three definedness ``require``s consumed contracts: they are opaque
    ``Prop``s stating the rest of the two callees' domains — the substitution
    helper's, discharged by obligations 11–14 (mapping.md §3.4), and the
    constructor's own non-sortal part, discharged by obligations 16–18
    (mapping.md §3.5) — each measured against the real callees on PRE-PATCH
    source, not assumed.

WITNESS PLACEMENT / BINDER COVERAGE. FIVE input binders, ALL opaque
(``boundSym : Binder``, ``condition : Cond``, ``baseSet : SetObj``,
``old : Old``, ``new : New``) — none is a transparent ``Nat``/``Bool`` that could be
moved across concrete literals. So every witness necessarily QUANTIFIES over
abstract binders and states its refutation at a point described by hypothesis;
the positional coverage parser reads head-quantified arguments as unreadable, so
binder coverage here is carried by the by-name signal (each binder is named in
the witnesses/rationales that abuse it). This is the documented opaque-carrier
situation, not an unattacked binder. FIVE rivals partition the clause. FOUR cover
its three argument positions: the (binder) position by ``weak-keyed-on-new`` (now
VERBATIM the deleted pre-fix rebuild — see below) and ``weak-keyed-on-old``, the
(cond) position by ``weak-cond-not-substituted``, the (base) position by
``weak-base-not-substituted``. Each of those holds the other positions fixed at
gold while exactly one is broken, so no rejection is confounded by another
position. The FIFTH, ``weak-keyed-on-binder-value``, keeps the binder OBJECT
correct and gets the constructor's INVOCATION SHAPE wrong instead — a decision
that only exists because the axiom surface names both real invocation shapes.
That is the whole of what the ``ensures`` still decides on this carrier: the two
ROUTING decisions a battery would otherwise have to attack (which computed
component reaches which constructor slot, and which way round the substitution's
two arguments go) are now ill-typed, and both former rivals are recorded as
retired with their measured type errors in the accounting block rather than
dropped.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-19495"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole gold rebuild body (the code + comment lines
# ---- strictly inside -- impl-start / -- impl-end). It lies wholly inside the
# ---- elided impl region and is unique in Solution.lean (both facts asserted at
# ---- load by _swap), so every variant's edit never touches the spec regions
# ---- (axioms / pure / pre / post + the method signature and the `ensures`) nor
# ---- the `prove_correct evalSubsFree` header. -------------------------------
_GOLD_IMPL = (
    "    -- Push the substitution through the condition and the base set, then rebuild\n"
    "    -- the set from those components, bound by the set's own original binder.\n"
    "    let newCond := substCond condition old new\n"
    "    let newBase := substSet baseSet old new\n"
    "    return mkSet boundSym newCond newBase"
)
assert _BASE.count(_GOLD_IMPL) == 1, "impl-body anchor drift — re-sync _GOLD_IMPL"


def _rival(body):
    """`_BASE` with the whole gold rebuild body replaced by a straight-line
    `body`. The spec, method signature and `prove_correct` header are untouched,
    so same_spec holds and the obligation survives (its frozen tactic script no
    longer closes the reshaped impl — which is the point; the rejection is
    attributed to the spec by the witness, not to the broken tactic)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# ---- witness helper. Reaches the post-image directly through
# ---- `NonDetT.run (evalSubsFree …)` (a Prop), since `extract_program_for` is
# ---- unavailable (the method is noncomputable over opaque callees). For a
# ---- straight-line rival the `NonDetT.run` term reduces under
# ---- `simp [NonDetT.run, pure]` to the rival's rebuild value; the single
# ---- hypothesis `wrong ≠ evalSubsSpec …` then separates it from the spec.
# ---- Against gold the reduction lands on `mkSet boundSym … = mkSet boundSym …`
# ---- and the hypothesis cannot close the residual `False`, so the witness
# ---- FAILS on gold — the discrimination the gate requires. No tester (the
# ---- method is noncomputable), no banned token. `wrong` is the rival's rebuild
# ---- expression; the same expression is the head hypothesis's LHS. The binders
# ---- are SORTED (`Binder`/`Cond`/`SetObj`/`Obj`), matching the method's
# ---- signature; a mis-sorted witness would not elaborate at all.
def _witness(wrong):
    return (
        "example (boundSym : Binder) (condition : Cond) (baseSet : SetObj)\n"
        "    (old : Old) (new : New)\n"
        f"    (h : {wrong}\n"
        "       ≠ mkSet boundSym (substCond condition old new)"
        " (substSet baseSet old new)) :\n"
        "    NonDetT.run (evalSubsFree boundSym condition baseSet old new)\n"
        "      ≠ DivM.res (evalSubsSpec boundSym condition baseSet old new) := by\n"
        "  unfold evalSubsFree evalSubsSpec\n"
        "  simp [NonDetT.run, pure]\n"
        "  intro heq\n"
        "  exact h (by simpa using heq)\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct reshape cannot verify, the spec is
    # SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps the `ensures out =
    # evalSubsSpec …` obligation and the frozen `prove_correct evalSubsFree by
    # loom_solve; simp_all [evalSubsSpec]` script; the reshape is definitionally
    # the frozen return, so the frozen proof closes the byte-identical
    # obligation (both verified out-of-band with real builds).
    # =====================================================================
    {
        "id": "pos-inline-return",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the two intermediate `let` bindings and build the rebuild
        # directly in the returned expression. The returned value is
        # definitionally the frozen one, so the frozen proof discharges the clause
        # unchanged.
        "module": _rival(
            "    return mkSet boundSym (substCond condition old new)\n"
            "      (substSet baseSet old new)"),
        "rationale": "inlining the substituted-condition / substituted-base "
                     "bindings into the returned rebuild leaves the value "
                     "definitionally identical, so `out = evalSubsSpec boundSym "
                     "condition baseSet old new` still holds and the frozen proof "
                     "closes without change. A correct reshape that failed to "
                     "verify would mean the spec is SPEC-TOO-STRONG on the impl's "
                     "data-flow shape.",
    },
    {
        "id": "pos-reordered-bindings",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the substituted base set BEFORE the substituted condition
        # (the two lets are independent), then rebuild in the same order. Same
        # values threaded; a second, structurally distinct correct impl so the
        # soundness surface is defended by more than one reshape.
        "module": _rival(
            "    let newBase := substSet baseSet old new\n"
            "    let newCond := substCond condition old new\n"
            "    return mkSet boundSym newCond newBase"),
        "rationale": "the two substitution bindings are independent, so computing "
                     "the base-set substitution before the condition substitution "
                     "threads the identical values into the rebuild; `out = "
                     "evalSubsSpec …` still holds and the frozen proof closes. A "
                     "second correct reshape (distinct `let` order) so the reshape "
                     "space is not a single point; if it FAILS => SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the sibling's admiss-rfp-true. The sibling's
    # probe asserts, inside the impl, that the F2P collapsed-to-true input yields
    # the base domain (its `Assert(Implies(cond_after==COND_TRUE, …))`). THIS
    # carrier models no COND/kind tag, so that exact probe has no counterpart. It
    # is re-aimed at the residual admissibility risk that DOES survive here: that
    # the post-image `out = evalSubsSpec …` is jointly SATISFIABLE, and resolves
    # to the slot assignment this battery's rivals are aimed at, at an F2P-shaped
    # point. MUST verify, else SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG.
    #
    # CONTENT-BEARING (repaired by audit). An earlier revision used `_BASE`
    # VERBATIM, which made this case a duplicate of the shipped frozen build: it
    # could only ever fail if the bundle itself did not verify (that is G-VERIFY's
    # job), so it attested NOTHING about admissibility. It now discharges, inside
    # the elided impl region and BEFORE the frozen body runs, two `have`s about
    # the obligation at an F2P-shaped point; the frozen body then runs unchanged,
    # so the real obligation is still closed the frozen way and the spec view is
    # untouched. Each `have` is machine-checked LIVE — the same shape asserting a
    # FALSE claim at the same point fails to elaborate (exit 1) where the true one
    # elaborates (exit 0): demanding the pre-fix binder in the existential fails,
    # as does resolving the condition slot to the raw `condition` or the base slot
    # to the raw `baseSet`. So these `have`s carry information rather than being
    # decorative.
    # =====================================================================
    {
        "id": "admiss-gold-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rival(
            "    -- ADMISSIBILITY (total carrier, abstract inputs). Discharged BEFORE the\n"
            "    -- frozen body runs, at an F2P-shaped point: a genuine symbolic binder\n"
            "    -- with `old` a free symbol distinct from it.\n"
            "    have _obligationSatisfiableAtF2P :\n"
            "        ∃ out : BuiltSet,\n"
            "          out = evalSubsSpec boundSym condition baseSet old new\n"
            "            ∧ out = mkSet boundSym (substCond condition old new)\n"
            "                      (substSet baseSet old new) :=\n"
            "      ⟨mkSet boundSym (substCond condition old new)\n"
            "          (substSet baseSet old new),\n"
            "        by simp [evalSubsSpec], rfl⟩\n"
            "    have _postImageResolvesSlotwise :\n"
            "        evalSubsSpec boundSym condition baseSet old new\n"
            "          = mkSet boundSym (substCond condition old new)\n"
            "              (substSet baseSet old new) := by\n"
            "      simp [evalSubsSpec]\n"
            + _GOLD_IMPL),
        "rationale": "ADMISSIBILITY on a total carrier with five opaque inputs. "
                     "The obligation `out = evalSubsSpec boundSym condition "
                     "baseSet old new` is shown jointly SATISFIABLE at an "
                     "F2P-shaped point (a genuine symbolic binder, `old` a free "
                     "symbol distinct from it) by an explicit existential "
                     "inhabitant, and shown to RESOLVE slot-wise to the binder / "
                     "substituted-condition / substituted-base assignment this "
                     "battery's rivals attack — so the contract is non-degenerate "
                     "there, not merely satisfiable. Both `have`s are discharged "
                     "before the frozen body runs, which then closes the real "
                     "obligation verbatim. Measured live: the same existential "
                     "demanding the pre-fix binder FAILS to elaborate, and so does "
                     "resolving the condition slot to the raw `condition` or the "
                     "base slot to the raw `baseSet`. If this case rejects => "
                     "PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE. NOTE the two "
                     "`require`s are NOT hypotheses in scope inside the impl "
                     "region (measured: `by assumption` fails on each), so this "
                     "case states the admissibility claim at the OBLIGATION level "
                     "rather than by re-deriving the guards.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each STRAIGHT-LINE (so its `NonDetT.run` term
    # reduces) with a machine-checked refutation witness conditioning on the
    # opaque carrier, and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================

    # MEASURED REFINEMENT EVIDENCE, shared by all five rivals below and quoted per
    # case. Each rival was refined to real Python (its rebuild expression put in
    # place of the gold `return self.func(self.sym, cond, base)` in the patched
    # `ConditionSet._eval_subs`) and run in the instance image with the gold patch
    # AND the test patch applied, both as whole test functions and — because a
    # single `assert` failure masks the rest — with the F2P test's top-level
    # assertions executed INDEPENDENTLY. Gold passes everything (F2P + all 8 P2P).
    # Every rival fails the F2P test `test_subs_CondSet` and passes all 8
    # PASS_TO_PASS tests, so each one's non-resolution rests on the failing test's
    # own evidence. The four discriminating assertions of that test, by their
    # position in it, are:
    #
    #   (a) non-collapsing rebuild, FiniteSet base, two-symbol condition
    #       `ConditionSet(x, x < y, {z, y}).subs(y, w)
    #            == ConditionSet(x, x < w, {z, w})`
    #   (b) collapse to the base domain, base `Interval(0, oo)`
    #       `ConditionSet(n, n < x, Interval(0, oo)).subs(x, p) == Interval(0, oo)`
    #   (c) collapse to the base domain, base `Interval(-oo, 0)` — the assertion the
    #       instance's own test patch CHANGED (it demanded `S.EmptySet` before)
    #       `ConditionSet(n, n < x, Interval(-oo, 0)).subs(x, p) == Interval(-oo, 0)`
    #   (d) issue 17341, the newly-added image-set assertion
    #       `ConditionSet(x, Contains(y, Interval(-1, 1)), img1).subs(y, 1/3)
    #            .dummy_eq(img2)`
    #
    # Measured failures: keyed-on-new (a,c,d); keyed-on-old (a,b,c,d);
    # keyed-on-binder-value (a,b,d); cond-not-substituted (a,b,c,d);
    # base-not-substituted (a,d). The RETIRED subst-direction-reversed rival was
    # measured on the same harness before the sorted substitution arguments made
    # it untypeable — it failed (a,b,c,d) and passed all 8 P2P — and its
    # disposition is now UNWRITABLE rather than refuted (accounting block below).

    # ---- (binder) THE HEADLINE BUG: rebuild keyed on the replacement `new` ----
    {
        "id": "weak-keyed-on-new",
        "kind": "uniqueness",
        "expect": "reject",
        # Rebuild the set keyed on the SUBSTITUTED value `new` instead of the
        # set's own original bound symbol — the reported symptom (the bound
        # variable mistaken for the substituted symbol) at the (binder) slot.
        # With the constructor's SECOND invocation shape in the axiom surface
        # (`mkSetOnValue`, mapping.md §3.3) this is now VERBATIM the deleted
        # pre-fix rebuild `ConditionSet(new, Contains(new, base), base)` — an
        # earlier revision could only express the weaker `mkSet new (subst …)
        # (subst …)` near-miss, because the value-keyed shape had no axiom.
        # It is also Solution_prepatch.lean's body.
        "module": _rival(
            "    let newBase := substSet baseSet old new\n"
            "    return mkSetOnValue (newObj new) newBase"),
        "refinement": "keyed on the replacement value rather than the set's own "
                      "binder — the (binder) decision the fix is about — and in "
                      "the value-keyed constructor shape, so this is the deleted "
                      "pre-fix rebuild verbatim, applied uniformly across the "
                      "branch. MEASURED (refined to the real rebuild, run in the "
                      "instance image with the gold patch and the test patch "
                      "applied): the failing test goes RED on THREE of its "
                      "assertions — the non-collapsing rebuild (a), the "
                      "`Interval(-oo, 0)` collapse (c), which is precisely the "
                      "assertion this instance's test patch CHANGED (it demanded "
                      "`S.EmptySet` before, the answer this rebuild still gives, "
                      "because binding the positive replacement over a membership "
                      "test in a non-positive interval makes the condition FALSE), "
                      "and the newly-added image-set assertion (d). It passes the "
                      "`Interval(0, oo)` collapse (b), where the membership test "
                      "happens to hold and the constructor returns the base domain "
                      "anyway. All 8 pass-to-pass tests stay green, so this "
                      "rival is non-resolving on exactly the failing test's own "
                      "evidence.",
        "rationale": "REJECT from the (binder) decision of `out = evalSubsSpec "
                     "boundSym …`: the spec keys the rebuild on `boundSym` and "
                     "carries the substituted condition, this impl keys it on "
                     "`new` in the value-keyed shape, so the two disagree whenever "
                     "`mkSetOnValue new … ≠ mkSet boundSym …`. Verifying would be "
                     "SPEC-TOO-WEAK on the binder clause (it would admit the "
                     "pre-fix rename verbatim). Refuted by conditioning on that "
                     "opaque inequality.",
        "witness": _witness(
            "mkSetOnValue (newObj new) (substSet baseSet old new)"),
    },

    # ---- (binder) a DIFFERENT wrong binder: keyed on the replaced symbol old ----
    {
        "id": "weak-keyed-on-old",
        "kind": "uniqueness",
        "expect": "reject",
        # A near-miss on the SAME clause at a DISTINCT wrong value: rebuild keyed
        # on the replaced free symbol `old` rather than the set's own binder. Not
        # the pre-patch shape, but an equally-wrong binder choice — given its own
        # witness at the distinguishing point, so its rationale claims a
        # sub-domain the manifest actually demonstrates.
        "module": _rival(
            "    let newBase := substSet baseSet old new\n"
            "    return mkSetOnValue (oldObj old) newBase"),
        "refinement": "a faithful counterpart that rebuilt the set keyed on the "
                      "replaced free symbol binds the set over a symbol that is "
                      "not even the replacement — one the caller has just asked to "
                      "be eliminated. MEASURED (same harness): RED on ALL FOUR "
                      "discriminating assertions — the non-collapsing rebuild (a), "
                      "both collapse assertions (b) and (c), and the newly-added "
                      "image-set assertion (d) — because the replaced symbol is "
                      "generally NOT a member of the substituted base, so the "
                      "membership test it is bound over is false and the empty set "
                      "comes back where the base domain is required. Strictly "
                      "broader than weak-keyed-on-new, at a distinct wrong binder. "
                      "All 8 pass-to-pass tests stay green. Non-resolving.",
        "rationale": "REJECT from the (binder) decision: the spec keys on "
                     "`boundSym`, this impl keys on `old`, disagreeing whenever "
                     "`mkSetOnValue old … ≠ mkSet boundSym …`. A second attacker "
                     "on the binder clause at a DISTINCT wrong value from "
                     "weak-keyed-on-new, so the clause is not demonstrated at a "
                     "single rename. Refuted by conditioning on that opaque "
                     "inequality.",
        "witness": _witness(
            "mkSetOnValue (oldObj old) (substSet baseSet old new)"),
    },

    # ---- (shape) RIGHT binder object, WRONG invocation shape ----
    # ADDED with the sorted/partiality model. The axiom surface now exposes the
    # constructor's TWO real invocation shapes (mapping.md §3.3), so a rival can
    # keep the correct binder OBJECT and still be wrong by reaching for the other
    # shape: bind the set's own binder over a membership test of itself, dropping
    # the set's condition. Neither binder rival above reaches this — both are
    # wrong on WHICH object keys the set, this one is wrong on WHICH INVOCATION of
    # the constructor is made with the right object.
    {
        "id": "weak-keyed-on-binder-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rival(
            "    let newBase := substSet baseSet old new\n"
            "    return mkSetOnValue (binderObj boundSym) newBase"),
        "refinement": "a faithful counterpart keeps the set's OWN binder but "
                      "rebuilds it in the value-keyed shape — bound over a "
                      "membership test of that binder in the substituted base — so "
                      "the set's actual filtering condition is silently dropped. "
                      "MEASURED (same harness): RED on the non-collapsing rebuild "
                      "(a), the `Interval(0, oo)` collapse (b) and the newly-added "
                      "image-set assertion (d); it passes (c), where the binder's "
                      "own negativity assumption happens to make the membership "
                      "test true. All 8 pass-to-pass tests stay green. "
                      "Non-resolving, and orthogonal to the two binder rivals: the "
                      "binder object is CORRECT here.",
        "rationale": "REJECT from the invocation SHAPE rather than the binder "
                     "object: the spec's post-image is `mkSet boundSym (substCond "
                     "…) (substSet …)`, this impl's is `mkSetOnValue (binderObj "
                     "boundSym) (substSet …)`, disagreeing whenever the two shapes "
                     "differ. Verifying would be SPEC-TOO-WEAK on WHICH invocation "
                     "of the constructor the rebuild is, even with the right "
                     "binder in hand — the decision the two-shape axiom surface "
                     "makes expressible. Refuted by conditioning on that opaque "
                     "inequality.",
        "witness": _witness(
            "mkSetOnValue (binderObj boundSym) (substSet baseSet old new)"),
    },

    # ---- (cond) substitution NOT pushed through the condition ----
    {
        "id": "weak-cond-not-substituted",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct binder and correct base substitution, but forward the RAW
        # condition instead of `substCond condition old new`. Attacks the (cond)
        # argument position: the substitution is not pushed through the condition.
        "module": _rival(
            "    let newBase := substSet baseSet old new\n"
            "    return mkSet boundSym condition newBase"),
        "refinement": "a faithful counterpart that rebuilt the set with the "
                      "un-substituted condition leaves the replaced free symbol "
                      "dangling in the filtering predicate — the substitution "
                      "never reaching the condition. MEASURED (same harness): RED "
                      "on ALL FOUR discriminating assertions, including BOTH "
                      "collapse ones — with the condition un-substituted the "
                      "predicate never becomes identically true, so the "
                      "constructor never collapses to the base domain and a "
                      "restricted set is returned where the base domain is "
                      "required — plus the non-collapsing rebuild and the "
                      "image-set assertion. All 8 pass-to-pass tests stay green. "
                      "Definitively non-resolving.",
        "rationale": "REJECT from the (cond) decision of `out = evalSubsSpec "
                     "boundSym …`: the spec's condition slot is `substCond "
                     "condition old new`, this impl's is the raw `condition`, "
                     "disagreeing whenever the substitution changes the condition. "
                     "This is the only rival that attacks the condition slot, "
                     "holding binder and base fixed at gold. Refuted by "
                     "conditioning on that opaque inequality.",
        "witness": _witness(
            "mkSet boundSym condition (substSet baseSet old new)"),
    },

    # ---- (base) substitution NOT pushed through the base set ----
    {
        "id": "weak-base-not-substituted",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct binder and correct condition substitution, but forward the RAW
        # base set instead of `substSet baseSet old new`. Attacks the (base)
        # argument position. This is the velvet re-siting of the nagini
        # `weak-build-true-wrong-base` rival (the base slot carries the wrong set).
        "module": _rival(
            "    let newCond := substCond condition old new\n"
            "    return mkSet boundSym newCond baseSet"),
        "refinement": "a faithful counterpart that rebuilt the set over the "
                      "un-substituted base set filters the ORIGINAL domain "
                      "instead of the substituted one — the substitution never "
                      "reaching the base set. MEASURED (same harness): RED, and "
                      "this is the NARROWEST of the five — exactly two assertions, "
                      "the non-collapsing rebuild (a) and the newly-added "
                      "image-set assertion (d), the latter being the one whose "
                      "discriminator really is the base slot: the image set's free "
                      "symbol must be replaced for the collapsed result to "
                      "reproduce the intended set, so forwarding the raw base "
                      "returns a domain still carrying the un-replaced symbol. It "
                      "survives both interval collapses (b) and (c), where the "
                      "substitution does not touch the base at all. All 8 "
                      "pass-to-pass tests stay green. Definitively non-resolving.",
        "rationale": "REJECT from the (base) decision of `out = evalSubsSpec "
                     "boundSym …`: the spec's base slot is `substSet baseSet old "
                     "new`, this impl's is the raw `baseSet`, disagreeing whenever "
                     "the substitution changes the base set. This is the only "
                     "rival that attacks the base slot, holding binder and "
                     "condition fixed at gold. Refuted by conditioning on that "
                     "opaque inequality.",
        "witness": _witness(
            "mkSet boundSym (substCond condition old new) baseSet"),
    },

    # ---- (arg order) RETIRED BY THE PARTIALITY MODEL: the substitution's two
    # ---- arguments are now SORTED (`Old`, `New`), so supplying them in the
    # ---- reverse order is a TYPE ERROR rather than a verification failure and
    # ---- the case can no longer carry a witness. Recorded with its measured
    # ---- error text in the accounting block below (RETIRED BY THE PARTIALITY
    # ---- MODEL), not silently dropped.
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. INVENTORY CORRECTED BY A THIRD AUDIT. The previous
# draft of this block asserted "the sibling battery has 8 SPEC cases (2 soundness
# positives + 1 admissibility + 5 uniqueness rivals) plus 1 AXIOM_TESTS probe" and
# enumerated only those 8. That was true of the sibling as it stood when this port
# was first written (git 2cb887e7f: 8 SPEC + 1 axiom probe) and is FALSE of the
# sibling as it stands now: importing it reports 18 SPEC cases + 1 AXIOM_TESTS
# probe. So this block was silently claiming completeness over a 10-case shortfall
# it had never looked at — the omission lane's whole purpose. Re-derived below
# against the CURRENT sibling; each of the 10 additional cases now has its own
# per-case disposition rather than being outside the enumeration.
#
# The sibling's 18 SPEC cases: pos-build-reorder, pos-rfp-inline (2 soundness);
# admiss-rfp-true (1 admissibility); and 15 uniqueness —
# weak-rfp-never-delivers-selfcall, weak-rfp-never-delivers-loop,
# weak-rfp-measure-not-kept, weak-rfp-partial-then-never-delivers,
# weak-build-never-delivers (5 DIVERGENCE); weak-rfp-true-keyed-on-new,
# weak-rfp-open-keyed-on-new, weak-rfp-true-to-empty, weak-build-open-wrong-sym,
# weak-build-true-wrong-base (5, the originally-enumerated value rivals);
# weak-build-drop-empty-base, weak-build-listed-ignore-members,
# weak-build-merged-keeps-outer-sym, weak-build-merged-keeps-outer-base,
# weak-build-listed-wrong-sym (5 further `build`-internal rivals).
#
# The two carriers are NOT the same partition. The sibling models the change as
# TWO functions over an int-tagged carrier: a constructor deep-model `build`
# (returning `Result0(kind, sym, base, cond)` with kind in {EMPTY,BASE,SET} keyed
# on a COND tag in {FALSE,TRUE,OPEN}) and the patched branch
# `replace_free_parameter`. THIS bundle models the SAME change at the level the
# change lives — the uniform rebuild of the set from its own binder together with
# the substituted condition and substituted base — over an OPAQUE `Obj` carrier
# with no kind/COND tag.
# The per-branch reduction (false->empty, true->base, open->set) is a property of
# the UNCHANGED constructor `mkSet` (an A-reference validated by G-AX), NOT of the
# changed method, so the sibling rivals that attack `build`'s kind/base tags do
# not re-site; the rivals that attack the REBUILD's binder/argument choice re-site
# onto `mkSet`'s three argument positions (binder / condition / base).
#
#   sibling case                  -> here                          status
#   ---------------------------------------------------------------------------
#   pos-build-reorder             -> pos-reordered-bindings         RE-EXPRESSED
#   pos-rfp-inline                -> pos-inline-return              RE-EXPRESSED
#   admiss-rfp-true               -> admiss-gold-satisfiable        RE-AIMED
#   weak-rfp-true-keyed-on-new    -> weak-keyed-on-new              PORTED (headline)
#   weak-rfp-open-keyed-on-new    -> weak-keyed-on-new (MERGED)     MERGED
#   weak-rfp-true-to-empty        -> (none)                         DROPPED (no kind tag)
#   weak-build-open-wrong-sym     -> weak-keyed-on-old              RE-SITED
#   weak-build-true-wrong-base    -> weak-base-not-substituted      RE-SITED
#   weak-rfp-never-delivers-selfcall -> (none)               DIVERGENCE (unwitnessable)
#   weak-rfp-never-delivers-loop  -> (none)                  DIVERGENCE (unwitnessable)
#   weak-rfp-measure-not-kept     -> (none)                  DIVERGENCE (unwitnessable)
#   weak-rfp-partial-then-never-delivers -> (none)           DIVERGENCE (unwitnessable)
#   weak-build-never-delivers     -> (none)                  DIVERGENCE (unwitnessable)
#   weak-build-drop-empty-base    -> (none)                         DROPPED (no kind tag)
#   weak-build-listed-ignore-members -> (none)                      DROPPED (no kind tag)
#   weak-build-merged-keeps-outer-sym -> (none)                      DROPPED (no kind tag)
#   weak-build-merged-keeps-outer-base -> (none)                     DROPPED (no kind tag)
#   weak-build-listed-wrong-sym   -> (none)                         DROPPED (no kind tag)
#   (n/a)                         -> weak-cond-not-substituted      ADDED
#   (n/a)                         -> weak-keyed-on-binder-value      ADDED (audit)
#   (n/a)                         -> weak-slots-exchanged            RETIRED (sorts)
#   (n/a)                         -> weak-subst-direction-reversed   RETIRED (sorts)
#   ax-ref-build-evalsubs-...     -> (none)                         G-AX's job
#
# THE FIVE DIVERGENCE CASES (added to this table by the third audit; they were
# outside the previous enumeration entirely). All five attack the sibling's
# `Requires(MustTerminate(n))` totality obligation, which this bundle DOES carry
# (`termination "total"`). Each was re-expressed on this signature and BUILT, and
# every one is genuinely REJECTED — so the class is defended, not vacuous:
#   * the two NON-DELIVERY-by-self-call shapes (`return ← evalSubsFree …` and its
#     let-bound form) fail with `fail to show termination for evalSubsFree …
#     failed to infer structural recursion`;
#   * the no-measure loop fails with `Decreasing annotations are required in total
#     correctness semantics`;
#   * the measure-CLAIMED-but-not-kept shape (the sibling's
#     weak-rfp-measure-not-kept, exactly) fails BEHAVIOURALLY with `unsolved goals
#     case «decreasing_1: i»`, which is the direct analogue of the sibling's own
#     rationale ("the measure is VERIFIED rather than assumed");
#   * weak-rfp-partial-then-never-delivers and weak-build-never-delivers have no
#     separate mechanism here — the first is a guarded self-call (this signature has
#     no branch structure to make the guard meaningful, and its non-delivering tail
#     is the self-call shape above), and the second attacks divergence inside
#     `build`, which on this carrier is the OPAQUE constructor `mkSet`, a callee
#     with no impl region for a rival to diverge in.
# None is SHIPPABLE, for the witness reason set out at length in the CARRIER NOTE's
# divergence paragraph above: the rejection is real but no witness can reach a
# loop-bearing rival's post-image on this carrier (measured, 3 witness shapes, all
# exit 1 on the RIVAL half). Recorded as a carrier limit per case, NOT as vacuity.
#
# THE FIVE FURTHER `build`-INTERNAL RIVALS (also added by the third audit) are
# DROPPED for the same demonstrated reason as weak-rfp-true-to-empty, and it is the
# reason already argued at length below rather than a new one: every one of them
# attacks a branch of the sibling's `build` deep-model keyed on its
# {EMPTY,BASE,SET,REFUSED} kind tag and its {PLAIN,EMPTY,LISTED,MERGED} base tag —
# the empty-base collapse (weak-build-drop-empty-base), the member-by-member
# decision over an explicit listing (weak-build-listed-ignore-members and
# weak-build-listed-wrong-sym), and the unpacking of a nested set in the base slot
# (weak-build-merged-keeps-outer-sym / -outer-base). NONE of those reductions is a
# property of the CHANGED method here. This bundle's changed surface chooses only
# WHICH binder, condition and base reach the constructor; the constructor itself is
# the opaque A-reference `mkSet`, whose behaviour has no tag to violate and is
# validated against the real callee by axiom_check.py under G-AX. There is no
# `Result0`, no `kind`, no `listed_base` and no `merged_sym` on this carrier to
# write a rival over — they are not merely hard to reach, they are unnameable.
# Carrier narrowing, demonstrated per case, not convenience.
#
# TALLY, restated over the CURRENT sibling's 18 SPEC cases (the previous tally
# balanced against the stale 8-case inventory and so appeared complete while 10
# cases sat outside it): 1 ported (headline) + 1 merged + 2 re-sited + 2 added
# uniqueness rivals (one of them added by an independent audit, below); 2 positives
# (both re-expressed); 1 admissibility (re-aimed); 6 dropped uniqueness (carrier
# narrowing — weak-rfp-true-to-empty plus the 5 further `build`-internal rivals
# above, each with its own demonstrated reason); 5 DIVERGENCE cases correctly
# rejected here but unwitnessable, recorded as a carrier limit; 2 retired
# uniqueness rivals (both made UNWRITABLE by the partiality model, below); 1 axiom
# probe dropped (G-AX's lane). 2 + 1 + 5 + 6 + 2 + 2 = 18 sibling SPEC cases
# accounted for, 8 SPEC cases here. No case was dropped because its
# proof was hard, and neither retirement weakens the battery: an impl the sorts
# make untypeable is excluded from the whole space the spec quantifies over, which
# is a stronger disposition than a refutation, and the REAL refusals that justify
# each sort are measured in the instance image by axiom_check.py (obligations
# 6-15) rather than asserted here.
#
# MERGED (weak-rfp-open-keyed-on-new -> weak-keyed-on-new): on the sibling's
#   tagged carrier "TRUE-branch keyed on new" and "OPEN-branch keyed on new" are
#   two separate sub-domains of the COND tag. THIS carrier has no COND tag — the
#   rebuild is UNIFORM (the intended behaviour keys the rebuild on the set's own
#   binder across the whole branch, collapse or not; mapping.md §1) — so
#   "keyed on new" is a
#   SINGLE wrong-binder rival regardless of whether the substituted condition
#   would have simplified. Both sibling rivals collapse onto weak-keyed-on-new;
#   there is no second sub-domain to attack separately.
#
# RE-SITED (the ARGUMENT is unchanged; only the carrier position is):
#  * weak-build-open-wrong-sym attacked build's OPEN case minting the set on a
#    fixed wrong constant (0) rather than the passed bound symbol. Here the
#    bound-symbol propagation lives in the rebuild's (binder) position, so the
#    analogue is a wrong binder — re-sited as weak-keyed-on-old, which keys the
#    rebuild on the REPLACED symbol `old` (a wrong key distinct from the
#    headline's `new`). Note the SORTED consequence: `old : Obj` is not a
#    `Binder`, so this rival cannot write `mkSet old …` at all; the only way to
#    key a real set on a value is the value-keyed invocation shape, hence it
#    returns `mkSetOnValue old (substSet baseSet old new)`. The wrongness is the
#    same one the sibling attacked and the type discipline is what routes it.
#  * weak-build-true-wrong-base attacked build's TRUE case returning a DIFFERENT
#    base. Here the base is the rebuild's (base) argument
#    `substSet baseSet old new`, so the analogue is forwarding the wrong base —
#    re-sited as weak-base-not-substituted (the base slot carries the
#    un-substituted `baseSet`, which is well-sorted and therefore writable).
#
# ADDED (weak-cond-not-substituted): the sibling threads `cond_after` in as an
#   already-computed INPUT to replace_free_parameter, so it has no rival that
#   attacks the condition-substitution step (that step is upstream of its model).
#   THIS carrier makes `substCond condition old new` an explicit argument position
#   of the rebuild, so the (cond) slot is a distinct load-bearing decision and
#   needs its own attacker — otherwise a rival that forwarded the raw condition
#   would verify and the battery would say nothing about that slot. Note the raw
#   `condition : Cond` IS well-sorted for that slot (the real constructor accepts
#   an un-substituted condition — it is a legal `ConditionSet`, merely the wrong
#   one), so the sorts do not pre-empt this rival; the `ensures` clause is what
#   rejects it.
#
# ADDED BY AUDIT (weak-keyed-on-binder-value): the position-wise rivals all vary
#   WHICH handle lands in a slot while keeping the constructor's INVOCATION SHAPE
#   at gold's. That leaves the shape itself unattacked, even though the shape is
#   exactly what the deleted pre-fix code got wrong. This rival keeps the binder
#   OBJECT correct (`binderObj boundSym` — the same symbol gold binds) and gets
#   the SHAPE wrong: `mkSetOnValue (binderObj boundSym) (substSet baseSet old
#   new)`, a set keyed on the binder's VALUE with the condition dropped for a
#   membership test. It is a distinct decision from weak-keyed-on-new/-old (whose
#   key is a wrong object) and it exists only because the axiom surface now names
#   both real invocation shapes. Measured refined (below): it breaks three of the
#   four discriminating assertions where gold breaks none.
#
# RETIRED BY THE PARTIALITY MODEL (weak-subst-direction-reversed): this case
#   covered the ARGUMENT ORDER of the substitution calls themselves — both
#   components computed as `substCond condition new old` / `substSet baseSet new
#   old`, routed to the correct slots and keyed on the correct binder. An earlier
#   revision needed it as a rival because the substitution's two arguments were
#   both `Obj` and therefore freely transposable. They are no longer the same sort:
#   the replaced symbol and its replacement are now `Old` and `New`, because the
#   real callee `Basic.subs(old, new)` is not symmetric in them (it is defined at
#   `(y > 0).subs(y, I)` and RAISES `TypeError: Invalid comparison of complex I` at
#   `(y > 0).subs(I, y)`, measured by axiom_check.py obligations 11-15). So the
#   reversed call is now a TYPE ERROR rather than a verification failure, measured
#   verbatim at both the discarded and the returned position:
#     error: Application type mismatch: The argument
#       new
#     has type
#       New
#     but is expected to have type
#       Old
#     in the application
#       substCond condition new
#   It is retired rather than kept for the same mechanical reason as
#   weak-slots-exchanged below: the gate builds each witness in a file that RETAINS
#   the rival's impl region, so a type-incorrect rival cannot carry a witness and
#   the case would report `witness-unproven` (MALFORMED-TESTS) instead of a
#   refutation. Its refinement evidence was measured before retirement (RED on all
#   four discriminating assertions, all 8 P2P green) and is recorded above.
#
# RETIRED BY THE PARTIALITY MODEL (weak-slots-exchanged): this case previously covered ARGUMENT
#   ROUTING — both substitutions computed correctly, the correct binder, and the
#   two components then exchanged between the (cond) and (base) slots. Under the
#   SORTED callee model that impl is a TYPE ERROR, not a verification failure: a
#   `SetObj` cannot be written into the (cond) slot nor a `Cond` into the (base)
#   slot. It was retired rather than kept because a type-incorrect rival cannot
#   carry a witness — the gate builds the witness in a file that retains the
#   rival's impl region, so the file would fail to elaborate and the case would
#   report `witness-unproven` (MALFORMED-TESTS) instead of a refutation. The
#   coverage is not lost, it is STRONGER: routing is now excluded by
#   construction, and the same real refusals that justify the sorts are measured
#   by axiom_check.py obligations 9–10 (a set in the condition slot -> TypeError,
#   a condition in the base slot -> TypeError, on the problem statement's own F2P
#   input). Nothing replaces it as a rival: after the substitution arguments were
#   sorted too, there is no same-sorted transposition left anywhere on the
#   operation's surface for a rival to attack.
#
# DROPPED (weak-rfp-true-to-empty): attacks the {EMPTY,BASE,SET} kind tag — a
#   collapsed-to-true predicate yielding the EMPTY set instead of the BASE domain.
#   This carrier has no kind tag: the reduction of a rebuilt set to empty/base/set
#   is a property of the UNCHANGED constructor `mkSet` (an A-reference validated by
#   G-AX, mapping.md §3), not of the changed method, which only chooses WHICH
#   binder/condition/base to hand `mkSet`. There is no empty/base distinction on
#   the changed method's surface to violate. Carrier narrowing, not an omission of
#   convenience — the behaviour lives on the callee G-AX checks, not on the spec.
#
# RE-AIMED (admiss-rfp-true): the sibling asserts, inside the impl, that the F2P
#   collapsed-to-true input yields the base domain keyed on the original symbol
#   (its `Assert(Implies(cond_after==COND_TRUE, …))`). This carrier models no
#   COND/kind tag and offers no in-impl `Assert` facility, so that exact probe has
#   no counterpart. It is re-aimed at the residual admissibility risk that DOES
#   survive here: that `out = evalSubsSpec …` is jointly satisfiable and resolves
#   slot-wise to the assignment the rivals attack, at an F2P-shaped point
#   (admiss-gold-satisfiable). Note the single `require` is opaque
#   (`old ≠ binderObj boundSym`) and the branch's other guard is carried by the
#   `Binder` SORT rather than by a predicate: the reject witnesses rely on
#   neither, so the reject lane's discrimination does not depend on the guard
#   being satisfiable — the spec is substantive regardless. (The sorts cannot make
#   the obligation vacuous the way an unsatisfiable `require` could: `Binder`,
#   `Cond` and `SetObj` are opaque parameters of the method, not hypotheses, so
#   the method is quantified over whatever inhabits them and this case exhibits an
#   inhabitant of the post-image at abstract arguments.)
#   REPAIRED BY A SECOND AUDIT: this case previously used `_BASE` VERBATIM, which
#   made it a duplicate of the shipped frozen build — it could only fail if the
#   bundle itself did not verify (G-VERIFY's lane), so it attested nothing about
#   admissibility. It now carries two content-bearing `have`s discharged inside
#   the elided impl region before the frozen body runs, each shown LIVE by
#   building the corresponding FALSE claim at the same point and observing exit 1
#   (pre-fix binder in the existential; condition slot resolved to the raw
#   `condition`; base slot resolved to the raw `baseSet`). Also measured, and
#   recorded because it bounds what this lane can claim: the `require` is NOT a
#   hypothesis in scope inside the impl region (`by assumption` fails, goal
#   `⊢ old ≠ binderObj boundSym`), so the case states its claim at the OBLIGATION
#   level rather than by re-deriving the guard.
#
# AXIOM_TESTS: dropped. The changed operation (the uniform rebuild) is modeled
#   DEEPLY (`evalSubsSpec`), and the opaque `substCond` / `substSet` / `mkSet` /
#   `mkSetOnValue` are A-references validated by axiom_check.py under G-AX
#   (mapping.md §3, obligations 1–10), not consumed contracts. There is no
#   consumed-axiom lane to mirror, and this gate ignores AXIOM_TESTS regardless.
#   In particular the callees' DOMAIN claim — the thing the sorts encode — is not
#   an axiom this battery could probe from inside Lean: it is a claim about the
#   real Python callee, so it is measured in the instance image by G-AX
#   (obligations 6–10) and not restated here.
#
# WITNESS DISCRIMINATION. Re-derived from scratch on the PARTIALITY model (every
# number below is a fresh build against the current Solution.lean, not carried
# over from the revision that modeled both callees as total functions of unsorted
# arguments). For each of the FIVE reject cases: the witness built against its
# rival at exit 0, against the frozen impl at exit 1, and the consistency probe at
# exit 1 — 5 x (0 / 1 / 1), no exception; the gate's own three-build protocol,
# run on a byte-identical copy of this bundle, reports all five as
# `rejected (witness refutes the rival)` and the battery as
# `SOUND: 8 spec case(s) behaved as expected`.
# Each witness ELABORATES against its straight-line rival (its `NonDetT.run` term
# reduces to the rival's rebuild value — `mkSet …` or `mkSetOnValue …` according to
# the invocation shape the rival chose — which the single hypothesis separates from
# `evalSubsSpec …`) and FAILS against the frozen solution, whose reduction lands on
# `mkSet boundSym … = mkSet boundSym …` and leaves a residual `False` the
# hypothesis cannot close, e.g. for weak-keyed-on-new the recorded context is
#   h :
#     mkSetOnValue (newObj new) (substSet baseSet old new) ≠
#       mkSet boundSym (substCond condition old new) (substSet baseSet old new)
#   ⊢ False
# Each carries exactly ONE hypothesis about a single opaque composition; the
# gate's consistency probe cannot derive `False` from any of the five (checked),
# and that probe was shown LIVE on this very cell — a witness over the same
# binders carrying a deliberately contradictory pair
# (`substCond condition old new = condition` together with its negation) has a
# probe that SUCCEEDS at exit 0 — so the five exit-1 results are a measured
# non-forgery rather than an absence of evidence. No
# `sorry`/`admit`/`native_decide`/`axiom` appears. Each witness was also built
# against RESHAPED-but-CORRECT impls (a bound result; a partially-inlined rebuild)
# and failed on both — 10 builds, all exit 1 — so the witnesses track wrongness,
# not the frozen impl's syntactic shape.
#
# FORGERY TEST (attack B′), also re-derived on the partiality model, because every
# reject case's recorded `gold_signature` is a tactic failure (`introN`) rather
# than a plain evaluation — a shape that reads exactly like a hollow tactic
# mismatch. It is not hollow here, and the evidence is the PAIR, not a reading of
# the error: for each of the five witnesses a FORGERY was built differing ONLY in
# what it claims (the `≠` of the conclusion flipped to `=`, i.e. asserting that
# gold is CORRECT at that point, with the identical tactic script). Against the
# frozen impl the real witness fails with
#   `Tactic `introN` failed: There are no additional binders or `let` bindings in
#   the goal to introduce` + the residual context above,
# while the flipped claim fails with a DIFFERENT error, `No goals to be solved`
# — i.e. `simp` had already PROVED the agreement equation for gold (5/5). The
# gold-side exit code therefore tracks the claim, so it carries information about
# the spec rather than about the tactic. Corroborated by the AGREEMENT control
# `NonDetT.run (evalSubsFree …) = DivM.res (evalSubsSpec …)`: exit 0 against the
# frozen impl, exit 1 against every one of the five rivals, each with an explicit
# residual goal naming that rival's differing slot, e.g.
#   ⊢ mkSetOnValue (newObj new) (substSet baseSet old new) =
#       mkSet boundSym (substCond condition old new) (substSet baseSet old new)
# for weak-keyed-on-new and
#   ⊢ mkSet boundSym (substCond condition old new) baseSet =
#       mkSet boundSym (substCond condition old new) (substSet baseSet old new)
# for weak-base-not-substituted — 16 builds in that batch, every one as designed.
#
# INDEPENDENTLY REPRODUCED by the third audit, which rebuilt every one of these
# from the manifest rather than trusting the paragraph above (40 builds in the
# first batch). Per reject case, in the gate's own three-build protocol:
# rival 0 / gold 1 / consistency-probe 1, five for five. The forgery pair
# reproduces exactly as described: witness-on-gold fails with ``Tactic `introN`
# failed: There are no additional binders or `let` bindings in the goal to
# introduce`` over a context that exhibits the case's own hypothesis and ``⊢
# False``, while the SAME file with only the conclusion's ``≠`` flipped to ``=``
# fails with ``No goals to be solved`` — a DIFFERENT error, so the gold-side exit
# code tracks the claim and the ``introN`` signature is a real refutation rather
# than the hollow tactic mismatch its shape resembles. The flipped claim built
# against each RIVAL fails with the ``introN`` error instead, i.e. the pair is
# symmetric in the right direction. The agreement control reproduces too: exit 0
# on the frozen impl, exit 1 on all five rivals, each residual goal naming that
# rival's differing slot verbatim. The four ``require``s were also probed jointly
# for satisfiability (``example <all four as hypotheses> : False``): exit 1, so the
# guarded domain is non-empty and no reject case rests on an unsatisfiable guard.
#
# SPEC-STRENGTH PROBES (attacks D and E), 26 builds beyond the battery's own 8
# cases, all re-run on the partiality model.
#
# D (SPEC-TOO-WEAK): FIFTEEN wrong impls not present above, ALL rejected (exit 1),
# in three distinguishable ways.
#  * ELEVEN are rejected as TYPE ERRORS, before verification, by the partiality
#    model itself: a substitution receiver MANUFACTURED by the impl
#    (`substSet (mkSet …) …`); the same nested one level deeper; the audit's
#    verifying attack `let _probe := mkSet new condition baseSet` (the constructor's
#    binder slot handed a substituted VALUE); the stored base substituted AT the
#    binder (`substSet baseSet (binderObj boundSym) new`); the condition likewise;
#    the reversed substitution direction, both discarded and returned; `old`
#    supplied where the replacement belongs (`substCond condition old old`); a
#    built set forced into the constructor's base slot; and the two impls that
#    echo a component instead of building a set (the raw `baseSet`, and
#    `substSet baseSet old new`), which cannot be the result because the produced
#    set and the component sets are different sorts. Sample, verbatim:
#      error: Application type mismatch: The argument
#        new
#      has type
#        New
#      but is expected to have type
#        Binder
#      in the application
#        mkSet new
#  * THREE are well-sorted and rejected BEHAVIOURALLY by the `ensures`, with a
#    residual `unsolved goals`: both components raw; the value-keyed shape with a
#    raw base; a doubly-substituted condition in the (cond) slot.
#  * ONE is rejected for DIVERGENCE — `while true do pure ()` before the correct
#    return — with `Decreasing annotations are required in total correctness
#    semantics`, so the total-semantics obligation is live on this cell.
# The five battery rivals are behavioural rejections too, making 20 rejections in
# all. No wrong impl verifies, so no hole on this obligation.
#
# E (SPEC-TOO-STRONG): ELEVEN correct impls, all of which VERIFY (exit 0).
#  * SIX carry an extra DISCARDED call that the real callee genuinely accepts, so
#    the model must not reject them: a doubly-substituted condition, a doubly
#    substituted base, a rebuild from the raw components, and the value-keyed shape
#    on `old`, on `new`, and on the binder's own value. This is the other half of
#    the partiality claim — the sorts exclude the invocations that RAISE, and these
#    six show they do not also exclude the invocations that return, i.e. the model
#    is not "no extra calls allowed".
#  * THREE are reshapes of gold: a bound result, an unused extra binding, and a
#    partially-inlined rebuild. (The battery's own two positives — inline return
#    and reordered bindings — verify as well.)
# One further correct impl, `return evalSubsSpec boundSym condition baseSet old new`
# (echoing the pure spec function), fails with `No goals to be solved`, which is the
# frozen tactic script OVER-closing, not the spec rejecting the shape: the same impl
# with the now-redundant `simp_all` dropped from the elided proof body verifies at
# exit 0 (re-measured on this model). Recorded as a tactic artefact, NOT a spec
# defect.
#
# D AND E RE-RUN INDEPENDENTLY by the third audit (24 further builds), aimed at the
# corners the existing rivals leave alone rather than repeating the list above.
#  * D, all REJECTED with a residual `unsolved goals` on
#    `«ensures_1: out = evalSubsSpec …»`: a doubly-substituted base in the (base)
#    slot; the value-keyed shape over a RAW base; both components raw; a
#    doubly-substituted condition; the value-keyed shape on the replaced object
#    with the gold base; the value-keyed shape on the replacement over a
#    doubly-substituted base; and — the one aimed hardest at a possible hole — a
#    rival that FIRST performs the exact gold rebuild as a DISCARDED binding and
#    THEN returns the raw-condition rebuild, to check the `ensures` constrains the
#    RETURNED value and cannot be satisfied by having merely computed the right one
#    somewhere. It is rejected. No wrong impl verified.
#  * E, all VERIFYING (exit 0): a rebuild through three intermediate `let`
#    aliases of the inputs; an unused extra substitution binding; a discarded
#    value-keyed probe before the gold return; a bound result; and a degenerate
#    `if True then … else …` over the same value. So the spec is not strong on the
#    impl's data-flow SHAPE.
#  * E, the ONE apparent rejection, confirmed a TACTIC artefact and NOT a spec
#    hole, independently of the paragraph above: `have hspec : evalSubsSpec … =
#    mkSet …  := by simp [evalSubsSpec]` followed by returning `evalSubsSpec …`
#    fails with `No goals to be solved` — the same over-closing signature as the
#    bare echo, from the frozen script's `simp_all` having nothing left to do, not
#    from the obligation being unmet. Dropping the redundant `simp_all` from the
#    elided proof body makes the echo verify at exit 0 (rebuilt and confirmed).
#
# BINDER / CLAUSE COVERAGE. The single clause `out = evalSubsSpec boundSym
# condition baseSet old new` = `mkSet boundSym (substCond condition old new)
# (substSet baseSet old new)` is attacked at all THREE argument positions:
# (binder) by weak-keyed-on-new and weak-keyed-on-old, (cond) by
# weak-cond-not-substituted, (base) by weak-base-not-substituted. Each of those
# holds the other two positions fixed at gold, so no rejection is confounded. The
# constructor's INVOCATION SHAPE — orthogonal to which handle sits in a slot — is
# attacked by weak-keyed-on-binder-value. TWO decisions that earlier revisions had
# to attack with a rival are now UNWRITABLE rather than merely unproven, which is
# the stronger disposition: component ROUTING between the (cond) and (base) slots
# (weak-slots-exchanged) and the substitution calls' own ARGUMENT ORDER
# (weak-subst-direction-reversed) are both type errors under the partiality model,
# and the real refusals that license each are measured in the instance image by
# axiom_check.py (obligations 9–10 and 11–15) instead of being asserted here.
# All FIVE method binders are opaque (`boundSym : Binder`, `condition : Cond`,
# `baseSet : SetObj`, `old : Old`, `new : New`) with no transparent literal to move
# across, so every witness quantifies over abstract binders and conditions on the
# carrier; the positional coverage parser reads that as unreadable and binder
# coverage falls to the by-name signal (each binder is named in the
# rivals/witnesses that abuse its position). This is the documented opaque-carrier
# situation, not a single-point battery.
AXIOM_TESTS = []
