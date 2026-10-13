"""properties.py — G-PBT falsification battery for django__django-12050 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct resolveSeq`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, one input binder):

  resolveSeq (value : SeqVal) return (out : SeqVal)
    ensures out.kind = value.kind                       -- (C1) THE FIX
    ensures out.elems = value.elems.map resolveElem     -- (C2) element-wise map

The method resolves an input value that is itself a homogeneous ordered sequence
of sub-values: it resolves each sub-value independently and reassembles them into
a sequence of the SAME kind as the input. ``SeqVal`` carries a ``kind`` tag
(``SeqKind.list`` / ``SeqKind.tuple``, ``DecidableEq``) and an ordered
``elems : List Int``. ``resolveElem : Int → Int`` is the per-element resolution:
it is UNCHANGED by the fix and modeled OPAQUELY (an A-reference, its concrete
value never pinned — only that the SAME map is applied to every element).

TWO independent top-level clauses, both load-bearing:

  * (C1) ``out.kind = value.kind`` — the single line carrying the fix: the result
    is reassembled into the input's kind, never silently coerced to the other
    kind. The pre-patch behaviour forced the result kind to one fixed kind
    regardless of the input; ``Solution_prepatch.lean`` reverts to
    ``kind := SeqKind.tuple`` and violates C1 exactly when the input is a list —
    the F2P scenario Q(name=['a','b']) (a list input) whose resolved rhs must
    read as a list, not a tuple.
  * (C2) ``out.elems = value.elems.map resolveElem`` — every input element
    carried through, in order, with the per-element resolution applied. A
    short/long result (a dropped element), an identity passthrough (raw element,
    resolution skipped), or a broadcast (one element's resolution repeated) each
    diverges from this map.

CARRIER NOTE — WHY EVERY WITNESS REFUTES THE HOARE TRIPLE. The spec is a
``method`` CONTRACT, not a bare predicate, so a witness must reach the post-image
through the method. Every witness here does it the same way: it refutes the
triple directly at a concrete input,

    ¬ triple True (resolveSeq v) (fun out => out.kind = … ∧ out.elems = ….map resolveElem)

checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. ``rw [triple, wp_pure]`` unfolds the weakest
precondition symbolically and the residual goal then mentions ``resolveElem``
only where the rival's divergence genuinely involves it.

The alternative shape — Velvet's ``derive_tester_for`` machinery
(``resolveSeqTester v = false`` closed by ``decide``) — is NOT used here, and the
reason is a measured property of this carrier rather than a stylistic choice. The
tester's postcondition decision procedure compares the element lists, so for any
NON-EMPTY ``elems`` it needs ``decEq (resolveElem e) …``; the opaque
``resolveElem`` blocks the kernel and ``decide`` is stuck for EVERY claim, true or
false. The gold-side exit code then carries no information at all
(``witness-undecided``) — measured on exactly that shape, and it is how an earlier
length-clause witness stated at ``elems := [7]`` failed. Restricting every
witness to ``elems := []`` to keep the tester reducing would pin the ``elems``
binder at ONE value across the whole reject set, so the battery would say nothing
about the spec's dependence on the element list. The triple route dissolves both
problems at once:

  * Rivals whose divergence is PURELY STRUCTURAL — a wrong result KIND (C1) or a
    wrong element COUNT (C2 length) — reduce, after ``loomLogicSimp``, to a
    CONSTRUCTOR clash carrying no opaque term (``¬ SeqKind.tuple = SeqKind.list``;
    ``¬ [] = [resolveElem 7]``), which ``decide`` closes. Against the frozen
    solution the same script reduces the goal to ``¬ True`` and ``decide``
    DISPROVES it — an evaluated verdict, not a stuck reduction. So these witnesses
    sit at non-empty, VARYING ``elems`` (``[7]``, ``[8, 9]``) and at BOTH kinds.
  * Rivals whose divergence is in an element VALUE (identity passthrough,
    broadcast) are inherently ABOUT the opaque map, so no literal input decides
    them. These are refuted by CONDITIONING ON THE CARRIER: the triple is refuted
    at a point described by hypothesis (``h : resolveElem 5 ≠ 5`` for identity;
    ``h : resolveElem 3 ≠ resolveElem 4`` for broadcast), so the refutation holds
    exactly on the sub-domain where the rival diverges — a stronger statement than
    any single literal input could make, and precisely the technique the opaque
    carrier calls for. Each conditioning hypothesis is a SINGLE assumption about a
    SINGLE opaque application, so it is jointly satisfiable (the gate's
    ``example … : False`` consistency probe leaves ``False`` unsolved on both —
    verified), never a contradiction-forgery.

Every witness was SEEN to discriminate with ``scripts/lean_verify.sh``: it
ELABORATES green against its rival (EXIT 0) and FAILS against the frozen solution
(EXIT ≠ 0).

The two CONDITIONED witnesses fail on gold with ``simp made no progress`` rather
than with an evaluated verdict, so for those the exit code alone is not admissible
evidence and the FORGERY pair was measured on both:

  * FLIP THE CLAIM. Dropping the ``¬`` — asserting the triple HOLDS at the
    witness's own point — builds green against the frozen solution (exit 0) and
    RED against the rival (exit 1), the exact inverse of the witness. So gold's
    exit code does track what is being claimed; it is not a constant. NOTE on
    reproducing this: the flipped claim must be closed by the witness's own
    UNFOLDING PREFIX only (``unfold``/``rw [triple, wp_pure]``/``simp only
    [loomLogicSimp, List.map]``) and nothing after it. `simp` discharges the
    post-image outright on gold, so any additional closing tactic errors with
    ``No goals to be solved`` and the flip then fails on BOTH sides for a reason
    that is about the script rather than the claim — which reads like a hollow
    case and is not one. Against the rival the same prefix leaves the divergence
    as an explicit open goal (``⊢ [5] = [resolveElem 5]``;
    ``⊢ [resolveElem ([3, 4].headD 0), resolveElem ([3, 4].headD 0)] =
    [resolveElem 3, resolveElem 4]``), which is the informative half.
  * REVEAL THE TYPE. Replacing the closing step with a deliberate type error
    (``exact (hcon : Nat)``) prints the hypothesis's real type on each side. On
    gold: ``hcon has type True`` — ``simp`` PROVED the post-image equation there,
    which is why it then "made no progress" on a goal already discharged. On the
    identity rival: ``hcon has type [5] = [resolveElem 5]``; on the broadcast
    rival: ``[resolveElem ([3, 4].headD 0), resolveElem ([3, 4].headD 0)] =
    [resolveElem 3, resolveElem 4]`` — concrete equations, NOT proved, which is
    exactly the divergence each rival is accused of. That pair is a semantic
    refutation, not a tactic mismatch.

The four STRUCTURAL witnesses need no such pair: their gold-side failure is
``decide proved that the proposition ¬True is false``, an evaluated verdict that
already names the claim it decided.

ADVERSARIAL READ of the nagini sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl must verify, else SPEC-TOO-STRONG. THREE are
    shipped, and they are deliberately of two different strengths. Two are
    DEFINITIONALLY EQUAL to the frozen body (bind the kind into a local; inline
    the element map into the return): they verify under the frozen tactic script
    verbatim, which makes them cheap but also means they attest only that the
    spec does not depend on the impl's surface syntax. The third
    (`pos-control-foldr`) is NOT defeq — it builds the element list by an
    explicit `foldr` that agrees with `List.map` only by induction — so it is the
    one that tests C2 as a proposition about the element list. It needs a retuned
    tactic script (the residual list identity is a proof obligation, not a
    syntactic match), and the statement it discharges is byte-identical.
  * ADMISSIBILITY — RE-AIMED, and aimed at the OBLIGATION, not at a side fact.
    The sibling injects an in-impl witness asserting an F2P-shaped input
    satisfies its fractional-permission Requires. This method has no ``require``
    clause and this backend no permission surface, so there is no precondition to
    probe — but the analogue on a TOTAL carrier is not "nothing to test": it is
    the obligation being UNSATISFIABLE at exactly an F2P-shaped input, which
    reads identically to one every impl meets. ``admiss-nondegenerate`` therefore
    discharges the post-image ITSELF — both clauses conjoined — stated over the
    value the body actually CONSTRUCTS (the returned local), and specialised by
    hypothesis to the F2P-shaped coordinate (a LIST with two elements), where it
    additionally claims the result reads back as that kind and not as the other.
    Stating it over the constructed value is the load-bearing detail: an earlier
    form of this case asserted the same facts of CLOSED RECORD LITERALS, which is
    a carrier tautology (``⟨⟨rfl, rfl⟩, decide⟩`` closes it with no impl in
    scope) and which therefore discharged even when injected into a rival
    violating BOTH clauses — measured, the build then fails listing only
    ``ensures_1``/``ensures_2`` while ``admiss_1`` sits in context as proved.
    Liveness is accordingly measured against the IMPL, not against the assert's
    own text: holding the assert fixed and varying the constructed value (kind
    forced to the other kind; a dropped element; raw unresolved elements) leaves
    ``admiss_1`` unsolved in each case, with the residual goal naming the wrong
    value.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend, MEASURED not assumed.
    The sibling carries two MANDATORY framing rivals (write ``value.items`` /
    ``value.kind``, held at ``Acc(.,1/2)`` read-only) because a fractional heap
    permission can be illegally overwritten. Lean/Velvet are referentially
    transparent: there is no heap, no aliasing, and no permission system. Both
    framing rivals were nevertheless ATTEMPTED here rather than waved off, and
    the carrier refuses them before any spec reasoning happens: ``value := …``
    and ``value.kind := …`` in the impl region each fail to elaborate with
    ```value` cannot be mutated, only variables declared using `let mut` can be
    mutated``. So the rejection would attest to a syntactic property of the
    binder, never to the spec — there is no read-only input to overwrite and no
    substitute probe to fabricate. NOT ported (per the porting map: this class is
    vacuous on a referentially-transparent backend).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C2 pins the elements to
    ``value.elems.map resolveElem``, a function of the ACTUAL input elements;
    there is no answer-key value to echo (any impl whose elements satisfy C2 must
    have applied the real ``resolveElem`` to the real input elements). The nagini
    file makes the same observation. The honest cheapest-reshape positive
    controls cover the no-wrong-echo surface.
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

    RETRACTED, and re-measured. The lines that stood here claimed the opposite:
    that a ``while True do pure ()`` prefix spliced at the head of the frozen
    body VERIFIES at exit 0, that the same prefix returning the unambiguously
    WRONG value ``{ kind := SeqKind.tuple, elems := [] }`` ALSO VERIFIES, that
    the post-image is therefore satisfied on an unreachable exit with the
    returned value entirely unconstrained, and that closing the class would mean
    flipping the option to ``"total"``. Every part of that is false of this
    artifact. The frozen file already sets ``"total"``, as all 500 velvet bundles
    do, and none sets ``"partial"``; in Loom the option is itself what opens
    ``TotalCorrectness`` scope, so the setting and the ``open`` cannot disagree.
    Under ``total`` a postcondition is claimed of ALL runs, not only terminating
    ones, and every loop owes a measure that STRICTLY DECREASES, so a diverging
    prefix is REJECTED: with no ``decreasing`` clause the elaborator refuses
    outright, and with a clause whose measure is constant the descent goal itself
    fails under that clause's own name. There is no unreachable-exit vacuity here
    and nothing to escalate. The class still ships no case, on the witness path
    rather than the spec: a reject case needs a witness that ELABORATES against
    the rival, and a diverging rival's module does not compile at all, so the
    case would score MALFORMED rather than rejecting.
    That is the shape with NO measure. A rival that CARRIES a measure which
    does not decrease is refused at the ``prove_correct`` site instead, which
    the witness file strips, so that module does elaborate; but its post-image
    is then an unreduced ``forIn Lean.Loop.mk`` term carrying
    ``invariantGadget`` / ``onDoneGadget`` / ``decreasingGadget``, which the
    kernel will not normalise to a value a concrete-input tester can decide.
    Both shapes therefore land ``witness-unproven``.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival is right on part
    of the domain and diverges on one sub-domain (a wrong kind on one input kind,
    a dropped last element, a raw/broadcast element value).
"""
from pathlib import Path

