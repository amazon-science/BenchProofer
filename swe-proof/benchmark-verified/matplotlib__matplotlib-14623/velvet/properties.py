"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-14623 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region, or inside a ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
all four ``prove_correct`` obligations survive with byte-identical statements)
and swaps in a candidate implementation;
it is judged by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must ELABORATE against the
rival and FAIL against the frozen solution).

TWO OPERATIONS ARE DEFENDED, because the gold patch has two coordinated halves
and each is independently observable. The caller half (``commitLimits``) captures
the requested orientation and reinstates it after the axis normalizer; the callee
half (``defaultMemberAdjust``) removes the orientation handling from the DEFAULT
normalizer member so the reinstatement is not a second exchange. Reverting either
half alone breaks the failing test's own pre-existing legs (measured: F2P 0/1,
P2P 397/400), so a battery that attacked only one of them would leave a rival
that implements that one perfectly and the other pre-patch — which is exactly the
rival that refuted the previous revision of this bundle, now shipped as
reject-member-restores-order. Cases below are grouped: the first seventeen attack
``commitLimits`` (``defaultMemberAdjust`` verbatim gold), the last six attack
``defaultMemberAdjust`` (``commitLimits`` verbatim gold).

DEFENDED SURFACE #1
(``commitLimits (lo hi : Endpoint) return (out : Endpoint × Endpoint)``):
  Commit a requested endpoint pair to the view, going through an axis normalizer
  that turns the request into a well-formed interval; the requested ORIENTATION
  must be reinstated by THIS operation, read off the REQUESTED endpoints, because
  the normalizer's answer no longer records which way round the request was.
  Two input binders, ``lo`` and ``hi``, NO precondition (the operation is total
  over the carrier: either sign, either order, degenerate included), and SIX
  independent top-level postcondition clauses:

    (Q1) out = committedLimits lo hi                     the exact committed pair
    (Q2) (lo > hi) → out = ((normalize lo hi).2, (normalize lo hi).1)
    (Q3) (lo ≤ hi) → out = normalize lo hi
    (Q4) n.1 ≤ n.2 → (lo > hi) → out.2 ≤ out.1           orientation preserved …
    (Q5) n.1 ≤ n.2 → (lo < hi) → out.1 ≤ out.2           … in both directions
    (Q6) n.1 < n.2 → ((lo > hi) ↔ out.2 < out.1)         and IF AND ONLY IF

  over ``n := normalize lo hi``, where
  ``committedLimits lo hi = if lo > hi then (n.2, n.1) else (n.1, n.2)``.

DEFENDED SURFACE #2
(``defaultMemberAdjust (e0 e1 : Endpoint) return (out : Endpoint × Endpoint)``):
  The DEFAULT normalizer member: sort the two requested values, widen the
  resulting ASCENDING interval so it is resolvable, and report THAT pair — not the
  pair put back the way the arguments arrived. Two input binders, NO precondition
  (total over the carrier: either sign, either order, degenerate included), and
  FOUR independent top-level clauses:

    (P1) out = defaultMemberPair e0 e1                   the exact reported pair
    (P2) e1 < e0 → out = expandAscending e1 e0            a reversed pair is
                                                          sorted, NOT restored
    (P3) ¬ (e1 < e0) → out = expandAscending e0 e1        an ordered pair in place
    (P4) (defaultMemberPair e0 e1).1 ≤ (defaultMemberPair e0 e1).2
           → out.1 ≤ out.2                                the ORDER form of the
                                                          same content

  where ``defaultMemberPair e0 e1 = if e1 < e0 then expandAscending e1 e0 else
  expandAscending e0 e1``. P4 is the clause a caller-side orientation authority
  relies on and the one the PRE-PATCH member breaks on a reversed pair; it is
  conditioned on the widened interval being itself ordered, the one observable
  this member is not entitled to assume.

  There are TWO subordinate obligations, ``prove_correct normalizeRange`` and
  ``prove_correct expandRange`` (``:|`` stubs whose sole ``ensures`` are
  ``r = normalize a b`` and ``r = expandAscending a b``); they are the callee
  wrappers the two operations consult and are not operations under spec, so they
  are defended (every variant keeps them verbatim) but not independently
  attacked — see the ACCOUNTING footer.

LAYERING NOTE — which stub each surface may reach is part of the frozen spec.
The two surfaces are two LEVELS of one real call graph: the normalizer chain
surface #1 consults is a FAMILY, and surface #2 is one of its members, so the
declaration order in ``Solution.lean`` is widener stub, member operation, chain
stub, setter operation, and an operation may only bind the stubs declared above
it. Surface #2's impl region therefore cannot name ``normalizeRange`` at all —
a member that consulted the chain would re-enter itself, since on the default
path the member the chain dispatches to IS that member, and the refined program
would not terminate. Reordering those declarations is a SPEC change (the Lean
spec view elides only impl regions and ``prove_correct`` bodies), so no case in
this battery can undo it; each member-side case below reaches ``expandRange``
and the pure vocabulary only, which is exactly the real member's own reach.

CARRIER NOTE — the normalizer's OUTPUT ORDER is an observable, not a promise.
``normalize`` is an OPAQUE axiom (``Endpoint → Endpoint → Endpoint × Endpoint``)
and NOTHING is assumed about the order of its two results. That is deliberate and it is the
repair this battery defends: the modeled callee is a FAMILY (one member per
scale × locator), and its members disagree about ordering — the default
locators canonicalize to ascending, while others hand the pair back in the order
they received it. So the operation under spec is not entitled to either
behaviour, and the orientation content is stated with the normalizer's own
reported order as a HYPOTHESIS (Q4/Q5/Q6) rather than as a fact about the callee.
The exact-value clause Q1 is what pins ``out``: it says the committed pair is a
re-arrangement of ``normalize lo hi``'s own two components, selected by the
REQUEST's orientation, and it holds for every member of the family.

This dictates the witness technique, and so does the carrier itself. An
``Endpoint`` can be COMPARED and MOVED but never computed, so it carries no
numerals at all (measured: an assert naming ``10`` reports ``failed to
synthesize OfNat Endpoint 10``) — a rival cannot be refuted at a literal input
by ``decide``, and there is no literal to name one at. Every witness therefore
names its point by the ORDER RELATION its binders stand in (descending
``lo > hi``, degenerate ``v v``, ascending ``lo < hi``, sub-origin
``b < originEndpoint``) and CONDITIONS on the carrier: a rival that re-arranges the normalizer's
components wrongly contradicts Q1 for EVERY value whose relevant components are
separated, a fact provable from ONE hypothesis about one opaque term, WITHOUT
evaluating the normalizer. Each witness carries exactly that one hypothesis; it
is satisfiable (a lone (dis)equality/inequality between opaque terms), so the
gate's consistency probe cannot derive ``False`` from it, and it is additionally
TRUE of at least one realisable member of the modeled family — see
WITNESS-POINT DISCIPLINE.

WITNESS MECHANICS. ``extract_program_for`` is DEAD here: ``commitLimits`` depends
on the opaque ``normalize`` so it is ``noncomputable`` and no executable program /
tester can be extracted (measured — the sibling astropy-14855 pattern). Each
witness therefore reaches Q1 DIRECTLY over the method's own ``.run``. Under
demonic choice the ``normalizeRange`` stub's ``:|`` picks ``normalize lo hi`` (the
``findableEqPair`` instance supplies the constructive witness), so
``(commitLimits lo hi).run`` reduces to ``DivM.res (<the rival's committed pair>)``
by ``simp only [commitLimits, normalizeRange, committedLimits, NonDetT.run,
NonDetT.bind, NonDetT.pickSuchThat, pickSuchThat, findableEqPair, bind, pure]``.
The witness then states ``(commitLimits lo hi).run ≠ DivM.res (committedLimits lo
hi)``, selects BOTH sides' branches (``if_pos``/``if_neg``: the reference side's
guard from the witness's own order hypothesis, and — where the rival branches on
a DIFFERENT test than the reference does — the rival's guard too, from that same
hypothesis via the order's asymmetry/irreflexivity; a guard on the normalizer's
own reported order is discharged from the conditioning hypothesis), injects
through ``DivM.res.injEq`` + ``Prod.ext_iff``, and closes against the
hypothesis. Leaving the RIVAL's guard undischarged is the one shape that looks
like a refutation and is not: the injection then equates a whole ``if`` term
with a pair, the build fails on the rival, and the gate correctly records
``witness-unproven`` — a proof/tactic gap attributable to nothing. Against the frozen impl the
two sides are definitionally equal, so the disequality is unprovable and the
witness FAILS on gold — the discrimination the gate requires. No tester, no
banned token (``sorry``/``admit``/``native_decide``/``axiom``).

A BRANCH SELECTION THAT NAMES THE RIVAL'S OWN GUARD MUST BE A ``simp only``,
NEVER A ``rw`` — and this is a DISCRIMINATION property, not a style choice
(audited; six witnesses were converted, and the recorded gold-side signature of
each moved class as a result). Where the rival branches on a test of its own,
that guard does not exist in the frozen file. ``rw`` FAILS when its pattern is
absent, so on gold such a witness died at ``Tactic `rewrite` failed: Did not
find an occurrence of the pattern if <the rival's own guard> …`` — before ever
stating the claim. That exit code is a SYNTACTIC accident of the rival's shape:
it would have been recorded identically for a witness asserting gold is CORRECT
there, so the gate's gold-side half attested to nothing about the SPEC.
``simp only`` skips a non-matching lemma instead of failing, so on gold the
REFERENCE guard still selects, the two sides reduce to the same term, and the
injected hypothesis becomes reflexivity — gold's error is then an
``Application type mismatch`` reporting ``heq.left`` at type ``X = X`` where the
claim needs a genuine inequality, i.e. the reduction PROVED the equation for
gold and could not for the rival. (Three witnesses here name only the
REFERENCE's guard, because their rival commits unconditionally and has none:
``reject-no-restore``, ``reject-always-swap``, ``reject-partial-no-expand``.
For those the pattern IS present in the frozen file, ``rw`` matches on both
sides, and the recorded gold signature is already the semantic one; they are
deliberately left as ``rw``, which additionally FAILS loudly if the reference
guard should ever stop matching.) Verified per case by the
forgery pair (attack B′): flipping ``≠`` to ``=`` turns gold's build into
``No goals to be solved`` (the unfold alone proves gold correct at that point),
and revealing the hypothesis type prints ``True`` on gold against a concrete
equation such as ``(normalize lo hi).1 = (normalize lo hi).2`` on the rival. The
ground truth under both: ``simp only [<the unfold set>]`` alone closes
``(commitLimits lo hi).run = DivM.res (committedLimits lo hi)`` for arbitrary
binders (exit 0), while the same script leaves a false neighbour unsolved.

The second operation's witnesses are built the same way over ``_UNFOLD2`` and
``defaultMemberPair``, with one measured difference: the sort guard ``e1 < e0``
survives in the reduced goal at TWO different types (``Endpoint``, once per sorted
argument, and ``Endpoint × Endpoint``, for the pair), and a single ``rw [if_pos …]``
instantiates only one of them — so those witnesses discharge the guard with
``simp only [if_pos …]``, which matches at every type. ``norm_num`` is NOT
available in this environment ("unknown tactic", measured), so the literal
comparison is proved by ``decide``.

WITNESS-POINT DISCIPLINE. A hypothesis about an opaque callee is satisfiable in
Lean for almost anything, so the consistency probe alone does not make a
conditioning hypothesis HONEST — it must also be true of some realisable member
of the callee family. Two facts about that family are used, both established
executably by axiom_check.py (G-AX):
  * the two reported components DIFFER at a request whose endpoints differ, and
    at a degenerate request too (a degenerate interval is widened), so
    ``(normalize a b).1 ≠ (normalize a b).2`` is realisable at every point used;
  * the reported order can be EITHER WAY at a descending request — ascending on
    the default-locator members (so ``(normalize 10 1).1 < (normalize 10 1).2``
    is realisable) and descending on the order-preserving members (so
    ``(normalize 10 1).2 < (normalize 10 1).1`` is realisable too).
