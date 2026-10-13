"""properties.py — G-PBT falsification battery for astropy__astropy-7671 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct meetsRequirement`` obligation survives with a byte-identical
statement) and swaps in a candidate impl; it is judged by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over three input binders — the available
label ``have_``, the required label ``version``, and the ordering mode
``inclusive``):

    meetsRequirement (have_ : List Char) (version : List Char) (inclusive : Bool)
        return (out : Except CmpErr Bool)
      require  ∀ c ∈ version, c.toNat < 128            -- (PRE) modeled domain: ASCII label
      ensures  out = labelGE have_ (cleanLabel version) inclusive   -- (C) the sole clause

The single load-bearing clause (C) pins the result to the verdict the order
comparison returns for the available label against the required label REDUCED to
its orderable leading portion — never the raw required label, and under the
selected ordering mode. Two carriers meet in that clause and they behave very
differently under the verifier:

  * ``cleanLabel`` is TRANSPARENT — a fully-unfolded ``def`` in the ``pure``
    region (``epochLen``/``segLen``/``digitRun``/``dottedTail``). The
    DISCRIMINATING content of the fix lives entirely in the FIRST ARGUMENT the
    comparison is consulted with: the required label reduced to its orderable
    leading portion (``cleanLabel version``) rather than the raw label. That
    reduction is what the frozen spec pins.

  * ``labelGE`` is OPAQUE — an ``axiom`` with no ``ensures`` (the weakest
    sufficient contract for an UNCHANGED partial ordering callee, directive 7).
    Nothing is claimed about which verdict it returns for any pair; only that
    it is a deterministic function of its three arguments. The ``Except CmpErr
    Bool`` return carries the callee's bool-or-fail partiality.

CARRIER NOTE (decisive for the witness route). The clause is a single
application of an OPAQUE callee, so no witness can COMPUTE the final verdict:
``labelGE …`` never reduces, and nothing may be claimed about which verdict it
returns (directive 7). Every reject witness therefore keeps exactly one
hypothetical step — that the opaque callee separates the two argument tuples
(``labelGE … ≠ labelGE …``), a weak and satisfiable assumption, since the rival
author cannot know the callee agrees there and generically it does not.

But that is the ONLY step left hypothetical, and this is the audit's main
revision to the witness route. The clause's FIRST argument is transparent:
``cleanLabel`` is a fully-unfolded ``def`` and is kernel-COMPUTABLE at literals
(audit build, exit 0: ``decide`` closes ``cleanLabel "0.12dev".toList =
"0.12".toList``). An earlier revision of this manifest stated its witnesses over
free variables and left the reduction to hypothesis too, which discriminated but
under-attested: the witness would have read identically had ``cleanLabel`` been
the IDENTITY and the fix a no-op. Each witness now fixes a concrete input, keeps
the required label at the F2P-shaped ``"0.12dev"``, discharges the ASCII
precondition by ``decide``, and REWRITES ``cleanLabel "0.12dev".toList`` to the
literal ``"0.12".toList`` by ``decide`` before refuting — so the discriminating
input appears in the clear and the reduction is demonstrated, not assumed.

AGREEMENT-POINT DISCIPLINE (the second audit's finding, and the reason the four
witnesses do NOT all name the same available label). `hne` is the one step left
hypothetical, and the gate can only test that it is SATISFIABLE — which on an
opaque callee it always is, since no tactic derives ``False`` from ``labelGE a ≠
labelGE b``. So satisfiability does not distinguish a point where the modeled
operation really separates the two argument tuples from one where it demonstrably
AGREES, and a witness conditioned on agreement-point separation refutes its rival
from a hypothesis false of the operation being modeled. Measured: at the
F2P-shaped available label ``"0.12.2"`` against the reduced required label
``"0.12"`` the modeled ordering callee returns the same verdict in BOTH modes
(the available label is strictly above the required one, hence both at-least and
strictly-above), so that point is an agreement point for the two MODE rivals
though not for the two LABEL rivals. The mode witnesses are therefore stated on
the EQUALITY BOUNDARY (available label ``"0.12"``, equal to the reduced required
label) at the mode literal exposing each rival's wrong arm, where the non-strict
and strict verdicts genuinely differ. Each witness now names a point at which its
own rival's defect is OBSERVABLE, not merely one at which the tactic cannot close
the goal.

Under the remaining hypothesis the rival's answer provably differs from the
spec's required ``labelGE "0.12.2".toList "0.12".toList inclusive``; against
gold the answer IS that term, so the disequality cannot hold and the witness
FAILS on gold. Route as in the structurally-identical opaque-oracle sibling
astropy__astropy-14508 (``triple`` + ``wp_pure``). Each witness's binders are
jointly satisfiable, which the gate's consistency probe confirms by trying (and
failing) to derive ``False`` from them alone; all three required builds were run
per reject case (rival exit 0, gold exit 1, probe exit 1).

GOLD-SIDE FAILURE IS SEMANTIC, and the audit established this by experiment
rather than by reading the message. Every reject case's gold-side error is an
``Application type mismatch`` on ``hne hcon``, which is the most ordinary Lean
error there is and could equally mean the witness is simply malformed. Two
controls settle it. (a) TYPE-REVEAL: replacing the final step with a deliberate
type error (``exact (hcon : Nat)``) prints ``hcon``'s real type on each side, and
the two DIFFER — against gold it is the reflexive ``labelGE … "0.12".toList
inclusive = labelGE … "0.12".toList inclusive``, against each rival it is the
non-reflexive equation the rival actually owes (e.g. ``labelGE … "0.12dev".toList
inclusive = labelGE … "0.12".toList inclusive``). So ``wp_pure`` did reduce on
both sides and gold's hypothesis is genuinely the reflexive one. (b) CLAIM-FLIP:
the forgery that asserts the OPPOSITE — that the triple HOLDS — builds clean
against gold (exit 0) and fails against every rival (exit 1, ensures goal open).
Gold's exit code therefore tracks the claim rather than being constant, which is
precisely what the hollow-signature cases in the corpus lack.

WITNESS MECHANICS. Velvet's tester machinery (``derive_tester_for`` →
``…Tester args = false``) is DEAD here: the method is ``noncomputable`` (it
consults the opaque ``labelGE``) so extraction has no executable code, and the
postcondition's ``Decidable`` instance stalls on the opaque term. Each witness
instead speaks DIRECTLY to the method's Hoare triple. The ``method`` command
opens ``TotalCorrectness DemonicChoice``, so ``triple`` is the total-correctness
triple ``prove_correct`` discharges. Each rival's body is a straight-line
``let … ; return <expr>`` (a ``pure``), so ``wp_pure`` reduces the weakest
precondition to the equality ``<expr> = labelGE have_ (cleanLabel version)
inclusive``, which the separation hypothesis refutes. The witness supplies the
precondition (``hpre``) to the triple so the reduction fires. ``triple`` /
``wp_pure`` come from the frozen ``Velvet.Std`` import; no banned token
(sorry/admit/native_decide/axiom/opaque).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini's mandatory #1 class:
    ``frame-mutate-want`` / ``frame-mutate-have``) — VACUOUS. Those rivals write
    through a fractional (1/2) heap reference to a read-only input and are
    rejected for INSUFFICIENT PERMISSION. This backend is referentially
    transparent: no heap, no aliasing, no fractional permission, and this bundle
    declares NO ``mut`` binder — ``have_`` and ``version`` are immutable values.
    There is no read-only field to overwrite and no substitute probe to build.
    Not fabricated (per the porting map: this class is vacuous on Lean/Velvet).

  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.

  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The result is grounded in the
    method's own inputs: ``labelGE`` applied to ``have_``, the transparent
    ``cleanLabel version``, and ``inclusive`` (directive 8 — a function OF the
    inputs, not a free answer-key). There is no separate oracle a wrong impl
    could echo; the honest cheapest impl (return that expression directly) IS
    gold, carried as a POSITIVE control, not a wrong echo.

  * SOUNDNESS / positive controls — APPLY. A structurally-different but faithful
    impl must still verify against the byte-identical obligation, else the spec
    is SPEC-TOO-STRONG on the shape of the impl. Note the trap this carrier sets
    for the positive lane: because the frozen body is a chain of ``let``s, the
    obvious "different shapes" (inline one ``let``, inline both) are DEFINITIONAL
    reducts, and a lane of nothing but reducts passes honestly while testing no
    proof content. So one positive is deliberately a reshape that is NOT
    definitionally the frozen return (``pos-split-on-mode``).

  * ADMISSIBILITY — RE-AIMED, and REPAIRED during audit. The nagini sibling
    self-calls on F2P-shaped parameters to show the precondition ADMITS a normal
    in-domain input. Here the precondition ``∀ c ∈ version, c.toNat < 128`` (the
    ASCII modeled domain) is non-trivial, and the residual risk is that it is
    over-strong or the post-image unsatisfiable at a real input. The port
    discharged this with the frozen file VERBATIM (an empty diff), which is not
    an admissibility test at all: it restates G-VERIFY and cannot fail while
    G-VERIFY passes, so it could not detect PRECOND-TOO-STRONG — a precondition
    excluding every real input leaves the obligation vacuously dischargeable and
    that case green. The lane now discharges the precondition BY EVALUATION at
    the concrete graded label shapes, and separately REFUTES it at a
    non-ASCII-digit label so the domain is shown to be a real restriction rather
    than ``True`` in disguise, before closing the frozen obligation.
    See ``admiss-precond-admits-f2p-shapes``.

    THIRD AUDIT: that first repair was ITSELF hollow and has been re-repaired.
    Its concrete-input ``have`` carried an author-written precondition which its
    proof ``intro``d and never used, so the frozen ``require`` was never
    consulted: with the frozen precondition made UNSATISFIABLE the case still
    verified at exit 0 — precisely the PRECOND-TOO-STRONG scenario this lane
    exists to detect, passing green. The step now proves the obligation
    generically, instantiates it at the F2P input, and consumes the frozen
    precondition there by ``decide`` to yield a ``triple True``, so the ``decide``
    is the only bridge and the frozen goal is closed from that same generic fact.
    Re-measured: verifies (exit 0), and FAILS (exit 1) under an unsatisfiable
    frozen precondition. Both exit codes are recorded in the case's own note.

  * PARTIAL-DOMAIN uniqueness rivals — APPLY, and all of the nagini shapes are
    represented (see REFINEMENT and the ACCOUNTING footer): they collapse onto
    FOUR observable defects on this carrier, attacking the sole clause's
    dependence on WHICH arguments the opaque callee is consulted with (the
    reduced-vs-raw required label, the operand ROLES, the ordering MODE inverted,
    and the ordering MODE pinned to a literal) — covering all three input binders,
    with the mode binder attacked both bijectively and constantly. The audit
    UN-MERGED the last of these: the port had folded the mode-pinned nagini shape
    into the mode-inverted one, but `labelGE h c false` is constant in the
    `inclusive` binder while `labelGE h c (!i)` still depends on it, so they are
    distinct argument tuples here and nothing collapses them.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file's ``AXIOM_TESTS``
drive the real extractor / ordering callees in Docker; that is G-AX's job
(axiom_check.py / mapping.md) and the G-PBT gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7671"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the three code lines
# ---- strictly inside meetsRequirement's -- impl-start / -- impl-end). Every
# ---- variant replaces exactly this text, so each edit lies wholly inside the
# ---- one elided impl region and same_spec holds by construction. Unique in the
# ---- file (asserted by _swap at load); the frozen spec drifts loudly if the
# ---- Solution.lean ever changes.
_IMPL = (
    "    let cleaned := cleanLabel version\n"
    "    let result := labelGE have_ cleaned inclusive\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "meetsRequirement impl region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY meetsRequirement's impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESS builder.
# ----
# ---- AUDIT REVISION (why this is no longer stated over free variables). The
# ---- earlier builder stated every refutation over the FREE binders `have_
# ---- version inclusive` under the hypothesis `hne : <rival_expr> ≠ labelGE
# ---- have_ (cleanLabel version) inclusive`. That version did discriminate
# ---- (re-measured: rival 0 / gold 1 / probe 1 on all three rivals, and the
# ---- forgery pair below separates), but it left the load-bearing half of the
# ---- clause — that `cleanLabel version` is not `version` — entirely to
# ---- HYPOTHESIS. A reader had to take on trust that the two argument tuples
# ---- `hne` separates are ever actually distinct: with `cleanLabel` a total
# ---- function, `hne` is satisfiable for the trivial reason that nothing is
# ---- claimed about the opaque `labelGE`, so the witness would have read
# ---- identically had `cleanLabel` been the IDENTITY and the fix a no-op.
# ----
# ---- The carrier does not force that. `cleanLabel` is transparent and — as an
# ---- audit build confirmed — kernel-COMPUTABLE at literals: `decide` closes
# ---- `cleanLabel "0.12dev".toList = "0.12".toList` (exit 0). So the reduction
# ---- half is DEMONSTRATED here rather than assumed: each witness fixes the
# ---- F2P-shaped input (available `"0.12.2"`, required `"0.12dev"`), discharges
# ---- the ASCII precondition by `decide`, and rewrites `cleanLabel
# ---- "0.12dev".toList` to the literal `"0.12".toList` by `decide` before the
# ---- refutation. Only the opaque callee's disagreement at the two now-LITERAL
# ---- tuples stays hypothetical, which is the irreducible minimum on an opaque
# ---- carrier (nothing can be claimed about `labelGE`'s verdicts, by directive
# ---- 7). The remaining `hne` mentions the discriminating input in the clear.
# ----
# ---- MECHANICS. `wp_pure` reduces the weakest precondition of the rival's
# ---- `return` to `<rival_expr> = labelGE "0.12.2".toList (cleanLabel
# ---- "0.12dev".toList) inclusive`; the `decide` rewrite turns the RHS into
# ---- `labelGE "0.12.2".toList "0.12".toList inclusive`, which `hne` refutes
# ---- (ELABORATES against the rival). Against gold the return IS that term, so
# ---- the reduced goal is `t = t` and `hne` cannot close it — the witness FAILS
# ---- on gold. Checked in a file whose `prove_correct` block is stripped, so no
# ---- tactic script masks the verdict.
#
# `_HAVE` / `_VER` / `_VER_CLEAN`: the F2P-shaped triple. `_VER_CLEAN` is the
# machine-checked value of `cleanLabel _VER`, not an assumption — the `show ...
# from by decide` step inside each witness re-derives it on every build, so a
# drift in the frozen parser breaks the witness loudly instead of silently.
_HAVE = '"0.12.2".toList'
_VER = '"0.12dev".toList'
_VER_CLEAN = '"0.12".toList'

# ---- SECOND AUDIT REVISION (the AGREEMENT-POINT defect, and why the mode
# ---- rivals now use a different available label from the label rivals).
# ----
# ---- Every witness's remaining hypothesis `hne` asserts that the opaque callee
# ---- SEPARATES two argument tuples at one concrete point. The gate can only ask
# ---- whether `hne` is SATISFIABLE, and on an opaque callee it always is — no
# ---- tactic can derive `False` from `labelGE a ≠ labelGE b`. So the consistency
# ---- probe cannot distinguish a point where the modeled callee really does
# ---- separate the tuples from one where it demonstrably AGREES, and a witness
# ---- conditioned on agreement-point separation refutes its rival from a
# ---- hypothesis that is false of the operation being modeled. The case then
# ---- attests to the tactic's inability to close `f x = f y` for syntactically
# ---- distinct `x`,`y`, not to the clause.
# ----
# ---- This is a real defect and it was measured, not reasoned: at the F2P-shaped
# ---- available label `"0.12.2"` against the reduced required label `"0.12"`, the
# ---- modeled ordering callee returns the SAME verdict in both modes (the
# ---- available label is strictly above the required one, so it is both at-least
# ---- and strictly-above). `hne` for the two MODE rivals is therefore false of
# ---- the callee there in every instantiation of the mode binder, while `hne` for
# ---- the two LABEL rivals is true there (the raw required label is not orderable
# ---- against the available one at all, and the reversed roles invert the
# ---- verdict).
# ----
# ---- Repair: state each witness at a point where its own rival's defect is
# ---- OBSERVABLE. A mode defect is observable exactly on the EQUALITY BOUNDARY —
# ---- available label equal to the reduced required label — where the non-strict
# ---- order is satisfied and the strict one is not. So the mode witnesses move
# ---- the available label to `"0.12"` (still the F2P-shaped required label
# ---- `"0.12dev"`, still reduced by `decide` to `"0.12"`, so the reduction stays
# ---- demonstrated) and instantiate the mode binder to the LITERAL that exposes
# ---- the arm each rival gets wrong: `inclusive := false` for the inverting rival
# ---- (it answers the strict request non-strictly, which the boundary satisfies)
# ---- and `inclusive := true` for the mode-pinned rival (it answers the
# ---- non-strict request strictly, which the boundary does not satisfy).
# ---- Instantiating rather than generalizing is what makes the hypothesis
# ---- checkable against the modeled callee at all: over a free `inclusive` the
# ---- claim is a disjunction across both arms, and on this rival pair only one
# ---- arm is the wrong one.
_EQ_HAVE = '"0.12".toList'          # available label ON the equality boundary


def _witness(rival_expr, have=_HAVE, mode="inclusive", binder="(inclusive : Bool)"):
    """A refutation at one concrete point of clause C.

    `have`/`mode` default to the F2P-shaped available label and a free mode
    binder, which is the right point for a rival whose defect is in the LABEL
    arguments. A rival whose defect is in the MODE must be refuted on the
    equality boundary and at the mode literal that exposes its wrong arm — see
    the revision note above — so those cases pass `have=_EQ_HAVE` and a literal
    `mode`, and drop the binder along with it.
    """
    head = f"example {binder}\n" if binder else "example\n"
    return (
        head
        + f"    (hne : {rival_expr}\n"
        f"        ≠ labelGE {have} {_VER_CLEAN} {mode}) :\n"
        f"    ¬ (triple (∀ c ∈ {_VER}, c.toNat < 128)\n"
        f"        (meetsRequirement {have} {_VER} {mode})\n"
        f"        (fun out => out = labelGE {have} (cleanLabel {_VER}) {mode})) := by\n"
        "  simp only [meetsRequirement, triple]\n"
        "  intro h\n"
        "  have hcon := h (by decide)\n"
        "  rw [wp_pure] at hcon\n"
        f"  rw [show cleanLabel {_VER} = {_VER_CLEAN} from by decide] at hcon\n"
        "  exact hne hcon\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG on the SHAPE of the impl. Each keeps
    # the single `ensures` clause and the frozen `prove_correct meetsRequirement
    # by loom_solve` script; both verified out-of-band with real builds, EXIT 0.
    # The two are deliberately of DIFFERENT strength, and the distinction is the
    # point: `pos-inline-return` is a definitional (zeta) reduct of the frozen
    # body, so it confirms the obligation survives re-elaboration but tests no
    # new proof content; `pos-split-on-mode` is NOT definitionally the frozen
    # return (checked directly: `rfl` does not relate `if i then f true else f
    # false` to `f i`) and so is the control that actually shows the clause is
    # reprovable at a new impl shape. A positive lane containing only reducts
    # would pass honestly while testing nothing, which is why the second slot
    # carries the non-definitional shape.
    # =====================================================================
    {
        "id": "pos-inline-return",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: collapse the two `let` bindings into a single return of the
        # pinned expression. `cleanLabel` is a pure def and `labelGE` a pure
        # function, so this is definitionally the frozen return; `out = labelGE
        # have_ (cleanLabel version) inclusive` still discharges under the frozen
        # `loom_solve`. Ports the nagini pos-delegate-grounded-oracle ARGUMENT
        # (the honest cheapest impl — return the grounded expression directly —
        # must verify).
        "module": _impl("    return labelGE have_ (cleanLabel version) inclusive"),
        "rationale": "PASS SOURCE = clause C. The honest cheapest impl returns the "
                     "pinned expression `labelGE have_ (cleanLabel version) "
                     "inclusive` directly (no intermediate lets). Both callees are "
                     "pure, so this is definitionally the frozen return and the "
                     "clause discharges under the frozen `loom_solve`. Shows the "
                     "spec is not ungrounded-oracle-echo-vulnerable and not "
                     "over-fit to the two-let shape. If it FAILS => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-split-on-mode",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: BRANCH on the ordering mode and consult the comparison with the
        # mode flag instantiated to a LITERAL in each arm. Faithful (each arm
        # supplies exactly the flag its guard establishes) but — unlike a `let`
        # inlining — NOT definitionally the frozen return: the frozen body is
        # `labelGE have_ (cleanLabel version) inclusive` with `inclusive` a free
        # Bool variable, and closing this needs a genuine case analysis on that
        # variable, which no amount of zeta/beta reduction supplies. Verified
        # DIRECTLY (audit build, exit 0) that `rfl` does NOT relate the two
        # returns while the frozen `loom_solve` still discharges the obligation,
        # so this case exercises real proof content rather than reduction. Ports
        # the nagini pos-single-return-reshape ARGUMENT (a structurally different
        # shape must still verify) onto the one binder that admits a genuinely
        # non-definitional faithful reshape here.
        "module": _impl(
            "    if inclusive then\n"
            "      return labelGE have_ (cleanLabel version) true\n"
            "    else\n"
            "      return labelGE have_ (cleanLabel version) false"),
        "rationale": "PASS SOURCE = clause C. A faithful shape that BRANCHES on the "
                     "ordering mode and passes the flag as a literal in each arm. "
                     "Distinct from pos-inline-return in the way that matters: "
                     "inlining a `let` is a definitional (zeta) reduction of the "
                     "frozen body, so it re-tests reduction rather than the spec, "
                     "whereas relating `if inclusive then f true else f false` to "
                     "`f inclusive` requires a genuine case analysis on the Bool "
                     "binder — `rfl` alone does not close it (checked directly). So "
                     "this is the positive control that actually shows the clause is "
                     "reprovable at a NEW impl shape, not merely at a reduct of the "
                     "frozen one. If it FAILS => SPEC-TOO-STRONG (the clause is "
                     "provable only for syntactic reducts of the frozen return).",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-self-call.
    #
    # AUDIT REPAIR. The previous case in this slot was `"module": _BASE` — the
    # frozen file VERBATIM, with an empty diff. It passed honestly and tested
    # nothing this battery does not already own: "the frozen solution verifies"
    # is exactly G-VERIFY's assertion, re-run under a second gate's name, and it
    # cannot fail while G-VERIFY passes. In particular it could not have
    # detected PRECOND-TOO-STRONG, which is the one direction the admissibility
    # lane exists to test: a precondition that excluded every real input would
    # leave the frozen obligation vacuously dischargeable and this case green.
    #
    # The analogue of nagini's self-call on a total carrier (per the audit brief)
    # is to discharge the obligation AT A CONCRETE F2P-SHAPED INPUT, by
    # evaluation, as a `have`, before closing the frozen obligation. That is what
    # this case now does — see the THIRD-AUDIT REPAIR note below for the shape the
    # `have` must take for its `decide` to be load-bearing, which the first
    # attempt got wrong. The carrier permits it: `cleanLabel`
    # is transparent and kernel-computable, so `decide` settles both the
    # precondition and the parser at literals (audit build, exit 0).
    #
    # The `have`s live in the `prove_correct` TACTIC BODY, which the consumer
    # spec view elides, so `same_spec` still holds (mechanically confirmed:
    # `variant_problems` reports NONE for this module) and the frozen obligation
    # is still closed on the frozen impl — the case adds evidence ahead of the
    # obligation, it does not weaken it. The one substantive change the third
    # audit made to the closing step is that `loom_solve` is replaced by `exact
    # hgen have_ version inclusive`, which discharges the SAME frozen goal from
    # the generic fact proven in-body; that is what ties `hgen` to the frozen
    # statement, and it is strictly more constrained than `loom_solve`, not less
    # (a drifted `hgen` fails to typecheck against the goal — measured: a changed
    # frozen `require` makes it a `Type mismatch`). Three things are
    # machine-checked that the empty-diff version left implicit:
    #
    #   (1) NON-VACUITY of the precondition — it is satisfied at each F2P and
    #       PASS_TO_PASS-shaped required label ('0.12', '0.12dev', '1.2rc1') and
    #       at the empty label. A precondition admitting NO input would make the
    #       obligation vacuous; these `decide`s refute that.
    #   (2) The precondition is a REAL restriction, not `True` in disguise: it
    #       is refuted at a required label carrying a non-ASCII decimal digit
    #       (the modeled-domain boundary mapping.md §2.1 records). Both halves
    #       matter — (1) alone is consistent with `require True`, which would
    #       admit inputs the deep model does not track.
    #   (3) The post-image is NON-TRIVIAL at the F2P input: the required label's
    #       orderable leading portion is genuinely SHORTER than the raw label
    #       there (`cleanLabel "0.12dev".toList ≠ "0.12dev".toList`), so the
    #       clause's argument is not the identity on the very input that motivates
    #       the reduction, and the obligation is not satisfiable by ignoring it.
    #
    # THIRD-AUDIT REPAIR — the `have hf2p` above was HOLLOW, and the defect is
    # exactly the one the previous repair set out to close. Its precondition was
    # AUTHOR-WRITTEN text (`triple (∀ c ∈ "0.12dev".toList, c.toNat < 128) ...`),
    # and its proof `intro hpre; rw [wp_pure]` INTRODUCED that hypothesis and then
    # never used it — the postcondition is closed by reduction alone, so the
    # precondition was inert. Two consequences, both machine-measured during this
    # audit rather than argued:
    #
    #   * Replacing that `have`'s precondition with `True` still verified (exit 0),
    #     so the frozen `require` was never consulted.
    #   * The decisive control: making the FROZEN `require` unsatisfiable
    #     (`∀ c ∈ version, c.toNat < 0`) — the literal PRECOND-TOO-STRONG /
    #     vacuous-obligation scenario this lane exists to detect — left the case
    #     GREEN at exit 0. So the lane could not have detected the one thing it
    #     claimed to detect, which is the same hollowness as the empty-diff version
    #     it replaced, one level less obvious.
    #
    # What makes a `decide` load-bearing is that the triple it feeds must have NO
    # remaining precondition to hide behind. So the repaired shape proves the
    # obligation once, generically, as `hgen`; instantiates it at the concrete
    # F2P-shaped input; and derives a triple whose precondition is `True` by
    # supplying the frozen precondition at that input via `exact hinst (by decide)`.
    # Now the `decide` is the only bridge, and the frozen goal is closed by `exact
    # hgen have_ version inclusive` so `hgen` cannot drift from the frozen
    # statement. Re-measured with the same control: the repaired case verifies
    # (exit 0) and, with the frozen `require` made unsatisfiable, FAILS (exit 1).
    # The lane now detects PRECOND-TOO-STRONG.
    #
    # THIRD-AUDIT CONFIRMATION, with one correction to WHICH step catches a
    # PRECOND-TOO-STRONG spec. The repair above was re-derived independently and
    # then attacked with five different over-strong preconditions, and it holds —
    # but it turns out to fail CLOSED in two distinct ways, and the note above
    # named only the second:
    #
    #   * Change the frozen `require` alone (to `∧ False`, to `∀ c ∈ version,
    #     c.toNat < 0`, to `True`, to a clause banning the letter 'd', to a length
    #     bound) and the case fails at the LAST line — `exact hgen have_ version
    #     inclusive` is a `Type mismatch`, because `hgen`'s restatement no longer
    #     matches the frozen goal (exit 1 on all five). That is the drift guard,
    #     and it is why `hgen` is closed into the goal rather than left beside it.
    #   * The `decide` is what catches an over-strong precondition in the case that
    #     actually matters — a battery authored AGAINST such a spec, where `hgen`
    #     restates the over-strong `require` faithfully and so typechecks. Measured
    #     by co-varying both: `Tactic 'decide' proved that the proposition ... is
    #     false` (exit 1) for a precondition excluding the F2P label by letter, by
    #     length, and by an unsatisfiable bound. So the `decide` IS load-bearing,
    #     which is the claim the previous revision made and did not isolate.
    #
    # Both directions were needed to establish it, and neither alone does: the
    # first shows the case cannot drift from the frozen spec, the second shows it
    # would go red at exactly the input the F2P names.
    #
    # MUST verify, else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-precond-admits-f2p-shapes",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl UNCHANGED (this lane must not vary the impl — the question
        # is about the precondition's domain, not about a candidate body). Only
        # the `prove_correct` tactic body gains the evaluated `have`s, which the
        # spec view elides.
        "module": _swap(
            _BASE,
            "prove_correct meetsRequirement by\n  loom_solve",
            "prove_correct meetsRequirement by\n"
            "  -- (1) the modeled domain is NON-EMPTY: the precondition is\n"
            "  -- satisfied at the graded required-label shapes and at the empty\n"
            "  -- label, so the obligation below is not discharged vacuously.\n"
            "  have hadmits : (∀ c ∈ \"0.12\".toList, c.toNat < 128)\n"
            "      ∧ (∀ c ∈ \"0.12dev\".toList, c.toNat < 128)\n"
            "      ∧ (∀ c ∈ \"1.2rc1\".toList, c.toNat < 128)\n"
            "      ∧ (∀ c ∈ (\"\" : String).toList, c.toNat < 128) := by decide\n"
            "  -- (2) ...and it is a REAL restriction, not `True` in disguise:\n"
            "  -- refuted at a required label carrying a non-ASCII decimal digit,\n"
            "  -- the modeled-domain boundary (mapping.md 2.1).\n"
            "  have hrestricts : ¬ (∀ c ∈ \"0.1\\u0669\".toList, c.toNat < 128) := by\n"
            "    decide\n"
            "  -- (3) the post-image is non-trivial AT an in-domain input: the\n"
            "  -- required label's orderable leading portion is strictly shorter\n"
            "  -- than the raw label there, so the clause's first-argument\n"
            "  -- reduction is not the identity where it matters.\n"
            "  have hnontrivial : cleanLabel \"0.12dev\".toList = \"0.12\".toList\n"
            "      ∧ cleanLabel \"0.12dev\".toList ≠ \"0.12dev\".toList := by decide\n"
            "  -- (4) THE ADMISSIBILITY STEP PROPER (see the THIRD-AUDIT REPAIR note\n"
            "  -- below for why it is shaped this way). `hgen` proves the frozen\n"
            "  -- obligation over its own binders and is discharged into the frozen\n"
            "  -- goal by `exact hgen have_ version inclusive` at the end, so it is\n"
            "  -- TIED to the frozen statement rather than being an author-written\n"
            "  -- restatement of it: if the frozen `require` changed, `hgen` would no\n"
            "  -- longer typecheck against the goal.\n"
            "  have hgen : ∀ (h v : List Char) (i : Bool),\n"
            "      triple (∀ c ∈ v, c.toNat < 128) (meetsRequirement h v i)\n"
            "        (fun out => out = labelGE h (cleanLabel v) i) := by\n"
            "    intro h v i\n"
            "    simp only [meetsRequirement, triple]\n"
            "    intro hpre\n"
            "    rw [wp_pure]\n"
            "  -- ...and now the load-bearing half: INSTANTIATE that contract at the\n"
            "  -- concrete F2P-shaped input and CONSUME its precondition BY\n"
            "  -- EVALUATION. The resulting triple has precondition `True`, so the\n"
            "  -- `by decide` is the only thing standing between `hinst` and `hf2p`:\n"
            "  -- a precondition excluding this input makes that `decide` fail and\n"
            "  -- takes the whole case red. THIS is what makes the lane detect\n"
            "  -- PRECOND-TOO-STRONG, and it is machine-measured — see the note.\n"
            "  have hf2p : triple True\n"
            "      (meetsRequirement \"0.12.2\".toList \"0.12dev\".toList true)\n"
            "      (fun out => out = labelGE \"0.12.2\".toList\n"
            "        (cleanLabel \"0.12dev\".toList) true) := by\n"
            "    have hinst := hgen \"0.12.2\".toList \"0.12dev\".toList true\n"
            "    simp only [triple] at hinst ⊢\n"
            "    intro _\n"
            "    exact hinst (by decide)\n"
            "  -- the frozen obligation, closed from `hgen` at its own binders.\n"
            "  exact hgen have_ version inclusive"),
        "rationale": "PASS SOURCE = the precondition ADMITS the modeled domain, is a "
                     "genuine restriction of it, and the frozen contract is "
                     "SATISFIABLE at a concrete graded input with its precondition "
                     "consumed by evaluation. Structure: `hadmits` satisfies the "
                     "precondition at the graded required-label shapes ('0.12', "
                     "'0.12dev', '1.2rc1', empty); `hrestricts` REFUTES it at a "
                     "non-ASCII-digit label, so the modeled domain is a real "
                     "restriction and not `True` in disguise (both halves are needed "
                     "— satisfaction alone is consistent with `require True`, which "
                     "would admit inputs the deep model does not track and would turn "
                     "the on-domain-only impl noted in the footer into a real hole); "
                     "`hnontrivial` evaluates the parser to show the clause's "
                     "first-argument reduction is NOT the identity at the F2P input; "
                     "`hgen` proves the frozen obligation over its own binders and "
                     "`hf2p` instantiates it at `have_ = '0.12.2'`, `version = "
                     "'0.12dev'`, `inclusive = true`, DISCHARGING THE PRECONDITION "
                     "THERE BY EVALUATION. The frozen goal is then closed by `exact "
                     "hgen have_ version inclusive`, which is what ties `hgen` to the "
                     "frozen statement instead of restating it. Everything sits in "
                     "the tactic body, which the spec view elides, so same_spec holds "
                     "and the obligation is unweakened. If any `decide` failed => "
                     "PRECOND-TOO-STRONG (a legitimate in-domain input excluded) or "
                     "SPEC-UNSATISFIABLE. Re-aimed from the nagini self-call probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness
    # stated at the F2P-shaped input (only the opaque callee's disagreement stays
    # hypothetical), and an honest refinement note saying whether its faithful
    # real counterpart resolves. All four attack the sole clause C by consulting
    # the opaque callee with the WRONG argument tuple, and between them they vary
    # EVERY one of the three input binders:
    #   raw `version` in the second operand      -> weak-raw-required-label
    #   `have_`/`version` roles reversed         -> weak-operands-swapped
    #   `inclusive` negated (bijective in it)    -> weak-mode-flag-inverted
    #   mode pinned to a literal (constant in it)-> weak-mode-pinned-strict
    # so no binder of the clause is left unattacked, and the `inclusive` binder is
    # attacked in two inequivalent ways.
    #
    # The two REFINEMENT lanes are kept distinct on purpose: the first two rivals
    # are verify-does-not-imply-resolve discriminators (their faithful real
    # counterparts fail the graded set), the two mode rivals are resolve-PRESERVING
    # spec-pinning probes. An earlier revision claimed all of them broke resolve;
    # the audit measured that and it was false for the mode pair. Retained with
    # the claim corrected rather than dropped, since pinning the mode is still
    # real spec content.
    # =====================================================================
    {
        "id": "weak-raw-required-label",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-patch shape (= Solution_prepatch.lean): consult the order
        # comparison with the RAW required label, skipping the reduction to its
        # orderable leading portion. Correct on every label whose orderable
        # portion IS the whole label, but diverges wherever the label carries
        # trailing annotation — exactly where the fix matters. Ports the nagini
        # rival-no-strip-raw AND rival-keep-marker (both compare against a label
        # still carrying its qualifier tail; on this carrier they collapse to one
        # rival — the loop internals the keep-marker rival edited are now inside
        # the frozen `cleanLabel` def, so editing them would break same_spec).
        "module": _impl(
            "    let result := labelGE have_ version inclusive\n"
            "    return result"),
        "refinement": "the pre-patch code passes the RAW required label to the "
                      "order comparison. On the F2P-added good version '0.12dev' "
                      "(available '0.12.2') the raw comparison fails outright (the "
                      "callee is partial and cannot order a label carrying trailing "
                      "annotation against a purely-numeric one — the reported "
                      "crash), so the failing test, which asserts that comparison "
                      "yields a definite satisfied verdict, does NOT resolve. Its "
                      "faithful real patch IS the base_commit code (no leading-"
                      "portion reduction), which does not resolve. G-DIFF "
                      "discriminator (Solution_prepatch.lean fails the obligation).",
        "rationale": "REJECT from clause C `out = labelGE have_ (cleanLabel "
                     "version) inclusive`: the rival returns `labelGE have_ version "
                     "inclusive` (raw label), which differs from the spec's "
                     "`labelGE have_ (cleanLabel version) inclusive` wherever "
                     "`cleanLabel version ≠ version`. Refuted by conditioning on "
                     "the satisfiable single hypothesis `labelGE have_ version "
                     "inclusive ≠ labelGE have_ (cleanLabel version) inclusive`. "
                     "Against gold the return IS the spec RHS, so `hne` cannot "
                     "close it and the witness fails on gold. If it VERIFIED => "
                     "SPEC-TOO-WEAK (the leading-portion reduction unmodeled).",
        "witness": _witness(f"labelGE {_HAVE} {_VER} inclusive"),
    },
    {
        "id": "weak-operands-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult the order comparison with the two labels in the WRONG ROLES:
        # ask whether the (cleaned) required label meets the available one, rather
        # than whether the available label meets the required one. Reduces the
        # required label correctly but tests the ordering in the wrong direction,
        # so the verdict is inverted on the asymmetric sub-domain. A distinct
        # argument tuple from the raw-label rival (same clause, different binder),
        # so `hne` names a different point (the `have_`/`version` roles are
        # varied). Attacks the clause's dependence on the FIRST vs SECOND operand
        # of the comparison — a binder the raw-label rival holds fixed.
        "module": _impl(
            "    let cleaned := cleanLabel version\n"
            "    let result := labelGE cleaned have_ inclusive\n"
            "    return result"),
        "refinement": "asking whether the required label meets the available one "
                      "(operands reversed) inverts the decision on the asymmetric "
                      "sub-domain. On the F2P (available '0.12.2', required '0.12', "
                      "inclusive) the correct verdict is that the available label "
                      "meets the requirement (satisfied), but the reversed query "
                      "asks whether '0.12' meets '0.12.2' — the opposite, "
                      "unsatisfied — so the good-version assertion FAILS. A faithful "
                      "patch comparing in that reversed direction does NOT resolve.",
        "rationale": "REJECT from clause C: the spec pins `labelGE have_ (cleanLabel "
                     "version) inclusive` (available label against the reduced "
                     "required label), but the rival returns `labelGE (cleanLabel "
                     "version) have_ inclusive` (roles reversed), which differs "
                     "wherever the comparison is not symmetric in its two label "
                     "arguments. Refuted by conditioning on the satisfiable single "
                     "hypothesis `labelGE (cleanLabel version) have_ inclusive ≠ "
                     "labelGE have_ (cleanLabel version) inclusive`. Against gold "
                     "the return IS the spec RHS, so `hne` cannot close it. Varies "
                     "the have_/version binder roles vs weak-raw-required-label. "
                     "If it VERIFIED => SPEC-TOO-WEAK (the operand ORDER of "
                     "the comparison unpinned).",
        "witness": _witness(f"labelGE {_VER_CLEAN} {_HAVE} inclusive"),
    },
    {
        "id": "weak-mode-flag-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Consult the order comparison under the WRONG ordering mode: pass the
        # negated flag, so a non-strict request is answered strictly and vice
        # versa. Reduces the required label correctly and keeps both operands in
        # their correct roles — the ONLY defect is the mode. A distinct argument
        # tuple of clause C that varies the `inclusive` binder, which the label
        # rivals hold fixed; `weak-mode-pinned-strict` varies it the OTHER way
        # (constant rather than inverted).
        "module": _impl(
            "    let cleaned := cleanLabel version\n"
            "    let result := labelGE have_ cleaned (!inclusive)\n"
            "    return result"),
        "refinement": "answering a non-strict request with the strict order (and "
                      "vice versa) diverges exactly where the available label "
                      "EQUALS the reduced required label: the request is then "
                      "satisfied non-strictly but not strictly. "
                      "AUDIT CORRECTION — this rival is RESOLVE-PRESERVING on this "
                      "instance, and the manifest previously claimed otherwise. An "
                      "earlier revision asserted that the library's own import-time "
                      "dependency guard sits on that equality boundary, so an "
                      "inverted mode would raise at import and fail PASS_TO_PASS. "
                      "That claim was MEASURED and is false: the graded environment "
                      "pins the numeric-array dependency well ABOVE every label the "
                      "library asks for, so available != required at every guard and "
                      "the boundary is never reached; and the graded comparison-test "
                      "labels are each strictly below or strictly above the available "
                      "one, so inverting the mode changes no graded verdict either. "
                      "So this rival's faithful real patch DOES resolve, and the case "
                      "is retained on the narrower ground it actually earns: it is a "
                      "SPEC-PINNING probe, showing the frozen clause fixes the "
                      "ordering MODE (the binder no other rival varies), not a "
                      "verify-does-not-imply-resolve discriminator. The nagini ge/gt "
                      "rivals' original 'boundary-invisible' observation was right; "
                      "what does not follow from it is a licence to claim the "
                      "opposite.",
        "rationale": "REJECT from clause C `out = labelGE have_ (cleanLabel "
                     "version) inclusive`: the rival returns `labelGE have_ "
                     "(cleanLabel version) (!inclusive)`, which differs wherever "
                     "the comparison distinguishes its two modes. Refuted by "
                     "conditioning on the satisfiable single hypothesis `labelGE "
                     "have_ (cleanLabel version) (!inclusive) ≠ labelGE have_ "
                     "(cleanLabel version) inclusive`; against gold the return IS "
                     "the spec RHS, so `hne` cannot close it and the witness fails "
                     "on gold with a SEMANTIC type mismatch (`t = t` will not "
                     "inhabit `f (!i) = f i`). Varies the `inclusive` binder, which "
                     "both other rivals hold fixed, so this is the third distinct "
                     "argument tuple of C. If it VERIFIED => SPEC-TOO-WEAK (the "
                     "ordering MODE unpinned — the spec would admit an impl that "
                     "answers the wrong strictness). SECOND-AUDIT REPAIR: the "
                     "witness previously stated `hne` at the F2P-shaped available "
                     "label `\"0.12.2\"`, where the modeled callee returns the SAME "
                     "verdict in both modes — so its hypothesis was FALSE of the "
                     "operation being modeled and the rejection attested to a "
                     "tactic's inability to close `f (!i) = f i` rather than to "
                     "clause C. Restated on the EQUALITY BOUNDARY (available label "
                     "equal to the reduced required label) at `inclusive := false`, "
                     "where the rival answers the strict request non-strictly and "
                     "the two verdicts genuinely differ.",
        "witness": _witness(f"labelGE {_EQ_HAVE} {_VER_CLEAN} (!false)",
                            have=_EQ_HAVE, mode="false", binder=""),
    },
    {
        # ADDED BY AUDIT. Ports the nagini `rival-inclusive-only-gt` shape the
        # port had MERGED away into weak-mode-flag-inverted. The merge was not
        # justified: the two rivals are observably DIFFERENT impls here.
        # `(!inclusive)` inverts the mode (wrong in BOTH directions and, on a
        # `Bool` binder, still a bijection of the flag), whereas this one PINS
        # the mode to the strict literal `false` — it answers a non-strict
        # request strictly and leaves the strict request correct, which is the
        # surgically-minimal nagini shape and a strictly weaker defect. On this
        # carrier they are distinct argument tuples of clause C (`labelGE h c
        # (!i)` vs `labelGE h c false`), so nothing collapses them, and a rival
        # constant in the `inclusive` binder probes something the inverting one
        # cannot: that the clause pins the mode to the binder's VALUE rather
        # than merely to some function of it. Landed with its own machine-
        # checked witness (audit builds: rival exit 0, gold exit 1, consistency
        # probe exit 1).
        "id": "weak-mode-pinned-strict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let cleaned := cleanLabel version\n"
            "    let result := labelGE have_ cleaned false\n"
            "    return result"),
        "refinement": "always consult the STRICT order, ignoring the requested "
                      "mode. Like weak-mode-flag-inverted this is "
                      "resolve-preserving on this instance (measured: the graded "
                      "labels never sit on the equality boundary, and the "
                      "library's own dependency guards run against a pinned "
                      "version far above every label they ask for, so no graded "
                      "verdict changes) — so it too is retained as a "
                      "SPEC-PINNING probe rather than as a "
                      "verify-does-not-imply-resolve discriminator. Its faithful "
                      "real counterpart drops the mode branch and always uses "
                      "`>`, which the documented non-strict semantics forbids "
                      "('the available label is AT LEAST the required one') and "
                      "which any caller relying on the equality case would see.",
        "rationale": "REJECT from clause C `out = labelGE have_ (cleanLabel "
                     "version) inclusive`: the rival returns `labelGE have_ "
                     "(cleanLabel version) false`, discarding the `inclusive` "
                     "binder entirely. Distinct from weak-mode-flag-inverted, "
                     "which applies a bijection to that binder and so still "
                     "DEPENDS on it: this rival is CONSTANT in it, so it is the "
                     "case that shows the clause pins the mode to the binder's "
                     "value and not merely to some invertible function of it. "
                     "Refuted at the F2P-shaped input with the required label's "
                     "reduction discharged by `decide`, under the single "
                     "satisfiable hypothesis that the opaque callee separates "
                     "the strict and requested modes there. Against gold the "
                     "return IS the spec RHS, so `hne` cannot close it. If it "
                     "VERIFIED => SPEC-TOO-WEAK (the clause would admit an impl "
                     "that ignores the requested mode outright). SECOND-AUDIT "
                     "REPAIR: as with weak-mode-flag-inverted, the witness "
                     "previously named the F2P-shaped available label `\"0.12.2\"`, "
                     "at which the modeled callee AGREES across modes, so `hne` was "
                     "false of the modeled operation there. Restated on the "
                     "EQUALITY BOUNDARY at `inclusive := true` — the non-strict "
                     "request the rival answers strictly, which is exactly the arm "
                     "it gets wrong and where the boundary separates the verdicts.",
        "witness": _witness(f"labelGE {_EQ_HAVE} {_VER_CLEAN} false",
                            have=_EQ_HAVE, mode="true", binder=""),
    },
    {
        # ADDED BY THE THIRD AUDIT — the clause's RESULT, which no other shipped
        # rival varies.
        #
        # The gap this closes was visible in the battery's own footer: all four
        # rivals above attack WHICH ARGUMENT TUPLE the opaque callee is consulted
        # with (reduced-vs-raw label, operand roles, mode inverted, mode pinned),
        # and every one of them leaves the callee's RETURN untouched — the impl
        # forwards `labelGE …` verbatim. So the clause's second half, that the
        # result is that verdict RATHER THAN a function of it, had no attacker in
        # the shipped lane. The footer recorded two such probes as having been run
        # out-of-band and correctly rejected, but a probe named in a comment is not
        # a case the gate re-runs; the same reasoning that made the reject lane
        # mandatory applies to a clause feature defended only in prose.
        #
        # The rival keeps the correct argument tuple (correct reduction, correct
        # operand roles, correct mode) and NEGATES the boolean payload while
        # forwarding the failure case untouched, via `Except.map`. That is a
        # minimal, surgical defect: it is not reachable by varying any binder, so
        # it is a genuinely new attack rather than a fifth spelling of the four
        # above. It also exercises the `Except CmpErr Bool` carrier, which is the
        # part of the return type that models the callee's bool-or-fail
        # partiality, and which the four argument-tuple rivals never touch.
        #
        # Audit builds, all four run: rival exit 0, gold exit 1, consistency probe
        # exit 1, and the B'-forgery pair separates (claim-flip: gold exit 0 /
        # rival exit 1), so gold's exit code tracks the claim here exactly as it
        # does for the other four.
        "id": "weak-verdict-payload-negated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let cleaned := cleanLabel version\n"
            "    let result := labelGE have_ cleaned inclusive\n"
            "    return result.map (fun b => !b)"),
        "refinement": "negate the comparison's Boolean verdict while forwarding "
                      "its failure case unchanged. This is a "
                      "verify-does-not-imply-resolve rival of the strongest kind: "
                      "its faithful real counterpart answers every satisfied "
                      "requirement as unsatisfied and vice versa, so on the F2P "
                      "matrix EVERY good-version assertion flips to unsatisfied "
                      "and every bad-version assertion to satisfied — the graded "
                      "set fails wholesale, not marginally. Its defect is also "
                      "orthogonal to the four rivals above: it is invisible to "
                      "any variation of the three input binders, because the "
                      "argument tuple it consults the comparison with is exactly "
                      "the frozen one.",
        "rationale": "REJECT from clause C `out = labelGE have_ (cleanLabel "
                     "version) inclusive`: the rival returns `(labelGE have_ "
                     "(cleanLabel version) inclusive).map (fun b => !b)`, which "
                     "differs from the pinned term wherever the comparison "
                     "returns a verdict at all. Attacks the one feature of the "
                     "clause the other four rivals leave undefended — they all "
                     "vary WHICH arguments the callee is consulted with and "
                     "forward its result verbatim, so the claim that the result "
                     "IS that verdict rather than a function of it had no case "
                     "behind it. Refuted at the F2P-shaped input with the "
                     "required label's reduction discharged by `decide`, under "
                     "the single satisfiable hypothesis that negating the "
                     "payload changes the value there — which is weaker than the "
                     "other rivals' hypotheses, since it is falsifiable only if "
                     "the opaque callee's verdict is its own negation. Against "
                     "gold the return IS the spec RHS, so `hne` cannot close it. "
                     "If it VERIFIED => SPEC-TOO-WEAK (the clause would pin only "
                     "which arguments the comparison is asked about, not what is "
                     "done with its answer).",
        "witness": _witness(
            f"(labelGE {_HAVE} {_VER_CLEAN} inclusive).map (fun b => !b)"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING. The nagini sibling ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) PLUS 2 AXIOM_TESTS,
# contracting ONE function `version_meets_minimum(have, want, inclusive)` over a
# TWO heap-list carrier (`have`/`want` held at fractional Acc(...,1/2)
# permissions) with @Pure helpers `normalize`/`loose_ge`/`loose_gt` FULLY
# UNFOLDED over the inputs and a backward strip loop with load-bearing
# invariants.
#
# CARRIER on velvet. This bundle contracts the SAME behaviour as ONE method
# `meetsRequirement` over three VALUE binders (`have_ : List Char`, `version :
# List Char`, `inclusive : Bool`), pinning the SINGLE clause `out = labelGE have_
# (cleanLabel version) inclusive`. The qualifier-stripping helper `normalize` (+
# the strip loop) is modeled DEEPLY and TRANSPARENTLY as the pure `cleanLabel`
# def; the ordering helpers `loose_ge`/`loose_gt` are collapsed into ONE OPAQUE
# axiom `labelGE … inclusive` (an unchanged callee, weakest contract = none,
# directive 7 — it pins no verdict, so it cannot make a wrong impl verify). The
# `Except CmpErr Bool` return carries the callee's bool-or-fail partiality that
# nagini modeled only as an unmodeled raise.
#
#   nagini case                 kind          -> here                     disposition
#   -----------------------------------------------------------------------------------
#   pos-delegate-grounded-oracle soundness    -> pos-inline-return        PORTED
#   pos-single-return-reshape    soundness    -> pos-split-on-mode        PORTED (re-shaped)
#   admiss-self-call             admissibility -> admiss-precond-admits-f2p-shapes
#                                                                          RE-AIMED (repaired by audit)
#   rival-no-strip-raw           uniqueness   -> weak-raw-required-label   PORTED
#   rival-keep-marker            uniqueness   -> weak-raw-required-label   MERGED (same carrier point)
#   rival-ge-gt-swap             uniqueness   -> weak-mode-flag-inverted   PORTED
#   rival-inclusive-only-gt      uniqueness   -> weak-mode-pinned-strict   PORTED (un-merged by audit)
#   frame-mutate-want            uniqueness   -> (none)                    VACUOUS
#   frame-mutate-have            uniqueness   -> (none)                    VACUOUS
#   (added: wrong operand ROLE)  uniqueness   -> weak-operands-swapped     ADDED
#   (added: wrong RESULT)        uniqueness   -> weak-verdict-payload-negated
#                                                                          ADDED (third audit)
#   AXIOM_TESTS (2)                            -> (none)                   G-AX
#
# 2 ported positives + 1 re-aimed admissibility + (3 ported + 1 merged + 2 added)
# uniqueness = 8 velvet cases (2 soundness + 1 admissibility + 5 uniqueness).
#
# ADDED BY THE THIRD AUDIT (weak-verdict-payload-negated). The four rivals the
#   second audit left all vary WHICH ARGUMENT TUPLE the opaque callee is consulted
#   with and forward its result verbatim, so the clause's other half — that the
#   result IS that verdict rather than some function of it — was defended only in
#   this footer's prose. The footer did record two payload probes as run
#   out-of-band and correctly rejected, but a probe named in a comment is not a
#   case the gate re-runs, and the argument for making the reject lane mandatory
#   applies verbatim to a clause feature whose only attacker is a sentence. Landed
#   as a shipped case with the full four-build evidence set (rival 0 / gold 1 /
#   probe 1, claim-flip gold 0 / rival 1). Its defect is unreachable by varying
#   any of the three input binders, so it is a new attack rather than a fifth
#   spelling of the existing four, and it is the only rival that exercises the
#   `Except CmpErr Bool` carrier that models the callee's bool-or-fail
#   partiality.
#
# PORTED (rival-ge-gt-swap -> weak-mode-flag-inverted) and PORTED, UN-MERGED BY
#   AUDIT (rival-inclusive-only-gt -> weak-mode-pinned-strict). Two corrections
#   here, and they run in opposite directions.
#
#   (a) The RESOLVE claim was wrong and is now retracted in the case's own
#   `refinement`. An earlier revision first dropped both rivals as
#   "resolve-preserving" (they diverge only on the equality boundary, which the
#   graded test never probes — its available label is '0.12.2' and every
#   graded required label is strictly below or strictly above it), then reinstated
#   them on the theory that the library's own import-time dependency guard sits ON
#   that boundary, so an inverted mode would raise at import and fail
#   PASS_TO_PASS. The audit MEASURED that theory against the real callee in the
#   graded environment and it is false: the environment pins the numeric-array
#   dependency far ABOVE every label the library asks for, so available !=
#   required at every guard and the boundary is never reached; inverting the mode
#   changes no graded verdict, F2P or PASS_TO_PASS. So the original
#   "boundary-invisible" observation was right. Both mode rivals are
#   resolve-preserving on this instance and are retained as SPEC-PINNING probes —
#   they show the frozen clause fixes the ordering mode — not as
#   verify-does-not-imply-resolve discriminators. What does not follow from
#   "resolve-preserving" is a licence to claim the opposite, which is the defect
#   the audit actually repaired.
#
#   (b) The MERGE was also wrong, in the other direction: these two nagini shapes
#   do NOT collapse on this carrier. `labelGE h c (!i)` inverts the mode and so
#   still depends on the `inclusive` binder bijectively, whereas `labelGE h c
#   false` is CONSTANT in it — distinct argument tuples of clause C, and the
#   constant one probes something the inverting one cannot (that the clause pins
#   the mode to the binder's VALUE, not merely to some invertible function of it).
#   Both are now shipped, each with its own machine-checked witness (audit builds:
#   rival exit 0 / gold exit 1 / consistency probe exit 1 for each), which also
#   refutes any suggestion that the `inclusive` binder is unattackable here.
#
# PORTED (pos-delegate-grounded-oracle -> pos-inline-return): the honest cheapest
#   impl, returning the whole pinned expression. A definitional (zeta) reduct of
#   the frozen body, so it certifies the obligation survives re-elaboration.
# PORTED, RE-SHAPED (pos-single-return-reshape -> pos-split-on-mode): the nagini
#   case is a genuine structural reshape, and its first velvet rendering (keep
#   one `let`, inline the other) was ANOTHER zeta reduct — a positive lane of
#   nothing but reducts passes honestly while testing no proof content. Replaced
#   with a branch on the ordering mode that passes the flag as a literal per arm:
#   faithful, in scope, verifies under the frozen `loom_solve` (real build), and
#   demonstrably NOT definitional (`rfl` does not relate `if i then f true else
#   f false` to `f i`; checked with a direct build).
# RE-AIMED, REPAIRED BY AUDIT (admiss-self-call ->
#   admiss-precond-admits-f2p-shapes): the nagini self-call re-establishes the
#   fractional-permission + value-fact precondition at a call site. This carrier
#   has no permissions; the analogous residual risk is that the ASCII
#   precondition is over-strong or the post-image unsatisfiable. The port
#   discharged that with the frozen file verbatim, an EMPTY diff — which is
#   G-VERIFY restated and cannot fail while G-VERIFY passes, so the lane detected
#   nothing. The analogue of the self-call on a total carrier is to discharge the
#   obligation at a concrete F2P-shaped input by EVALUATION, as a `have`, before
#   closing the frozen obligation, which the transparent kernel-computable
#   `cleanLabel` makes possible here. Repaired to that shape, plus a refutation of
#   the precondition at a non-ASCII-digit label so the modeled domain is shown to
#   be a real restriction.
#
#   RE-REPAIRED BY THE THIRD AUDIT, because the shape above was hollow in a way
#   only a build could show. The concrete-input `have` stated its own precondition
#   as author-written text and proved its body by `intro hpre; rw [wp_pure]` —
#   which never USES `hpre`, since the postcondition falls out of reduction alone.
#   So the frozen `require` was inert in the very step that was supposed to
#   exercise it. Controls: replacing that precondition with `True` still verified
#   (exit 0), and — decisively — making the FROZEN `require` unsatisfiable
#   (`c.toNat < 0`), i.e. the exact PRECOND-TOO-STRONG / vacuous-obligation
#   scenario, ALSO still verified (exit 0). The lane was green on the one input
#   class it exists to fail on. Repaired by deriving a `triple True` at the F2P
#   input from the generic obligation, so the frozen precondition must be
#   discharged by `decide` to get there, and closing the frozen goal by `exact
#   hgen have_ version inclusive` so the generic fact cannot drift from the frozen
#   statement. Re-measured: verifies (exit 0); under an unsatisfiable frozen
#   `require` it FAILS (exit 1, `decide` proved the proposition false); under a
#   changed frozen `require` the final `exact` fails to typecheck.
# PORTED + MERGED (rival-no-strip-raw + rival-keep-marker -> weak-raw-required-
#   label): both nagini rivals compare against a required label still carrying
#   its qualifier tail — no-strip via the comparison operand, keep-marker via the
#   loop body that fails to discard the marker. On this carrier the loop internals
#   are inside the frozen transparent `cleanLabel` def, so a keep-marker edit
#   would change the `pure` region and BREAK same_spec (a MALFORMED-TESTS scope
#   violation, not a finding). The audit CONFIRMED this mechanically rather than
#   taking it on trust: perturbing the parser's final `version.take (e + r + d)`
#   inside the `pure` region reports `spec view differs (same_spec failed)`, so
#   the merge is forced by the carrier and is not a difficulty dodge. Both
#   collapse to the ONE observable rival —
#   consult `labelGE` with the RAW required label — refuted at the argument tuple
#   where `cleanLabel version ≠ version`. Not an omission for difficulty: the two
#   mechanisms are indistinguishable on this carrier's single opaque clause.
# ADDED (weak-operands-swapped): consult the comparison with the two labels in
#   REVERSED roles (required-meets-available instead of available-meets-required).
#   This varies the `have_`/`version` binder ROLES — the clause's dependence on
#   the FIRST vs SECOND operand — which the raw-label rival holds fixed, so the
#   four reject witnesses probe DISTINCT argument tuples. Its faithful real
#   patch compares in the wrong direction and fails the F2P good-version
#   assertion, so it is a genuine verify-does-not-imply-resolve rival.
# (No uniqueness case is dropped. Of the five, `weak-raw-required-label`,
#   `weak-operands-swapped` and `weak-verdict-payload-negated` are
#   verify-does-not-imply-resolve rivals — their faithful counterparts fail the
#   graded set — while the two mode rivals are resolve-preserving SPEC-PINNING
#   probes, as the audit correction above records. The distinction is stated per
#   case rather than blurred, because a manifest that calls all of them
#   resolve-breaking is making a claim about the graded environment it has not
#   measured.)
# VACUOUS (frame-mutate-want, frame-mutate-have): nagini's MANDATORY #1 class
#   rejects an illegal WRITE through a fractional (1/2) heap reference to a
#   read-only input. This backend is referentially transparent — no heap, no
#   aliasing, no fractional permission — and this bundle declares NO `mut` binder;
#   `have_`/`version` are immutable values. No read-only field to overwrite and no
#   substitute probe. Not fabricated (porting map: vacuous on Lean/Velvet).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# AXIOM_TESTS (2): dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   `cleanLabel` == the real leading-portion extractor and `labelGE` == the real
#   ordering callee); this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. Three input binders — `have_`, `version`, `inclusive`.
#   The sole clause C `out = labelGE have_ (cleanLabel version) inclusive` is
#   DEFENDED (pos-inline-return re-elaborates it; pos-split-on-mode reproves it at
#   a non-definitional shape; the admissibility case shows the precondition admits
#   the graded input shapes, restricts a real domain, and leaves the post-image
#   non-trivial there) and ATTACKED (all four uniqueness rivals). The four reject
#   witnesses, each stated at the F2P-shaped input `have_ = "0.12.2"`, `version =
#   "0.12dev"` with `cleanLabel version` EVALUATED to `"0.12"`, probe four
#   distinct argument tuples of C:
#     labelGE "0.12.2" "0.12dev" inclusive   (weak-raw-required-label: raw label
#                                             in the SECOND operand — attacks the
#                                             reduction, and the only rival whose
#                                             two tuples differ in a term the
#                                             witness computes rather than assumes)
#     labelGE "0.12" "0.12.2" inclusive      (weak-operands-swapped: have_/version
#                                             roles reversed — attacks the operand
#                                             ORDER, varying the have_/version
#                                             binder placement the first rival
#                                             holds fixed)
#     labelGE "0.12" "0.12" (!false)         (weak-mode-flag-inverted: the ordering
#                                             MODE, inverted — depends on the
#                                             `inclusive` binder bijectively.
#                                             Stated on the EQUALITY BOUNDARY at
#                                             `inclusive := false`, not at the
#                                             F2P available label, because that
#                                             label is an AGREEMENT point for the
#                                             two modes — see the header)
#     labelGE "0.12" "0.12" false            (weak-mode-pinned-strict: the mode
#                                             pinned to a literal — CONSTANT in the
#                                             `inclusive` binder, so it pins the
#                                             clause to the binder's value and not
#                                             merely to a function of it. Also on
#                                             the equality boundary, at
#                                             `inclusive := true`, the arm this
#                                             rival gets wrong)
#   and a FIFTH rival attacks the clause's other half — not which arguments the
#   callee is consulted with, but what is done with its answer:
#     (labelGE "0.12.2" "0.12" inclusive).map (!·)
#                                            (weak-verdict-payload-negated, added
#                                             by the third audit: the ARGUMENT
#                                             TUPLE is the frozen one and the
#                                             RESULT is transformed. Unreachable
#                                             by varying any input binder, and the
#                                             only rival that exercises the
#                                             `Except CmpErr Bool` carrier
#                                             modeling the callee's bool-or-fail
#                                             partiality)
#   So every binder of the clause is varied by some rival, the `inclusive` binder
#   in two inequivalent ways, the callee's RESULT is varied by a fifth, and no part
#   of the clause is carried untested. The reject lane is NON-EMPTY, so
#   SPEC-TOO-WEAK is detectable.
#
# SPEC-TOO-WEAK / SPEC-TOO-STRONG probes. The port ran a set of these; the audit
#   re-ran them with real builds and added more. WRONG impls the spec correctly
#   REJECTED (audit builds, each exit 1 with the ensures goal left open, which is
#   a SEMANTIC rejection and not a tactic mismatch): clean the AVAILABLE label
#   too; clean the available label and skip the required one; return a constant
#   verdict `ok true`; return a constant failure; swallow the failure into a
#   verdict via `toOption.getD`; take only the leading segment (`version.take
#   (segLen version)`, dropping the dotted tail); drop the epoch before reducing;
#   reduce only under a vacuous length guard; pass the mode as the literal `true`;
#   answer correctly only for labels longer than three characters. CORRECT
#   reshapes the spec correctly ACCEPTED (exit 0): beta-redex; a second
#   pass-through `let`; `id` around the reduced argument; rebuild the `Except` by
#   `match`; branch on the mode (shipped as pos-split-on-mode).
#
#   AUDIT CORRECTION to a claim this footer used to make. It recorded the
#   double-reduction reshape (`cleanLabel (cleanLabel version)`) as a faithful
#   correct impl that the frozen ONE-LINE script merely cannot see, implying a
#   richer tactic body would close it. The idempotence half is confirmed (the
#   real extractor is idempotent on all 200k randomized labels plus the boundary
#   table — re-measured during audit, zero counterexamples), but the "the frozen
#   script is just too short" half was never demonstrated and is not free: two
#   richer bodies were tried during audit (unfolding the parser defs before
#   `loom_solve`, and a `simp_all [cleanLabel]` fallback) and BOTH still fail
#   with the ensures goal open, because closing the goal needs a genuine
#   idempotence LEMMA about `cleanLabel`, which the variant scope forbids adding
#   (no new `theorem`/`lemma`). So the accurate statement is narrower: this is a
#   faithful impl whose obligation is not closable within the admissible variant
#   scope on this carrier. It is recorded, still not shipped (it would fail), and
#   it is NOT a spec hole — the clause is semantically satisfied by that impl;
#   what is missing is a proof of parser idempotence, which is a property of the
#   deep model rather than of the contract.
#
#   SECOND-AUDIT PROBES (independent re-derivation, all with real builds). WRONG
#   impls the spec correctly REJECTED, each exit 1 with the `ensures` goal left
#   open — a SEMANTIC rejection, and each aimed at a clause feature the shipped
#   four leave unattacked: reduce the required label with the bare leading digit
#   run (`version.take (digitRun version)`, which is not the segment grammar and
#   mishandles a leading zero); reduce it with the epoch STRIPPED rather than
#   included (`cleanLabel (version.drop (epochLen version))`, attacking the
#   epoch sub-domain no shipped witness reaches); take epoch + leading segment
#   but DROP the dotted tail; and two probes against the `Except` PAYLOAD, which
#   no shipped rival touches — negate the `ok` boolean while forwarding the
#   failure, and collapse the `error` case into `ok false`. The last two matter
#   because the four shipped rivals all vary the callee's ARGUMENTS and none
#   varies its RESULT, so the payload was the one part of the clause with no
#   attacker; the spec pins it. CORRECT reshapes the spec correctly ACCEPTED
#   (exit 0): a redundant `if cleanLabel version = version` branch whose two arms
#   are extensionally equal, and a `match` on the mode instead of an `if`.
#
#   One correct reshape needs a NARROWER claim than "accepted": hand-inlining
#   `cleanLabel`'s own body into the impl fails under the frozen one-line
#   `loom_solve` (exit 1, goal open) but VERIFIES (exit 0) under either
#   `simp only [cleanLabel]` or `unfold cleanLabel` before it. So this is a
#   proof-depth limit of the frozen script, NOT a SPEC-TOO-STRONG hole — and
#   unlike the double-reduction reshape below it needs no new lemma, just the
#   definitional unfolding, which is inside the admissible variant scope.
#
#   Two further audit probes worth recording because they are the ones that would
#   have been holes. An impl correct only ON the modeled domain (compare cleanly
#   when the required label is all-ASCII, else return `ok true` / a failure)
#   VERIFIES — exit 0. That is not a spec defect but the precondition doing its
#   job: outside `∀ c ∈ version, c.toNat < 128` the contract claims nothing, so
#   an impl may do anything there, and mapping.md 2.1 records that domain
#   deliberately. It is noted here because it is the shape a reader might mistake
#   for SPEC-TOO-WEAK, and because it is the reason the admissibility case above
#   now REFUTES the precondition at a non-ASCII digit rather than only satisfying
#   it: an unrestricted precondition would turn that verifying impl into a real
#   hole.
#
#   THIRD-AUDIT PROBES (independent re-derivation from the frozen artifact and the
#   nagini design doc; every number below is an exit code observed on a real
#   build, not a restatement of an earlier revision's claim).
#
#   * The four inherited witnesses were rebuilt from scratch — rival 0 / gold 1 /
#     consistency probe 1 on all four. Each gold-side failure is an `Application
#     type mismatch` on `hne hcon`, and the B'-forgery pair was run on all four
#     rather than the error being read and judged: the TYPE-REVEAL control
#     (`exact (hcon : Nat)`) prints `hcon`'s real type on each side and they
#     DIFFER — reflexive against gold (`labelGE h c i = labelGE h c i`),
#     non-reflexive against each rival (the equation the rival actually owes) —
#     and the CLAIM-FLIP control (drop the `¬`, assert the triple HOLDS at the
#     same point under the same binders) builds clean on gold (exit 0) and fails
#     on every rival (exit 1, `unsolved goals` with the two distinct callee
#     applications printed). So gold's exit code tracks the CLAIM here rather
#     than being constant, which is the property the corpus's hollow signatures
#     lack. `wp_pure` demonstrably reduced on both sides.
#
#   * The AGREEMENT-POINT claim the second audit made about the two mode rivals
#     was re-measured against the real ordering callee rather than accepted:
#     at the F2P-shaped available label the callee returns the same verdict in
#     BOTH modes (available strictly above required, so both at-least and
#     strictly-above), while on the equality boundary the two modes genuinely
#     differ (non-strict satisfied, strict not). So the second audit's relocation
#     of the mode witnesses to the boundary was necessary and is correct, and each
#     of the five `hne` hypotheses is TRUE of the modeled operation at the point
#     its own witness names — not merely satisfiable.
#
#   * NEW WRONG impls, none of which the spec admits (each exit 1 with the
#     `ensures` goal open — a semantic rejection): read the ordering mode off the
#     required label's LENGTH instead of the binder; answer a single in-domain
#     label (`"1.2rc1"`) wrongly and everything else correctly, which is the
#     narrowest in-domain defect available and the one a coarse spec would miss;
#     negate the payload while forwarding the failure (now SHIPPED as
#     weak-verdict-payload-negated rather than left in this comment); collapse the
#     failure case into `ok false`; reduce with the bare leading digit run;
#     reduce with the epoch stripped rather than included; take epoch + leading
#     segment but drop the dotted tail; clean the AVAILABLE label too; return a
#     constant verdict.
#
#   * NEW CORRECT reshapes, all ACCEPTED (exit 0), so no SPEC-TOO-STRONG hole in
#     any of them: a `match` reconstructing the `Except` constructor-by-
#     constructor; a beta-redex; `id` around the reduced argument; a `match` on
#     the mode; a redundant `if cleanLabel version = version` whose arms are
#     extensionally equal; a three-way `let` chain; and a branch on the
#     precondition's OWN decidable test (`version.all (·.toNat < 128)`) whose two
#     arms are identical — the last is worth naming because a spec over-fit to the
#     frozen straight-line shape would reject it.
#
#   * `pos-split-on-mode`'s non-definitional claim was checked directly rather
#     than trusted: `rfl` does NOT relate `if inclusive then f true else f false`
#     to `f inclusive` (exit 1), while the case itself verifies under the frozen
#     `loom_solve`. So that positive does exercise proof content beyond reduction,
#     as its rationale claims.
#
#   * The MERGE of nagini's `rival-keep-marker` was re-confirmed mechanically:
#     perturbing the parser's own `version.take (e + r + d)` — the only way to
#     render that rival's mechanism here — reports `spec view differs (same_spec
#     failed)`, because the loop internals it edited now live in the frozen `pure`
#     region. The merge is forced by the carrier, not a difficulty dodge.
AXIOM_TESTS = []