INSTANCE = "django__django-12050"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl body (the two statements between and INCLUDING the
# ---- markers): a single anchor lying wholly inside the impl region and unique
# ---- in the file (both facts asserted at load by _swap). Every rival and
# ---- positive reshape swaps on this block, keeping same_spec by construction
# ---- and leaving the frozen `prove_correct resolveSeq` statement intact.
_IMPL = (
    "    -- impl-start\n"
    "    let resolvedElems := value.elems.map resolveElem\n"
    "    return { kind := value.kind, elems := resolvedElems }\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"
# (Retained as a drift assertion on the marker itself. The admissibility case no
#  longer splices after this marker — it swaps the whole impl block via
#  `_rewrite_impl`, because its assert must NAME the value the body constructs.)

# ---- the frozen proof body (tactic script only; elided from the spec view).
# ---- The positive controls and the admissibility case keep it verbatim — the
# ---- post-image is a point-wise equality that `loom_solve` discharges for every
# ---- faithful reshape and for the (live, satisfiable) admissibility assert, so
# ---- no proof retuning is needed.
_PROOF = "prove_correct resolveSeq by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


def _rewrite_impl(new_block):
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_block)


def _rewrite_impl_proof(new_block, new_proof):
    """Solution.lean with the impl body AND the tactic script replaced.

    Both regions are elided from the consumer spec view, so `same_spec` holds and
    the `prove_correct resolveSeq` STATEMENT stays byte-identical — only the
    script that discharges it changes. Needed for a positive control whose
    returned element list is NOT definitionally equal to the frozen one: bare
    `loom_solve` leaves the residual list identity as an open goal, which is a
    PROOF gap, not a spec gap, and retuning the script is exactly how the two are
    told apart. (A reshape that could only pass by WEAKENING the statement would
    be caught by `variant_scope`; this changes the tactic body alone.)
    """
    return _swap(_rewrite_impl(new_block), _PROOF, new_proof)


# ---- witness machinery. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so every witness refutes the method's Hoare `triple` DIRECTLY at a
# ---- concrete input: `¬ triple True (resolveSeq v) (fun out => C1 ∧ C2)` says
# ---- the candidate's post-image at `v` contradicts the frozen post-image there.
# ---- `triple`, `wp_pure`, `loomLogicSimp` all come from the frozen `Velvet.Std`
# ---- import; nothing extra is imported and no new declaration is introduced.
#
# WHY NOT the tester route. Velvet's `derive_tester_for` machinery
# (`resolveSeqTester v = false` + `decide`) is the usual velvet witness shape,
# but here it only reduces when `elems` is EMPTY: for any non-empty `elems` the
# tester's element comparison needs `decEq (resolveElem e) (…)` and the opaque
# `resolveElem` blocks the kernel, so `decide` is stuck for EVERY claim, true or
# false, and the gold-side exit code carries no information (`witness-undecided`;
# measured — that is exactly how a length-clause witness stated at `elems := [7]`
# failed). Restricting every witness to `elems := []` would in turn pin the
# `elems` binder at ONE value across the whole reject set and say nothing about
# the spec's dependence on the element list. The `triple` route avoids both: it
# unfolds the weakest precondition symbolically, so the residual goal mentions
# `resolveElem` only where the rival's divergence genuinely needs it.
def _w_triple(kind_lit, elems_lit, tail, binder=""):
    """`¬ triple …` for `{ kind := SeqKind.<kind_lit>, elems := <elems_lit> }`."""
    head = f"example {binder}:\n" if binder else "example :\n"
    return (
        head +
        "    ¬ triple (l := Prop) (True)\n"
        f"        (resolveSeq {{ kind := SeqKind.{kind_lit}, elems := {elems_lit} }})\n"
        f"        (fun out => out.kind = SeqKind.{kind_lit} ∧ "
        f"out.elems = {elems_lit}.map resolveElem) := by\n"
        "  unfold resolveSeq\n"
        "  rw [triple, wp_pure]\n" + tail)


# STRUCTURAL rivals (a wrong result KIND, or a wrong element COUNT). After
# `loomLogicSimp` the residual goal is a constructor clash that carries no opaque
# term (`¬ SeqKind.tuple = SeqKind.list`, `¬ [] = [resolveElem 7]`), so `decide`
# closes it — and on gold the very same script reduces the goal to `¬ True` and
# `decide` DISPROVES it, an evaluated verdict rather than a stuck one.
def _w_kind(kind_lit, elems_lit):
    return _w_triple(kind_lit, elems_lit,
                     "  simp only [loomLogicSimp]\n  decide\n")


_W_DROP_LAST = _w_triple(
    "list", "[7]",
    "  simp only [loomLogicSimp, List.map]\n  decide\n")

# VALUE rivals (identity passthrough / broadcast) diverge in an element VALUE, so
# the divergence is inherently ABOUT the opaque `resolveElem` and no literal
# input can decide it. They are refuted by CONDITIONING ON THE CARRIER: the
# refutation is stated at a point described by hypothesis, so it holds exactly on
# the sub-domain where the rival is wrong — a stronger claim than any single
# literal could make. Each uses ONE hypothesis about ONE opaque application, so
# the assumptions are jointly satisfiable (the gate's `example … : False` probe
# leaves `False` unsolved on both — verified).
_W_IDENTITY = _w_triple(
    "tuple", "[5]",
    "  simp only [loomLogicSimp, List.map]\n"
    "  intro hcon\n"
    "  simp only [List.cons.injEq, and_true] at hcon\n"
    "  exact h hcon.symm\n",
    binder="(h : resolveElem 5 ≠ 5) ")

_W_BROADCAST = _w_triple(
    "tuple", "[3, 4]",
    "  simp only [loomLogicSimp, List.map]\n"
    "  intro hcon\n"
    "  simp only [List.cons.injEq, and_true] at hcon\n"
    "  exact h hcon.2\n",
    binder="(h : resolveElem 3 ≠ resolveElem 4) ")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the frozen `prove_correct` proof verbatim (the
    # post-image is a point-wise equality `loom_solve` discharges for any
    # faithful reshape).
    # =====================================================================
    {
        "id": "pos-control-kindvar",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the input kind into a local `k0` before constructing the
        # result. Same value flow; out.kind = k0 = value.kind still holds.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let k0 := value.kind\n"
            "    let resolvedElems := value.elems.map resolveElem\n"
            "    return { kind := k0, elems := resolvedElems }\n"
            "    -- impl-end"),
        "rationale": "binding the input kind into a local `k0` and constructing "
                     "`{ kind := k0, elems := … }` returns the same value, so "
                     "`out.kind = value.kind` (C1) and `out.elems = value.elems.map "
                     "resolveElem` (C2) still hold on the whole domain; the frozen "
                     "proof is untouched. A correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG on the shape of the impl. (Sibling: "
                     "pos-control-kindvar.)",
    },
    {
        "id": "pos-control-inline",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline the element map into the return instead of naming it in
        # a `let`. Same value flow.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { kind := value.kind, elems := value.elems.map resolveElem }\n"
            "    -- impl-end"),
        "rationale": "inlining the element map `value.elems.map resolveElem` into "
                     "the returned record leaves the returned value unchanged, so "
                     "the post-image (C1 and C2) is unchanged; a correct reshape "
                     "must verify, else SPEC-TOO-STRONG. (Sibling: "
                     "pos-control-hoist, re-shaped to an inline form on this "
                     "carrier.)",
    },
    {
        "id": "pos-control-foldr",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: build the element list with an explicit `foldr` that conses the
        # per-element resolution, instead of calling `List.map`. UNLIKE the other
        # two positives, the returned record is NOT definitionally equal to the
        # frozen one — `List.foldr (fun x acc => resolveElem x :: acc) [] es` and
        # `es.map resolveElem` are equal only by an INDUCTION on `es`, which is
        # why bare `loom_solve` leaves `⊢ List.foldr … = List.map resolveElem
        # value.elems` open (measured). So this is the positive that actually
        # exercises C2 as a PROPOSITION about the element list rather than as a
        # syntactic identity, and it is the one that would catch a C2 clause
        # phrased so tightly that only the frozen spelling could discharge it.
        "module": _rewrite_impl_proof(
            "    -- impl-start\n"
            "    let resolvedElems := value.elems.foldr\n"
            "      (fun x acc => resolveElem x :: acc) []\n"
            "    return { kind := value.kind, elems := resolvedElems }\n"
            "    -- impl-end",
            "prove_correct resolveSeq by\n"
            "  loom_solve\n"
            "  induction value.elems <;> simp_all"),
        "rationale": "builds the element list by an explicit `foldr` that conses "
                     "each element's resolution rather than by `List.map`. The "
                     "returned value is the SAME list, but it is not "
                     "definitionally the frozen one — the two agree only by "
                     "induction on the element list — so this positive tests C2 "
                     "(`out.elems = value.elems.map resolveElem`) as a real "
                     "proposition about the elements instead of as a syntactic "
                     "match, which the other two positives (both defeq to the "
                     "frozen body) cannot do. The tactic script is retuned with "
                     "the induction that closes the residual list identity; both "
                     "the impl region and the tactic body are elided from the "
                     "spec view, so the frozen obligation's STATEMENT is "
                     "unchanged. A faithful correct reshape MUST verify, else "
                     "SPEC-TOO-STRONG on the shape of the element computation. "
                     "(No sibling: added by audit — the two ported positives "
                     "were both definitionally equal to the frozen impl, so the "
                     "soundness lane passed on syntax alone.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has no `require` clause, so the sibling's
    # "a normal input satisfies the precondition" probe has no precondition to
    # aim at. The analogue on a TOTAL carrier is the obligation being
    # unsatisfiable at exactly an F2P-shaped input, which a positive that
    # DISCHARGES THE OBLIGATION AT THAT CONCRETE INPUT — by evaluation, as a
    # `have`/`assert`, before closing the frozen obligation verbatim — tests
    # directly. So the assert instantiates the ACTUAL post-image (both clauses,
    # conjoined) at the F2P-shaped coordinate: a LIST whose elems has TWO
    # entries, the shape of the failing scenario. Two facts are claimed of that
    # point:
    #
    #   (a) the post-image HOLDS there — the value the frozen impl builds at
    #       that input, `{ kind := SeqKind.list, elems := [1,2].map resolveElem }`,
    #       satisfies C1 (`.kind = SeqKind.list`) AND C2 (`.elems = [1,2].map
    #       resolveElem`) simultaneously. If the two clauses were jointly
    #       unsatisfiable at the F2P input, this assert could not discharge and
    #       the obligation would be vacuous exactly where the fix must bite.
    #   (b) the post-image is not met by EVERY value there — the pre-patch-shaped
    #       value at the same coordinate (same elems, kind forced to tuple) has
    #       `.kind ≠ SeqKind.list`, so C1 genuinely EXCLUDES something at this
    #       input. Without (b) an assert can be true of any impl; with it the
    #       assert pins that the obligation discriminates at the F2P point.
    #
    # WHY THE ASSERT MUST NAME THE VALUE THE BODY BUILDS. An earlier form of this
    # case stated (a) and (b) over CLOSED record literals — `({ kind :=
    # SeqKind.list, elems := [1,2].map resolveElem } : SeqVal).kind = SeqKind.list`
    # and the tuple-shaped twin's `.kind ≠ SeqKind.list`. That proposition is a
    # TAUTOLOGY of the carrier: both conjuncts are record-projection reductions
    # plus a two-constructor clash, and `refine ⟨⟨rfl, rfl⟩, ?_⟩; decide` closes it
    # in a file that declares only `SeqKind`/`SeqVal`/`resolveElem` — no
    # `resolveSeq`, no `out`, no impl in scope at all (measured, exit 0). Because
    # it mentioned no impl, it discharged for ANY body: injected into a rival that
    # returns `{ kind := SeqKind.tuple, elems := value.elems }` — violating BOTH
    # C1 and C2 — the build fails listing ONLY `ensures_1`/`ensures_2`, with
    # `admiss_1 : SeqKind.tuple ≠ SeqKind.list` sitting in context as a DISCHARGED
    # hypothesis (measured, exit 1). An admissibility positive that passes
    # identically for a doubly-wrong impl tests nothing about the obligation.
    #
    # So the assert is stated over `result` — the very local the body returns —
    # which is what couples it to the impl. It claims:
    #
    #   (a) the post-image holds of the constructed value ON THE WHOLE DOMAIN:
    #       `result.kind = value.kind ∧ result.elems = value.elems.map resolveElem`
    #       — both clauses CONJOINED, so they are not jointly unsatisfiable;
    #   (b) SPECIALISED AT THE F2P-SHAPED COORDINATE, by hypothesis on the input:
    #       when `value = { kind := SeqKind.list, elems := [1, 2] }` (a LIST with
    #       two entries — the failing scenario's shape), the result reads back as a
    #       list and NOT as the other kind (`result.kind = SeqKind.list ∧
    #       result.kind ≠ SeqKind.tuple`) with its elements the resolved input
    #       elements. This is the total-carrier analogue of PRECOND-TOO-STRONG: an
    #       obligation unsatisfiable at exactly the interesting input would read
    #       like one every impl meets, and discharging it there by evaluation is
    #       what rules that out.
    #
    # LIVENESS measured against the IMPL (not against the assert's own text, which
    # is the mistake the tautological form made): with this assert held fixed and
    # only the constructed value varied, each of three wrong bodies leaves
    # `admiss_1` UNSOLVED (exit 1), and the residual goal names the wrong value —
    # kind forced to tuple (`⊢ SeqKind.tuple = value.kind ∧ …`); a dropped element
    # (`⊢ List.map resolveElem value.elems.dropLast = List.map resolveElem
    # value.elems ∧ …`); raw elements (`⊢ value.elems = List.map resolveElem
    # value.elems ∧ …`). The frozen tactic body closes both the assert and the
    # method's own obligation for the faithful body (exit 0, no retuning).
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The gold value flow is kept verbatim; the returned record is merely
        # NAMED (`result`) so the in-region assert can speak about it. `return
        # result` returns exactly what the frozen body returns.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let resolvedElems := value.elems.map resolveElem\n"
            "    let result : SeqVal := { kind := value.kind, elems := resolvedElems }\n"
            "    assert (with_name_prefix `admiss (\n"
            "      (result.kind = value.kind ∧ result.elems = value.elems.map resolveElem) ∧\n"
            "      (value = { kind := SeqKind.list, elems := [(1 : Int), 2] } →\n"
            "        (result.kind = SeqKind.list ∧ result.kind ≠ SeqKind.tuple) ∧\n"
            "        result.elems = [(1 : Int), 2].map resolveElem)))\n"
            "    return result\n"
            "    -- impl-end"),
        "rationale": "discharges the OBLIGATION ITSELF, stated over the value the "
                     "body actually constructs (`result`), at an F2P-shaped "
                     "coordinate — a LIST input whose element sequence has two "
                     "entries. (a) The post-image's two clauses are asserted "
                     "CONJOINED on the whole domain (`result.kind = value.kind ∧ "
                     "result.elems = value.elems.map resolveElem`), so they are "
                     "not jointly unsatisfiable; (b) specialised by hypothesis to "
                     "the F2P-shaped input, the result reads back as the input's "
                     "kind and NOT as the other kind, with its elements the "
                     "resolved input elements — the total-carrier analogue of "
                     "PRECOND-TOO-STRONG, since an obligation unsatisfiable at "
                     "exactly the interesting input would read like one every "
                     "impl meets. Crucially the claim is IMPL-LINKED: liveness is "
                     "measured by holding the assert fixed and varying the "
                     "constructed value — kind forced to tuple, a dropped "
                     "element, or raw unresolved elements each leave `admiss_1` "
                     "unsolved with the residual goal naming the wrong value. "
                     "(Sibling: admiss-f2p-shaped-input, re-aimed from "
                     "precondition admissibility to obligation satisfiability AT "
                     "the F2P-shaped input, since this method has no `require` "
                     "clause and this backend no permission surface. Repaired by "
                     "audit: the ported form stated closed record literals, a "
                     "carrier tautology that discharged even for an impl "
                     "violating both clauses.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-always-tuple",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG: force the result kind to tuple regardless of the input kind —
        # exactly the pre-patch shape. Correct on C2 (elements) and on every
        # tuple input; diverges on C1 for a list input.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { kind := SeqKind.tuple, elems := value.elems.map resolveElem }\n"
            "    -- impl-end"),
        "refinement": "forcing the result kind to tuple regardless of the input "
                      "kind is EXACTLY the pre-patch behaviour: a list input is "
                      "coerced to a tuple. The F2P scenario builds a list-valued "
                      "lookup Q(name=['a','b']) and asserts the resolved rhs reads "
                      "as a list (\"['a', 'b']\"); with a tuple result the rhs is "
                      "('a', 'b') and the assertion fails — the un-patched branch "
                      "is exactly what does NOT resolve.",
        "rationale": "REJECT from C1 (`out.kind = value.kind`): out.kind is pinned "
                     "to tuple, but value.kind may be list, so the equality is "
                     "unprovable. Verifying would be SPEC-TOO-WEAK (the fix "
                     "unpinned). Refuted at the LIST input with elems [8, 9] — the "
                     "kind clash is a constructor mismatch that decides without "
                     "evaluating the opaque element map, so the refutation is "
                     "stated at a two-element input rather than being forced onto "
                     "the empty list.",
        "witness": _w_kind("list", "[8, 9]"),
    },
    {
        "id": "weak-always-list",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror coercion: force the result kind to list. Correct on C2 and on
        # every list input; diverges on C1 for a tuple input. The witness holds
        # `kind` at the OTHER value (tuple) than every other reject case, so it
        # moves the kind binder off list.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { kind := SeqKind.list, elems := value.elems.map resolveElem }\n"
            "    -- impl-end"),
        "refinement": "the mirror coercion turns a tuple input into a list. The "
                      "issue demands the return type MATCH the input type in BOTH "
                      "directions (type-dependent field lookups break either way); "
                      "a patch always returning a list would fail a tuple-input "
                      "case the same way the pre-patch fails the list-input F2P. "
                      "It would NOT resolve.",
        "rationale": "REJECT from C1 (`out.kind = value.kind`): out.kind is pinned "
                     "to list, but value.kind may be tuple. Refuted at a TUPLE "
                     "input with a SINGLETON elems [7], so C1's dependence on the "
                     "input kind is demonstrated in the tuple direction as well as "
                     "the list one.",
        "witness": _w_kind("tuple", "[7]"),
    },
    {
        "id": "weak-flip-kind",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the kind for every input (list<->tuple). Always the wrong kind.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let k := match value.kind with\n"
            "      | SeqKind.list => SeqKind.tuple\n"
            "      | SeqKind.tuple => SeqKind.list\n"
            "    return { kind := k, elems := value.elems.map resolveElem }\n"
            "    -- impl-end"),
        "refinement": "inverting the kind for every input (list->tuple AND "
                      "tuple->list) matches no real patch; it fails both the "
                      "list-input F2P case and any tuple case. A supporting twin "
                      "of the coercion attacks — the result type never matches the "
                      "input type.",
        "rationale": "REJECT from C1 (`out.kind = value.kind`): out.kind is the "
                     "OPPOSITE kind for every input, so the equality never holds. "
                     "Refuted at the TUPLE input with elems [8, 9] (the flip yields "
                     "list; a decidable constructor mismatch). This is a DIFFERENT "
                     "coordinate point from weak-always-tuple, which is refuted at "
                     "the list input: the flip rival is wrong on BOTH kinds, and "
                     "witnessing it on the tuple side is what separates it from the "
                     "one-directional coercion rivals rather than sharing their "
                     "point.",
        "witness": _w_kind("tuple", "[8, 9]"),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the LAST element before mapping. Correct on C1 (kind) and on the
        # empty input; the result is one element short for any non-empty input.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { kind := value.kind, elems := value.elems.dropLast.map resolveElem }\n"
            "    -- impl-end"),
        "refinement": "dropping the last element returns a sequence one element "
                      "short of the input. A patch that built the result short by "
                      "one would resolve ['a','b'] to a one-element ['a'] (repr "
                      "\"['a']\" != \"['a', 'b']\"), and any multi-item lookup "
                      "would silently lose a value — it would NOT resolve.",
        "rationale": "REJECT from C2 (`out.elems = value.elems.map resolveElem`): "
                     "the result is `value.elems.dropLast.map resolveElem`, one "
                     "element short, so the list equality fails for any non-empty "
                     "input. Refuted at the LIST input with a length-1 elems: after "
                     "unfolding the weakest precondition the residual goal is "
                     "`¬ [] = [resolveElem 7]`, a nil-vs-cons CONSTRUCTOR clash that "
                     "decides without evaluating the opaque element map — a "
                     "computable projection (the element COUNT) of a divergence that "
                     "the tester route could not decide. The only witness attacking "
                     "C2 via length.",
        "witness": _W_DROP_LAST,
    },
    {
        "id": "weak-identity-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        # Append the RAW elements instead of their per-element resolution. Correct
        # on C1 and on the empty input; wrong on C2 wherever an element is not a
        # fixpoint of the resolution.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return { kind := value.kind, elems := value.elems }\n"
            "    -- impl-end"),
        "refinement": "returning the raw elements skips the per-element resolution "
                      "the branch performs. The real per-element rule resolves "
                      "expression-bearing sub-values; a passthrough leaves an "
                      "unresolved sub-value in the rhs, breaking lookups whose "
                      "items are expressions — a patch dropping the recursive "
                      "per-element resolution does NOT resolve.",
        "rationale": "REJECT from C2 (`out.elems = value.elems.map resolveElem`): "
                     "the result is the raw `value.elems`, which the verifier "
                     "cannot prove equals `value.elems.map resolveElem` because "
                     "`resolveElem` is opaque (no fixpoint is a theorem). Refuted "
                     "by CONDITIONING on `resolveElem 5 ≠ 5` at the TUPLE input [5] "
                     "— the exact sub-domain where the raw element differs from its "
                     "resolution. A distinct coordinate point from the C2-length "
                     "rival (which sits at the list input [7]), so the two C2 "
                     "witnesses do not collapse onto one input, and the single "
                     "hypothesis is satisfiable. (Sibling: "
                     "uniq-identity-passthrough.)",
        "witness": _W_IDENTITY,
    },
    {
        "id": "weak-broadcast-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Resolve only the FIRST element and repeat its resolution at every
        # position. Correct on C1, on the empty/singleton input, and at position 0;
        # wrong on C2 at any later position whose element resolves differently.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let h := value.elems.headD 0\n"
            "    return { kind := value.kind, elems := value.elems.map (fun _ => resolveElem h) }\n"
            "    -- impl-end"),
        "refinement": "broadcasting the first element's resolution into every "
                      "position returns the first item's resolution for all "
                      "positions (['a','b'] -> ['a','a']-shaped), failing any "
                      "multi-item lookup's value comparison — a patch resolving "
                      "only the first sub-value and repeating it does NOT resolve. "
                      "Correct only at position 0 (partial-domain).",
        "rationale": "REJECT from C2 (`out.elems = value.elems.map resolveElem`): "
                     "for position k>=1 the result element is `resolveElem "
                     "(head)`, which the verifier cannot prove equals `resolveElem "
                     "(elem k)` (two distinct opaque applications). Refuted by "
                     "CONDITIONING on `resolveElem 3 ≠ resolveElem 4` at the "
                     "TWO-element tuple [3, 4] — a DISTINCT input point and a "
                     "distinct conditioning term from the identity rival, so the "
                     "two C2 witnesses probe different sub-domains and do not "
                     "collapse onto one input. (Sibling: uniq-broadcast-first.)",
        "witness": _W_BROADCAST,
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery ships 11 SPEC cases (2
# soundness positives, 1 admissibility, 2 MANDATORY frame-mutation rivals, 6
# uniqueness/partial-domain rivals) plus an AXIOM lane (2 axiom probes). This
# bundle contracts the SAME sequence-resolution behavior with ONE method
# (`resolveSeq`) whose single post-image has TWO independent clauses (C1 kind /
# C2 element-wise map); the sibling's per-clause rivals re-express directly
# against those two clauses.
#
#   sibling case                    kind          -> here                        disposition
#   ------------------------------------------------------------------------------------------
#   pos-control-hoist               soundness     -> pos-control-inline           RE-SHAPED
#   pos-control-kindvar             soundness     -> pos-control-kindvar          PORTED
#   (no sibling)                    soundness     -> pos-control-foldr            ADDED (audit)
#   admiss-f2p-shaped-input         admissibility -> admiss-nondegenerate         RE-AIMED
#   frame-mut-items                 uniqueness    -> (none)                       VACUOUS
#   frame-mut-kind                  uniqueness    -> (none)                       VACUOUS
#   uniq-always-tuple               uniqueness    -> weak-always-tuple            PORTED
#   uniq-always-list                uniqueness    -> weak-always-list             PORTED
#   uniq-flip-kind                  uniqueness    -> weak-flip-kind               PORTED
#   uniq-drop-last                  uniqueness    -> weak-drop-last               PORTED
#   uniq-identity-passthrough       uniqueness    -> weak-identity-passthrough    PORTED
#   uniq-broadcast-first            uniqueness    -> weak-broadcast-first         PORTED
#   AXIOM_TESTS (2 probes)          axiom         -> (none)                       N/A (G-AX)
#
# 6 uniqueness ported, 3 soundness (1 ported + 1 re-shaped + 1 ADDED by audit),
# 1 admissibility re-aimed; 2 uniqueness vacuous (frame); axiom lane dropped.
#
# ADDED (pos-control-foldr): an audit found the soundness lane passing on syntax
#   alone — both ported positives are DEFINITIONALLY EQUAL to the frozen body, so
#   the frozen tactic script closes them unchanged and neither could have detected
#   a C2 clause that only the frozen spelling discharges. The added positive
#   builds the element list by an explicit `foldr`, which equals `List.map` only
#   by induction, so it exercises C2 as a proposition; it verifies with the
#   induction supplied in the (elided) tactic body. Measured alongside it: two
#   further non-defeq correct reshapes — reverse-then-reverse
#   (`(es.reverse.map resolveElem).reverse`, closed by
#   `rw [← List.map_reverse, List.reverse_reverse]`) and an if/match kind case
#   split — ALSO verify, so the spec admits faithful reshapes generally and is not
#   SPEC-TOO-STRONG on the element computation.
#
# RE-SHAPED (pos-control-hoist -> pos-control-inline): the sibling's hoist binds
#   the per-item normalisation into a local before appending inside a loop. This
#   carrier's impl is loop-free (a single `List.map` in a `return`), so the
#   faithful cheap reshape that carries the same argument is INLINING the map into
#   the return. A second, local-binding reshape (pos-control-kindvar) is kept, so
#   the soundness surface is defended both by an inline form and by a local-`let`
#   form.
# RE-AIMED (admiss-f2p-shaped-input -> admiss-nondegenerate): the sibling asserts
#   a concrete F2P-shaped input satisfies its half-permission Requires. This
#   method has no `require` clause and no permission surface, so there is no
#   precondition to probe — but the total-carrier analogue is the OBLIGATION being
#   unsatisfiable at exactly an F2P-shaped input. So the assert discharges the
#   post-image itself (C1 AND C2 conjoined) over the value the body CONSTRUCTS,
#   specialised by hypothesis to the F2P-shaped coordinate — a LIST with two
#   elements — where it also claims the result reads back as that kind and not as
#   the other. The gold value flow is kept verbatim (the returned record is merely
#   NAMED so the assert can refer to it) and the frozen proof discharges both the
#   assert and the method's obligation (verified, exit 0 — no retuning).
#   REPAIRED BY AUDIT: the ported form stated these facts of CLOSED RECORD
#   LITERALS, which is a carrier tautology — `refine ⟨⟨rfl, rfl⟩, ?_⟩; decide`
#   closes it in a file with no `resolveSeq` in scope — and it consequently
#   discharged when injected into a rival violating BOTH clauses (build fails on
#   `ensures_1`/`ensures_2` only, `admiss_1` proved in context). Liveness is now
#   measured against the IMPL rather than the assert's own text: with the assert
#   fixed, kind-forced-to-tuple / a dropped element / raw unresolved elements each
#   leave `admiss_1` unsolved (three variants, all exit 1), the residual goal
#   naming the wrong constructed value.
# PORTED (the six value/kind rivals): uniq-always-tuple / uniq-always-list /
#   uniq-flip-kind attack C1 (the kind clause, the fix) and uniq-drop-last attacks
#   C2 via LENGTH; all four are refuted by refuting the method's Hoare triple and
#   closing a CONSTRUCTOR clash with `decide` (a wrong kind, or a nil-vs-cons
#   length mismatch, carries no opaque term). uniq-identity-passthrough /
#   uniq-broadcast-first attack C2 via element VALUE, which is inherently about the
#   opaque `resolveElem`; both are refuted by CONDITIONING on the carrier (the
#   triple refuted at a point described by hypothesis), at two DISTINCT input points
#   with two distinct single-hypothesis conditioning terms.
# VACUOUS (frame-mut-items, frame-mut-kind): the sibling's two MANDATORY
#   frame-mutation rivals write the read-only input's items / kind field (held at
#   Acc(.,1/2)), rejected for INSUFFICIENT PERMISSION. This backend is
#   referentially transparent: there is no heap, no aliasing, and no permission
#   system. Both rivals were ATTEMPTED here rather than assumed vacuous, and the
#   carrier refuses each before any spec reasoning: `value := { kind :=
#   SeqKind.tuple, elems := [] }` and `value.kind := SeqKind.tuple` in the impl
#   region both fail to elaborate with "`value` cannot be mutated, only variables
#   declared using `let mut` can be mutated". A rejection on those terms attests
#   to the binder's syntax, not to the spec — the discrimination a witness is
#   required to supply is unavailable because there is no frame clause to violate.
#   Omitted as a MEASURED carrier fact, NOT fabricated (porting map: this class is
#   vacuous on a referentially-transparent backend).
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
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` pair has ONE binder — `value :
#   SeqVal`, whose fields are `kind : SeqKind` and `elems : List Int` — and TWO
#   independent top-level clauses (C1 kind / C2 element-wise map). The six reject
#   witnesses sit at SIX DISTINCT coordinate points (pts = 6; no two rivals share
#   an input):
#     * weak-always-tuple        { list,  [8, 9] }
#     * weak-always-list         { tuple, [7] }
#     * weak-flip-kind           { tuple, [8, 9] }
#     * weak-drop-last           { list,  [7] }
#     * weak-identity-passthrough{ tuple, [5] }     (conditioned resolveElem 5 ≠ 5)
#     * weak-broadcast-first     { tuple, [3, 4] }  (conditioned resolveElem 3 ≠
#                                                    resolveElem 4)
#   So `value.kind` ranges over BOTH of its two values across the reject set (two
#   list points, four tuple points), demonstrating C1's dependence on the input
#   kind in both directions — a rival mishandling only one kind cannot hide. And
#   `value.elems` ranges over four shapes at three lengths ({[5]}, {[7]}, {[3,4]},
#   {[8,9]}), so the element list is never pinned: varying the count is what
#   separates the C2 length rival from the C2 value rivals, and varying the element
#   VALUES is what separates the two conditioned value rivals from each other.
#   Notably NO witness sits at `elems := []`, the one point at which every rival in
#   this battery except the kind-coercion ones would AGREE with gold — the empty
#   list is a universal agreement point for the length and value rivals, so a
#   battery that probed only there would attest to nothing about C2.
#   BOTH clauses are attacked: C1 by weak-always-tuple / weak-always-list /
#   weak-flip-kind, C2 by weak-drop-last (length) and weak-identity-passthrough /
#   weak-broadcast-first (value).
#
# SPEC-TOO-WEAK PROBE (audit, not shipped as cases — all were REJECTED, so none is
#   a finding). Six further wrong impls aimed at what the shipped rivals leave
#   unattacked were built against the frozen spec; every one failed to verify, each
#   on the clause named:
#     * element ORDER reversed (`(elems.map resolveElem).reverse`) — C2 residual
#       `⊢ (List.map resolveElem value.elems).reverse = List.map resolveElem
#       value.elems`. Order is genuinely pinned, not just count.
#     * result TOO LONG (`(elems ++ elems).map resolveElem`) — C2. The shipped
#       length rival is short-by-one only, so the long direction was untested.
#     * resolution applied TWICE (`resolveElem (resolveElem x)`) — C2; the spec
#       does not admit an idempotence assumption about the opaque map.
#     * ARGUMENT SHIFT (`resolveElem (x + 1)`) — C2; the map must be applied to
#       the element itself, not to a perturbation of it.
#     * DROP FIRST element (`elems.tail.map resolveElem`) — C2, the mirror of the
#       shipped drop-last direction.
#     * kind correct only for a NON-EMPTY element list (forced to one kind when
#       `elems.isEmpty`) — C2 residual `⊢ (if value.elems.isEmpty = true then
#       SeqKind.tuple else value.kind) = value.kind`. Aimed specifically at
#       `elems := []`, the one coordinate no shipped witness sits at, on the theory
#       that the empty list is this battery's universal agreement point; C1 pins
#       the kind there too, so the gap is in the WITNESS coverage, not in the spec.
#
# AXIOM_TESTS: dropped. The bundle declares NO consumed `axiom` (mapping.md §3:
#   `resolveElem` is an A-reference — an opaque deep-model callee validated
#   element-wise by G-CONF, not a consumed contract), so there is nothing for a
#   soundness/containment probe to check here; that is G-AX's job regardless, and
#   this gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