Value-preservation is the one place a naive point is wrong: on strictly-positive
DISTINCT endpoints the chain is value-preserving, so ``(normalize a b).1 ≠ a`` is
FALSE there and a witness resting on it would refute its rival only at an input
the carrier never realises. It becomes true at a DEGENERATE request, which the
chain widens. Hence the two value-attacking rivals are refuted at (3,3) and
(4,4), not at a distinct point.

The SECOND operation's witnesses obey the same rule against a HARDER carrier, and
this is the one place where an attractive rival had to be dropped rather than
shipped. ``expandAscending`` models the shared widening helper, which SORTS ITS
ARGUMENTS INTERNALLY before widening and does not reinstate the incoming order.
It is therefore SYMMETRIC in its two arguments. So a hypothesis of
the shape ``expandAscending 10 1 ≠ expandAscending 1 10`` — which would refute
every rival that sorts the wrong way round, sorts descending, or gates the sort —
is FALSE of the real callee, and no such rival is shipped: it would be refuted only
at a point the carrier does not realise. What IS realisable, and what all four of
the new witnesses rest on, is
  * ``(expandAscending 1 10).1 < (expandAscending 1 10).2`` — the widener leaves a
    resolvable interval alone and in ascending order (measured: returns
    (1.0, 10.0)); used by reject-member-restores-order and -swap-always;
  * ``(expandAscending 3 3).1 ≠ 3`` — a DEGENERATE interval is widened away from
    its endpoints (measured: (3,3) ↦ (2.85, 3.15)); used by
    reject-member-degenerate-raw;
  * ``normalize 3 3 ≠ expandAscending 3 3`` — the full per-scale chain and the
    shared 5% widener disagree on how much to widen a degenerate request (a date
    axis widens by 1e-7 days); used by reject-echo-sibling-expression,
    which is the caller-level statement of that rival (the member level cannot
    name the chain — see the note on that case).
Consequence worth stating plainly: the second operation's content is entirely
about WHICH ARGUMENTS the widener is applied to and WHICH ORDER its answer is
reported in, and only the second of those is observable through a symmetric
callee. The clauses are written to pin exactly that (P2/P3 name the arguments,
P1/P4 the reported order), and the battery attacks exactly what it can honestly
attack.

DEFINITIONAL-EQUALITY LIMIT OF THIS CARRIER (measured, load-bearing for how the
positives must be read). The frozen impl's body is a ``let``-staged conditional
over the two components of one opaque call, so every reshape that only re-stages
VALUES is the same term up to zeta/delta reduction: ``example : gold = <reshape>
:= rfl`` ELABORATES for dropping the ``swapped`` capture, naming ``n.1``/``n.2``
as locals, ``Prod.swap n``, and spelling the guard ``hi < lo``. Such a positive
verifies under the FROZEN tactic script verbatim and therefore imposes no new
proof burden — honest, but a control of the staging only. Under the repaired
spec the frozen script is just ``loom_solve``, which also absorbs a CONTROL-FLOW
restructuring (branch first, commit inside each arm; measured exit 0 with the
frozen body). The one positive the frozen script does NOT close is committing
the pure reference expression ``committedLimits lo hi`` directly: ``loom_solve``
leaves ``(normalize lo hi).1 ≤ (normalize lo hi).2 → lo < hi →
(committedLimits lo hi).1 ≤ (committedLimits lo hi).2`` unsolved (measured exit
1) and the obligation must genuinely be reproven, which it is with the retuned
(spec-elided) body ``all_goals grind [committedLimits]``. That case, not a value
re-staging, is what makes the SPEC-TOO-STRONG direction real here.

WHY THE REPAIRED SURFACE IS STRONGER, NOT WEAKER (the hole this battery closes).
The previous revision carried ``require 0 < lo`` / ``require 0 < hi`` and an
axiom ``normalize_ascending`` asserting the normalizer always reports ascending
on positive distinct endpoints. Both are gone:
  * the preconditions EXCLUDED the F2P inputs (the failing test drives (4.0,
    -5.0) and (5.0, -3.0) on a linear axis), so a rival gating the orientation
    restore on ``0 < lo ∧ 0 < hi`` satisfied the spec while failing the test.
    That rival is now SHIPPED as reject-positivity-gate and is REJECTED.
  * the axiom was FALSE of the real patched code on several scales, and it also
    handed the impl-prover a fact it is not entitled to. Deleting it removes an
    assumption (a strengthening) and forces the orientation content to be stated
    against the observable.
Widening the domain and deleting an axiom both ADD obligations; the exact-value
clause Q1 was kept, and Q2/Q3/Q6 are new. reject-ascending-gate and
reject-postcall-flag are the two rivals that exploit exactly the freedom the
deleted axiom used to hide, and both are rejected.

THE SECOND HOLE, AND WHY MODELING A SECOND OPERATION CLOSES IT (not narrows it).
The revision that fixed the above still modeled only the CALLER half of the gold
patch, and the audit refuted it: an impl that implements the commit block exactly
and leaves ``ticker.py`` at base_commit satisfies the frozen spec, because the
spec could not see the callee half at all. Measured against the instance, that
refinement does NOT resolve — F2P 0/1, P2P 397/400 — since with the pre-patch
member the caller's reinstatement becomes a SECOND exchange on the linear
default-locator path, and the failing test's own pre-existing legs
(a descending request of ``(4, -5)``, another of ``(5, -3)``) come out ascending.
The old narrative
claimed the hunk "needs no clause" because it only changes which member reports
which order; that claim was wrong, and it was wrong in the direction that hides a
hole. The repair ADDS an operation, four clauses, one bare axiom and a SECOND
prepatch twin: nothing was weakened, no precondition appeared (``defaultMemberAdjust``
is total over the carrier too), and the spec now obligates both halves. Six new
cases below measure it, four of them rivals in four distinct families.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-14623"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen commitLimits impl body (the three
# ---- comment lines and the four statements). It lies wholly inside the single
# ---- commitLimits -- impl-start / -- impl-end region and is unique in
# ---- Solution.lean (both facts asserted at load by _swap), so each edit keeps
# ---- same_spec by construction and leaves both `prove_correct` STATEMENTS
# ---- intact. ----
_IMPL = (
    "    -- Read the requested orientation BEFORE consulting the normalizer: its\n"
    "    -- answer no longer records which way round the request was.\n"
    "    let swapped := lo > hi\n"
    "    let n ← normalizeRange lo hi\n"
    "    -- Commit the normalizer's endpoints in the requested orientation.\n"
    "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
    "    return out"
)
assert _BASE.count(_IMPL) == 1, "commitLimits impl region drifted from expected text"

# ---- the frozen commitLimits proof block. A tactic body is elided from the
# ---- consumer spec view, so a positive control that reshapes the impl may
# ---- retune it without touching the spec or dropping the obligation. Unique
# ---- (`prove_correct normalizeRange by\n  loom_solve` is a different string). ----
_PROVE = (
    "prove_correct commitLimits by\n"
    "  loom_solve <;>\n"
    "    intros <;>\n"
    "    split <;>\n"
    "    simp_all [asymm, not_lt] <;>\n"
    "    exact absurd \u2039hi < lo\u203a (not_lt_of_ge \u2039lo \u2264 hi\u203a)\n"
)
assert _BASE.count(_PROVE) == 1, "prove_correct commitLimits body drifted"


def _impl(new_impl):
    """Full Solution.lean with ONLY commitLimits' impl-region body replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_and_proof(new_impl, new_proof):
    """Reshape the impl AND retune the (elided) commitLimits tactic body."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROVE, new_proof)


# ---- impl-region anchor #2: the WHOLE frozen defaultMemberAdjust impl body (the
# ---- two comment lines and the five statements). Solution.lean carries FOUR
# ---- `-- impl-start` / `-- impl-end` regions (the marker reader returns a LIST
# ---- of impl spans, so several are supported) and this text lies wholly inside
# ---- the defaultMemberAdjust one and is unique in the file. The SECOND DEFENDED
# ---- OPERATION lives here: it is the callee-side half of the same gold patch,
# ---- and it is modeled because a refinement that implements `commitLimits`
# ---- exactly while leaving this member at its PRE-PATCH behaviour verified
# ---- against the caller-only spec and did NOT resolve (see the footer). ----
_IMPL2 = (
    "    -- Sort the two arguments, adjust, and report the adjusted pair AS IS: the\n"
    "    -- order the arguments arrived in is not reinstated here.\n"
    "    let reversed := e1 < e0\n"
    "    let a := if reversed then e1 else e0\n"
    "    let b := if reversed then e0 else e1\n"
    "    let e ← expandRange a b\n"
    "    return e"
)
assert _BASE.count(_IMPL2) == 1, \
    "defaultMemberAdjust impl region drifted from expected text"

# ---- the frozen defaultMemberAdjust proof block (distinct string from _PROVE and
# ---- from the expandRange / normalizeRange stubs' blocks). ----
_PROVE2 = (
    "prove_correct defaultMemberAdjust by\n"
    "  loom_solve\n"
)
assert _BASE.count(_PROVE2) == 1, "prove_correct defaultMemberAdjust body drifted"


def _impl2(new_impl):
    """Full Solution.lean with ONLY defaultMemberAdjust's impl body replaced.

    `commitLimits` — the OTHER defended operation — is left verbatim, so a case
    built here is a rival for the callee-side half alone. That separation is the
    point: the two halves of the gold patch are independently observable (each
    one alone, with the other reverted, breaks the pre-existing linear legs of
    the failing test), so each gets its own rivals and its own prepatch twin.
    """
    return _swap(_BASE, _IMPL2, new_impl)


def _impl2_and_proof(new_impl, new_proof):
    """Reshape the MEMBER's impl AND retune its (elided) tactic body.

    The member-side counterpart of `_impl_and_proof`. A `prove_correct` tactic
    body is elided from the consumer spec view exactly as the caller's is, so a
    member-side positive whose reshape carries a real reproof burden may retune
    it without touching a spec byte or dropping the obligation — which is what
    `pos-member-demorgan-guard` needs, and what its absence here had previously
    made look like an unshippable tactic gap.
    """
    return _swap(_swap(_BASE, _IMPL2, new_impl), _PROVE2, new_proof)


# ---- witness preamble: none needed. Each witness is a self-contained `example`
# ---- over the method's own `.run`; the simp set below is what reduces it. The
# ---- unfold set is shared by every reject witness. ----
_UNFOLD = (
    "  simp only [commitLimits, normalizeRange, committedLimits, NonDetT.run, "
    "NonDetT.bind,\n"
    "    NonDetT.pickSuchThat, pickSuchThat, findableEqPair, bind, pure]\n"
)

# ---- the same for the second operation: `(defaultMemberAdjust e0 e1).run`
# ---- reduces to `DivM.res (<the rival's reported pair>)` under this set, and the
# ---- witness then states a disequality against `defaultMemberPair e0 e1`.
# ---- `norm_num` is NOT available in this environment (measured: "unknown
# ---- tactic"), so the literal sort guard is discharged with an explicit
# ---- `simp only [if_pos …]` / `if_neg …` carrying a `by decide` proof — as
# ---- a simp LEMMA, not a `rw`, because the guard occurs at two different types
# ---- (`Endpoint` for each sorted argument, `Endpoint × Endpoint` for the pair)
# ---- and a single
# ---- `rw` instantiates only one of them (measured). ----
_UNFOLD2 = (
    "  simp only [defaultMemberAdjust, expandRange, defaultMemberPair, NonDetT.run, "
    "NonDetT.bind,\n"
    "    NonDetT.pickSuchThat, pickSuchThat, findableEqPair, bind, pure]\n"
)

