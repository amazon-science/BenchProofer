"""properties.py — G-PBT falsification battery for sympy__sympy-20428 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct symbolicNonzero`` obligation survives with a
byte-identical header) and swaps in a candidate implementation. It is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (ONE contracted method over a two-observation carrier):

  symbolicNonzero (e : SymExpr) return (out : Bool)
    require e.literalZero → e.identicallyZero              -- P1 (the domain)
    ensures out = nonzeroSpec e                            -- C1 (load-bearing)

  where ``nonzeroSpec e = !e.identicallyZero`` is a transparent ``def`` over the
  method's own argument. The ``axioms`` region is EMPTY: there is no opaque
  callee and no answer key to echo, so C1 is grounded in the input (directive 8)
  and the whole carrier computes under ``decide``.

  The carrier has TWO boolean observations, and the entire adversarial surface
  lives in the gap between them:

    identicallyZero — the element denotes the value zero, however written;
    literalZero     — the element's representation IS the bare literal zero.

  P1 pins ``literalZero → identicallyZero`` (a literal-zero representation
  always denotes zero) and deliberately does NOT pin the converse. So the
  reachable domain is EXACTLY THREE states, and the battery probes all three:

    (identicallyZero=true,  literalZero=false)  the DISCRIMINATING state — an
                                                element that denotes zero while
                                                being written differently from
                                                the literal zero;
    (identicallyZero=true,  literalZero=true)   the bare literal zero;
    (identicallyZero=false, literalZero=false)  an ordinary nonzero element.

    (identicallyZero=false, literalZero=true) is excluded by P1.

WHICH CLAUSE CONSTRAINS THE IMPL, AND THE BINDER HAZARD. C1 is the only
impl-constraining clause, and it mentions ``identicallyZero`` ONLY. That makes
``literalZero`` precisely the binder the brief warns about: it appears nowhere in
the post-image, so a battery whose every witness held it at one value would say
nothing about whether the spec's INDEPENDENCE from it is real, and a rival that
keyed on it in the untested sub-domain would slip through. The reject witnesses
therefore vary ``literalZero`` across both its reachable values (``false`` at the
discriminating state, ``true`` at the bare literal zero), and one rival
(rival-literal-kept) is built specifically to be correct EVERYWHERE except at
``literalZero = true`` — the near-miss that only a witness at that point refutes.

ADVERSARIAL READ of the nagini classes on this carrier (case-by-case accounting
in the footer):

  * CARRIER NARROWING. The nagini sibling contracts TWO functions over a
    two-facet ``Coeff``: the truth-value decision and a downstream
    length-collapse that propagates it. This bundle models only the purely
    functional core — the truth-value decision — so the four nagini cases
    attached to the downstream propagation have NO counterpart here. Their
    ARGUMENT (keying the answer on the structural observation rather than the
    mathematical one; never collapsing at all) is already carried on the one
    modeled method by rival-literal-shape and rival-always-nonzero, so nothing
    adversarial is lost — only the second attachment point. Case-count parity
    with nagini is not the target and is not chased.

  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling records this class
    as MANDATORY and its #1 weakness: both functions hold only a half share of
    the input's fields, so a rival that WRITES the input to satisfy the
    postcondition vacuously is rejected for insufficient permission. Lean and
    Velvet are referentially transparent: ``e`` is an immutable value, the method
    declares no ``mut`` binder, and there is no heap, aliasing, or fractional
    permission system to subvert. There is no read-only input to overwrite, so
    the class is vacuous. No substitute probe is fabricated.

  * UNGROUNDED-ORACLE ECHO — N/A as an attack, exactly as the sibling records.
    C1 is pinned to ``nonzeroSpec e``, a transparent ``def`` of the method's own
    argument, not an opaque answer key sitting in the module. There is no wrong
    echo to build: the cheapest honest impl IS the correct impl. Carried instead
    as the positive controls.

  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. Two
    rivals key the answer on the structural observation instead of the
    mathematical one (one totally, one only in the ``literalZero`` sub-domain);
    two are degenerate constants, one in each direction.

  * DIVERGENCE - INAPPLICABLE to this impl, CLOSED BY THE SEMANTICS against any
    rival that manufactures it, and therefore NOT ported. The frozen impl region
    is LOOP-FREE and non-recursive, so there is no control flow here to make
    diverge; a diverging rival has to bring a loop of its own, and when it does
    the semantics refuse it. REWRITTEN by a later audit, twice, and this revision
    RETRACTS the "one extra annotation line buys vacuous verification back" claim
    the previous one carried. Both forms are measured rejected on this cell:

    (a) the measure-LESS spin is REJECTED, exit 1:
            let mut i : Nat := 0
            while true invariant True done_with True do i := i + 1
            return false                                  -> exit 1
        with ``Decreasing annotations are required in total correctness
        semantics`` raised on the ``method`` command itself;

    (b) and the measure-CARRYING form, the sharper one that cannot be dismissed
        as merely lacking the annotation, is ALSO REJECTED, on the measure's own
        goal. With a measure that provably does NOT decrease, and no ``done_with``
        clause:
            let mut i : Nat := 0
            while true invariant True decreasing i do i := i + 1
            return false
        built with the frozen spec view intact and every proof reduced to a bare
        ``loom_solve``, the result is exit 1 with ``unsolved goals``,
        ``case «decreasing_1: i» ... ⊢ i + 1 < i``. The measure is CHECKED.

    The mechanism, stated correctly this time. ``termination "total"`` is not
    merely a linter: Loom's ``set_option`` elaborator both records the option and
    runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), and Velvet's ``method``
    macro opens the same namespace (``Velvet/Velvet/Syntax.lean:386``). The frozen
    file's line 7 is ``open TotalCorrectness DemonicChoice`` and there is no
    ``open PartialCorrectness`` anywhere in it, so the total scope is what
    resolves ``WPGen.forWithInvariantLoop``: the ``TotalCorrectness`` copy
    (``Loom/MonadAlgebras/NonDetT/Basic.lean:544``) takes ``measure : β → Nat``
    and emits ``measure b' < measure b`` as ``decreasing_<n>``, which is the goal
    quoted in (b). The ``PartialCorrectness`` twin at :211 takes
    ``measure : β → Option ℕ`` and drops it, and that is the rule this bundle does
    NOT use. So there are two independent refusals here, not a linter and a hole:
    the naive rival dies at elaboration, the annotated rival dies on the descent
    goal. Nothing is escalated and no edit to the frozen ``Solution.lean`` is
    wanted.

    It is NOT ported, and the reason is NOT referential transparency and NOT that
    the spec admits the rival: it is the WITNESS CONTRACT. A reject case needs a
    witness that ELABORATES against the rival and FAILS against gold, and a
    diverging rival's module does not compile at all (the descent obligation fails
    at the ``method`` itself, ahead of any appended tester), so the first half is
    unreachable for any witness and the case would land INCONCLUSIVE instead of
    rejected. Confirmed from the other direction too: the diverging rival's
    ``forIn Lean.Loop.mk`` term does not normalise, so this battery's tester
    witness fails against the RIVAL with ``Tactic `decide` failed ... its
    `Decidable` instance ... did not reduce to `isTrue` or `isFalse```, and a
    ``witness_reference`` cannot help because it substitutes only the gold half of
    the check. Recorded as closed by the semantics and unwitnessable, with the
    goal in (b) as the evidence.

WITNESS MECHANICS ON THIS BUNDLE. The spec is a ``method`` CONTRACT, not a bare
predicate, so each witness reaches C1 through Velvet's own tester machinery
(``extract_program_for`` / ``prove_precondition_decidable_for`` /
``prove_postcondition_decidable_for`` / ``derive_tester_for``) and states
``symbolicNonzeroTester <element> = false`` at ONE concrete element: the
extracted program's result violates the postcondition there. The carrier is
fully transparent (empty ``axioms`` region, two ``Bool`` fields, a loop-free
impl), so no witness needs to CONDITION on an opaque term — every one states its
refutation at literal field values and closes under ``decide``. No witness binds
a hypothesis, so there are no assumptions that could be jointly unsatisfiable and
the gate's consistency probe is not reached. No banned token
(sorry/admit/native_decide/axiom/opaque). Every witness input satisfies P1, so
none is vacuously excluded (the tester short-circuits to ``true`` when a
``require`` clause is false, which would make ``= false`` unprovable).

Each witness was checked out-of-band with ``scripts/lean_verify.sh``, in a file
whose ``prove_correct`` block is stripped so no tactic script can mask the
verdict: all four ELABORATE against their rival (exit 0) and all four FAIL
against the frozen solution with ``Tactic `decide` proved that the proposition
... is false`` (exit 1) — gold's tester decides to ``true`` at that element, so
``= false`` is refuted. That failure is a POSITIVE semantic statement, not a
stuck reduction: gold's impl is loop-free and its tester reduces fully, so the
gold half genuinely says "the spec IS satisfied here", which is the inference the
two-build check needs.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini sibling also ships none
(``meta.axioms == []``); the changed operation is modeled deeply and concretely,
so nothing rests on an axiom. This gate ignores ``AXIOM_TESTS`` regardless.

``admissibility`` LANE — NOW CARRIED (``adm-f2p-element``), added by a later
audit, in the shape the porting brief prescribes for a total carrier: an
in-region ``assert`` that discharges the obligation AT A CONCRETE F2P-SHAPED
INPUT, by evaluation, before the frozen obligation closes verbatim. It pins, by
kernel evaluation rather than by prose, that the domain predicate HOLDS at the
discriminating element and that the spec's value there is the one this battery
claims throughout. Measured: verifies (exit 0).

Its limit is stated rather than glossed, because the earlier text here was right
about the mechanism even though it drew the wrong conclusion from it: the assert
names LITERAL elements, so it is a closed tautology about those literals and it
still verifies under a ``require`` that admits nothing. Measured on this cell —
``adm-f2p-element`` verifies (exit 0) under ``require False`` and under a
``require`` conjoined with ``e.identicallyZero = false``, which forbids the very
element it names. So this case is an honest pointwise VALUE control and a
demonstration that the domain predicate evaluates to ``true`` at the F2P element;
it is NOT by itself a PRECOND-TOO-STRONG detector, and it is not filed as one.

What does detect PRECOND-TOO-STRONG here is the reject lane: the derived tester
short-circuits to ``true`` off-domain, so a witness proving
``Tester <element> = false`` is a machine-checked proof that ``<element>`` is
in-domain, and all three reachable states carry one. Measured both directions —
rival-literal-shape's witness holds under the frozen ``require`` (exit 0) and
FAILS (exit 1) against a ``require`` that excludes its point, and likewise for
rival-always-zero at ``(false,false)``.

SPEC PROBES RUN BY THE AUDIT (recorded so they are not re-derived). Seven NEW
wrong impls beyond the four rivals were built against the frozen spec and ALL
were rejected with a semantic residual goal, not a tactic artifact: reporting
nonzero when either the mathematical test says nonzero or the representation is
the bare literal zero; the same disjunction written as a negated conjunction;
keying on whether the two observations DISAGREE; keying on whether they AGREE;
being wrong only at the bare literal zero; and two demonic-choice impls that
return an unconstrained boolean (``let r :| True`` and a tautologous
``r = true ∨ r = false``) — the latter two are the interesting ones, since they
confirm C1 forces the result to be PRODUCED rather than merely inhabited (goal
``i = !e.identicallyZero`` with ``i`` free). Seven NEW correct reshapes were also
built and ALL verify: the negation as ``!= true``, a term-level ``if``, an
applied lambda, a ``mut`` accumulator, ``decide (… = false)``, a triple negation,
and a demonic choice pinned to ``r = nonzeroSpec e``.

A LATER, INDEPENDENT audit re-ran the class with six further wrong impls and six
further correct reshapes, none of them in the battery. All six wrong impls were
rejected, each on a semantic residual goal over the two observations: the XOR of
the two observations; their equality; ``!identicallyZero && literalZero``;
``!identicallyZero || literalZero``; and both unconstrained demonic-choice
shapes. All six reshapes verify: a triple negation, ``decide (… = false)``, an
applied lambda, a ``mut`` accumulator, a demonic choice pinned to
``r = nonzeroSpec e``, and a direct ``return nonzeroSpec e``. So the VALUE clause
carries no SPEC-TOO-WEAK and no SPEC-TOO-STRONG hole on this carrier, now on two
independent passes. NO hole is open: the divergence class above is closed by the
loop semantics the frozen file selects, and it ships no case only because a rival
that fails to compile admits no witness.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20428"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- The frozen impl body, verbatim: everything strictly BETWEEN the method's
# ---- `-- impl-start` and `-- impl-end` (both markers, and the comment lines,
# ---- live INSIDE the elided impl region). Every variant replaces exactly this
# ---- text, so each edit lies wholly inside the one impl region and same_spec
# ---- holds by construction — both facts asserted at load by _swap.
_IMPL = (
    "    -- Report nonzero iff the element is not identically zero — the mathematical\n"
    "    -- zero test, not a comparison of the representation against the literal zero.\n"
    "    return !e.identicallyZero\n"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- The frozen proof, verbatim. A correct reshape may retune THIS block (it is
# ---- elided from the spec view, and only the `prove_correct symbolicNonzero`
# ---- header must survive); rivals leave it as-is, so the wrong impl leaves the
# ---- postcondition goal unsolved and the rival MODULE fails to build — which is
# ---- what expect="reject" requires. The witness, not the module build, is what
# ---- attributes the rejection to the spec.
_PROOF = (
    "prove_correct symbolicNonzero by\n"
    "  loom_solve\n"
    "  simp_all [nonzeroSpec]"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes whose
    residual goal no longer matches the frozen tactic script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness builder. The spec is a `method` contract, so the refutation goes
# ---- through Velvet's tester: `symbolicNonzeroTester <element> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- element. Every element below satisfies P1 (`literalZero → identicallyZero`),
# ---- so the tester does not short-circuit to `true` on a false precondition.
def _witness(identically_zero, literal_zero):
    return (
        "extract_program_for symbolicNonzero\n"
        "prove_precondition_decidable_for symbolicNonzero\n"
        "prove_postcondition_decidable_for symbolicNonzero\n"
        "derive_tester_for symbolicNonzero\n\n"
        "example : symbolicNonzeroTester "
        f"{{ identicallyZero := {identically_zero}, "
        f"literalZero := {literal_zero} }} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. All three were confirmed with real
    # builds (exit 0).
    # =====================================================================
    {
        "id": "pos-negation-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the decision written as an equality against `false` rather
        # than as a boolean negation. Same value on every state, different
        # expression shape; the frozen proof closes unchanged.
        "module": _impl("    return (e.identicallyZero == false)\n"),
        "rationale": (
            "PORTS the nagini pos-ct-negate: a structurally-different CORRECT "
            "impl of the truth-value decision, written as an equality against "
            "`false` instead of a boolean negation of the mathematical-zero "
            "observation. Identical value on all three reachable states, "
            "different expression shape, and no loop or helper fold so no "
            "induction lemma is needed. Defends C1 (`out = nonzeroSpec e`): if a "
            "faithful correct impl in this shape could not verify, C1 would be "
            "SPEC-TOO-STRONG (over-fit to one spelling of the negation)."
        ),
    },
    {
        "id": "pos-branch-dispatch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: an explicit two-way branch on the mathematical-zero
        # observation returning the two constants, instead of one boolean
        # expression. Control flow differs, so the frozen tactic tail no longer
        # matches the residual goal shape and the proof is retuned to run over
        # both branches — the obligation header is byte-identical and nothing is
        # assumed.
        "module": _impl_reproved(
            "    if e.identicallyZero then\n"
            "      return false\n"
            "    else\n"
            "      return true\n",
            "prove_correct symbolicNonzero by\n"
            "  loom_solve <;> simp_all [nonzeroSpec]"),
        "rationale": (
            "RE-EXPRESSES the nagini branch-shape positives (pos-sl-direct / "
            "pos-sl-reorder) on the one method this bundle models: an explicit "
            "two-way branch on the mathematical-zero observation returning the "
            "two constants, instead of a single boolean expression. Same value on "
            "every reachable state, genuinely different CONTROL FLOW, so it tests "
            "that C1 is satisfiable by a dispatching impl and not only by the "
            "expression form. The proof is retuned over the two branches (the "
            "`prove_correct symbolicNonzero` header is byte-identical; no lemma, "
            "no assumption). If it failed => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-require-conjunct",
        "kind": "soundness",
        "expect": "verify",
        # A correct impl that is correct ONLY BECAUSE OF P1: it reports nonzero
        # iff the element is neither identically zero nor the bare literal zero.
        # On the state P1 excludes this would be wrong, so the proof must
        # actually CONSUME the require clause. That makes it the control which
        # shows P1 is load-bearing and usable rather than decorative.
        "module": _impl_reproved(
            "    return (!e.identicallyZero && !e.literalZero)\n",
            "prove_correct symbolicNonzero by\n"
            "  loom_solve\n"
            "  simp_all [nonzeroSpec]\n"
            "  cases hz : e.identicallyZero <;> cases hl : e.literalZero "
            "<;> simp_all"),
        "rationale": (
            "ADDED (no nagini counterpart). A correct impl that is correct ONLY "
            "on the required domain: it reports nonzero iff the element is "
            "neither identically zero NOR the bare literal zero. On all three "
            "reachable states that agrees with C1, but on the fourth state — the "
            "one P1 (`literalZero → identicallyZero`) excludes — it would "
            "disagree, so the proof must actually CONSUME P1 to close. This is "
            "the admissibility-adjacent control the nagini side gets for free "
            "from its class invariant: it shows P1 is LOAD-BEARING and usable "
            "rather than decorative, and that C1 is not covertly demanding "
            "correctness off the declared domain (which would be SPEC-TOO-STRONG "
            "and would make the require clause a lie). Confirmed to verify."
        ),
    },

    # =====================================================================
    # POINTWISE VALUE PINNING (soundness). Formerly filed as the
    # `admissibility` lane; RELABELLED after an audit measured that no
    # expect="verify" case can detect PRECOND-TOO-STRONG on this backend.
    # Verification is MONOTONE in precondition strength — shrinking the domain
    # only ADDS hypotheses to the obligation — so a positive control cannot fail
    # because the domain got smaller. Measured with real builds: this very case
    # still VERIFIES (exit 0) under `require False`, a precondition that admits
    # NOTHING, and likewise under a `require` conjoined with
    # `e.identicallyZero = false` (which forbids both zero-denoting states,
    # including the discriminating one this case names). So its admissibility
    # reading was unearned and has been withdrawn.
    #
    # Where admissibility IS machine-checked: the reject lane's witnesses. The
    # derived tester is `if decide(pre) then (match Exec with res r =>
    # decide(post) | _ => false) else true`, so it short-circuits to `true` on a
    # FALSE precondition — hence a witness proving `Tester <element> = false`
    # can only exist when `<element>` SATISFIES P1. Each reject witness is
    # therefore a machine-checked proof that its own point is in-domain, and the
    # four of them cover all three states P1 admits. Measured: re-running
    # rival-literal-shape's witness against a spec whose `require` excludes
    # `(true,false)` FAILS (exit 1) where it succeeds under the frozen require
    # (exit 0), and rival-always-zero's witness likewise fails when the require
    # excludes `(false,false)`. That is the PRECOND-TOO-STRONG detector this
    # bundle actually has, and it lives in the `uniqueness` cases below.
    # =====================================================================
    {
        "id": "pos-three-state-values",
        "kind": "soundness",
        "expect": "verify",
        # Dispatch explicitly on each of the three states P1 admits, returning
        # the value C1 demands there, and fall through to the general decision.
        # What verifying establishes is that C1's value at each of the three
        # states is EXACTLY the one written here — in particular that the
        # DISCRIMINATING element (denotes zero, representation is not the bare
        # literal zero) must report as zero. Machine-checked to be load-bearing
        # pointwise: flipping the returned constant at any ONE of the three
        # dispatch arms makes the case FAIL (exit 1, three separate builds), so
        # each arm is pinned and none is decorative.
        "module": _impl_reproved(
            "    let discriminating : SymExpr := "
            "{ identicallyZero := true,  literalZero := false }\n"
            "    let bare          : SymExpr := "
            "{ identicallyZero := true,  literalZero := true  }\n"
            "    let ordinary      : SymExpr := "
            "{ identicallyZero := false, literalZero := false }\n"
            "    if e = discriminating then\n"
            "      return false\n"
            "    else\n"
            "      if e = bare then\n"
            "        return false\n"
            "      else\n"
            "        if e = ordinary then\n"
            "          return true\n"
            "        else\n"
            "          return !e.identicallyZero\n",
            "prove_correct symbolicNonzero by\n"
            "  loom_solve <;> simp_all [nonzeroSpec]"),
        "rationale": (
            "CARRIES the value half of the nagini admiss-issue-coeff and "
            "admiss-nonzero-coeff onto this carrier, as a SOUNDNESS control. It "
            "constructs each of the three states P1 admits and dispatches on them "
            "explicitly, returning the value C1 demands at each: the "
            "DISCRIMINATING element (denotes zero, representation is not the bare "
            "literal zero — the state the whole issue is about) must report zero; "
            "the bare literal zero must report zero; an ordinary element must "
            "report nonzero. Verifying establishes that C1 agrees with the written "
            "value at all three, and each arm is measured load-bearing: flipping "
            "the constant at any ONE arm makes the case fail (three builds, exit 1 "
            "each). If it failed => SPEC-TOO-STRONG. It does NOT establish "
            "admissibility: verification is monotone in precondition strength, and "
            "this case was measured to still verify under `require False`. The "
            "PRECOND-TOO-STRONG evidence is the reject witnesses, whose tester "
            "short-circuits to `true` off-domain (see the lane comment above). The "
            "general decision is kept as the fall-through so C1 still discharges "
            "on every other input. Confirmed to verify."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY. Added by a later audit; the port shipped no case of this
    # kind. Shape per the porting brief for a total carrier: discharge the
    # obligation AT a concrete F2P-shaped input, by evaluation, as an in-region
    # `assert`, and then close the frozen obligation verbatim (the impl below the
    # assert is the frozen body, so C1 still discharges universally).
    #
    # What it pins by kernel evaluation rather than by prose: the domain
    # predicate `literalZero -> identicallyZero` HOLDS at the discriminating
    # element (denotes zero, representation not the bare literal zero), and the
    # spec's value at each of the three reachable states is the one this battery
    # claims throughout. Confirmed to verify (exit 0).
    #
    # Its limit, measured and stated rather than glossed: the assert names
    # LITERAL elements, so it is a closed tautology about those literals and it
    # still verifies under a `require` admitting nothing — measured, exit 0 under
    # `require False` and under a `require` conjoined with
    # `e.identicallyZero = false`, which forbids the element it names. So this is
    # an honest pointwise VALUE + domain-evaluation control, NOT a
    # PRECOND-TOO-STRONG detector; that detector is the reject lane's witnesses,
    # whose tester short-circuits to `true` off-domain.
    # =====================================================================
    {
        "id": "adm-f2p-element",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            "      ((({ identicallyZero := true, literalZero := false } "
            ": SymExpr).literalZero\n"
            "          → ({ identicallyZero := true, literalZero := false } "
            ": SymExpr).identicallyZero)\n"
            "       ∧ nonzeroSpec { identicallyZero := true,  literalZero := false } "
            "= false\n"
            "       ∧ nonzeroSpec { identicallyZero := true,  literalZero := true  } "
            "= false\n"
            "       ∧ nonzeroSpec { identicallyZero := false, literalZero := false } "
            "= true))\n"
            "    return !e.identicallyZero\n",
            "prove_correct symbolicNonzero by\n"
            "  loom_solve <;> simp_all [nonzeroSpec]"),
        "rationale": (
            "CARRIES the `admissibility` kind the port dropped, and the lane the "
            "coverage reporter flagged as absent. It is the transliteration of "
            "the nagini admiss-issue-coeff / admiss-nonzero-coeff onto a total "
            "carrier: rather than a CALL that must discharge a callee "
            "precondition at a literal (the nagini mechanism, unavailable here), "
            "it discharges the obligation at concrete F2P-shaped inputs as an "
            "in-region `assert` that must ELABORATE, then closes the frozen "
            "obligation verbatim. Two things become machine-checked that prose "
            "otherwise asserted: (i) the domain predicate `literalZero → "
            "identicallyZero` evaluates to true AT the discriminating element — "
            "the element the public problem statement is about, an element that "
            "denotes zero while not being written as the bare literal zero — so "
            "that element is genuinely in-domain and the obligation is not "
            "unsatisfiable there; and (ii) C1's value at each of the three states "
            "the domain admits is exactly the one every other case in this "
            "battery reasons from (zero, zero, nonzero). If the assert failed, "
            "either the domain predicate would be false at the F2P element "
            "(PRECOND-TOO-STRONG) or the spec's value there would differ from the "
            "battery's premise. Scope: the assert is over literals, so it is a "
            "closed tautology and does NOT by itself detect PRECOND-TOO-STRONG "
            "(measured: still verifies under `require False`). That detector is "
            "the reject lane, whose tester short-circuits to `true` off-domain."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete element, and the refinement argument that its faithful real
    # counterpart would NOT resolve. All four attack C1. Across the four
    # witnesses BOTH carrier observations vary, and all three states P1 admits
    # are probed (pts=3 — the entire reachable domain).
    # =====================================================================
    {
        "id": "rival-literal-shape",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-CHANGE behavior verbatim (Solution_prepatch.lean): the decision
        # keyed on the STRUCTURAL observation — is the representation the bare
        # literal zero — instead of the mathematical one. Correct on the two
        # states where the observations agree, wrong on exactly the
        # discriminating state.
        "module": _impl("    return !e.literalZero\n"),
        "refinement": (
            "this is the pre-change behavior: the truth value keyed on whether "
            "the element's REPRESENTATION is the bare literal zero, rather than "
            "on whether it denotes zero. Its faithful real patch is the unpatched "
            "repository. The failing test constructs a constant polynomial over "
            "the symbolic-expression domain whose sole coefficient denotes zero "
            "while being written as a non-trivial radical expression, and asserts "
            "the polynomial equals the zero polynomial; under this behavior that "
            "coefficient reports nonzero, so it is retained instead of discarded "
            "and the polynomial is not the canonical zero — the assertion fails "
            "and the instance does NOT resolve. This is the exact defect the fix "
            "corrects, so a verifying rival here would be a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "PORTS nagini weak-ct-prepatch-lit0. REJECT from C1 "
            "(`out = nonzeroSpec e`), which pins the result to the MATHEMATICAL "
            "observation `identicallyZero` alone: on the discriminating state the "
            "rival returns nonzero (`!literalZero = !false = true`) while C1 "
            "demands zero (`!identicallyZero = !true = false`). P1 does not "
            "forbid that state (it pins only the converse implication), so the "
            "counterexample is in-domain. Refuted at "
            "`(identicallyZero=true, literalZero=false)` — the state the issue is "
            "about, and the only element on which this rival is wrong at all, so "
            "no other witness point could refute it. If it verified => "
            "SPEC-TOO-WEAK (the spec admits the bug)."
        ),
        "witness": _witness("true", "false"),
    },
    {
        "id": "rival-literal-kept",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS. Agrees with gold on the discriminating state AND on ordinary
        # elements — it defers to the mathematical observation there — and is
        # wrong ONLY when the representation IS the bare literal zero. Its sole
        # failing point is `literalZero = true`, the value of that binder no
        # other clause of the spec constrains, so this is the rival that forces
        # the battery to probe it.
        "module": _impl(
            "    if e.literalZero then\n"
            "      return true\n"
            "    else\n"
            "      return !e.identicallyZero\n"),
        "refinement": (
            "reports nonzero whenever the element's representation IS the bare "
            "literal zero, and otherwise defers to the mathematical zero test — "
            "so it handles the issue's own element correctly and is wrong only on "
            "the plainest input of all. Its faithful real patch is the correct "
            "test disjoined with a literal-zero escape hatch. It does NOT "
            "resolve: the bare literal zero coefficient now reports nonzero, so "
            "it is never discarded and even the ordinary zero polynomial over the "
            "symbolic-expression domain keeps a coefficient instead of being the "
            "canonical zero. That breaks the failing test's own right-hand side "
            "(the zero polynomial it compares against), and it breaks the "
            "PASS_TO_PASS tests over zero and nonzero polynomials — and the "
            "harness reports `resolved` only when the PASS_TO_PASS set holds too."
        ),
        "rationale": (
            "ADDED (no nagini counterpart; the sibling's rivals are all wrong on "
            "the discriminating state, so none isolates this sub-domain). REJECT "
            "from C1: at the bare literal zero, C1 demands zero "
            "(`!identicallyZero = false`) but the rival returns nonzero. This is "
            "the deliberate NEAR-MISS of the battery — it agrees with gold on the "
            "discriminating state and on ordinary elements, so it is correct over "
            "MORE of the domain than rival-literal-shape, and its ONLY failing "
            "point is `literalZero = true`. That matters because C1 mentions "
            "`literalZero` nowhere: it is the binder the post-image is "
            "independent of, and without a witness at `literalZero = true` a "
            "rival keying on it would verify and the battery would never notice. "
            "Refuted at `(identicallyZero=true, literalZero=true)`, its sole "
            "failing element. If it verified => SPEC-TOO-WEAK (C1's independence "
            "from the structural observation untested)."
        ),
        "witness": _witness("true", "true"),
    },
    {
        "id": "rival-always-nonzero",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate: every element reports nonzero, so nothing is ever
        # recognised as zero. Correct on ordinary elements, wrong on BOTH
        # zero-denoting states.
        "module": _impl("    return true\n"),
        "refinement": (
            "a degenerate rival calling every element nonzero, so no coefficient "
            "is ever recognised as zero and none is ever discarded. Its faithful "
            "real patch is a truth test that always answers nonzero. It does NOT "
            "resolve: the failing test's constant polynomial retains its "
            "zero-denoting coefficient and is not the canonical zero polynomial, "
            "so the assertion fails; and the polynomial it is compared against "
            "would not be canonical either. The PASS_TO_PASS tests over zero and "
            "nonzero polynomials fail alongside it."
        ),
        "rationale": (
            "PORTS nagini weak-ct-const-true. REJECT from C1: on any element that "
            "denotes zero, C1 demands `false` and the rival returns `true`. "
            "Refuted at `(identicallyZero=true, literalZero=true)` — the bare "
            "literal zero, a point on which this rival and rival-literal-kept do "
            "genuinely fail for the SAME reason (an element that denotes zero "
            "reported nonzero), which is the only condition under which the brief "
            "permits a shared witness point. It is deliberately NOT refuted at "
            "the discriminating state, so that rival-literal-shape's witness "
            "stays the unique probe of that element and the two constant-valued "
            "rivals bracket the domain from the other side. If it verified => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness("true", "true"),
    },
    {
        "id": "rival-always-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Degenerate in the OTHER direction: every element reports zero. The only
        # rival wrong on an element that does NOT denote zero, so the only one
        # whose witness probes `identicallyZero = false` — without it the
        # `identicallyZero` binder would be held at `true` by every witness.
        "module": _impl("    return false\n"),
        "refinement": (
            "the opposite degenerate rival: every element reports zero, so every "
            "coefficient is discarded as if it denoted zero. Its faithful real "
            "patch is a truth test that always answers zero. It does NOT resolve: "
            "every polynomial collapses to the canonical zero regardless of its "
            "actual coefficients, so the PASS_TO_PASS tests over nonzero "
            "polynomials, their arithmetic, degrees and coefficient accessors all "
            "fail — and the harness reports `resolved` only when the PASS_TO_PASS "
            "set holds in addition to the failing test. Its accidental agreement "
            "with the failing test's assertion is exactly why the refinement "
            "argument has to be made on the PASS_TO_PASS side rather than assumed."
        ),
        "rationale": (
            "ADDED (the nagini sibling carries only the always-truthy constant). "
            "REJECT from C1: on an ordinary element that does not denote zero, C1 "
            "demands `true` and the rival returns `false`. Refuted at "
            "`(identicallyZero=false, literalZero=false)` — and this is the ONLY "
            "rival in the battery that is wrong on an element with "
            "`identicallyZero = false`, so it is the only one whose witness can "
            "probe that value of the binder C1 actually reads. Without it every "
            "witness would hold `identicallyZero` at `true`, and the battery "
            "would demonstrate nothing about the spec's behavior on the other "
            "half of the load-bearing observation. It also completes coverage of "
            "all three states P1 admits. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("false", "false"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
#   nagini case                -> here
#   -----------------------------------------------------------------------
#   pos-ct-negate              -> pos-negation-form           PORTED
#   pos-sl-direct              -> pos-branch-dispatch         RE-EXPRESSED
#   pos-sl-reorder             -> pos-branch-dispatch         RE-EXPRESSED
#   admiss-issue-coeff         -> adm-f2p-element             PORTED
#                                 (+ pos-three-state-values, value half)
#   admiss-nonzero-coeff       -> adm-f2p-element             PORTED
#                                 (+ pos-three-state-values, value half)
#   frame-ct-write-mzero       -> (none)                      VACUOUS
#   frame-sl-write-lit0        -> (none)                      VACUOUS
#   nonterm-ct-spin            -> (none)                      SPEC-CLOSED
#   nonterm-sl-spin            -> (none)                      SPEC-CLOSED
#   weak-ct-prepatch-lit0      -> rival-literal-shape         PORTED
#   weak-ct-const-true         -> rival-always-nonzero        PORTED
#   weak-sl-via-lit0           -> (none)                      CARRIER NARROWING
#   weak-sl-const-keep         -> (none)                      CARRIER NARROWING
#   (no sibling)               -> rival-literal-kept          ADDED (near-miss)
#   (no sibling)               -> rival-always-zero           ADDED
#   (no sibling)               -> pos-require-conjunct        ADDED
#   AXIOM_TESTS (none)         -> (none)                      N/A
#
# 9 velvet SPEC cases: 4 soundness, 1 admissibility, 4 uniqueness, against
# nagini's 13. That is CARRIER NARROWING, not a thinner battery: nagini contracts
# TWO functions and this bundle models ONE.
#
# `admissibility` LANE — CARRIED by adm-f2p-element, added by a later audit. The
# port originally shipped none and argued the lane was undetectable here; the
# argument was that verification is MONOTONE in precondition strength, so
# shrinking the domain only adds hypotheses and can never make a correct impl
# fail. That mechanism is real and is confirmed below, but it does not license
# dropping the lane: the brief's prescribed shape for a total carrier is an
# in-region `assert` that discharges the obligation AT a concrete F2P-shaped
# input, by evaluation, before closing the frozen obligation verbatim, and that
# is a build the battery was simply not making. adm-f2p-element makes it and
# VERIFIES (exit 0). What it machine-checks is that the domain predicate
# `literalZero → identicallyZero` evaluates to TRUE at the discriminating element
# — so the obligation is not unsatisfiable at the F2P-shaped input — and that
# C1's value at each of the three admitted states is the one this battery reasons
# from throughout.
#
# The monotonicity limit is recorded on the case rather than used to omit it: the
# assert is over LITERALS, hence a closed tautology, so it still verifies under a
# `require` that admits nothing (measured: exit 0 under `require False`, and exit
# 0 under a `require` conjoined with `e.identicallyZero = false`, which forbids
# the very element it names). So adm-f2p-element is not filed as a
# PRECOND-TOO-STRONG detector. The nagini sibling gets one because its witnesses
# are CALLS (`Assert(coeff_truthy(Coeff(0,1)) == False)`) and a call must
# discharge the callee's precondition at that literal; the velvet analogue is not
# available — a self-call from inside the impl region fails to elaborate for a
# TOOLING reason, not a spec one (`fail to show termination for symbolicNonzero
# ... the type SymExpr does not have a `.brecOn` recursor`, plus a consequent
# `Tactic `unfold` failed`).
#
# What DOES detect PRECOND-TOO-STRONG here is the reject lane: the derived tester
# short-circuits to `true` when the precondition is false, so a witness proving
# `Tester <element> = false` is itself a machine-checked proof that `<element>` is
# in-domain. All three states P1 admits carry such a witness, and the sensitivity
# is measured in both directions — rival-literal-shape's witness holds under the
# frozen `require` (exit 0) and FAILS (exit 1) against a `require` excluding its
# point, and likewise rival-always-zero at `(false,false)`.
#
# CARRIER NARROWING (weak-sl-via-lit0, weak-sl-const-keep, and the -sl positives):
#   the nagini sibling contracts a second function — a downstream length-collapse
#   that PROPAGATES the truth-value decision — and attaches four cases to it. This
#   bundle models only the purely functional core, the truth-value decision
#   itself, so those cases have no attachment point here. Their ARGUMENT is not
#   lost: weak-sl-via-lit0 keys the collapse on the structural observation, which
#   is rival-literal-shape's attack one level down; weak-sl-const-keep never
#   collapses at all, which is rival-always-nonzero's. Both are already carried on
#   the modeled method, and fabricating a second rival for a behavior this bundle
#   does not model would be chasing parity, which the porting brief forbids.
# VACUOUS (frame-ct-write-mzero, frame-sl-write-lit0): the nagini sibling calls
#   the frame-mutation class MANDATORY and its #1 weakness — both functions hold
#   only a half share of the input's fields, so a rival that WRITES the input to
#   discharge the postcondition vacuously is rejected for insufficient
#   permission. Velvet is referentially transparent: `e` is an immutable value,
#   no `mut` binder, no heap, no aliasing, no fractional permissions. There is no
#   read-only input to overwrite. No substitute probe fabricated.
#   DEMONSTRATED rather than asserted, since "the carrier collapses this" is a
#   reason that has to be shown: the closest available forgery is to REBIND the
#   input name inside the impl region and answer from the rebound value, tried
#   both as a shadowing `let e : SymExpr := …` and as `let mut e := e; e := …`.
#   Both were built and both are REJECTED (exit 1), with residual goal
#   `⊢ e.identicallyZero = false` — i.e. C1's `e` still denotes the METHOD'S
#   ARGUMENT, so no rebinding inside the body can reach the postcondition. That
#   is the precise sense in which the class has no attack surface here: it is not
#   that a write is forbidden, it is that a write is UNOBSERVABLE to the spec.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness DemonicChoice``, and the two AGREE: Loom's
#   ``set_option`` elaborator itself runs ``openScope `TotalCorrectness``
#   (``Loom/MonadAlgebras/WP/Options.lean:169-186``) and Velvet's ``method``
#   macro opens the same namespace (``Velvet/Velvet/Syntax.lean:386``), so line 7
#   is redundant with line 4 rather than in conflict with it. There is no
#   ``open PartialCorrectness`` anywhere in this file for a later line to
#   restore. Both namespaces define ``WPGen.forWithInvariantLoop`` and the
#   difference IS the guarantee -- the ``PartialCorrectness`` version takes a
#   loop measure and DISCARDS it -- which is why the two lines have to move
#   together, and they do here. Under the total scope a postcondition is claimed
#   of ALL runs and not only of terminating ones, so a spliced loop owes a
#   descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
#
#   THE CLASS IS CLOSED, both ways, re-measured here:
#     (a) measure-less spin + `return false`            -> exit 1 (rejected at
#         elaboration, `Decreasing annotations are required in total correctness
#         semantics`)
#     (b) the SAME spin plus one annotation line - a measure that provably does
#         NOT decrease (`decreasing i` with `i := i + 1`), no `done_with` -
#         and `return false`, the unambiguously WRONG constant
#                                                       -> exit 1, REJECTED with
#         `unsolved goals`, `case «decreasing_1: i» ... ⊢ i + 1 < i`
#   built with the frozen spec view intact, the proof reduced to a bare
#   `loom_solve`, and no banned token. THIS RETRACTS the previous revision of
#   this block, which recorded (b) as `VERIFIES (exit 0)` and called it a
#   surviving hole where "the wrong answer is laundered through an exit the loop
#   never reaches". Under the total rule the descent obligation fires before any
#   exit argument is reached, so nothing is laundered. Form (b) is the sharper of
#   the two, since it cannot be waved off as merely missing an annotation.
#
#   Mechanism, corrected: `termination "total"` is not merely a LINTER. It is
#   true that the `decreasing` elaborator errors when the measure syntax is
#   literally ABSENT, which is what (a) hits, but the option ALSO opens the total
#   scope, and that scope is what resolves `WPGen.forWithInvariantLoop` to the
#   `TotalCorrectness` copy (Loom `MonadAlgebras/NonDetT/Basic.lean:544`), which
#   takes `measure : β → Nat` and EMITS `measure b' < measure b` as
#   `decreasing_<n>`. That is the goal quoted in (b). The `PartialCorrectness`
#   twin at :211 takes `measure : β → Option ℕ` and never mentions it again in
#   its `get` field, so under THAT namespace the side-condition would never be
#   generated; this file does not open it. No repair is available because none is
#   needed, and no edit to the frozen Solution.lean is wanted.
#
#   No reject case is shipped, and the reason is the WITNESS CONTRACT, not spec
#   weakness. A reject case needs a witness that (1) ELABORATES against the rival
#   and (2) FAILS against gold; a diverging rival's module does not compile at
#   all, since the descent obligation fails at the `method` itself ahead of any
#   appended tester, so (1) is unreachable for ANY witness and the gate returns
#   `witness-unproven` -> INCONCLUSIVE -> MALFORMED-TESTS, a FAILING gate rather
#   than a rejection. Confirmed from the other direction too: the diverging
#   rival's `forIn Lean.Loop.mk` term does not normalise, so this battery's
#   tester witness fails against the RIVAL with ``Tactic `decide` failed ... its
#   `Decidable` instance ... did not reduce to `isTrue` or `isFalse``, and a
#   `witness_reference` cannot help because it substitutes only the gold half.
#   Disposition: SPEC-CLOSED and unwitnessable, with the goal in (b) as evidence.
# AXIOM lane: the nagini sibling ships AXIOM_TESTS = [] as well (meta.axioms is
#   empty; the changed operation is modeled deeply, so nothing rests on an
#   axiom). Nothing to drop, and this gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   OBLIGATIONS: one (`prove_correct symbolicNonzero`). DEFENDED by four
#     soundness positives plus one admissibility case; ATTACKED by four rivals.
#   CLAUSES: C1 (`out = nonzeroSpec e`) is the only impl-constraining clause and
#     every rival attacks it. Its value at each of the three reachable states is
#     pinned pointwise by pos-three-state-values (each arm measured load-bearing:
#     flipping any one arm's constant fails). P1 (`literalZero →
#     identicallyZero`) is the domain: it is shown LOAD-BEARING rather than
#     decorative by pos-require-conjunct, whose impl is correct only on the
#     required domain — measured, that impl FAILS (exit 1) when P1 is weakened to
#     `require True`, with residual goal exactly the excluded state
#     (`identicallyZero = false`, `literalZero = true` ⊢ False), while the frozen
#     impl still verifies under `require True`. That P1 ADMITS each of the three
#     states is machine-checked by the reject witnesses, not by any positive: the
#     tester short-circuits to `true` off-domain, so `Tester <e> = false` is only
#     provable for an in-domain `<e>`.
#   BINDERS: the sole input binder `e` has two observations, and the reject
#     witnesses vary BOTH — `identicallyZero` takes `true` (rival-literal-shape,
#     rival-literal-kept, rival-always-nonzero) and `false` (rival-always-zero);
#     `literalZero` takes `false` (rival-literal-shape, rival-always-zero) and
#     `true` (rival-literal-kept, rival-always-nonzero). Varying `literalZero`
#     is the point that needed deliberate work: C1 does not mention it, so it is
#     exactly the binder a battery would otherwise pin at one value, and
#     rival-literal-kept exists to make a rival that abuses it refutable.
#   POINTS: pts=3 — `(true,false)`, `(true,true)`, `(false,false)`. That is EVERY
#     state P1 admits; the fourth, `(false,true)`, is excluded by P1 and no
#     witness could be stated there (the tester short-circuits to `true` on a
#     false precondition, making `= false` unprovable). So the reject lane probes
#     the reachable domain exhaustively and no rival distinguishable by any input
#     can escape it.
#   SHARED WITNESS POINT: rival-literal-kept and rival-always-nonzero share
#     `(true,true)`. Permitted because they genuinely fail there for the SAME
#     reason — an element that denotes zero is reported nonzero — and because it
#     is rival-literal-kept's SOLE failing element, so its witness cannot be
#     moved to a more discriminating point. rival-always-nonzero is the broader
#     rival of the pair (it also fails at `(true,false)`), so the shared point
#     does not let the near-miss borrow a claim it has not demonstrated.
#
# WITNESS MECHANICS: the carrier is fully transparent (empty `axioms` region, two
#   `Bool` fields, loop-free impls), so no witness needs to condition on an
#   opaque term; each states `symbolicNonzeroTester <element> = false` at literal
#   field values and closes under `decide`. No witness binds a hypothesis, so the
#   gate's consistency probe is not reached and no assumption could be vacuous.
#   All four checked with scripts/lean_verify.sh in a prove_correct-stripped
#   file: rival exit 0, gold exit 1 with "Tactic `decide` proved that the
#   proposition ... is false". Gold's impl is loop-free so its tester reduces
#   FULLY — the gold half is a positive "the spec is satisfied here", not a stuck
#   reduction, which is the inference the two-build check needs.
AXIOM_TESTS = []
