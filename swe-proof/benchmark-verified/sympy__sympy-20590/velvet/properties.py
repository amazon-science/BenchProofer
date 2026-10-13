"""properties.py — G-PBT falsification battery for sympy__sympy-20590 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both regions the consumer spec view elides, so ``markers.same_spec`` holds and
every ``prove_correct <name>`` obligation survives) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes iff
(in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does NOT
verify AND its refutation ``witness`` discriminates: the witness must ELABORATE
against the rival and FAIL against the frozen solution).

=== DEFENDED SURFACE (adversarial read) ===

THREE contracted methods, over a carrier that is a pure immutable value
(``List Bool`` — one closed-layout flag per contributing type in a chain) plus
two total transparent ``def``s over it. No ``require`` clause anywhere (the
pre-conditions regions are empty), so every method is TOTAL over its domain.

  M1  mixinPinsClosedLayout return (out : Bool)
        C1  ensures out = true                                   -- constant pin

  M2  coreInstanceAdmitsNamespace (others : List Bool) return (out : Bool)
        C2  ensures out = instanceAdmitsNamespace (others ++ [true])
        C3  ensures allClosedLayout others = true → out = false

  M3  coreBindUndeclared (others : List Bool) return (out : Except AttrError Bool)
        C4  ensures out = bindUndeclared (others ++ [true])
        C5  ensures allClosedLayout others = true
                      → out = Except.error AttrError.bindingRefused

WHICH CLAUSE CONSTRAINS WHICH IMPL. C1 is a CONSTANT pin on a nullary method —
the only impl-constraining clause of M1, and the whole of it. C2 and C4 are the
load-bearing clauses of M2/M3: each is a function of the method's OWN input
``others``, universally quantified, so an impl cannot satisfy either by
returning a constant — it must compute the chain rule over ``others ++ [true]``
at EVERY ``others``. C3 and C5 are the same rule INSTANTIATED at the all-closed
sub-domain (the actual repo shape); they are implied by C2/C4 respectively but
are attacked independently below, because a rival can agree with the general
rule off that sub-domain while diverging on it (or vice versa).

GROUNDEDNESS. ``allClosedLayout`` / ``instanceAdmitsNamespace`` /
``bindUndeclared`` are TRANSPARENT total ``def``s over the method's own argument
(a front-recursive conjunction and two derived decisions), NOT an opaque
answer-key oracle. So the ungrounded-oracle-echo class does not apply, exactly
as on the nagini sibling: the post-image is *produced by* the modeled rule, and
the honest cheapest impl satisfying it is carried as a POSITIVE control instead
(three of them, one per method).

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and the nagini sibling says so first:
    its own docstring records that ALL inputs are pure immutable value sequences
    with NO read-only heap permission, so ``has_readonly_input`` is False there
    already and it ships no frame-mutation rival. Here the same holds a fortiori:
    Lean and Velvet are referentially transparent, ``others`` is an immutable
    value, no method declares a ``mut`` parameter, and there is no heap, aliasing
    or permission system to subvert. No substitute probe is fabricated.

  * DIVERGENCE / NON-TERMINATION — the nagini sibling DOES carry two of these
    (its P1-repair pair, one per contracted function, rejected there by
    ``MustTerminate``). On this bundle the class is GENUINELY VACUOUS, not a
    known spec hole: the frozen solution sets
    ``set_option loom.semantics.termination "total"``, so a diverging impl is
    REJECTED by the verifier for a reason internal to the spec —
    ``error: Decreasing annotations are required in total correctness
    semantics``. Measured directly on this bundle: splicing a measureless
    ``while b`` spin into M1's impl region fails to verify with exactly that
    error, and so does the sharper shape that CARRIES a measure which does not
    decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 / decreasing q``,
    body ``q := q``), which is REJECTED on the measure's OWN descent goal:
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. So the refusal is not merely
    the missing-annotation linter. There is no ``partial`` cohort to contrast this
    with, as an earlier version of this bullet claimed: all 500 velvet bundles set
    ``"total"`` and open ``TotalCorrectness``, and the ``set_option`` elaborator
    itself runs ``openScope `TotalCorrectness``
    (``Loom/MonadAlgebras/WP/Options.lean:169-186``), so the option and the ``open``
    cannot disagree. Because the class is vacuous here rather than a hole, NO
    reject case is shipped for it: a reject case needs a witness that refutes the
    rival at a concrete input, and a rival that never returns has no returned
    value to refute — the rejection is carried by the termination obligation, not
    by a value-level counterexample. Recorded as vacuous-under-``total``, with the
    measurement, rather than as a dropped case.

  * PARTIAL-DOMAIN / VALUE — the whole reject surface here (11 rivals), against
    C1–C5. See the accounting footer.

=== OUT-OF-BAND PROBES THAT ARE NOT SHIPPED AS CASES ===

Additional wrong impls were built and measured against the frozen spec to look
for a spec hole beyond what the shipped rivals attack. None verified, so none is
a hole and none is shipped (a rival that is merely redundant costs builds
without adding coverage):

  * M2 computing the chain as `others.dropLast ++ [true]` — a different chain
    mutilation from the head-only truncation. FAILS (exit 1); refutable at
    `others = [false]`.
  * M3 correct only for chains of length ≤ 2 and absorbing above that (a
    length-gated partial-domain miss past every point the battery probes).
    FAILS (exit 1); refutable at `others = [true, true, true]`, and that witness
    fails against gold, so the shipped four-point binder coverage is not hiding a
    longer-chain hole.
  * M3 returning `Except.ok false` on the absorbed branch — probes whether C4
    pins the CARRIED value and not just the ok/error tag. FAILS (exit 1),
    so C4 does pin the payload.

Five more were added in audit, aimed specifically OFF the four points the
shipped witnesses probe (`[]`, `[true]`, `[false]`, `[true, false]`), since a
spec hole that the battery's own probe points cannot see is exactly what a
four-point binder coverage could be hiding. All five FAIL (exit 1) — no hole:
  * M2 wrong ONLY at `others = [false, true]` (an unprobed point, and the
    order-swap of the one length-2 point the battery does probe).
  * M3 wrong ONLY at `others = [false, true]` — the same unprobed point on the
    binding observable.
  * M2 consulting only the chain TAIL (`others.drop 1 ++ [true]`), the mirror of
    the shipped head-only truncation.
  * M2 constant `true` — the dual of rival-ns-never-admits, wrong exactly ON the
    all-closed sub-domain where that one is right.
  * M3 correct below length 3 and absorbing at length >= 3, i.e. wrong only past
    every length the battery probes.
So C2/C4 are pinned pointwise across the whole binder, not merely at the four
witnessed points: the universal quantifier is doing real work everywhere.

Correct reshapes were also built to look for a SPEC-TOO-STRONG hole. Every
faithful one that was tried is accepted:

  * M2 as `!allClosedLayout others` and M3 branching on `allClosedLayout others`
    (both dropping the appended flag entirely — sound because it is `true`, the
    conjunction's identity): both VERIFY (exit 0) under the frozen tactic body.
    Now shipped jointly as admiss-gold-total's subject.
  * M2 as `instanceAdmitsNamespace (true :: others)` (the flag consed on the
    FRONT rather than appended): VERIFIES (exit 0) under the frozen tactic body.
  * M2 as `others.any (fun f => !f)` and as
    `instanceAdmitsNamespace ((others ++ [true]).reverse)`: both need the elided
    tactic body retuned (the frozen `simp` set does not relate `List.any` or
    `List.reverse` to the fold), and both then VERIFY (exit 0) — a proof-shape
    cost, not a spec rejection. Recorded here rather than shipped because the
    positives already carried are enough to defend all three obligations.
  * Re-measured in audit, same class, two further spellings: M2 as
    `others.contains false` and as `!others.all (fun f => f)`. Both FAIL (exit 1)
    under the FROZEN tactic body, and the residual goal is purely a lemma gap —
    `decide (false ∈ others) = !allClosedLayout others` (resp.
    `(others.all fun f => f) = allClosedLayout others`): the frozen simp set does
    not relate `List.contains` / `List.all` to the front-recursive fold. Adding
    an induction on `others` to the ELIDED body makes the `contains` spelling
    VERIFY (exit 0). Same proof-shape cost as the `any`/`reverse` pair, NOT a
    SPEC-TOO-STRONG hole: the spec accepts the reshape, the frozen tactic script
    just does not carry the bridging lemma.

WITNESS MECHANICS ON THIS BUNDLE. The Velvet tester path
(``prove_postcondition_decidable_for`` → ``derive_tester_for`` →
``<name>Tester args = false := by decide``) is DEAD on M3 and ALIVE on M2.
Re-measured case by case:

  * M3: dead. ``prove_postcondition_decidable_for coreBindUndeclared`` leaves
    ``unsolved goals … ⊢ Decidable (out = bindUndeclared (others ++ [true]))``
    and ``⊢ Decidable (allClosedLayout others = true → out = Except.error …)``,
    because ``Except AttrError Bool`` carries no ``DecidableEq`` instance in
    this workspace (measured separately: ``failed to synthesize Decidable
    (Except.ok true ≠ Except.error AttrError.bindingRefused)``).
  * M2: ALIVE. ``extract_program_for`` then
    ``prove_postcondition_decidable_for coreInstanceAdmitsNamespace`` then
    ``derive_tester_for coreInstanceAdmitsNamespace`` elaborates cleanly
    (exit 0), and ``#print axioms coreInstanceAdmitsNamespaceTester`` reports
    ``[propext, Classical.choice, Quot.sound]`` — NO ``sorryAx``. A tester-shaped
    witness on M2 does discriminate: ``coreInstanceAdmitsNamespaceTester [true]
    = false := by decide`` elaborates against the open-contributor rival
    (exit 0) and fails against gold (exit 1, ``Tactic `decide` proved that the
    proposition … is false``). Omitting ``extract_program_for`` is what makes
    the path LOOK dead — the bare
    ``prove_postcondition_decidable_for``/``derive_tester_for`` pair then fails
    with ``no executable found for coreInstanceAdmitsNamespace, please extract
    the program first``, which is a missing prerequisite and not an
    undecidable postcondition.

So the tester path was an available second option on M2, not an unavailable one.
It is not used, because the carrier is fully TRANSPARENT and the
extracted-program path is uniformly available on BOTH methods, states the
refutation against the post-image the load-bearing clause actually names, and
therefore reads the same way on M2 and M3. That is a presentation choice with a
measured alternative behind it, not a tooling wall. Every
witness uses ``extract_program_for <method>`` and states, at one concrete
``others``, that the rival's OWN returned value differs from the transparent
post-image the load-bearing clause demands:

    (match <method>Exec <others> with | DivM.res r => r | _ => <the post-image>)
        ≠ <the post-image>

``…Exec`` is ``NonDetT.run`` of the impl and every rival here is loop-free, so
the whole term reduces under ``decide``; the fallback arm is set to the
post-image itself so a non-returning run could never make the ``≠`` true
vacuously. On M3 both sides are projected through ``Except.toOption``, because
``Except AttrError Bool`` has no ``DecidableEq`` instance in this workspace
(measured: ``failed to synthesize DecidableEq (Except AttrError Bool)``) while
the projection is decidable and still separates ``ok true`` from
``error bindingRefused``.

Against the FROZEN solution each of the ELEVEN witnesses FAILS with ``Tactic
`decide` proved that the proposition … is false`` — gold's value IS the
post-image at that input, which is exactly the discrimination the gate requires.
No witness binds a hypothesis (every input is a concrete ``List Bool`` literal
that decides the clause), so no consistency probe is needed and none can be
inconsistent. No banned token (sorry / admit / native_decide / axiom / opaque).
All ELEVEN pairs were checked out of band with ``scripts/lean_verify.sh``: each
ELABORATES against its rival (exit 0) and FAILS against gold (exit 1, the
``decide``-proved-false error above). Re-derived independently in audit: all 11
rival builds exit 0 and all 11 gold builds exit 1, every gold-side failure being
the ``decide``-proved-false evaluation (no stuck reduction, missing identifier or
type error anywhere in the 22 logs). The FORGERY pair was also run for all 11:
flipping the witness's ``≠`` to ``=`` inverts BOTH exit codes (gold 0, rival 1),
so each gold-side exit code tracks the CLAIM rather than being a
claim-independent failure.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries two
axiom-soundness / containment probes over the deep object-model rule; that is
G-AX's job (``axiom_check.py`` / ``mapping.md`` §3) and the G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "sympy__sympy-20590"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each is the WHOLE frozen impl body of one method —
# everything strictly BETWEEN that method's `-- impl-start` / `-- impl-end` — so
# every variant's edit lies wholly inside one impl region and same_spec holds by
# construction (both facts asserted at load by _swap). M1's anchor carries its
# two impl-region comment lines, which is what makes the bare `return true`
# unique to it: the same three words appear in other impl regions' text.
_IMPL_MIXIN = (
    "    -- The shared contributing type pins a closed instance layout (declares an\n"
    "    -- empty closed slot set, adding no named slots and no open namespace).\n"
    "    return true"
)

_IMPL_NS = (
    "    let trait := true\n"
    "    let chain : List Bool := others ++ [trait]\n"
    "    return instanceAdmitsNamespace chain"
)

_IMPL_BIND = (
    "    let trait := true\n"
    "    let chain : List Bool := others ++ [trait]\n"
    "    return bindUndeclared chain"
)

for _anchor in (_IMPL_MIXIN, _IMPL_NS, _IMPL_BIND):
    assert _BASE.count(_anchor) == 1, "impl region drifted from expected text"

# The frozen proof of M3, verbatim. Only ONE case retunes it (the positive that
# routes M3 through M2's contract, whose residual goal is stated in the named
# namespace predicate and so needs that predicate's own unfold added to the
# existing simp set). The `prove_correct coreBindUndeclared` header — the
# obligation — is preserved byte-for-byte; only the elided tactic body changes.
_PROOF_BIND = (
    "prove_correct coreBindUndeclared by\n"
    "  loom_solve\n"
    "  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout]"
)

assert _BASE.count(_PROOF_BIND) == 1, "proof region drifted from expected text"


def _mixin(body):
    return _swap(_BASE, _IMPL_MIXIN, body)


def _ns(body):
    return _swap(_BASE, _IMPL_NS, body)


def _bind(body, proof=None):
    src = _swap(_BASE, _IMPL_BIND, body)
    return src if proof is None else _swap(src, _PROOF_BIND, proof)


# ---------------------------------------------------------------------------
# Witness builders. The tester path is dead on M2/M3 (the postcondition is not
# synthesizably Decidable — see the module docstring), so each witness extracts
# the executable program and refutes the load-bearing clause DIRECTLY against the
# transparent post-image at one concrete input. The `| _ =>` arm is the
# post-image itself, so a non-returning run cannot satisfy the `≠` vacuously.

def _w_mixin():
    """Refute C1 (`out = true`) on the nullary method."""
    return (
        "extract_program_for mixinPinsClosedLayout\n"
        "\n"
        "example :\n"
        "    (match mixinPinsClosedLayoutExec with | DivM.res r => r | _ => true)"
        " ≠ true := by\n"
        "  decide\n"
    )


def _w_ns(others):
    """Refute C2 (`out = instanceAdmitsNamespace (others ++ [true])`) at `others`."""
    post = f"instanceAdmitsNamespace ({others} ++ [true])"
    return (
        "extract_program_for coreInstanceAdmitsNamespace\n"
        "\n"
        "example :\n"
        f"    (match coreInstanceAdmitsNamespaceExec {others} with"
        f" | DivM.res r => r | _ => {post})\n"
        f"      ≠ {post} := by\n"
        "  decide\n"
    )


def _w_bind(others):
    """Refute C4 (`out = bindUndeclared (others ++ [true])`) at `others`.

    Both sides are projected through `Except.toOption`: `Except AttrError Bool`
    has no `DecidableEq` instance here, while the projection is decidable and
    still separates the absorbed-binding outcome from the refusal outcome.
    """
    post = f"(bindUndeclared ({others} ++ [true])).toOption"
    return (
        "extract_program_for coreBindUndeclared\n"
        "\n"
        "example :\n"
        f"    (match coreBindUndeclaredExec {others} with"
        f" | DivM.res r => r.toOption | _ => {post})\n"
        f"      ≠ {post} := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen code form). One per method, so
    # every obligation is DEFENDED.
    # =====================================================================
    {
        "id": "pos-control-mixin",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: derive the closed-layout flag by NEGATING the open-layout
        # flag through a named local, instead of stating the closed-layout flag
        # directly. Same value (`!false = true`), different expression shape;
        # the frozen proof closes unchanged.
        "module": _mixin(
            "    let leavesLayoutOpen := false\n"
            "    return !leavesLayoutOpen"),
        "rationale": (
            "DEFENDS C1 (`out = true`) on M1: a correct impl expressing the "
            "closed-layout flag as the negation of the open-layout flag through "
            "a named local rather than as the flag itself. Same value, different "
            "shape, no proof scaffolding dropped — MUST verify, else C1 is "
            "SPEC-TOO-STRONG (over-fit to the literal code form). Ports the "
            "nagini pos-control shape onto M1, whose nagini counterpart "
            "(trait_pins_closed_layout) has the same constant contract."
        ),
    },
    {
        "id": "pos-control-ns-branch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: branch EXPLICITLY on the chain predicate and return the two
        # boolean literals, instead of routing through the named namespace
        # predicate. Logically identical to gold (`instanceAdmitsNamespace` is
        # `!allClosedLayout`), and the trait flag is inlined into the chain
        # rather than bound to a local first.
        "module": _ns(
            "    let chain : List Bool := others ++ [true]\n"
            "    if allClosedLayout chain then\n"
            "      return false\n"
            "    else\n"
            "      return true"),
        "rationale": (
            "DEFENDS C2 and C3 on M2: a correct impl that branches explicitly "
            "on the chain's all-closed predicate and returns the two literals, "
            "instead of routing through the named namespace predicate, and "
            "inlines the contributing flag into the chain rather than binding it "
            "to a local. Logically identical to gold; the frozen proof closes "
            "as-is. Ports the nagini pos-control-bind argument (reorder the "
            "branch, route through the named predicate the other way round) "
            "onto this method. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-bind-via-ns",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: instead of computing the binding outcome from the chain
        # directly, CALL the sibling contracted method for the namespace
        # decision and map its answer to the two outcomes. This is the
        # callee-under-spec shape (spec_guide §3): the caller's proof applies
        # the callee's own contract. The residual goal is then stated in the
        # named namespace predicate, so that predicate's unfold joins the
        # existing simp set — a retune of the ELIDED tactic body only; the
        # `prove_correct coreBindUndeclared` obligation header is byte-identical
        # and no lemma, axiom or `sorry` is added.
        "module": _bind(
            "    let admits ← coreInstanceAdmitsNamespace others\n"
            "    if admits then\n"
            "      return Except.ok true\n"
            "    else\n"
            "      return Except.error AttrError.bindingRefused",
            "prove_correct coreBindUndeclared by\n"
            "  loom_solve\n"
            "  all_goals simp_all [bindUndeclared, instanceAdmitsNamespace,\n"
            "    allClosedLayout_append, allClosedLayout]"),
        "rationale": (
            "DEFENDS C4 and C5 on M3, and additionally that C2/C4 are mutually "
            "CONSISTENT: a correct impl that obtains the namespace decision from "
            "the sibling contracted method and maps it to the two outcomes, "
            "rather than deriving the outcome from the chain itself "
            "(callee-under-spec). It consumes only the callee's own contract, so "
            "if the two clauses disagreed anywhere this could not verify. MUST "
            "verify, else SPEC-TOO-STRONG. Ports the nagini pos-control-bind "
            "(route through the named namespace predicate instead of the bare "
            "fold) at method granularity."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-open-chain. That case
    # built an open chain, CALLED the load-bearing function and asserted a
    # normal (non-raising) return, establishing the success path is LIVE under
    # nagini's `Requires`. Here no method carries a `require` at all (the
    # pre-conditions regions are empty), so nothing could exclude an input and
    # the "the precondition admits this input" half is vacuous. What remains is
    # the joint-satisfiability half: that the five-clause post-image across the
    # three methods can all be discharged by one gold-shaped computation over a
    # TOTAL domain. The frozen impl doing so IS that witness.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        # NOT the frozen impl. Shipping `_BASE` here would make this case a
        # restatement of G-VERIFY ("the frozen file verifies") and it would pass
        # without testing anything the frozen bundle does not already attest.
        # Instead: all THREE impls reshaped SIMULTANEOUSLY, none of them the
        # frozen text, each on the shortest independent route to its own clauses
        # — M1 via a negated open-layout flag, M2 and M3 dropping the explicit
        # `chain` local and deciding on `others` directly (sound because the
        # appended flag is `true`, the conjunction's identity). Joint
        # satisfiability then has to survive three simultaneous shape changes
        # rather than being read off the frozen file.
        "module": _bind(
            "    if allClosedLayout others then\n"
            "      return Except.error AttrError.bindingRefused\n"
            "    else\n"
            "      return Except.ok true",
        ).replace(_IMPL_MIXIN,
                  # The joint-satisfiability discharge, at TWO concrete
                  # F2P-shaped chains, BY EVALUATION, before the frozen
                  # obligation is closed. This is what makes the case test
                  # satisfiability-at-a-point rather than only "some reshape
                  # verifies": each `have` states what a clause DEMANDS at a
                  # named input and closes it by computation, so a clause that
                  # was unsatisfiable at that input — the total-carrier analogue
                  # of PRECOND-TOO-STRONG — would fail here even though the
                  # universally quantified obligation still closed.
                  "    -- All-closed chain (the value type's actual shape): the\n"
                  "    -- instance carries NO open namespace and the undeclared\n"
                  "    -- binding is refused. C2/C3 and C4/C5 at that point.\n"
                  "    have _h_closed_ns :\n"
                  "        instanceAdmitsNamespace ([true, true] ++ [true]) = false := by\n"
                  "      decide\n"
                  "    have _h_closed_ac : allClosedLayout [true, true] = true := by decide\n"
                  "    have _h_closed_bind : bindUndeclared ([true, true] ++ [true])\n"
                  "        = Except.error AttrError.bindingRefused := by\n"
                  "      simp [bindUndeclared, allClosedLayout]\n"
                  "    -- Open chain: the OTHER outcome of each clause is live too,\n"
                  "    -- so neither obligation is satisfiable only degenerately.\n"
                  "    have _h_open_ns :\n"
                  "        instanceAdmitsNamespace ([true, false] ++ [true]) = true := by\n"
                  "      decide\n"
                  "    have _h_open_bind :\n"
                  "        bindUndeclared ([true, false] ++ [true]) = Except.ok true := by\n"
                  "      simp [bindUndeclared, allClosedLayout]\n"
                  "    let leavesLayoutOpen := false\n"
                  "    return !leavesLayoutOpen", 1
                  ).replace(_IMPL_NS, "    return !allClosedLayout others", 1),
        "rationale": (
            "No method carries a `require`, so the "
            "precondition-admits-this-input half of the nagini "
            "admiss-open-chain has no literal counterpart. The analogue on a "
            "TOTAL carrier is the obligation being unsatisfiable at an "
            "F2P-shaped input, and this case tests that DIRECTLY rather than "
            "only by reshaping: the impl region discharges, BY EVALUATION as "
            "`have`s and before the frozen obligation is closed, what each "
            "clause demands at two concrete chains — the all-closed chain "
            "`[true, true]` (the value type's actual shape: C2/C3 demand no "
            "open namespace, C4/C5 demand the refusal outcome) and an open "
            "chain `[true, false]` (the opposite outcome of each clause, so "
            "neither is satisfiable only degenerately). If any clause were "
            "unsatisfiable at those points, or if C2/C4 conflicted with their "
            "C3/C5 instantiations there, those evaluations could not close even "
            "though the universally quantified obligation still did. On top of "
            "that, all three impls are reshaped simultaneously and none is the "
            "frozen text, so joint satisfiability is witnessed by a computation "
            "that shares no impl-region text with the frozen one. Else "
            "SPEC-UNSATISFIABLE / PRECOND-TOO-STRONG."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. Every obligation is ATTACKED; the
    # `others` binder is varied across [], [true], [false] and [true, false].
    # =====================================================================
    {
        "id": "rival-mixin-leaves-open",
        "kind": "uniqueness",
        "expect": "reject",
        # The shared contributing type leaves its instance layout OPEN. This is
        # the pre-change shape verbatim (it is Solution_prepatch's M1 body) and
        # the F2P discrimination anchor of refinement.md §D.
        "module": _mixin("    return false"),
        "refinement": (
            "The shared contributing type leaves its instance layout open. Its "
            "faithful real patch is the unpatched repo: the shared contributor "
            "declares no closed slot set, so every instance built through it "
            "acquires an open per-instance namespace, the failing test's "
            "assertion that the instance carries no such namespace is false, and "
            "binding an undeclared name silently succeeds instead of being "
            "refused. It would NOT resolve — this is exactly the reported defect."
        ),
        "rationale": (
            "REJECT from C1 (`out = true`): the constant pin admits only the "
            "closed-layout flag, so returning the open-layout flag contradicts "
            "it outright. Refuted by witness on the nullary method (no input to "
            "vary — M1 takes none). Ports the nagini reject-trait-false, the "
            "load-bearing soundness anchor for the whole F2P (refinement.md §D). "
            "If it VERIFIED => SPEC-TOO-WEAK (the anchor unpinned, and the "
            "prepatch admitted)."
        ),
        "witness": _w_mixin(),
    },
    {
        "id": "rival-ns-open-contributor",
        "kind": "uniqueness",
        "expect": "reject",
        # The namespace decision is computed over a chain whose appended
        # contributing flag is OPEN rather than closed — the pre-change chain.
        "module": _ns(
            "    let trait := false\n"
            "    let chain : List Bool := others ++ [trait]\n"
            "    return instanceAdmitsNamespace chain"),
        "refinement": (
            "Computes the namespace decision over a chain whose appended "
            "contributing flag is open — the pre-change chain. Its faithful real "
            "patch is the unpatched repo, where the instance DOES carry an open "
            "namespace, so the failing test's assertion that the instance "
            "exposes no such namespace is false. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 (`out = instanceAdmitsNamespace (others ++ "
            "[true])`) and from C3 (which pins `false` on the all-closed "
            "sub-domain): on an all-closed `others` the rival's chain still "
            "contains an open flag, so it reports an open namespace where the "
            "spec demands none. Refuted at `others = [true]` — the actual repo "
            "shape. Ports the nagini reject-always-true (the reported "
            "regression: binding always succeeds) onto the namespace observable. "
            "If it VERIFIED => SPEC-TOO-WEAK (the prepatch chain admitted)."
        ),
        "witness": _w_ns("[true]"),
    },
    {
        "id": "rival-ns-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the namespace decision: report an open namespace exactly when
        # every contributing type pins a closed layout, and none otherwise.
        "module": _ns(
            "    let chain : List Bool := others ++ [true]\n"
            "    return allClosedLayout chain"),
        "refinement": (
            "Inverts the namespace decision: reports an open per-instance "
            "namespace exactly when every contributing type pins a closed "
            "layout, and none when some type leaves its layout open. A faithful "
            "real patch with this behavior reports the namespace absent for the "
            "very types that legitimately keep one, breaking ordinary dynamic "
            "attribute use on open-layout types (PASS_TO_PASS behavior), while "
            "reporting it present for the fully-pinned value type the failing "
            "test observes. It would NOT resolve and would regress other tests."
        ),
        "rationale": (
            "REJECT from C2: the post-image is the NEGATION of the all-closed "
            "conjunction, so returning the conjunction itself diverges wherever "
            "the two differ — which, `Bool` being two-valued, is at EVERY "
            "`others`. Refuted at `others = [false]`: a chain with one open "
            "contributor, where the spec demands an open namespace and the rival "
            "reports none. A distinct WITNESS POINT from "
            "rival-ns-open-contributor (`[true]`), chosen so the four reject "
            "witnesses on this binder cover four different inputs; this rival is "
            "wrong at `[true]` too, and also violates C3 there (measured: the "
            "witness at `[true]` elaborates against this rival, and the "
            "agreement claim `= ` at `[true]` is refuted). It is a "
            "whole-domain inversion, NOT a near-miss. Ports the nagini "
            "reject-invert-branch onto the namespace observable. If it VERIFIED "
            "=> SPEC-TOO-WEAK (C2's direction unpinned)."
        ),
        "witness": _w_ns("[false]"),
    },
    {
        "id": "rival-ns-empty-chain",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: correct on every non-empty `others`, but reports an
        # open namespace when `others` is empty.
        "module": _ns(
            "    let chain : List Bool := others ++ [true]\n"
            "    if others.isEmpty then\n"
            "      return true\n"
            "    else\n"
            "      return instanceAdmitsNamespace chain"),
        "refinement": (
            "Correct on every non-empty chain of other contributors but reports "
            "an open namespace when there are none — the degenerate layout whose "
            "only contributor is the shared one. A faithful real patch of this "
            "shape lets a fully-pinned instance with no other contributing types "
            "be reported as carrying an open namespace, contradicting the "
            "immutability the failing test pins on exactly such a layout, so it "
            "would NOT resolve on that boundary."
        ),
        "rationale": (
            "PARTIAL-DOMAIN miss rejected by C2: with `others = []` the chain is "
            "the single closed contributing flag, so `instanceAdmitsNamespace` "
            "is `false` and reporting `true` contradicts the post-image. Also "
            "violates C3 (`allClosedLayout [] = true`, so the spec demands "
            "`false` there). Refuted at `others = []` — the empty boundary, a "
            "third distinct point for this binder. Ports the nagini "
            "reject-empty-domain. If it VERIFIED => SPEC-TOO-WEAK "
            "(domain-incomplete at the degenerate chain)."
        ),
        "witness": _w_ns("[]"),
    },
    {
        "id": "rival-ns-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult only the FIRST other contributor and ignore the rest of the
        # chain. Agrees with gold on every `others` of length <= 1 (so on the
        # actual repo shape) and diverges only when a later contributor leaves
        # its layout open — the genuine partial-domain break.
        "module": _ns(
            "    let chain : List Bool := others.take 1 ++ [true]\n"
            "    return instanceAdmitsNamespace chain"),
        "refinement": (
            "Consults only the most-derived other contributing type and ignores "
            "the rest of the chain. A faithful real patch of this shape checks "
            "the type's own layout declaration but not its inherited ones, so an "
            "instance whose OPEN layout comes from a deeper contributor is "
            "reported as carrying no namespace — the class of defect the issue "
            "describes (a layout re-opened by a contributor other than the "
            "type itself). It agrees with the fixed behavior on the value type's "
            "actual two-entry chain, so it would look right there while leaving "
            "the general rule broken; on any deeper open layout it reports the "
            "wrong answer, so it would NOT resolve as a correct fix."
        ),
        "rationale": (
            "REJECT from C2, which quantifies `others` UNIVERSALLY: truncating "
            "the chain to its head diverges from `instanceAdmitsNamespace "
            "(others ++ [true])` at any `others` whose openness lies past "
            "position 0. Refuted at `others = [true, false]` — a fourth distinct "
            "point, and the only one whose length exceeds 1, so it is the "
            "witness that exercises C2's dependence on the chain TAIL rather "
            "than on its head. NOT shared with any other rival: this is a "
            "near-miss that agrees with gold on every shorter chain, including "
            "the actual repo shape, so it is refuted precisely where it "
            "diverges. If it VERIFIED => SPEC-TOO-WEAK (the chain quantifier "
            "collapsed to its head)."
        ),
        "witness": _w_ns("[true, false]"),
    },
    {
        "id": "rival-ns-never-admits",
        "kind": "uniqueness",
        "expect": "reject",
        # Under-reporting: the instance is reported as carrying NO open
        # namespace, whatever the contributing types' layouts. This is M2's
        # analogue of rival-bind-always-refuse and the ONLY M2 rival that is
        # correct on the WHOLE all-closed sub-domain — so C3 cannot see it and
        # only C2 can. Measured: the agreement claim `=` holds against this
        # rival at both `others = [true]` and `others = []` (exit 0 each), i.e.
        # it matches gold everywhere C3 constrains.
        "module": _ns("    return false"),
        "refinement": (
            "Reports that no instance ever carries an open per-instance "
            "namespace, whatever the contributing types' layouts. A faithful "
            "real patch of this shape reports the namespace absent even for the "
            "types that legitimately keep one, so ordinary dynamic attribute use "
            "on open-layout types is misreported (PASS_TO_PASS behavior) even "
            "though the failing test's own assertion on the fully-pinned value "
            "type happens to hold. It is not a correct fix and would regress "
            "other tests."
        ),
        "rationale": (
            "REJECT from C2 alone: on an `others` containing an open flag the "
            "post-image is `true`, so a constant `false` contradicts it. This is "
            "the M2 case that shows C2 does work BEYOND its C3 instantiation — "
            "C3 constrains only the all-closed sub-domain, where `false` is "
            "exactly right, so C3 could not catch this rival at all (measured: "
            "it AGREES with gold at `others = [true]` and `others = []`). Its "
            "M3 counterpart is rival-bind-always-refuse; without this case the "
            "same property of C2 was attacked on the binding observable only, "
            "and M2's universal quantifier was never separated from its "
            "instantiation. Refuted at `others = [false]`. If it VERIFIED => "
            "SPEC-TOO-WEAK (C2 collapsed into C3)."
        ),
        "witness": _w_ns("[false]"),
    },
    {
        "id": "rival-bind-open-contributor",
        "kind": "uniqueness",
        "expect": "reject",
        # The binding outcome is computed over a chain whose appended
        # contributing flag is OPEN — the pre-change chain, on the binding
        # observable.
        "module": _bind(
            "    let trait := false\n"
            "    let chain : List Bool := others ++ [trait]\n"
            "    return bindUndeclared chain"),
        "refinement": (
            "Computes the binding outcome over a chain whose appended "
            "contributing flag is open — the pre-change chain. Its faithful real "
            "patch is the unpatched repo: binding an undeclared attribute name "
            "on an instance of the value type is ABSORBED instead of refused, so "
            "the failing test's expectation that such a binding raises is not "
            "met. It would NOT resolve — the reported regression, on the binding "
            "observable."
        ),
        "rationale": (
            "REJECT from C4 (`out = bindUndeclared (others ++ [true])`) and from "
            "C5 (which pins the refusal outcome on the all-closed sub-domain): "
            "on an all-closed `others` the rival's chain still contains an open "
            "flag, so it absorbs the binding where the spec demands refusal. "
            "Refuted at `others = [true]` — the actual repo shape. Ports the "
            "nagini reject-always-true onto the binding observable. If it "
            "VERIFIED => SPEC-TOO-WEAK (the prepatch chain admitted)."
        ),
        "witness": _w_bind("[true]"),
    },
    {
        "id": "rival-bind-always-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-refusal: the binding is refused unconditionally, ignoring the
        # chain entirely.
        "module": _bind("    return Except.error AttrError.bindingRefused"),
        "refinement": (
            "Refuses the binding unconditionally, whatever the contributing "
            "types' layouts. A faithful real patch that refuses every undeclared "
            "attribute binding regardless of layout breaks ordinary dynamic "
            "attribute use on the types that legitimately keep an open "
            "per-instance namespace (PASS_TO_PASS behavior), so it is not a "
            "correct fix and would regress other tests even while the failing "
            "test's own assertion happened to hold."
        ),
        "rationale": (
            "REJECT from C4: on an `others` containing an open flag the "
            "post-image is the absorbed-binding outcome, so an unconditional "
            "refusal contradicts it. Note C5 alone would NOT catch this rival — "
            "it constrains only the all-closed sub-domain, where refusal is "
            "correct — so this case is what shows C4 (the universally quantified "
            "clause) is doing work beyond its instantiation. Refuted at `others "
            "= [false]`. Ports the nagini reject-always-raise. If it VERIFIED => "
            "SPEC-TOO-WEAK (C4 collapsed into C5)."
        ),
        "witness": _w_bind("[false]"),
    },
    {
        "id": "rival-bind-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the binding decision: absorb when every contributing type pins
        # a closed layout, refuse when some type leaves its layout open.
        "module": _bind(
            "    let chain : List Bool := others ++ [true]\n"
            "    if allClosedLayout chain then\n"
            "      return Except.ok true\n"
            "    else\n"
            "      return Except.error AttrError.bindingRefused"),
        "refinement": (
            "Inverts the binding decision: absorbs the binding exactly when "
            "every contributing type pins a closed layout, and refuses it when "
            "some type leaves its layout open. A faithful real patch with this "
            "behavior lets the fully-pinned value type accept an arbitrary "
            "attribute binding — so the failing test's expectation that such a "
            "binding raises is not met — while refusing bindings on the "
            "open-layout types that should accept them. It would NOT resolve, "
            "and would regress other tests."
        ),
        "rationale": (
            "REJECT from C4 and C5: the spec refuses iff the whole chain is "
            "closed, so swapping the two outcomes diverges on BOTH sub-domains. "
            "Refuted at `others = [false]`, shared with rival-bind-always-refuse "
            "— and legitimately so: at that input both rivals refuse a binding "
            "the spec absorbs, the same failure for the same reason. They are "
            "distinguished elsewhere (this rival absorbs on the all-closed "
            "chain, where the other correctly refuses), and that sub-domain is "
            "covered by rival-bind-open-contributor's witness at `[true]`. Ports "
            "the nagini reject-invert-branch onto the binding observable. If it "
            "VERIFIED => SPEC-TOO-WEAK (C4's direction unpinned)."
        ),
        "witness": _w_bind("[false]"),
    },
    {
        "id": "rival-bind-empty-chain",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: correct on every non-empty `others`, but absorbs the
        # binding when `others` is empty.
        "module": _bind(
            "    let chain : List Bool := others ++ [true]\n"
            "    if others.isEmpty then\n"
            "      return Except.ok true\n"
            "    else\n"
            "      return bindUndeclared chain"),
        "refinement": (
            "Correct on every non-empty chain of other contributors but absorbs "
            "the binding when there are none — the degenerate layout whose only "
            "contributor is the shared one. A faithful real patch of this shape "
            "lets a fully-pinned instance with no other contributing types "
            "accept an undeclared attribute binding, contradicting the "
            "immutability the failing test pins on exactly such a layout, so it "
            "would NOT resolve on that boundary."
        ),
        "rationale": (
            "PARTIAL-DOMAIN miss rejected by C4: with `others = []` the chain is "
            "the single closed contributing flag, so `bindUndeclared` refuses "
            "and absorbing contradicts the post-image. Also violates C5 "
            "(`allClosedLayout [] = true`). Refuted at `others = []` — the empty "
            "boundary. Ports the nagini reject-empty-domain onto the binding "
            "observable. If it VERIFIED => SPEC-TOO-WEAK (domain-incomplete at "
            "the degenerate chain)."
        ),
        "witness": _w_bind("[]"),
    },
    {
        "id": "rival-bind-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult only the FIRST other contributor for the binding decision and
        # ignore the rest of the chain.
        "module": _bind(
            "    let chain : List Bool := others.take 1 ++ [true]\n"
            "    return bindUndeclared chain"),
        "refinement": (
            "Consults only the most-derived other contributing type when "
            "deciding the binding and ignores the rest of the chain. A faithful "
            "real patch of this shape refuses the binding based on the type's "
            "own layout declaration while ignoring an inherited open layout, so "
            "an instance that really does carry an open namespace from a deeper "
            "contributor would refuse a binding it must absorb — the mirror of "
            "the class of defect the issue describes. It agrees with the fixed "
            "behavior on the value type's actual two-entry chain, so it would "
            "look right there while leaving the general rule broken, and would "
            "NOT resolve as a correct fix."
        ),
        "rationale": (
            "REJECT from C4, which quantifies `others` UNIVERSALLY: truncating "
            "the chain to its head diverges from `bindUndeclared (others ++ "
            "[true])` at any `others` whose openness lies past position 0. "
            "Refuted at `others = [true, false]` — the only binding-side witness "
            "whose chain exceeds length 1, so it is what exercises C4's "
            "dependence on the chain TAIL. NOT shared with any other rival: a "
            "near-miss agreeing with gold on every shorter chain, including the "
            "actual repo shape, refuted precisely where it diverges. If it "
            "VERIFIED => SPEC-TOO-WEAK (the chain quantifier collapsed to its "
            "head)."
        ),
        "witness": _w_bind("[true, false]"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
#   nagini case                -> here
#   -----------------------------------------------------------------------
#   reject-trait-false         -> rival-mixin-leaves-open          PORTED
#   reject-always-true         -> rival-ns-open-contributor        PORTED (M2)
#                              -> rival-bind-open-contributor      PORTED (M3)
#   reject-invert-branch       -> rival-ns-inverted                PORTED (M2)
#                              -> rival-bind-inverted              PORTED (M3)
#   reject-always-raise        -> rival-bind-always-refuse         PORTED
#                              -> rival-ns-never-admits            PORTED (M2)
#   reject-empty-domain        -> rival-ns-empty-chain             PORTED (M2)
#                              -> rival-bind-empty-chain           PORTED (M3)
#   pos-control-bind           -> pos-control-ns-branch            RE-SHAPED
#                              -> pos-control-bind-via-ns          RE-SHAPED
#   (no direct sibling)        -> pos-control-mixin                ADDED
#   admiss-open-chain          -> admiss-gold-total                RE-AIMED
#   reject-diverge-bind        -> (none)                           VACUOUS (total)
#   reject-diverge-trait       -> (none)                           VACUOUS (total)
#   (frame-mutation class)     -> (none)                           VACUOUS
#   (no sibling)               -> rival-ns-head-only               ADDED
#   (no sibling)               -> rival-bind-head-only             ADDED
#   AXIOM_TESTS (2)            -> (none)                           DROPPED (G-AX)
#
# 15 velvet SPEC cases: 3 soundness, 1 admissibility, 11 uniqueness, against
# nagini's 9 SPEC cases. The count went UP rather than down because this bundle
# SPLITS nagini's single load-bearing function into two independently contracted
# observables (M2 the namespace decision, M3 the binding outcome), so four of
# nagini's five rivals port TWICE — once per observable — and each half needs its
# own witness.
#
# PORTED (7 rivals, from 5 nagini cases):
#   reject-trait-false -> rival-mixin-leaves-open. Verbatim: it is
#     Solution_prepatch's M1 body, and refinement.md §D names M1's constant pin
#     as THE F2P discrimination anchor. Same argument, same conclusion.
#   reject-always-true -> rival-ns-open-contributor + rival-bind-open-contributor.
#     Nagini's "binding always succeeds" is the reported regression. Here the
#     regression's CAUSE (the appended contributing flag left open) is what the
#     impl region can express, and it has two observable consequences, one per
#     method: the namespace is reported present, and the binding is absorbed. Both
#     ported, each refuted at the actual repo shape `others = [true]`.
#   reject-invert-branch -> rival-ns-inverted + rival-bind-inverted. The branch
#     inversion carries over intact to each observable.
#   reject-always-raise -> rival-bind-always-refuse + rival-ns-never-admits.
#     Over-refusal, PASS_TO_PASS argument preserved. The M2 counterpart is the
#     constant `false` return: M2 has no distinguished error outcome, but the
#     structural property that matters is "constant on the whole of the
#     instantiation clause's sub-domain, wrong only off it", and `return false` has
#     exactly that shape on M2 (measured: it AGREES with gold at `others = [true]`
#     and at `others = []`, the only two all-closed points the battery probes, so
#     C3 cannot see it). An earlier revision of this footer asserted
#     rival-ns-inverted covered this; that was wrong — the inversion is wrong
#     ON the all-closed sub-domain too (measured: the refutation witness at
#     `others = [true]` elaborates against it), so C3 catches it and it never
#     isolated C2's universal quantifier from its instantiation. Ported properly.
#   reject-empty-domain -> rival-ns-empty-chain + rival-bind-empty-chain. The
#     degenerate-boundary partial-domain attack, per observable.
# RE-SHAPED (pos-control-bind -> pos-control-ns-branch + pos-control-bind-via-ns):
#   the nagini positive routes the decision through the NAMED namespace predicate
#   with the branch reordered. Here that maps to two different reshapes, one per
#   method: M2 branches explicitly on the chain predicate instead of routing
#   through the named one (the reorder, the other way round), and M3 obtains the
#   decision by CALLING M2 under its contract (spec_guide §3 callee-under-spec) —
#   which additionally certifies C2 and C4 are mutually consistent, something no
#   nagini case could state because nagini contracts one function where this
#   bundle contracts two. The second retunes the ELIDED tactic body only (adds the
#   frozen `instanceAdmitsNamespace` unfold to the existing simp set); the
#   `prove_correct coreBindUndeclared` header is byte-identical and no lemma,
#   axiom or `sorry` is introduced.
# ADDED (pos-control-mixin): M1 has no nagini positive of its own (nagini's
#   trait_pins_closed_layout impl region is where nagini parked its admissibility
#   caller instead). Without it M1's obligation would be attacked but not
#   DEFENDED, so a spec over-fit to M1's literal code form would go unmeasured.
# ADDED (rival-ns-head-only, rival-bind-head-only): the chain-TRUNCATION rivals.
#   These have no nagini sibling because nagini's `chain` argument is effectively
#   the concrete Basic chain, whereas here `others` is UNIVERSALLY QUANTIFIED
#   (mapping.md §2, chain-shape note) — so "consult only the head" is a rival this
#   carrier admits and nagini's does not. They matter for coverage rather than
#   count: they are the ONLY witnesses whose `others` exceeds length 1, so without
#   them every reject witness would probe a chain of length 0 or 1 and the battery
#   would say nothing about C2/C4's dependence on the chain TAIL — a rival that
#   mishandled only deeper contributors would verify unnoticed. Real divergences
#   with machine-checked witnesses, not fabricated wrongness, and both are
#   NEAR-MISSES that agree with gold on the actual repo shape, so each is refuted
#   at the input where it actually diverges rather than sharing a cheaper witness.
# RE-AIMED (admiss-open-chain -> admiss-gold-total): the nagini case built an open
#   chain, called the load-bearing function and asserted a normal return, showing
#   the success path live under `Requires`. No method here carries a `require`, so
#   the precondition-admits-this-input half is vacuous; re-aimed at the residual
#   total-domain risk, that C1–C5 are JOINTLY satisfiable (general rule vs
#   all-closed instantiation vs constant pin). Its subject is a THREE-METHOD
#   simultaneous reshape, not the frozen impl: an earlier revision shipped `_BASE`
#   verbatim, which made the case a restatement of G-VERIFY — it passed honestly
#   while adding nothing, since "the frozen file verifies" is already recorded by
#   G-VERIFY and G-GOLD. Joint satisfiability is now witnessed by a computation
#   that shares no impl-region text with the frozen one.
#     STRENGTHENED IN AUDIT. The three-method reshape alone still only attested
#   "some non-frozen impl verifies", which is a soundness probe wearing an
#   admissibility label — it could not have failed for the reason this lane
#   exists to detect. The case now ALSO discharges, by EVALUATION as `have`s
#   inside M1's impl region and BEFORE the frozen obligation is closed, what each
#   clause DEMANDS at two concrete F2P-shaped chains: the all-closed `[true,
#   true]` (C2/C3 demand no open namespace; C4/C5 demand the refusal outcome) and
#   the open `[true, false]` (each clause's opposite outcome, so neither is
#   satisfiable only degenerately). That is the total-carrier analogue of
#   PRECOND-TOO-STRONG: a clause unsatisfiable at a named input fails these
#   evaluations even while the universally quantified obligation still closes.
#   Measured: verifies (exit 0), scope-clean. Note `bindUndeclared … = Except.error
#   …` is NOT closable by `decide` here (`failed to synthesize Decidable` — the
#   same missing `Except AttrError Bool` instance the M3 witnesses route around
#   via `Except.toOption`), so those two `have`s close by
#   `simp [bindUndeclared, allClosedLayout]` instead.
# VACUOUS — DIVERGENCE (reject-diverge-bind, reject-diverge-trait): the nagini
#   sibling's P1-repair pair, rejected there by `MustTerminate`. On THIS bundle the
#   class is genuinely vacuous, and NO spec hole is open: the frozen
#   solution sets `set_option loom.semantics.termination "total"`, and a
#   measureless `while` spliced into an impl region is rejected by the verifier
#   with `error: Decreasing annotations are required in total correctness
#   semantics` (re-measured on this bundle, M1's impl region: exit 1, that error
#   plus `Failed to prove assertion without names: WPGen`). A measure-CARRYING
#   spin (`while q > 0 / invariant 0 <= q / done_with q = 0 / decreasing q`, body
#   `q := q`) is rejected too, on the measure's own descent goal:
#   `case «decreasing_1: q»`, residual `q < q`. An earlier version of this line
#   called that the `total` half of a corpus-wide split and pointed at a `partial`
#   cohort admitting the diverging rival. There is no such cohort: all 500 velvet
#   bundles set "total" and open TotalCorrectness, so every one of them rejects it.
#   No reject case is shipped, and the reason is a MEASURED witness limit rather
#   than an argument: a reject case needs a witness refuting the rival at a
#   concrete input, and the natural witness over the diverging M1 body fails
#   against the RIVAL (exit 1) with `Tactic `decide` failed … because its
#   `Decidable` instance instDecidableNot did not reduce to `isTrue` or `isFalse``
#   — the loop elaborates through `Classical.choice`, which the kernel cannot
#   unfold, so the term never reduces and nothing is decided. That is precisely
#   the `witness-undecided` shape the gate screens for, so such a case could not
#   pass and should not be fabricated. Recorded as vacuous with the measurement,
#   not as a dropped case and not as a new hole.
#     RE-DERIVED IN AUDIT, and the un-shippability is now established by the
#   FORGERY test rather than by reading one error: the measureless `while` spliced
#   into M1's impl region is rejected by the verifier (exit 1, `Decreasing
#   annotations are required in total correctness semantics`), confirming the
#   `total` disposition. But the witness cannot carry it — built against the
#   DIVERGING RIVAL, the standard M1 witness and its FLIPPED twin (`≠` swapped for
#   `=`, i.e. the opposite claim) fail with BYTE-IDENTICAL error sets
#   (`Decreasing annotations …` + `Tactic `decide` failed for proposition`). An
#   error that is identical for a claim and its negation carries no information
#   about either, so the rival-side build — the half the gate REQUIRES to succeed
#   — can never succeed here, and `witness_reference` does not help because that
#   substitutes the GOLD-side subject, not the rival-side one. Hence: the class is
#   correctly dispositioned as vacuous-under-`total` (the verifier rejects the
#   rival for a reason internal to the spec, so there is no hole), and it is
#   un-shippable as a reject CASE for a reason that is measured, not argued.
# VACUOUS — FRAME/PERMISSION MUTATION: the nagini sibling ships NO such rival
#   either, and says why in its own docstring: all its inputs are pure immutable
#   value sequences with no read-only heap permission, so `has_readonly_input` is
#   False there already. Here the same holds a fortiori — Velvet is referentially
#   transparent, `others` is an immutable value, no method declares a `mut`
#   parameter, and there is no heap, aliasing or permission system to subvert. No
#   substitute fabricated.
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness and axiom-containment
#   probes over the deep object-model rule (the A-reference) are G-AX's job
#   (axiom_check.py, mapping.md §3); the G-PBT gate ignores AXIOM_TESTS regardless.
#
# NO nagini SPEC case was dropped for being hard to prove, and no soundness
# positive was dropped: all three positives and the admissibility case verify.
#
# CLAUSE / BINDER / POINT COVERAGE.
#   Obligations: all three are DEFENDED (pos-control-mixin / -ns-branch /
#     -bind-via-ns, plus admiss-gold-total on all three) and ATTACKED
#     (rival-mixin-leaves-open on M1; five rivals on M2; five on M3).
#   Clauses: C1 attacked by rival-mixin-leaves-open. C2 attacked by all five M2
#     rivals; C3 additionally by rival-ns-open-contributor, rival-ns-inverted and
#     rival-ns-empty-chain (all three violate the all-closed instantiation, not
#     just the general rule — for rival-ns-inverted this was MEASURED, the
#     refutation witness at `others = [true]` elaborating against it). C4 attacked
#     by all five M3 rivals; C5 additionally by rival-bind-open-contributor,
#     rival-bind-inverted and rival-bind-empty-chain.
#     The pair that shows the universally quantified clause does work BEYOND its
#     instantiation is rival-ns-never-admits (C2 beyond C3) and
#     rival-bind-always-refuse (C4 beyond C5): each is correct on the whole of the
#     instantiation's sub-domain and wrong only off it, so the instantiation clause
#     alone cannot reject it. Both halves are measured; before rival-ns-never-admits
#     was added only the M3 half was, and the M2 half was claimed rather than shown.
#   Binder: `others` is the sole input binder (M1 takes none) and the reject
#     witnesses vary it over FOUR distinct points — `[]` (empty boundary),
#     `[true]` (the actual repo shape, all-closed), `[false]` (an open
#     contributor) and `[true, false]` (length > 1, openness in the TAIL). No
#     witness holds it fixed; in particular the length-2 point exists precisely so
#     C2/C4's dependence on the chain tail is measured. M1's witness has no
#     argument to vary because M1 has no input — not a pinned binder.
#
# WITNESS MECHANICS: every witness uses `extract_program_for` and refutes the
#   load-bearing clause directly against the TRANSPARENT post-image at one concrete
#   input; every rival is loop-free so its `…Exec` reduces under `decide`, and the
#   M3 witnesses project both sides through `Except.toOption` because `Except
#   AttrError Bool` has no `DecidableEq` instance in this workspace (measured:
#   `failed to synthesize Decidable (Except.ok true ≠ Except.error
#   AttrError.bindingRefused)`). No witness binds a hypothesis, so no consistency
#   probe applies and none can be inconsistent. All ELEVEN checked out of band with
#   scripts/lean_verify.sh: each ELABORATES against its rival (exit 0) and FAILS
#   against gold (exit 1, `Tactic `decide` proved that the proposition … is
#   false` — a full semantic refutation with the reduced term printed, never a
#   stuck reduction, a missing identifier or a type error).
#
#   The gold-side exit codes carry information IN BOTH DIRECTIONS on this carrier,
#   which is the check that separates a real discriminator from a tactic mismatch:
#   flipping a witness's `≠` to `=` — claiming gold is CORRECT at the same input,
#   the exact opposite of a refutation — makes it ELABORATE against gold (exit 0)
#   and FAIL against the rival (exit 1). So `decide` genuinely evaluates these
#   claims rather than getting stuck for every claim regardless of truth.
#
#   The tester path (`prove_postcondition_decidable_for` → `derive_tester_for`) is
#   dead on M3 only, and ALIVE on M2 — see the module docstring for the four builds
#   that measure this. It is not used because the extracted-program path is
#   uniformly available on both methods and states the refutation against the
#   post-image the clause itself names; the earlier claim that the tester path was
#   dead on M2 as well was a measurement error (the probe had omitted
#   `extract_program_for`, so it failed on a missing prerequisite rather than on an
#   undecidable postcondition).
AXIOM_TESTS = []