# ---- shared witness tail: inject the pair equation and close it against the
# ---- conditioning hypothesis. `_CLOSE(...)` is the final `exact`. ----
_INJECT = (
    "  intro heq\n"
    "  rw [DivM.res.injEq, Prod.ext_iff] at heq\n"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-inline-orientation",
        "kind": "soundness",
        "expect": "verify",
        # Drop the intermediate `swapped` boolean: decide the committed
        # orientation directly from the request comparison at the point of use.
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- Decide the committed orientation directly from the request:\n"
            "    -- a descending request commits the endpoints exchanged.\n"
            "    let out := if lo > hi then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "rationale": "PASS SOURCE = Q1..Q6. Deciding the committed orientation "
                     "directly from `lo > hi` (dropping the intermediate `swapped` "
                     "capture) yields the SAME committed pair as gold on every "
                     "input, so `out = committedLimits lo hi` and every "
                     "conditioned orientation clause still holds. "
                     "SCOPE, stated honestly: this is the CHEAPEST positive, not a "
                     "structurally-different one. Dropping the `swapped` `let` is a "
                     "zeta-reduction, so the impl is the same term as gold up to "
                     "reduction (measured: `example : gold = inlineOrientation := "
                     "rfl` elaborates, exit 0) and it closes under the frozen "
                     "tactic script verbatim. It attests only that the spec does "
                     "not depend on that staging detail. The SPEC-TOO-STRONG "
                     "direction is carried by pos-pure-reference below, the one "
                     "reshape the frozen script provably fails to close.",
    },
    {
        "id": "pos-branch-select",
        "kind": "soundness",
        "expect": "verify",
        # Branch on the requested orientation FIRST, then consult the normalizer
        # inside each arm and return from that arm directly: genuinely different
        # CONTROL FLOW (two call sites, two `return`s, no single joined `out`).
        "module": _impl_and_proof(
            "    -- Branch on the requested orientation first, then commit the\n"
            "    -- normalized endpoints in that orientation from within the arm.\n"
            "    if lo > hi then\n"
            "      let n ← normalizeRange lo hi\n"
            "      return (n.2, n.1)\n"
            "    else\n"
            "      let n ← normalizeRange lo hi\n"
            "      return (n.1, n.2)\n",
            "prove_correct commitLimits by\n"
            "  loom_solve <;>\n"
            "    intros <;>\n"
            "    simp_all [asymm, not_lt, lt_asymm] <;>\n"
            "    exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›)\n"),
        "rationale": "PASS SOURCE = Q1..Q6. A faithful, structurally-different "
                     "correct impl: branch on the requested orientation first and "
                     "commit from inside the arm, two call sites and two returns, "
                     "so the committed pair is `committedLimits lo hi` on every "
                     "input and every conditioned clause holds. "
                     "REPROOF BURDEN, stated honestly: hoisting the branch ABOVE "
                     "the callee call makes the program's own `if` disappear from "
                     "each residual goal — `loom_solve` has already selected the "
                     "arm, so the committed pair arrives as the bare `x` bound by "
                     "the arm's `ensures_1 : x = normalize lo hi` — and the frozen "
                     "body's `split` then has no `if` left to split (measured exit "
                     "1 with the frozen body verbatim, three unsolved goals: Q5 as "
                     "`x.2 ≤ x.1` under `lo > hi ∧ lo < hi`, Q3 as `(x.2, x.1) = "
                     "normalize lo hi` under `lo > hi ∧ lo ≤ hi`, Q6 as `lo > hi ↔ "
                     "x.2 < x.1` under `¬ lo > hi`). All three are closed by "
                     "dropping that `split` and letting `simp_all` use the order's "
                     "own asymmetry (`[asymm, not_lt, lt_asymm]`, measured exit 0) "
                     "— a retune of the ELIDED tactic body only, no spec change. "
                     "Each residual is a CONTRADICTORY-ANTECEDENT goal, i.e. the "
                     "spec is not at issue: it is arithmetic about `lo` and `hi`, "
                     "which is why the retune needs no new fact about the callee. "
                     "If it could not verify ⇒ SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-pure-reference",
        "kind": "soundness",
        "expect": "verify",
        # Consult the callee (so the callee obligation is unchanged) and commit
        # the PURE REFERENCE expansion directly. Same value as gold on every
        # input, but the committed pair now arrives as an unreduced
        # `committedLimits` application rather than a materialised pair, so the
        # frozen `loom_solve` no longer closes the orientation goals and the
        # obligation must be reproven.
        "module": _impl_and_proof(
            "    -- Consult the normalizer, then commit the reference expansion of\n"
            "    -- the request directly instead of materialising the pair here.\n"
            "    let _n ← normalizeRange lo hi\n"
            "    let out := committedLimits lo hi\n"
            "    return out",
            "prove_correct commitLimits by\n"
            "  loom_solve <;>\n"
            "    intros <;>\n"
            "    simp_all [committedLimits, asymm, not_lt] <;>\n"
            "    split <;> simp_all [asymm]\n"),
        "rationale": "PASS SOURCE = Q1..Q6. Committing `committedLimits lo hi` is "
                     "value-identical to gold on EVERY input (it is the reference "
                     "expansion the clauses are stated against), so a spec that "
                     "rejected it would be rejecting its own intended behaviour. "
                     "This is the one reshape on this carrier that is NOT closed by "
                     "the frozen tactic body: `loom_solve` leaves "
                     "`(normalize lo hi).1 ≤ (normalize lo hi).2 → lo < hi → "
                     "(committedLimits lo hi).1 ≤ (committedLimits lo hi).2` "
                     "unsolved (measured exit 1) because the committed pair is no "
                     "longer syntactically a pair, so Q4/Q5/Q6 have to be proven "
                     "through the definition. It verifies with the retuned "
                     "spec-elided body `simp_all [committedLimits, asymm, not_lt] "
                     "<;> split <;> simp_all [asymm]` (measured exit 0), which is "
                     "what makes this the SPEC-TOO-STRONG carrier. The retune has "
                     "to UNFOLD `committedLimits` and then split its `if`, in that "
                     "order: on this carrier an endpoint supports only comparison, "
                     "so there is no decision procedure that can evaluate "
                     "`committedLimits lo hi` to a pair, and `grind` — even given "
                     "`committedLimits` as a fact — fails on all three orientation "
                     "goals (measured exit 1; its own diagnostics show it deriving "
                     "`committedLimits lo hi = normalize lo hi` yet unable to "
                     "connect that to `(committedLimits lo hi).2 < "
                     "(committedLimits lo hi).1`, because projecting a pair out of "
                     "an opaque `normalize` application gives it no further "
                     "equalities to close on). Unfolding first puts the `if` in the "
                     "goal where `split` can reach it, and each branch is then the "
                     "same contradictory-antecedent arithmetic the other positives "
                     "close. "
                     "NOT AN UNGROUNDED ORACLE ECHO: `committedLimits` is defined "
                     "over the opaque `normalize` (validated executably against the "
                     "real callee by axiom_check.py / G-AX), not an answer key — "
                     "there is no concrete endpoint value anywhere in the spec for "
                     "an impl to copy, and the rival lane below contains an echo "
                     "that IS wrong (reject-echo-transposed) and is rejected.",
    },

    # =====================================================================
    # ADMISSIBILITY — the operation is TOTAL (no `require`), so these probe the
    # domain the previous revision's preconditions excluded. Each keeps the gold
    # impl and adds a live in-region `assert` about a concrete request; the
    # assert is discharged in the retuned (spec-elided) tactic body, so the
    # method's own obligation still closes. MUST verify, else PRECOND-TOO-STRONG.
    # =====================================================================
    {
        "id": "admiss-f2p-descending",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_and_proof(
            "    let swapped := lo > hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    -- Every DESCENDING request — the failing test's own request shape\n"
            "    -- — is in-domain, the orientation restore is LIVE there (first\n"
            "    -- conjunct: the committed pair really is the normalizer's pair\n"
            "    -- exchanged), and the orientation obligation is SATISFIABLE there\n"
            "    -- (second conjunct: whenever the normalizer reports ascending, the\n"
            "    -- committed interval at that request is descending).\n"
            "    assert (with_name_prefix `assert (∀ a b : Endpoint, b < a →\n"
            "      committedLimits a b = ((normalize a b).2, (normalize a b).1) ∧\n"
            "      ((normalize a b).1 ≤ (normalize a b).2 →\n"
            "        (committedLimits a b).2 ≤ (committedLimits a b).1)))\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out",
            "prove_correct commitLimits by\n"
            "  loom_solve <;>\n"
            "    intros <;>\n"
            "    first\n"
            "      | (exact ⟨committedLimits_descending _ _ ‹_›,\n"
            "          fun _ => by rw [committedLimits_descending _ _ ‹_›]; exact id⟩)\n"
            "      | (split <;> simp_all [asymm, not_lt] <;>\n"
            "         exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›))\n"),
        "rationale": "the operation has NO precondition, so a descending request is "
                     "in-domain by construction; what this case establishes is that "
                     "the obligation is SATISFIABLE at the failing test's own "
                     "request SHAPE rather than vacuous or contradictory there. The "
                     "in-region `assert` carries two conjuncts, both about an "
                     "arbitrary descending request `b < a`: the restore is live "
                     "(`committedLimits a b` really is the normalizer's pair "
                     "exchanged, from `committedLimits_descending`), and Q4's "
                     "conclusion is discharged there under Q4's own antecedent. "
                     "WHY THE REQUEST IS NAMED BY ITS ORDER AND NOT BY A LITERAL: "
                     "an endpoint on this carrier is comparable and movable, never "
                     "computed, so it carries no numerals — the point `(10, 1)` is "
                     "not expressible and an assert naming it does not elaborate "
                     "(measured: `failed to synthesize OfNat Endpoint 10`). "
                     "Quantifying over the descending requests is the carrier's own "
                     "way of saying the same thing, and it is STRICTLY STRONGER than "
                     "the literal point would have been: it asserts the restore is "
                     "live and the orientation satisfiable at EVERY descending "
                     "request, the literal at one. The negative control is the same "
                     "assert with the orientation conclusion reversed "
                     "(`(committedLimits a b).1 ≤ (committedLimits a b).2`), which "
                     "does NOT verify (measured exit 1) — so the assert is live, not "
                     "decoration. The impl is otherwise gold, so Q1..Q6 discharge "
                     "too. If it cannot verify ⇒ PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-negative-endpoint",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_and_proof(
            "    let swapped := lo > hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    -- The ACTUAL failing-test request shape: descending, with the low\n"
            "    -- endpoint strictly BELOW the axis origin, on a scale whose\n"
            "    -- permitted domain is the whole line so nothing clamps it. The\n"
            "    -- previous revision's `require 0 < lo` / `require 0 < hi` excluded\n"
            "    -- exactly this region; the repaired operation is total, so the\n"
            "    -- restore is live here and the obligation is satisfiable here.\n"
            "    assert (with_name_prefix `assert (∀ a b : Endpoint,\n"
            "      b < a → b < originEndpoint →\n"
            "      committedLimits a b = ((normalize a b).2, (normalize a b).1) ∧\n"
            "      ((normalize a b).1 ≤ (normalize a b).2 →\n"
            "        (committedLimits a b).2 ≤ (committedLimits a b).1)))\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out",
            "prove_correct commitLimits by\n"
            "  loom_solve <;>\n"
            "    intros <;>\n"
            "    first\n"
            "      | (exact ⟨committedLimits_descending _ _ ‹_›,\n"
            "          fun _ => by rw [committedLimits_descending _ _ ‹_›]; exact id⟩)\n"
            "      | (split <;> simp_all [asymm, not_lt] <;>\n"
            "         exact absurd ‹hi < lo› (not_lt_of_ge ‹lo ≤ hi›))\n"),
        "rationale": "THE case that records the repair's domain widening. The "
                     "failing test drives a descending request with a NEGATIVE "
                     "endpoint — (4.0, -5.0) and (5.0, -3.0) on a linear axis — and "
                     "the previous revision's `require 0 < lo` / `require 0 < hi` "
                     "put that request OUTSIDE the operation's domain, which is how "
                     "reject-positivity-gate below used to slip through. With the "
                     "preconditions deleted the operation is total over the "
                     "carrier, and this assert shows the obligation is live "
                     "throughout that excluded region: the restore applies "
                     "(`committedLimits a b` is the normalizer's pair exchanged) and "
                     "the orientation conclusion holds there under Q4's antecedent. "
                     "HOW THE EXCLUDED REGION IS NAMED, and why this is the same "
                     "claim rather than a weaker one: `originEndpoint` is the "
                     "carrier's distinguished endpoint — the value a real endpoint "
                     "is compared against when code wants its SIGN — so "
                     "`b < originEndpoint` is exactly 'the low endpoint lies below "
                     "the origin', i.e. the negation of the deleted `0 < hi` "
                     "precondition. That is the whole content the literal (4, -5) "
                     "carried, and quantifying it makes the case stronger, not "
                     "weaker: the obligation is asserted live at EVERY descending "
                     "sub-origin request, not at one. It also has to be said this "
                     "way — an endpoint here supports only comparison, so it carries "
                     "no numerals and no negation, and an assert naming (4, -5) does "
                     "not elaborate (measured: `failed to synthesize OfNat Endpoint "
                     "4` and `failed to synthesize Neg Endpoint`). The two "
                     "hypotheses are jointly satisfiable and both are realised by "
                     "the failing test's own requests. Same negative control as the "
                     "case above (reversing the orientation conclusion fails to "
                     "verify, measured exit 1), so the sub-origin guard did not make "
                     "the assert vacuous. This case remains the ONLY one whose "
                     "in-domain point lies outside the quadrant the previous "
                     "revision admitted, and it is what pairs with "
                     "reject-positivity-gate: that rival guards the restore on the "
                     "endpoints being ABOVE the origin, and it is refuted at a "
                     "request this case shows to be in-domain. If it cannot verify "
                     "⇒ PRECOND-TOO-STRONG, i.e. the domain narrowed again.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness that
    # CONDITIONS on the opaque normalizer at one concrete input point.
    # =====================================================================

    # ---- the pre-patch bug: no orientation restore ----
    {
        "id": "reject-no-restore",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- NO orientation restore: commit the normalizer's pair as reported.\n"
            "    let out := (n.1, n.2)\n"
            "    return out"),
        "refinement": "this is the pre-patch behaviour exactly: it drops the "
                      "requested-orientation capture and the descending restore, "
                      "so a descending request is committed in whatever order the "
                      "normalizer chose. The faithful counterpart fails the failing "
                      "test, which drives a descending request and asserts the "
                      "committed interval stays descending, so it does NOT resolve "
                      "the F2P.",
        "rationale": "REJECT from Q1/Q2: on a descending request `lo > hi`, "
                     "`committedLimits` = `(n.2, n.1)` but the rival commits "
                     "`(n.1, n.2)`; these differ whenever the normalizer's two "
                     "components differ. Also violates Q4 and Q6. Refuted at "
                     "(10,1), a descending point, conditioned on "
                     "(normalize 10 1).1 ≠ (normalize 10 1).2.",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi)\n"
            "    (h : (normalize lo hi).1 ≠ (normalize lo hi).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  rw [if_pos hd]\n"
            + _INJECT +
            "  exact h heq.1\n",
    },

    # ---- comparison flipped to '<': restores on the WRONG branch ----
    {
        "id": "reject-cmp-lt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let swapped := lo < hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "restoring on `lo < hi` restores on the wrong branch: a "
                      "descending request is committed as the normalizer reported "
                      "it and an ascending request is committed exchanged. The "
                      "faithful counterpart fails both the failing "
                      "descending-request leg and the ascending regression legs, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from Q1/Q2: on a descending request `lo > hi`, "
                     "`swapped = lo < hi` is false, so the rival commits "
                     "`(n.1, n.2)` where `committedLimits` = `(n.2, n.1)`; these "
                     "differ whenever the normalizer's two components differ. Also "
                     "violates Q3 on the ascending side. Refuted at a descending "
                     "request, conditioned on (normalize lo hi).1 ≠ "
                     "(normalize lo hi).2. "
                     "TWO GUARDS, NOT ONE: this rival's committed pair is selected "
                     "by its OWN test `lo < hi`, not by the request test the "
                     "reference expansion uses, so the witness has to discharge "
                     "both — `if_pos hd` selects the exchanged branch on the "
                     "reference side and `if_neg (asymm hd)` selects the "
                     "as-reported branch on the RIVAL's side, `asymm hd` being "
                     "precisely why a descending request cannot also be ascending. "
                     "Discharging only the reference side leaves the rival's `if` "
                     "standing and the injection then compares a branch to a pair "
                     "(measured exit 1 on the rival: `heq.left has type (if lo < hi "
                     "then … else …).1 = ((normalize lo hi).2, …).1`), which is a "
                     "TACTIC gap and attributes nothing to the spec.",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi)\n"
            "    (h : (normalize lo hi).1 ≠ (normalize lo hi).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_pos hd, if_neg (asymm hd)]\n"
            + _INJECT +
            "  exact h heq.1\n",
    },

    # ---- boundary token swap: '>' relaxed to '>=', flipping the equal case ----
    {
        "id": "reject-cmp-ge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let swapped := lo ≥ hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "with `swapped = lo ≥ hi`, an EQUAL request captures "
                      "swapped=true, so the normalizer's expansion of a singular "
                      "request is committed exchanged rather than as reported. A "
                      "faithful counterpart commits a singular request the wrong "
                      "way round, a behaviour regression the singular-expansion "
                      "legs expose; it does NOT match gold on the equal "
                      "sub-domain.",
        "rationale": "REJECT from Q1/Q3, on the equal sub-domain only — a "
                     "near-miss agreeing with gold on every distinct request. At "
                     "`lo = hi` `committedLimits` takes the `¬ lo > hi` branch = "
                     "`(n.1, n.2)`, but the rival's `lo ≥ hi` is true so it commits "
                     "`(n.2, n.1)`; these differ whenever the normalizer's two "
                     "components differ. Refuted at the equal point (5,5), "
                     "conditioned on (normalize 5 5).1 ≠ (normalize 5 5).2 — "
                     "realisable because a degenerate request is WIDENED to a "
                     "non-degenerate interval (measured on the real chain: "
                     "(5,5) -> (1,10) style widening). "
                     "TWO GUARDS, NOT ONE: the two sides branch on DIFFERENT tests "
                     "at a degenerate request, which is the whole content of this "
                     "near-miss — `if_neg (lt_irrefl v)` selects the reference's "
                     "as-reported branch (`v > v` is false) and `if_pos (le_refl v)` "
                     "selects the rival's exchanged branch (`v ≥ v` is TRUE). "
                     "Discharging only the reference side leaves the rival's `if` "
                     "standing and the injection compares a branch to a pair "
                     "(measured exit 1 on the rival), a TACTIC gap that attributes "
                     "nothing to the spec.",
        "witness":
            "example (v : Endpoint)\n"
            "    (h : (normalize v v).1 ≠ (normalize v v).2) :\n"
            "    (commitLimits v v).run ≠ DivM.res (committedLimits v v) := by\n"
            + _UNFOLD +
            "  simp only [if_neg (lt_irrefl v), if_pos (le_refl v)]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },

    # ---- unconditional exchange ----
    {
        "id": "reject-always-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- Unconditional exchange: commit the normalizer's pair reversed\n"
            "    -- whatever the request was.\n"
            "    let out := (n.2, n.1)\n"
            "    return out"),
        "refinement": "committing the exchanged pair unconditionally reverses every "
                      "request, so an ascending request is committed the wrong way "
                      "round. The faithful counterpart fails the ascending "
                      "regression legs, so it does NOT resolve.",
        "rationale": "REJECT from Q1/Q3: on an ascending request `lo < hi`, "
                     "`committedLimits` = `(n.1, n.2)` but the rival commits "
                     "`(n.2, n.1)`; these differ whenever the normalizer's two "
                     "components differ. Also violates Q5 and Q6. Refuted at the "
                     "ascending point (1,10), moving both binders to the ascending "
                     "orientation, conditioned on "
                     "(normalize 1 10).1 ≠ (normalize 1 10).2.",
        "witness":
            "example (lo hi : Endpoint) (ha : lo < hi)\n"
            "    (h : (normalize lo hi).1 ≠ (normalize lo hi).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  rw [if_neg (not_lt.mpr (le_of_lt ha))]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },

    # ---- bypass the normalizer: commit the raw requested pair ----
    {
        "id": "reject-partial-no-expand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Commit the requested endpoints directly, bypassing the\n"
            "    -- normalized ones.\n"
            "    let _n ← normalizeRange lo hi\n"
            "    let out := (lo, hi)\n"
            "    return out"),
        "refinement": "committing the requested pair verbatim (dropping the "
                      "normalizer's conditioning) stores a DEGENERATE request "
                      "`(v, v)` as the singular pair instead of the widened "
                      "interval. A faithful counterpart breaks the "
                      "singular-expansion contract downstream — the committed "
                      "interval is no longer the well-formed one the normalizer "
                      "produces — so it does NOT match gold behaviour.",
        "rationale": "REJECT from Q1/Q3, attacking the normalized-VALUE half rather "
                     "than the ORDER half: the rival commits `(lo, hi)` where "
                     "`committedLimits` = `(n.1, n.2)` on a non-descending request; "
                     "these differ whenever the normalizer's low endpoint is not "
                     "the raw input `lo`. Refuted at the DEGENERATE point (3,3), "
                     "conditioned on (normalize 3 3).1 ≠ 3. "
                     "WITNESS POINT: it must be a degenerate request. On "
                     "strictly-positive DISTINCT endpoints the modeled chain is "
                     "value-preserving (measured: (2,7) -> (2,7)), so "
                     "`(normalize 2 7).1 ≠ 2` is satisfiable in Lean but FALSE of "
                     "the callee, and a witness there would refute the rival only "
                     "at an input the carrier never realises. A degenerate request "
                     "IS widened (measured: (3,3) -> (1,10)), making "
                     "`(normalize 3 3).1 ≠ 3` true of the modeled callee as well.",
        "witness":
            "example (v : Endpoint) (h : (normalize v v).1 ≠ v) :\n"
            "    (commitLimits v v).run ≠ DivM.res (committedLimits v v) := by\n"
            + _UNFOLD +
            "  rw [if_neg (lt_irrefl v)]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },

    # ---- equal-request-only near-miss: gold everywhere EXCEPT lo = hi ----
    {
        "id": "reject-equal-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- Correct on every distinct request; on a DEGENERATE request\n"
            "    -- commit the requested pair instead of the normalized one.\n"
            "    let out := if lo > hi then (n.2, n.1)\n"
            "               else if lo = hi then (lo, hi) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "this rival is behaviourally identical to gold on every "
                      "distinct request, so it resolves the failing "
                      "descending-request leg and every ascending regression leg; "
                      "it diverges only on a DEGENERATE request, where it commits "
                      "the singular pair `(v, v)` instead of the widened "
                      "well-formed interval the normalizer produces. A faithful "
                      "counterpart therefore still breaks the singular-expansion "
                      "contract downstream, so it does NOT match gold behaviour.",
        "rationale": "REJECT from Q1/Q3 alone, on the equal sub-domain: at "
                     "`lo = hi` `committedLimits` takes the `¬ lo > hi` branch = "
                     "`(n.1, n.2)`, but the rival commits the raw `(lo, hi)`; these "
                     "differ whenever the normalizer's low endpoint is not the raw "
                     "input. Refuted at (4,4), conditioned on "
                     "(normalize 4 4).1 ≠ 4 — true of the modeled callee (a "
                     "degenerate request is widened). This is the tightest "
                     "near-miss the surface admits AND the least constrained input: "
                     "Q4/Q5/Q6's request antecedents are all false at `lo = hi`, so "
                     "the exact-value clauses must carry the rejection unaided.",
        "witness":
            "example (v : Endpoint) (h : (normalize v v).1 ≠ v) :\n"
            "    (commitLimits v v).run ≠ DivM.res (committedLimits v v) := by\n"
            + _UNFOLD +
            "  simp only [if_true, and_self, if_neg (lt_irrefl v)]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },

    # ---- PARTIAL-DOMAIN GUARD, and the exact rival that refuted the previous
    # ---- revision: restore the orientation only where the deleted preconditions
    # ---- used to hold. ----
    {
        "id": "reject-positivity-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Restore the requested orientation ONLY when both requested\n"
            "    -- endpoints are strictly positive — i.e. only on the sub-domain\n"
            "    -- the previous revision's `require 0 < lo` / `require 0 < hi`\n"
            "    -- carved out. Everywhere else, commit the normalizer's pair as\n"
            "    -- reported (the pre-patch behaviour).\n"
            "    let swapped := lo > hi ∧ originEndpoint < lo ∧ "
            "originEndpoint < hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "gating the restore on strictly-positive endpoints leaves the "
                      "pre-patch behaviour in place for every request with a "
                      "non-positive endpoint. The faithful counterpart FAILS THE "
                      "FAILING TEST: it drives descending requests (4.0, -5.0) and "
                      "(5.0, -3.0) on a linear axis, whose committed intervals stay "
                      "in the normalizer's order instead of descending, and it also "
                      "breaks two passing tests. Measured, not asserted: this "
                      "counterpart was run against the instance and does NOT "
                      "resolve.",
        "rationale": "REJECT from Q1/Q2 at a NON-POSITIVE endpoint. This is the "
                     "rival that refuted the previous revision of this spec, which "
                     "carried `require 0 < lo` / `require 0 < hi` and therefore "
                     "said NOTHING about a request with a non-positive endpoint — "
                     "so the rival satisfied it while failing the F2P. The repaired "
                     "spec is total over the carrier, so the same rival is now "
                     "refuted at (4,-5), the failing test's own request shape: "
                     "`4 > -5` holds so `committedLimits 4 (-5)` = the normalizer's "
                     "pair exchanged, while the rival's guard is false (`0 < -5` "
                     "fails) so it commits the pair as reported. Conditioned on "
                     "(normalize 4 (-5)).1 ≠ (normalize 4 (-5)).2. NOTE this is the "
                     "ONLY rival refuted outside the strictly-positive quadrant; it "
                     "is the case that measures the domain widening, and it would "
                     "PASS (verify) against the previous revision.",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi) (hneg : hi < originEndpoint)\n"
            "    (h : (normalize lo hi).1 ≠ (normalize lo hi).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_neg (show ¬ (lo > hi ∧ originEndpoint < lo ∧ "
            "originEndpoint < hi)\n"
            "        from fun hc => absurd hc.2.2 (asymm hneg)),\n"
            "      if_pos hd]\n"
            + _INJECT +
            "  exact h heq.1\n",
    },

    # ---- reads the orientation off the CALLEE'S ANSWER instead of the request:
    # ---- the freedom the deleted `normalize_ascending` axiom used to hide. ----
    {
        "id": "reject-postcall-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- Read the orientation off the NORMALIZER'S ANSWER instead of the\n"
            "    -- request: commit the pair canonically ascending. The request's\n"
            "    -- own orientation is never consulted.\n"
            "    let swapped := n.1 > n.2\n"
            "    let out := if swapped then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "deriving the committed orientation from the normalizer's "
                      "reported order canonicalizes every committed interval "
                      "ascending, so a descending request whose normalized pair "
                      "came back ascending is committed ascending. That is the "
                      "pre-patch defect with an extra canonicalization step: the "
                      "faithful counterpart still fails the failing test's "
                      "descending legs, so it does NOT resolve.",
        "rationale": "REJECT from Q1/Q2. This is the rival that exploits exactly "
                     "the freedom the deleted `normalize_ascending` axiom used to "
                     "hide: while the spec ASSUMED the callee always reported "
                     "ascending, `n.1 > n.2` was provably false and reading the "
                     "flag after the call was indistinguishable from not restoring "
                     "at all. With the axiom gone, the flag must be read off the "
                     "REQUEST, and Q1 says so. Refuted at (10,1) conditioned on "
                     "(normalize 10 1).1 < (normalize 10 1).2 — realisable, and "
                     "indeed the DEFAULT-locator behaviour of the modeled callee "
                     "(it canonicalizes a descending request to ascending), so the "
                     "hypothesis is the honest common case rather than a corner. "
                     "There the rival's guard is false, so it commits `(n.1, n.2)` "
                     "while `committedLimits 10 1` = `(n.2, n.1)`.",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi)\n"
            "    (h : (normalize lo hi).1 < (normalize lo hi).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_neg (not_lt.mpr (le_of_lt h)), if_pos hd]\n"
            + _INJECT +
            "  exact (ne_of_lt h) heq.1\n",
    },

    # ---- PARTIAL-DOMAIN GUARD on the OBSERVABLE the repair introduced: restore
    # ---- only when the normalizer happened to report ascending. Satisfies every
    # ---- conditioned orientation clause (Q4/Q5/Q6) and nothing more. ----
    {
        "id": "reject-ascending-gate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let swapped := lo > hi\n"
            "    let n ← normalizeRange lo hi\n"
            "    -- Restore the requested orientation only when the normalizer\n"
            "    -- happened to report its pair ascending: a guard on exactly the\n"
            "    -- antecedent of the conditioned orientation clauses.\n"
            "    let out := if swapped ∧ n.1 ≤ n.2 then (n.2, n.1) else (n.1, n.2)\n"
            "    return out"),
        "refinement": "restoring only when the normalizer reported ascending leaves "
                      "a descending request unrestored whenever the normalizer "
                      "reported descending — the scales whose normalizer preserves "
                      "the order it received. A faithful counterpart therefore "
                      "still commits some descending requests in the wrong "
                      "orientation, so it does NOT match gold, which restores "
                      "unconditionally on `lo > hi`.",
        "rationale": "REJECT from Q1/Q2 — and this rival is the reason those "
                     "clauses had to be KEPT when the orientation content was "
                     "conditioned on the observable. It satisfies Q4, Q5 AND Q6 "
                     "identically to gold (its guard is literally Q4/Q5's "
                     "antecedent conjoined with the request test), so a spec "
                     "carrying only the conditioned clauses would accept it. Q1 "
                     "refuses: at a descending request whose normalized pair came "
                     "back DESCENDING the rival commits `(n.1, n.2)` where "
                     "`committedLimits` = `(n.2, n.1)`. Refuted at (10,1) "
                     "conditioned on (normalize 10 1).2 < (normalize 10 1).1, "
                     "realisable on the order-preserving members of the callee "
                     "family (the counterexamples that killed the old ascending "
                     "axiom: a descending request comes back descending).",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi)\n"
            "    (h : (normalize lo hi).2 < (normalize lo hi).1) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_neg (show ¬ (lo > hi ∧ (normalize lo hi).1 ≤ "
            "(normalize lo hi).2)\n"
            "        from fun hc => absurd h (not_lt.mpr hc.2)),\n"
            "      if_pos hd]\n"
            + _INJECT +
            "  exact (ne_of_lt h) heq.1.symm\n",
    },

    # ---- OVER-APPROXIMATION: commit a canonically oriented interval built from
    # ---- min/max, satisfying every orientation clause without committing the
    # ---- normalizer's own pair. ----
    {
        "id": "reject-canonicalize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    let n ← normalizeRange lo hi\n"
            "    -- Canonicalize the normalizer's pair to ascending FIRST, then\n"
            "    -- orient THAT by the request: the requested orientation is\n"
            "    -- honoured, but which endpoint the normalizer reported as the low\n"
            "    -- one is discarded.\n"
            "    let asc := if n.1 ≤ n.2 then (n.1, n.2) else (n.2, n.1)\n"
            "    let out := if lo > hi then (asc.2, asc.1) else asc\n"
            "    return out"),
        "refinement": "canonicalizing the normalized pair to ascending before "
                      "committing it discards which endpoint the normalizer "
                      "reported as low. Whenever the normalizer reports its pair "
                      "descending — the scales whose normalizer preserves the "
                      "received order — the faithful counterpart commits the two "
                      "endpoints the other way round from gold, so it does NOT "
                      "match gold behaviour.",
        "rationale": "REJECT from Q1/Q2/Q3, the pure OVER-APPROXIMATION rival: it "
                     "satisfies every orientation clause Q4/Q5/Q6 by construction "
                     "(its output is descending exactly when the request was), so "
                     "the orientation clauses alone cannot see it, and it is "
                     "refuted only by the exact-value clauses. That is what those "
                     "clauses are for: the spec pins the committed pair to the "
                     "normalizer's OWN components, re-arranged, not to any pair "
                     "with the right order. Refuted at (10,1) conditioned on "
                     "(normalize 10 1).2 < (normalize 10 1).1, where the "
                     "canonicalization step reverses the pair before the request's "
                     "orientation is applied, so the rival commits `(n.1, n.2)` "
                     "while `committedLimits` puts `n.2` first.",
        "witness":
            "example (lo hi : Endpoint) (hd : lo > hi)\n"
            "    (h : (normalize lo hi).2 < (normalize lo hi).1) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_neg (not_le.mpr h), if_pos hd]\n"
            + _INJECT +
            "  exact (ne_of_lt h) heq.1.symm\n",
    },

    # ---- ORACLE ECHO, wrong: echo the reference expansion at TRANSPOSED
    # ---- arguments. ----
    {
        "id": "reject-echo-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Echo the reference expansion, but read it off the TRANSPOSED\n"
            "    -- request `(hi, lo)`: the orientation is taken from the wrong end.\n"
            "    let _n ← normalizeRange lo hi\n"
            "    let out := committedLimits hi lo\n"
            "    return out"),
        "refinement": "echoing the reference expansion at the transposed request "
                      "normalizes the WRONG pair: the callee is consulted with the "
                      "endpoints exchanged, so both the interval it conditions and "
                      "the orientation it restores come from `(hi, lo)`. A faithful "
                      "counterpart swaps the requested endpoints before handing "
                      "them to the axis normalizer, which changes the committed "
                      "interval on every asymmetric request, so it does NOT match "
                      "gold behaviour.",
        "rationale": "REJECT from Q1 — the ECHO family, made wrong. A rival cannot "
                     "pass this spec by copying an answer key (there is none: the "
                     "committed pair is a re-arrangement of an opaque callee's "
                     "output), but it can echo the reference EXPRESSION at the "
                     "wrong arguments, and Q1 pins the arguments too. Refuted at "
                     "the ascending point (1,10): gold commits `normalize 1 10` "
                     "while the rival commits `((normalize 10 1).2, (normalize 10 "
                     "1).1)`, conditioned on the single disequality "
                     "(normalize 1 10).1 ≠ (normalize 10 1).2. Realisable on the "
                     "canonicalizing members of the callee family, where "
                     "`normalize 1 10 = (1, 10)` and `normalize 10 1 = (1, 10)`, so "
                     "the hypothesis reads 1 ≠ 10. This is also the case that "
                     "distinguishes the honest pos-pure-reference positive (same "
                     "expression, RIGHT arguments) from an echo.",
        "witness":
            "example (lo hi : Endpoint) (ha : lo < hi)\n"
            "    (h : (normalize lo hi).1 ≠ (normalize hi lo).2) :\n"
            "    (commitLimits lo hi).run ≠ DivM.res (committedLimits lo hi) := by\n"
            + _UNFOLD +
            "  simp only [if_pos ha, if_neg (not_lt.mpr (le_of_lt ha))]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },

    # ---- ORACLE ECHO across the two modeled operations: answer with the OTHER
    # ---- one's reference expression. Stated at THIS operation's level because
    # ---- that is the only level at which it can be stated: the member's level
    # ---- has no name for this operation's reference expression, nor for the
    # ---- chain that expression is written in terms of (Solution.lean's LAYERING
    # ---- block), and a rival that cannot be written is not a rival a battery can
    # ---- carry. Here both reference expressions are in scope, so the rival is
    # ---- writable and has to be refused. ----
    {
        "id": "reject-echo-sibling-expression",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    -- Echo the SIBLING operation's reference expression: report what\n"
            "    -- the default normalizer member owes, rather than what this\n"
            "    -- operation commits.\n"
            "    let _n ← normalizeRange lo hi\n"
            "    let out := defaultMemberPair lo hi\n"
            "    return out"),
        "refinement": "a limit setter that consults the axis normalizer chain, "
                      "throws its answer away, and commits the SHARED widener "
                      "applied to its own sorted request instead "
                      "(`transforms.nonsingular(min, max, expander=.05)`). Two "
                      "faithfulness failures at once: the wrong widening step (the "
                      "chain applies each scale's own expander — a date axis widens "
                      "a degenerate request by 1e-7 days, not by 5%) and no "
                      "reinstatement of the requested orientation, so a descending "
                      "request comes back ascending and the failing test's leg "
                      "stays broken.",
        "rationale": "REJECT from Q1 (measured). The ECHO family made "
                     "cross-operational: with TWO operations modeled in one file "
                     "there is a second reference expression lying around, and a "
                     "rival that reaches for it must be refused. Refuted at the "
                     "degenerate request (v, v) conditioned on "
                     "normalize v v ≠ expandAscending v v, realisable on the "
                     "members whose widening step is not the shared 5% expander "
                     "(measured by axiom_check.py: a date axis widens a degenerate "
                     "request by 1e-7 days, the shared widener by 5%). This "
                     "REPLACES the member-level form of the same rival (the "
                     "member answering with `committedLimits e0 e1`): that form is "
                     "no longer WRITABLE, because the chain's vocabulary is "
                     "declared below the member operation and so `normalize` and "
                     "`committedLimits` are not in scope there. Same hazard, same "
                     "discriminating fact, stated at the level where the two "
                     "expressions really do sit side by side.",
        "witness":
            "example (v : Endpoint) (h : normalize v v ≠ expandAscending v v) :\n"
            "    (commitLimits v v).run ≠ DivM.res (committedLimits v v) := by\n"
            + _UNFOLD +
            "  simp only [defaultMemberPair, if_neg (lt_irrefl v)]\n"
            "  intro heq\n"
            "  rw [DivM.res.injEq] at heq\n"
            "  exact h heq.symm\n",
    },

    # =====================================================================
    # THE SECOND DEFENDED OPERATION — `defaultMemberAdjust`, the callee-side
    # half of the same gold patch. Everything below attacks THIS method; the
    # `commitLimits` body is verbatim gold in every one of these cases.
    # =====================================================================
    {
        "id": "pos-member-branch-select",
        "kind": "soundness",
        "expect": "verify",
        # Restructure the control flow: branch on the sort test FIRST and call
        # the widener inside each arm, instead of sorting into two locals and
        # calling it once. Two call sites, two returns.
        "module": _impl2(
            "    if e1 < e0 then\n"
            "      let e ← expandRange e1 e0\n"
            "      return e\n"
            "    else\n"
            "      let e ← expandRange e0 e1\n"
            "      return e"),
        "refinement": "identical function of the two arguments — each arm applies "
                      "the widener to the same ascending pair the frozen body "
                      "computes, and reports it unchanged. Value-identical to gold "
                      "on every input, so the faithful counterpart is the gold "
                      "patch with the member's body written as an if/else.",
        "rationale": "MUST VERIFY (else SPEC-TOO-STRONG on the new operation). "
                     "P1-P4 are stated about the REPORTED PAIR, not about how many "
                     "times the widener is invoked or where, so a control-flow "
                     "restructuring must pass. Measured exit 0 under the FROZEN "
                     "tactic body `loom_solve`, i.e. no proof burden is added; it "
                     "is the staging control for the second operation.",
    },
    {
        "id": "pos-member-demorgan-guard",
        "kind": "soundness",
        "expect": "verify",
        # (uses _impl2_and_proof: the retune is of the member's ELIDED tactic
        # body only, so no spec byte moves and the obligation is kept.)
        # Sort with the DE MORGAN DUAL of the frozen guard — `e0 ≤ e1` on the
        # arguments as they arrived, rather than `e1 < e0` — and widen from
        # inside each arm. Two call sites, two returns, and the guard is a
        # DIFFERENT relation at a different argument order, so neither frozen
        # `@[grind]` lemma applies to the residual goals as written.
        "module": _impl2_and_proof(
            "    -- The De Morgan dual of the frozen sort guard: decide the ASCENDING\n"
            "    -- pair with `≤` on the arguments as they arrived, and widen from\n"
            "    -- inside the arm. Two call sites, two returns, same reported pair.\n"
            "    if e0 ≤ e1 then\n"
            "      let e ← expandRange e0 e1\n"
            "      return e\n"
            "    else\n"
            "      let e ← expandRange e1 e0\n"
            "      return e",
            "prove_correct defaultMemberAdjust by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "      | (rw [defaultMemberPair_ordered _ _ (not_lt.mpr ‹_›)]; simp_all)\n"
            "      | (rw [defaultMemberPair_reversed _ _ (lt_of_not_le ‹_›)]; simp_all)\n"
            "      | simp_all\n"),
        "refinement": "the same sort-then-widen composition with the guard written "
                      "as its De Morgan dual: `e0 ≤ e1` selects the as-arrived "
                      "argument order where `¬ (e1 < e0)` does, and the complementary "
                      "arm widens the exchanged pair. Value-identical to gold on "
                      "every input including the degenerate one, so the faithful "
                      "counterpart is the same member with an `if/else` on `<=`.",
        "rationale": "MUST VERIFY (else SPEC-TOO-STRONG on the member). This is the "
                     "member-side SPEC-TOO-STRONG carrier, and unlike the two "
                     "positives above it is NOT closed by the frozen tactic body: "
                     "`loom_solve` alone leaves P4 unsolved as `(defaultMemberPair e0 "
                     "e1).1 ≤ (defaultMemberPair e0 e1).2 → x.1 ≤ x.2` under `x = "
                     "expandAscending e0 e1` and `e0 ≤ e1` (measured exit 1), because "
                     "the arm's hypothesis is a `≤` on the arguments as they arrived "
                     "while the clause's reference pair is an `if` on the strict `<` "
                     "of the exchanged pair — nothing connects them until "
                     "`defaultMemberPair` is reduced through the RIGHT frozen lemma "
                     "for the arm. It verifies with the retuned (spec-elided) body "
                     "that picks that lemma per arm — `defaultMemberPair_ordered` "
                     "under `not_lt.mpr` for the ascending arm, "
                     "`defaultMemberPair_reversed` under `lt_of_not_le` for the other "
                     "(measured exit 0). Recorded honestly: an EARLIER revision of "
                     "this file claimed this reshape's retunes had been 'measured and "
                     "failed' and shipped it as a documented non-case. That claim was "
                     "wrong — the per-arm form above closes it — so the case is live "
                     "rather than described, which is the difference between a "
                     "measured positive and an asserted one.",
    },
    {
        "id": "pos-member-pure-reference",
        "kind": "soundness",
        "expect": "verify",
        # Report the pure reference expression directly, never calling the
        # widener stub at all.
        "module": _impl2(
            "    -- Report the pure reference pair directly: the widener stub is\n"
            "    -- never invoked, so nothing about the CALL survives — only the\n"
            "    -- value, which is what the clauses are about.\n"
            "    let out := defaultMemberPair e0 e1\n"
            "    return out"),
        "refinement": "`defaultMemberPair` IS the sort-then-widen composition in "
                      "pure form (`Solution.lean:74-75`), so this reports exactly "
                      "the pair the frozen body reports; value-identical to gold on "
                      "every input.",
        "rationale": "MUST VERIFY. Complements pos-member-branch-select from the "
                     "other side: that one keeps the calls and moves them, this one "
                     "removes them entirely. Together they establish that P1-P4 pin "
                     "the reported VALUE and nothing about the callee protocol — the "
                     "correct strength for a spec whose subject is which pair the "
                     "member hands back. Measured exit 0 under the frozen body.",
    },

    # ---- DROPPED OBLIGATION on the new operation, and the exact refinement that
    # ---- refuted the previous revision of this bundle: implement the caller half
    # ---- perfectly and leave this member at its PRE-PATCH behaviour. ----
    {
        "id": "reject-member-restores-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2(
            "    -- Sort, widen — and then PUT THE PAIR BACK the way the arguments\n"
            "    -- arrived, keeping the orientation authority on the callee side.\n"
            "    let reversed := e1 < e0\n"
            "    let a := if reversed then e1 else e0\n"
            "    let b := if reversed then e0 else e1\n"
            "    let e ← expandRange a b\n"
            "    let out := if reversed then (e.2, e.1) else (e.1, e.2)\n"
            "    return out"),
        "refinement": "this is the default locator's adjust step in its ORIGINAL "
                      "behaviour: the shared widener sorts internally and this "
                      "caller then reinstates the incoming order on the way out. "
                      "The faithful counterpart keeps the caller-side half of the "
                      "change and leaves this member's restore in place, and it "
                      "DOUBLE-SWAPS: the member "
                      "restores the requested order and then `commitLimits` "
                      "restores it again, so a descending request comes out "
                      "ascending on the LINEAR default-locator path. Measured "
                      "against the instance: does NOT resolve — F2P 0/1 and P2P "
                      "397/400, the three regressions being the pre-existing linear "
                      "legs of the failing test itself plus test_inverted_cla.",
        "rationale": "REJECT from P1/P2/P4. THIS IS THE RIVAL THAT REFUTED THE "
                     "PREVIOUS REVISION of this bundle, where the callee-side half "
                     "of the gold patch was not modeled at all: an impl that "
                     "implemented `commitLimits` byte-for-byte and left this member "
                     "alone verified against the frozen spec while failing the "
                     "test, so the spec could not see a load-bearing half of the "
                     "fix. It is refuted at (10, 1) — the failing test's own "
                     "request — conditioned on the widener reporting its ascending "
                     "argument pair in ascending order, which is the DEFAULT and "
                     "not a corner: `transforms.nonsingular(1, 10, expander=.05)` "
                     "returns (1.0, 10.0). Gold reports that pair; the rival "
                     "reports it exchanged.",
        "witness":
            "example (e0 e1 : Endpoint) (hr : e1 < e0)\n"
            "    (h : (expandAscending e1 e0).1 < (expandAscending e1 e0).2) :\n"
            "    (defaultMemberAdjust e0 e1).run ≠ "
            "DivM.res (defaultMemberPair e0 e1) := by\n"
            + _UNFOLD2 +
            "  simp only [if_pos hr]\n"
            + _INJECT +
            "  exact (ne_of_lt h) heq.1.symm\n",
    },

    # ---- OVER-APPROXIMATION on the new operation: get the F2P direction right by
    # ---- exchanging unconditionally, which also breaks the ascending direction. ----
    {
        "id": "reject-member-swap-always",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2(
            "    -- Report the widened pair EXCHANGED, whatever order the arguments\n"
            "    -- arrived in: descending is now this member's fixed output shape.\n"
            "    let reversed := e1 < e0\n"
            "    let a := if reversed then e1 else e0\n"
            "    let b := if reversed then e0 else e1\n"
            "    let e ← expandRange a b\n"
            "    let out := (e.2, e.1)\n"
            "    return out"),
        "refinement": "a member that returns `(vmax, vmin)` unconditionally. The "
                      "faithful counterpart appends `return e1, e0` to the default "
                      "locator's adjust step after the widening call, and every "
                      "ASCENDING request on the linear default path then commits "
                      "descending — including a plain ascending request of "
                      "`(1, 10)` that "
                      "essentially every axes test performs, so it does NOT "
                      "resolve.",
        "rationale": "REJECT from P1/P2/P3/P4 (all four unsolved, measured). The "
                     "over-approximation family: this rival satisfies the ONE fact "
                     "the previous revision's narrative used to justify leaving the "
                     "callee unmodeled — 'the member does not preserve the "
                     "requested order' — and it satisfies it in the strongest "
                     "possible way, by never preserving anything. P4 is what "
                     "refuses it: whenever the widened interval is itself ordered, "
                     "the member's OWN output must be ordered too, whichever way "
                     "round its arguments arrived. Refuted at the ASCENDING point "
                     "(1, 10), the direction the F2P leg does not test, under the "
                     "same default-widener hypothesis.",
        "witness":
            "example (e0 e1 : Endpoint) (ho : e0 < e1)\n"
            "    (h : (expandAscending e0 e1).1 < (expandAscending e0 e1).2) :\n"
            "    (defaultMemberAdjust e0 e1).run ≠ "
            "DivM.res (defaultMemberPair e0 e1) := by\n"
            + _UNFOLD2 +
            "  simp only [if_neg (asymm ho)]\n"
            + _INJECT +
            "  exact (ne_of_lt h) heq.1.symm\n",
    },

    # ---- PARTIAL-DOMAIN GUARD on the new operation: bypass the widener exactly
    # ---- where widening is the whole point of calling it. ----
    {
        "id": "reject-member-degenerate-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl2(
            "    -- Short-circuit the degenerate case: hand back the requested pair\n"
            "    -- untouched when the two endpoints coincide, and only widen\n"
            "    -- otherwise.\n"
            "    let reversed := e1 < e0\n"
            "    let a := if reversed then e1 else e0\n"
            "    let b := if reversed then e0 else e1\n"
            "    let e ← expandRange a b\n"
            "    let out := if e0 = e1 then (e0, e1) else (e.1, e.2)\n"
            "    return out"),
        "refinement": "a member that early-returns `(e0, e1)` when `e0 == e1` "
                      "instead of calling `mtransforms.nonsingular`. The faithful "
                      "counterpart drops the singular case the widener exists to "
                      "handle, so a zero-width axis stays zero-width and the "
                      "transform is degenerate — this is the direction "
                      "`test_inverted_cla` and the degenerate-limits tests read, so "
                      "it does NOT resolve.",
        "rationale": "REJECT from P1/P3 (measured). The partial-domain family "
                     "applied to the NEW operation: the rival agrees with gold "
                     "everywhere except on the sub-domain `e0 = e1`, where the "
                     "orientation content of P2/P4 is vacuous (a degenerate pair "
                     "has no orientation) and only the exact-value clauses can "
                     "carry the rejection. It is the tightest near-miss this "
                     "surface admits. Refuted at (3, 3) conditioned on "
                     "(expandAscending 3 3).1 ≠ 3, which is TRUE of the modeled "
                     "callee — `transforms.nonsingular(3, 3, expander=.05)` widens "
                     "to (2.85, 3.15) — while the analogous claim at a wide "
                     "interval would be FALSE (the widener is value-preserving "
                     "there), so the point is chosen by the carrier, not for "
                     "convenience. "
                     "GUARD MECHANICS: the reduced goal carries the sort guard "
                     "`v < v` at TWO types (once per sorted argument and once for "
                     "the pair) AND the rival's own degeneracy test `v = v`, which "
                     "`simp only` closes to `True` on its own. So the guard is "
                     "discharged as a simp LEMMA (`simp only [if_neg (lt_irrefl "
                     "v)]`), which matches at every type, rather than with a `rw` "
                     "that instantiates only one of them and leaves the rival's "
                     "branch standing (measured exit 1 on the rival: `heq.left has "
                     "type (if v < v then … else …).1 = (if True then (v, v) else "
                     "…).1`) — a TACTIC gap attributing nothing to the spec. With "
                     "the guard closed at every occurrence the rival's own branch "
                     "reduces to `(v, v)` and the injection puts `expandAscending v "
                     "v).1 = v` in hand, which the hypothesis refutes.",
        "witness":
            "example (v : Endpoint) (h : (expandAscending v v).1 ≠ v) :\n"
            "    (defaultMemberAdjust v v).run ≠ "
            "DivM.res (defaultMemberPair v v) := by\n"
            + _UNFOLD2 +
            "  simp only [if_neg (lt_irrefl v)]\n"
            + _INJECT +
            "  exact h heq.1.symm\n",
    },
]


# ===========================================================================
# ACCOUNTING. 23 SPEC cases: 6 soundness positives, 2 admissibility, 15
# uniqueness rivals. The battery defends TWO operations — (1) commit a requested
# endpoint pair through an axis normalizer, reinstating the request's
# orientation (`commitLimits`, 17 cases) and (2) the DEFAULT normalizer member,
# which sorts-and-widens and reports the widened ascending pair without putting
# it back (`defaultMemberAdjust`, 6 cases) — plus their two subordinate callee
# stubs. The two operations are the two coordinated halves of the gold patch and
# each is independently observable, which is why both are defended.
#
# WHAT CHANGED IN THIS REVISION, and why every change is a STRENGTHENING.
#   The previous revision's spec had `require 0 < lo`, `require 0 < hi` and an
#   axiom `normalize_ascending` (the callee always reports ascending on positive
#   distinct endpoints). Both were deleted, and three clauses were added.
#   * DOMAIN WIDENED. `commitLimits` is now total over the carrier: every
#     requested pair, either sign, either order, degenerate included. The old
#     preconditions excluded the failing test's own inputs ((4.0,-5.0),
#     (5.0,-3.0) on a linear axis), which is how reject-positivity-gate slipped
#     through. Recorded by admiss-negative-endpoint (the point is in-domain and
#     the obligation is live there) and enforced by reject-positivity-gate (the
#     rival is now refuted AT that point).
#   * AXIOM DELETED. `normalize_ascending` was false of the real patched code on
#     several scales, and it also gave the impl-prover a fact the operation is
#     not entitled to. With it gone the normalizer's output order is an
#     OBSERVABLE: Q4/Q5/Q6 take it as a hypothesis. Fewer assumptions = a
#     stronger obligation, and the two rivals that lived in the gap it left
#     (reject-postcall-flag, reject-ascending-gate) are now refuted.
#   * CLAUSES ADDED. Q2/Q3 spell the committed pair branch-by-branch against the
#     normalizer's result, and Q6 makes the orientation correspondence
#     BI-directional at a non-degenerate reported interval. Q1 (the exact
#     committed pair) was kept verbatim; it is the clause that refuses every
#     rival which gets the orientation right but the pair wrong
#     (reject-canonicalize, reject-ascending-gate).
#   * A SECOND OPERATION ADDED. The revision that made the above changes still
#     modeled only the caller half of the gold patch, and an impl that leaves the
#     callee half at base_commit verified against it while NOT resolving (F2P
#     0/1, P2P 397/400 — measured). `defaultMemberAdjust` + P1-P4 + a second
#     prepatch twin close that: the spec now obligates the member to report the
#     WIDENED ASCENDING pair, which is what makes the caller's reinstatement the
#     only exchange in the composition. Strictly more obligations (a whole
#     operation's worth), one more bare axiom (`expandAscending`, a function type
#     asserting nothing about values or order) and no new precondition anywhere.
#     reject-member-restores-order IS that refuting refinement, now rejected.
#
# ATTACK FAMILIES (15 rivals; each family is why its rival exists).
#   over-approximation      reject-canonicalize      right order, wrong pair
#   partial-domain guard    reject-positivity-gate   guard = the deleted precond
#                           reject-ascending-gate    guard = the new antecedent
#   boundary token swap     reject-cmp-ge            `>` relaxed to `≥`
#                           reject-cmp-lt            `>` flipped to `<`
#   oracle echo             reject-echo-transposed   right expression, wrong args
#                           reject-echo-sibling-expression  the OTHER modeled
#                                                    operation's expression
#   freedom left by repair  reject-postcall-flag     orientation read off the
#                                                    callee, not the request
#   dropped obligation      reject-no-restore        the pre-patch bug (G-DIFF)
#                           reject-always-swap       unconditional exchange
#   value (not order) half  reject-partial-no-expand normalizer bypassed
#                           reject-equal-raw         bypassed at `lo = hi` only
#   ---- and on the SECOND operation (`defaultMemberAdjust`) ----
#   dropped obligation      reject-member-restores-order  the pre-patch member,
#                                                    i.e. THE refinement that
#                                                    refuted the last revision
#                                                    (also the 2nd G-DIFF twin)
#   over-approximation      reject-member-swap-always exchange unconditionally
#   partial-domain guard    reject-member-degenerate-raw  widener bypassed exactly
#                                                    where widening is the point
#   (the ORACLE ECHO rival for this operation is stated at the caller's level,
#   reject-echo-sibling-expression: the member's level has no name for the
#   chain or for the caller's reference expression, so the member-level form
#   of it does not elaborate and would prove nothing.)
#   NOT SHIPPED, and why: the "sort the wrong way round" / "sort descending" /
#   "gate the sort" family. The shared widener sorts internally,
#   so it is SYMMETRIC in its arguments; refuting any
#   of those rivals needs `expandAscending 10 1 ≠ expandAscending 1 10`, which is
#   FALSE of the real callee. Shipping one would refute it only at a point the
#   carrier never realises — a forged witness under a satisfiable hypothesis. The
#   honest coverage of that freedom is P2/P3 naming the arguments plus G-CONF,
#   which executes the member against the real post-patch source.
#
# TUNED WRONG IMPLS PROBED BEYOND THE SHIPPED 15 (no clause weakened; each was
#   built against the frozen spec and each was REJECTED, exit 1, so none is a
#   spec hole and none needed shipping): the callee handed its arguments
#   transposed (`normalizeRange hi lo`); the member never sorting at all; the
#   member's sort guard relaxed `<` to `≤`; the caller committing only the `lo`
#   component twice (`(n.1, n.1)`); the orientation guard conjoined with a
#   sub-origin test (`lo > hi ∧ originEndpoint < lo`) and with a super-origin
#   test (`lo > hi ∧ hi ≤ originEndpoint`) — the two partial-domain guards the
#   shipped `reject-positivity-gate` region generalises; and the member
#   exchanging its pair exactly on the degenerate request (`e0 = e1`). Q1-Q6 and
#   P1-P4 refuse all seven.
#   CORRECT RESHAPES PROBED for the SPEC-TOO-STRONG direction, all three VERIFY
#   (exit 0), so the spec is not over-tight on the shapes it most plausibly could
#   be: the caller's guard written `hi < lo` instead of `lo > hi`; the commit
#   written with `Prod.swap n`; and the member with no callee call at all,
#   returning the `if`-expression over `expandAscending` directly. Two further
#   reshapes are REJECTED but are NOT faithful on this carrier, and the reason is
#   the carrier and not the spec: passing the member's pair reversed
#   (`if e1 < e0 then e0 else e1`, …) and pre-sorting the caller's callee
#   arguments (`normalizeRange (min lo hi) (max lo hi)`). Both are behaviour-
#   preserving only if the opaque callees are SYMMETRIC / sort-invariant, which
#   the bare axioms deliberately do not assert; measured in isolation, neither
#   `normalize (min lo hi) (max lo hi) = normalize lo hi` nor the reversed-argument
#   identity is provable, so on this carrier they denote DIFFERENT functions and
#   their rejection is correct. (Callee symmetry is real in the source and is
#   checked where it is checkable: axiom_check.py §G and G-CONF.)
#
# WITNESS DISTINCTNESS. An `Endpoint` carries no numerals, so a witness point is
# not a literal pair — it is a REGION of the carrier, named by the order relation
# its binders stand in. What has to be distinct is therefore the (region,
# hypothesis) pair, and every rival gets its own: all three request orientations
# (descending, degenerate, ascending) are exercised, one region lies outside the
# quadrant the previous revision admitted, and the DESCENDING region carries five
# rivals under FOUR mutually exclusive hypotheses about the normalizer's reported
# order — which is itself the point, since the repaired spec must hold whichever
# way the callee reports.
#   region                        hypothesis   rival
#   lo > hi   descending          n.1 ≠ n.2    reject-no-restore, reject-cmp-lt
#   lo > hi   descending          n.1 < n.2    reject-postcall-flag
#   lo > hi   descending          n.2 < n.1    reject-ascending-gate,
#                                              reject-canonicalize
#   lo > hi ∧ hi < originEndpoint descending, sub-origin
#                                 n.1 ≠ n.2    reject-positivity-gate  <- outside
#                                              the old precondition's quadrant
#   v v       degenerate          n.1 ≠ n.2    reject-cmp-ge
#   v v       degenerate          n.1 ≠ v      reject-partial-no-expand,
#                                              reject-equal-raw
#   lo < hi   ascending           n.1 ≠ n.2    reject-always-swap
#   lo < hi   ascending           cross-point  reject-echo-transposed
#   v v       degenerate  normalize v v ≠ expandAscending v v
#                                              reject-echo-sibling-expression
# Neither binder is pinned in any witness: `lo` and `hi` are universally
# quantified and constrained only by their order, so each rival is refuted on a
# whole region rather than at one sampled pair — strictly more than a literal
# point established, and the only form the carrier admits. Two rivals sharing a
# (region, hypothesis) row are refuted by DIFFERENT clauses on different branches
# (reject-no-restore fails the descending branch of Q2 outright; reject-cmp-lt
# additionally mis-selects on the ascending side, and its witness has to discharge
# the rival's own `lo < hi` guard, which reject-no-restore has no analogue of).
# The second operation's three rivals add three more (region, hypothesis) rows,
# and they exercise both orientations plus the degenerate case:
#   e1 < e0   descending  (expandAscending e1 e0).1 < .2
#                                              reject-member-restores-order
#   e0 < e1   ascending   (expandAscending e0 e1).1 < .2
#                                              reject-member-swap-always
#   v v       degenerate  (expandAscending v v).1 ≠ v
#                                              reject-member-degenerate-raw
# The two order-attacking rows are the SAME hypothesis at OPPOSITE orientations,
# which is the content of P4: whichever way round the arguments arrive, what the
# member reports is ordered whenever the widened interval is.
#
# POSITIVES AND THE REPROOF BURDEN. Only the cheapest positive
# (pos-inline-orientation, a zeta-reduction of gold) closes under the frozen
# tactic body; the other two need a RETUNE of that body, which is elided from the
# consumer spec view and so changes no spec byte. Both retunes are recorded with
# the frozen-body measurement they replace, because "it did not verify" is the
# default outcome of reshaping an impl on a tactic backend and a positive that
# hid its reproof burden would be claiming more than it measured:
#   * pos-branch-select — hoisting the request branch ABOVE the callee call
#     removes the program's own `if` from each residual goal, so the frozen body's
#     `split` has nothing to split (measured exit 1, three unsolved goals: Q5, Q3
#     and Q6, each under a contradictory antecedent about `lo` and `hi`). Closed
#     by dropping that `split` and letting `simp_all [asymm, not_lt, lt_asymm]`
#     use the order's own asymmetry (measured exit 0).
#   * pos-pure-reference — committing the reference expansion leaves the pair
#     un-materialised, so Q4/Q5/Q6 have to go through the definition (measured
#     exit 1 under the frozen body). Closed by `simp_all [committedLimits, asymm,
#     not_lt] <;> split <;> simp_all [asymm]` (measured exit 0): unfold FIRST,
#     then split the definition's own `if`. `grind [committedLimits]` does NOT
#     close it on this carrier (measured exit 1 on all three orientation goals) —
#     an endpoint supports only comparison, so nothing can evaluate
#     `committedLimits lo hi` to a pair and projecting out of an opaque
#     `normalize` application yields no further equalities. That case carries the
#     SPEC-TOO-STRONG direction. All three are honest positives: each is
#     value-identical to gold on every input. The second operation
# adds three more. Two close under ITS frozen body (`loom_solve`, measured exit
# 0): pos-member-branch-select moves the widener call INTO two branches (two call
# sites, two returns) and pos-member-pure-reference removes the call entirely and
# reports `defaultMemberPair e0 e1`. Between them they establish that P1-P4 pin
# the reported VALUE and nothing about the callee protocol — but both are staging
# controls, so neither carries the member-side SPEC-TOO-STRONG direction on its
# own. The third does:
#   * pos-member-demorgan-guard — the De Morgan dual of the frozen sort guard,
#     `if e0 ≤ e1 then expandRange e0 e1 else expandRange e1 e0` (two call sites,
#     two returns). `loom_solve` alone leaves P4 unsolved (measured exit 1: the
#     arm's hypothesis is a `≤` on the arguments as they arrived, the clause's
#     reference pair an `if` on the strict `<` of the exchanged pair, and nothing
#     connects them until `defaultMemberPair` is reduced through the frozen lemma
#     matching that arm). Closed by a per-arm retune of the ELIDED tactic body —
#     `rw [defaultMemberPair_ordered _ _ (not_lt.mpr ‹_›)]` for the ascending arm,
#     `rw [defaultMemberPair_reversed _ _ (lt_of_not_le ‹_›)]` for the other, each
#     followed by `simp_all` (measured exit 0). So the member surface now has a
#     positive with a real reproof burden, matching the caller's
#     pos-pure-reference.
#   CORRECTION OF RECORD, made by audit rather than asserted: an earlier revision
#   of this footer listed that reshape among positives whose "retunes measured and
#   failed", concluding the residue was proof engineering the battery would not
#   ship. The per-arm form above closes it, so the claim was false and the case is
#   now LIVE. The lesson is the general one about this class: "no retune works" is
#   a claim about a search, and it must be re-run before it is repeated.
# ONE positive remains measured-and-dropped, and it is a genuine tactic gap:
#   (a) `expandRange (min e0 e1) (max e0 e1)`. Value-identical to gold, and that
#       is PROVEN in isolation against the frozen `@[grind]` lemmas by an
#       `rcases le_or_lt` plus the order rewrites (exit 0):
#           expandAscending (min e0 e1) (max e0 e1) = defaultMemberPair e0 e1
#       with the FALSE neighbour `expandAscending e0 e1 = defaultMemberPair e0 e1`
#       left unsolved by the same script, so the proof is discriminating and not
#       an artefact of the tactic. What does NOT close is the `prove_correct`
#       obligation: the residue is lattice normalisation (`e0 ⊓ e1` / `e0 ⊔ e1`
#       against the `if`-form of `defaultMemberPair`), and it survived
#       `grind [defaultMemberPair, min_def, max_def]`, `rcases le_or_lt` with
#       `min_def`/`max_def`, and `rcases le_or_lt` with the pointwise rewrites
#       `min_eq_right`/`max_eq_left` + the two frozen lemmas (all re-measured at
#       audit, all exit 1 on P4). Recorded rather than shipped because the gap is
#       demonstrably PROOF ENGINEERING and not spec strength — the value-identity
#       proof above is the evidence — and a shipped failing positive would report
#       SPEC-TOO-STRONG for the wrong reason. The missing step, if it is ever
#       wanted live, is a body that discharges the clauses FROM the value-identity
#       lemma rather than re-deriving them per branch.
#
# ADMISSIBILITY WITHOUT A PRECONDITION, AND WITHOUT A LITERAL. The method has no
# `require`, so an admissibility case cannot be "the precondition admits this
# input". Both cases instead assert the obligation is LIVE and SATISFIABLE over a
# REGION of requests — the restore applies there, and the orientation conclusion
# holds there under its own antecedent — and both have a measured negative
# control (reverse the asserted orientation conclusion and the case fails to
# verify, exit 1), so neither assert is decoration. That is the total-carrier
# analogue of PRECOND-TOO-STRONG: if the domain were narrowed again, or the
# clauses made contradictory at a real request, these cases would fail.
#   The region is named by the ORDER relation, not by a literal pair, for the
#   same carrier reason the witnesses are: an `Endpoint` is comparable and
#   movable but never computed, so it has no numerals and no negation, and an
#   assert naming (10,1) or (4,-5) does not elaborate at all (measured: `failed
#   to synthesize OfNat Endpoint 10`, `failed to synthesize Neg Endpoint`). So
#   admiss-f2p-descending quantifies over the DESCENDING requests `b < a` and
#   admiss-negative-endpoint over the descending SUB-ORIGIN requests `b < a ∧
#   b < originEndpoint`, `originEndpoint` being the carrier's distinguished
#   endpoint — the value a real endpoint is compared against for its SIGN — so
#   that second region is exactly the negation of the deleted `0 < hi`
#   precondition, i.e. the region the previous revision excluded and the failing
#   test's own requests inhabit. Quantifying is STRICTLY STRONGER than the
#   literals were: the obligation is asserted live at every request in the
#   region, not at one sampled pair. This is also what pairs
#   admiss-negative-endpoint with reject-positivity-gate, whose guard is that
#   both endpoints lie ABOVE the origin: the rival is refuted on a region this
#   case shows to be in-domain.
#
# normalizeRange and expandRange (the two subordinate `:|` callee stubs):
#   DEFENDED (every variant keeps `do let r :| r = normalize a b; return r` /
#   `do let r :| r = expandAscending a b; return r` and both `prove_correct`
#   blocks verbatim, so their obligations discharge in every case) but NOT
#   independently attacked. They are callee wrappers, not operations under spec:
#   their only `ensures` are `r = normalize a b` and `r = expandAscending a b`,
#   sound by construction of the `:|` choice, and a rival in either would have no
#   F2P consequence — the fix is the orientation capture/restore in `commitLimits`
#   and the removal of the member-side restore in `defaultMemberAdjust`, both of
#   which ARE attacked. A deliberate, reported non-attack.
#
# VACUOUS (frame / permission-mutation): Velvet is referentially transparent and
#   this bundle declares no `mut` binder — the two inputs are immutable
#   `Endpoint` values with no heap footprint — so there is no read-only input to overwrite
#   and no substitute probe to build. The nagini sibling likewise records
#   has_readonly_input=False. Not fabricated.
#
# NOT SHIPPABLE (divergence / non-termination), with the measurement: this file
#   sets `loom.semantics.termination "total"`, so a diverging rival IS rejected —
#   but it is rejected in a way that CANNOT carry a discriminating witness, which
#   is what the reject lane requires. Measured three ways:
#     - an unbounded `while k ≥ 0 do k := k + 1` before the (otherwise correct)
#       commit: exit 1, `Decreasing annotations are required in total correctness
#       semantics` at the impl region;
#     - a local `let rec spin (m : Nat) : Nat := spin (m + 1)`: exit 1,
#       `fail to show termination for`;
#     - the CONTROL that settles it: a plainly TERMINATING `let mut k := 3;
#       while k > 0 do k := k - 1` fails with the BYTE-IDENTICAL first error and
#       the same second error (`Failed to prove assertion without names: WPGen`).
#   So the message is the loop-form obligation demanding an explicit measure, not a
#   detection of divergence: the verifier rejects the terminating and the diverging
#   loop indistinguishably, and the exit code discriminates nothing about
#   termination. The witness half then fails outright — the error is raised while
#   elaborating the impl region, which `witness_file` retains, so it precedes any
#   appended `example`. Measured: the diverging rival with a spec-shaped witness,
#   with a trivial `1 + 1 = 2` witness, and the recursive variant with the trivial
#   witness all exit 1 on that same impl-region error, while the SAME trivial
#   witness against the frozen solution exits 0. A shipped case here would record
#   "rejected" for a compile-time refusal of the loop syntax and attribute it to
#   the spec, which is precisely the vacuous pass the witness rule exists to stop.
#   Consistent with the port's design document, which carries no `diverge-*` /
#   `nonterm-*` case, and with the wider corpus (0 of 456 velvet batteries that
#   discuss divergence ship one as a live case).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job (axiom_check.py validates
#   that `normalize` and `expandAscending` each model a FUNCTION of their two
#   arguments — the only property the bare axioms assert — across scales,
#   locators and signs, and records the realisability of each conditioning
#   hypothesis this battery uses, including the four new ones) and this gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
