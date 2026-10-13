"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24627 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant sharing the FROZEN spec byte-for-byte (region surgery:
only text inside ``-- impl-start``/``-- impl-end`` — and, where a case
legitimately re-proves, inside ``-- proof-start``/``-- proof-end`` — is changed,
so ``markers.same_spec`` holds by construction and the single
``theorem correct_clearAxes`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff the file elaborates with the obligation closed and
no new ``axiom``/``sorry``/``admit``/``native_decide``/``theorem``;
``expect:"reject"`` passes iff it does NOT verify AND the case's refutation
``witness`` holds of the rival while FAILING on the frozen solution.

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a fresh
invention. The nagini sibling models the reset as a HEAP MUTATION over a
``Container`` holding a ``List[Element]``, with fractional permissions carrying
the per-member field access; its postcondition has two load-bearing clauses —
(1) the container's collection is empty afterwards, and (3) every FORMER member
is fully de-parented on BOTH back-references. This Lean bundle models the SAME
single purely-functional core, but referential transparency forces the mutation
to be re-expressed as a returned PAIR: ``result.1`` is the container's fresh
(empty) collection and ``result.2`` are the former members, functionally
updated. So nagini's clause (1) becomes the ``result.1 = []`` conjunct, nagini's
clause (3) becomes the positional ∀-clause over ``result.2``, and the carrier
GAINS two obligations nagini's heap model got for free — the former-member list
must have the same LENGTH as the input, and each former member's untouched
payload must be PRESERVED (the frame conjunct ``a.data = c.data``). Both of those
gained clauses are attacked below; see the accounting block at the bottom.

DEFENDED SURFACE (one modeled behavior, one obligation).
``problem_spec_clearAxes artists result`` pins EXACTLY, in order:

  * (C0 emptied)   ``result.1 = []`` — the container's collection is empty once
    the reset returns. This is nagini clause (1).
  * (C1 length)    ``result.2.length = artists.length`` — every element that had
    been a member is accounted for, none dropped and none invented. Positional
    correspondence with the input; carrier-specific (nagini's heap model kept
    member identity implicitly, so it had no counterpart clause).
  * (C2 per-member) ``∀ i < artists.length, ∃ a c, result.2[i]? = some a ∧
    artists[i]? = some c ∧ a.axes = none ∧ a.figure = none ∧ a.data = c.data``.
    Three independent sub-obligations at every position:
      - (C2a) the first back-reference is cleared to absent;
      - (C2b) the second back-reference is cleared to absent;
      - (C2c) FRAME: every other field the member carries is preserved.
    C2a ∧ C2b is nagini clause (3) — the DISCRIMINATING clause, exactly what the
    F2P observes (after the reset, every former member reports both owners as
    absent) and exactly what ``Solution_prepatch.lean`` violates. C2c is the
    frame obligation nagini discharged with permissions and this carrier must
    state explicitly (spec_guide §0.5): without it a rival could clear the
    back-references while corrupting the payload and still verify.

BINDER STRUCTURE. The spec predicate has ONE input binder, ``artists`` (plus the
``result`` position, which is what a rival PRODUCES and so is not something a
reject case can vary). ``artists`` is load-bearing in three independent ways —
its LENGTH, its per-position CONTENT, and which POSITION is being read — and the
reject witnesses vary all three: the NINE witnesses probe nine DISTINCT input
points, at lengths 1, 2 and 3, refuting at index 0, at index 2, and at the
length/emptied clauses where no index is involved. So no rival is refuted at a
point another rival already covers, and a rival mishandling only a particular
list length or only a non-first position is caught by its own witness rather
than incidentally.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS as a PROBE, but its OBLIGATION is
    live and attacked. The nagini sibling's DEFENDED SURFACE prose records that
    its own frame-mutation weakness class does not apply: the per-member
    back-references are FULL-permission inputs by design (the reset writes them),
    so there is no read-only input a rival could overwrite to satisfy a
    postcondition vacuously, and ``has_readonly_input == False`` there. On this
    referentially transparent carrier it is doubly inapplicable — values are
    immutable, there is no aliasing and no fraction to split. No substitute
    permission probe is fabricated. What DOES carry over is the frame
    OBLIGATION itself, which this carrier must state as a conjunct rather than
    get from a permission: ``weak-clobber-payload`` below attacks C2c directly.

  * DIVERGENCE / NON-TERMINATION — GENUINELY VACUOUS here, and this is the one
    disposition where the reason matters. ``implementation_clearAxes`` is a
    total Lean ``def``, and this bundle carries NO
    ``set_option loom.semantics.termination`` line at all — plain Lean, where
    totality is the elaborator's own obligation rather than a configurable
    semantics. So a diverging rival cannot be written and then judged: it is
    refused before the spec is ever consulted. MEASURED, both spellings, rather
    than asserted:

      - ``def implementation_clearAxes artists := implementation_clearAxes
        artists`` (no measure) is refused by the equation compiler —
        ``fail to show termination for implementation_clearAxes ... failed to
        infer structural recursion``, exit 1. The termination obligation is
        discharged by the carrier, so this is a REJECTION, which is the correct
        disposition under a total carrier;
      - the ``partial def`` spelling (``partial`` is not in ``variant_scope``'s
        banned-token set, so it passes the scope check and had to be built) also
        exits 1: ``Tactic `unfold` failed to unfold
        `implementation_clearAxes```, because a ``partial def`` is opaque and no
        equation is available to reduce. It is rejected too — but for an
        UNFOLDING reason, not a semantic one, so it is not shippable as a reject
        case: its witness cannot discriminate (the same unfold failure would
        greet any claim). That is why the class stays unshipped even though the
        rival is rejected.

    This is NOT the velvet situation (``the corpus-wide termination-semantics finding``: under
    ``set_option loom.semantics.termination "partial"`` a non-terminating impl
    satisfies every ``ensures`` VACUOUSLY and verifies while its faithful patch
    hangs the F2P — a KNOWN SPEC HOLE in 401 of 500 bundles; this instance's own
    velvet sibling reads ``"total"``). On lean the class collapses because the
    carrier forbids the rival, not because the spec admits it — so it is a
    vacuous CLASS, not a known hole. The nagini sibling ships no
    ``diverge-*``/``nonterm-*`` case either.

  * UNGROUNDED-ORACLE ECHO — VACUOUS, for the same reason the nagini sibling
    records: the postcondition is grounded in constants and in the input
    (``= none``, ``= []``, lengths, and a per-position equation against
    ``artists[i]?``), never pinned to an opaque answer key an implementation
    could echo. In its place the battery carries honest cheapest-implementation
    POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the whole uniqueness lane
    lives: rivals correct on part of the domain but diverging exactly where the
    behavior bites (one back-reference only; the first member skipped; the last
    member skipped; no de-parenting at all; the collection not emptied; a member
    dropped; the payload corrupted; the snapshot taken too late).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at ONE CONCRETE
ground input, destructures it to the offending conjunct, and reduces the rival's
own output into that conjunct with ``simp [implementation_clearAxes]``. Every
witness's ``example`` head binds NOTHING (all inputs are ground record/list
literals, all fields concrete ``Nat``/``Option Nat``), so there are no
hypotheses whose joint satisfiability could be in question and the gate's
consistency probe has nothing to check — the conditioning technique is not
needed here because this carrier computes. Each witness was checked with two
real ``lake env lean`` builds: it HOLDS of its rival (exit 0) and FAILS on the
frozen solution (exit 1, leaving ``⊢ False`` with the spec conjunct reduced to
``True`` — i.e. gold satisfies the clause at that point), so it discriminates
rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
leaves some former member still claiming an owner it no longer belongs to (or
leaves the collection/payload wrong), so the F2P — which walks every former
member and asserts BOTH owner references are absent — fails on it. A rival that
verified against this spec would therefore be a genuine
verify-does-not-imply-resolve break, not an artifact.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed behavior is modeled deeply), the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.

WHY SPEC-TOO-WEAK IS UNREACHABLE HERE (audit result, machine-checked). The
uniqueness lane above probes clause by clause, but the spec admits a stronger
statement than any finite set of rivals can show: it pins its result UNIQUELY.
An independent audit proved, against the frozen spec verbatim and with no added
axiom,

    theorem spec_determines (artists) (r s) :
        problem_spec_clearAxes artists r → problem_spec_clearAxes artists s →
        r = s

(C0 fixes ``result.1 = []``; C1 fixes the length; C2's positional ∃, being
functional in ``artists[i]?``, fixes every member's three fields — the two owner
references to ``none`` and ``data`` to the input's). So the spec is a TOTAL
FUNCTIONAL CHARACTERIZATION: any impl satisfying it is extensionally equal to
the frozen one, and therefore NO wrong impl can verify, whatever shape it takes.
That is the structural reason the four extra tuned-wrong rivals an audit threw
at it (a reversed former-member list; the first owner's token fed into the
second reference; the payload incremented rather than zeroed; every position
overwritten with the head) were all rejected AND all provably refutable. It also
bounds what the reject lane can be blamed for: a rival that verified here would
contradict a proven theorem, so ``spec_holes`` for this cell is empty by proof
rather than by not having looked. The uniqueness cases remain the per-clause
attribution — which conjunct does the work — and are what a reader needs;
``spec_determines`` is why the list is known to be exhaustive.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24627"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _swaps(src, *pairs):
    """Apply a sequence of (old, new) surgical swaps, each anchored + unique."""
    for old, new in pairs:
        src = _swap(src, old, new)
    return src


# ---------------------------------------------------------------------------
# Region anchors. Each is unique in Solution.lean (asserted by _swap at import)
# and lies ENTIRELY inside the region it is meant to edit, so same_spec is
# structurally guaranteed rather than merely hoped for.
# ---------------------------------------------------------------------------
# --- impl region ---
# The snapshot of the members to be dropped.
_I_SNAPSHOT = "  let oldChildren := artists"
# The fresh (empty) collection the container is left holding.
_I_FRESH = "  let mut newChildren : List Artist := []"
# The loop header, per-member update, and accumulation step.
_I_LOOPHEAD = "  for chld in oldChildren do"
_I_UPDATE = "    let chld := { chld with axes := none, figure := none }"
_I_ACCUM = "    formerChildren := formerChildren ++ [chld]"
_I_RETURN = "  return (newChildren, formerChildren)"

# --- proof region ---
# The closed-form lemma's tactic body: the accumulator induction is only needed
# while the impl accumulates element-by-element, so a positive that builds the
# former-member list in one step replaces exactly this body.
_P_CLOSED_FORM = """  unfold implementation_clearAxes
  simp only [Id.run, bind]
  have := loop_helper_clearAxes artists []
  simp only [Id.run] at this
  rw [this]
  rfl"""
# The obligation's opening `intro`, so a case may prepend a ground `have`
# WITHOUT touching the theorem STATEMENT.
_P_INTRO = "  intro artists"


# ---------------------------------------------------------------------------
# Witness scaffolds. Every witness states the frozen spec predicate at a ground
# input and destructures to the ONE conjunct its rival violates, so the
# refutation is attributed to a named clause rather than to "something differs".
# `_m` builds a member literal; heads bind nothing (see module docstring).
# ---------------------------------------------------------------------------
def _m(payload, owner_a, owner_b):
    a = "none" if owner_a is None else f"(some {owner_a})"
    b = "none" if owner_b is None else f"(some {owner_b})"
    return f"{{ data := {payload}, axes := {a}, figure := {b} }}"


def _members(*rows):
    """A ground `List Artist` literal, one member per row."""
    return "[" + ",\n     ".join(rows) + "]"


def _witness(members, destructure, hyp):
    return (f"example : ¬ problem_spec_clearAxes\n"
            f"    {members}\n"
            f"    (implementation_clearAxes\n"
            f"      {members}) := by\n"
            f"  unfold problem_spec_clearAxes\n"
            f"  rintro {destructure}\n"
            f"  simp [implementation_clearAxes] at {hyp}\n")


def _w_member(members, i):
    """Refute the per-member clause (C2) at position `i`."""
    return (f"example : ¬ problem_spec_clearAxes\n"
            f"    {members}\n"
            f"    (implementation_clearAxes\n"
            f"      {members}) := by\n"
            f"  unfold problem_spec_clearAxes\n"
            f"  rintro ⟨-, -, h⟩\n"
            f"  have hi := h {i} (by simp)\n"
            f"  simp [implementation_clearAxes] at hi\n")


def _w_emptied(members):
    """Refute the emptied-collection clause (C0)."""
    return _witness(members, "⟨hnew, -, -⟩", "hnew")


def _w_length(members):
    """Refute the length clause (C1)."""
    return _witness(members, "⟨-, hlen, -⟩", "hlen")


# NINE DISTINCT ground input points, one per rival (pts=9). Lengths 1, 2 and 3
# are all exercised, and the payload/owner tokens differ per point so no two
# rivals are refuted at the same input.
_P1_A = _members(_m(7, 1, 2))
_P1_B = _members(_m(6, 9, 9))
_P1_C = _members(_m(2, 3, 4))
_P1_D = _members(_m(13, 1, 1))
_P2_A = _members(_m(3, 5, 6), _m(4, 5, 6))
_P2_B = _members(_m(9, 2, 3), _m(8, 2, 3))
_P2_C = _members(_m(11, 7, 8), _m(12, 7, 8))
_P3_A = _members(_m(1, 4, 4), _m(2, 4, 4), _m(5, 4, 4))
_P3_B = _members(_m(20, 3, 3), _m(21, 3, 3), _m(22, 3, 3))
# ADDED BY AUDIT. A tenth point, at payload ZERO: the one payload value at which
# `weak-clobber-payload`'s reset-to-0 is INVISIBLE, which is why the frame clause
# needs a second rival whose corruption is observable there (see
# `weak-payload-shift`). Two members so the shift is seen at more than one
# position, and both owners set so the clause is reached at all.
_P2_D = _members(_m(0, 4, 5), _m(1, 4, 5))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_clearAxes` statement byte-identical and adds no
    # declaration. All three confirmed by a real build.
    # =====================================================================
    {
        "id": "pos-fresh-after",
        "kind": "soundness",
        "expect": "verify",
        # Reordering positive: the frozen impl binds the container's fresh
        # (empty) collection BEFORE walking the members; here it is produced
        # AFTER the walk instead. This is the port of nagini's
        # `pos-rebind-after`, whose whole point is that emptying the collection
        # and de-parenting the members are independent steps whose ORDER the
        # spec must not constrain. On the nagini carrier that reorder was
        # delicate (the post-loop rebind made the field expression stop denoting
        # the old collection, so the sibling had to add a stable local alias plus
        # an extra framing invariant to keep the retained permission connected to
        # its `Old(...)` handle). On this carrier there is no heap and no
        # permission, so the same reorder is a pure `let` motion and the frozen
        # proof still closes unchanged — the framing work the sibling documents
        # has no counterpart to do.
        "module": _swaps(
            _BASE,
            (_I_FRESH + "\n", ""),
            (_I_RETURN, "  let newChildren : List Artist := []\n" + _I_RETURN),
        ),
        "rationale": "correct reorder: the fresh empty collection is produced "
                     "AFTER the members are walked rather than before. Both "
                     "steps are independent, so C0/C1/C2 all still hold on "
                     "every input and this MUST verify — else the spec would "
                     "reject a faithful correct reordering (SPEC-TOO-STRONG). "
                     "Definitionally the frozen body, so the frozen proof "
                     "closes unchanged; statement byte-identical, no new "
                     "axiom/lemma. Ports nagini's pos-rebind-after.",
    },
    {
        "id": "pos-field-order",
        "kind": "soundness",
        "expect": "verify",
        # Clear the two back-references in the opposite order. Ports nagini's
        # `pos-swap-fields`, which writes the SECOND owner reference and then
        # the FIRST, as two separate writes.
        #
        # AUDIT NOTE (measured, do not "simplify" this back). The obvious
        # spelling — reordering the two fields INSIDE one record-update literal,
        # `{ chld with figure := none, axes := none }` — is vacuous on this
        # carrier and this case previously shipped it. Lean elaborates a
        # multi-field record update by field DECLARATION order, not by written
        # order, so `#print implementation_clearAxes` emits the byte-identical
        # term for both spellings (verified: the two `#print` outputs diff
        # empty). The case then "verified" by being the frozen impl under
        # another name — an honest pass that tested nothing, since a reshape the
        # elaborator erases cannot exercise the spec at all.
        #
        # Two SEQUENTIAL updates survive elaboration as two distinct steps
        # (`axes := chld.axes, figure := none` then `axes := none,
        # figure := chld.figure`), so the impl really is a different term that
        # the spec must still accept, which is what this lane is for. Confirmed
        # by real builds: the variant verifies with the frozen proof script
        # unchanged, and its printed term differs from gold's.
        "module": _swap(
            _BASE, _I_UPDATE,
            "    let chld := { chld with figure := none }\n"
            "    let chld := { chld with axes := none }"),
        "rationale": "correct reshape: the member's two owner references are "
                     "cleared in the opposite order, as two SEPARATE writes "
                     "(second owner first, then first owner). Clearing them is "
                     "order-independent — both still end absent — so C2a and "
                     "C2b both still hold and this MUST verify, else "
                     "SPEC-TOO-STRONG. Ports nagini's pos-swap-fields, which "
                     "is likewise two reversed writes rather than one reordered "
                     "literal; the one-literal spelling is erased by "
                     "elaboration on this carrier (see the comment above) and "
                     "would make the case vacuous.",
    },
    {
        "id": "pos-guarded-deparent",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E: correct reshapes the spec must not reject).
        # The one positive whose per-member step BRANCHES: it clears the two
        # owner references only when at least one of them is actually set, and
        # passes an already-deparented member through untouched. Both branches
        # land the same value, so it is extensionally the frozen impl and MUST
        # verify — but it is the near-miss of `weak-skip-first`/`weak-skip-last`,
        # which are also guarded per-member steps and are REJECTED. So this case
        # is what shows the spec discriminates on the guard's MEANING rather than
        # on the presence of a guard: a conditional deparent is fine when the
        # condition cannot leave a member parented, and fatal when it can.
        # Re-proves: the guard has to be case-split away before the accumulator
        # induction closes, so `_P_CLOSED_FORM` is replaced by an inlined
        # induction that does `cases` on the member's two references. Statement
        # byte-identical, no new declaration, no assumption token. Confirmed by a
        # real build (exit 0).
        "module": _swaps(
            _BASE,
            (_I_UPDATE,
             "    let chld := if chld.axes.isSome || chld.figure.isSome then "
             "{ chld with axes := none, figure := none } else chld"),
            (_P_CLOSED_FORM, """  unfold implementation_clearAxes
  simp only [Id.run, bind]
  have h : ∀ (xs : List Artist) (init : List Artist),
      Id.run (forIn xs init (fun chld r =>
        (pure (ForInStep.yield (r ++ [if chld.axes.isSome || chld.figure.isSome then
          { chld with axes := none, figure := none } else chld])) : Id _)))
        = init ++ xs.map (fun c => { c with axes := none, figure := none }) := by
    intro xs init
    induction xs generalizing init with
    | nil => simp
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      rw [ih]
      rcases a with ⟨d, ax, fg⟩
      cases ax <;> cases fg <;> simp
  have := h artists []
  simp only [Id.run] at this
  rw [this]
  rfl"""),
        ),
        "rationale": "correct reshape with a BRANCHING per-member step: the two "
                     "owner references are cleared only when one of them is "
                     "still set, and an already-deparented member is passed "
                     "through. Both branches yield the same member, so C0/C1/C2 "
                     "hold on every input and this MUST verify, else "
                     "SPEC-TOO-STRONG. Its value is the contrast with "
                     "weak-skip-first/weak-skip-last, which are guarded "
                     "per-member steps that ARE rejected: together they show "
                     "the spec keys on whether the guard can leave a member "
                     "parented, not on whether a guard is present. Re-proved "
                     "honestly (the guard is case-split before the accumulator "
                     "induction); statement byte-identical, no new "
                     "axiom/lemma.",
    },
    {
        "id": "pos-bulk-update",
        "kind": "soundness",
        "expect": "verify",
        # Structurally DIFFERENT correct shape (no nagini counterpart — the
        # sibling's carrier has to mutate in place, element by element, so it
        # cannot express this): build the whole former-member list in ONE bulk
        # positional update instead of accumulating it a member at a time. This
        # changes the impl's control flow (the loop disappears), so the frozen
        # closed-form lemma's accumulator induction no longer applies and the
        # case RE-PROVES: `_P_CLOSED_FORM`'s body becomes a direct
        # `unfold` + `rfl`. Both the theorem STATEMENT and the obligation's own
        # tactic script are untouched, and no declaration is added or removed —
        # the pre-existing accumulator lemma simply goes unused.
        "module": _swaps(
            _BASE,
            (_I_LOOPHEAD + "\n" + _I_UPDATE + "\n" + _I_ACCUM + "\n",
             "  formerChildren := oldChildren.map "
             "(fun c => { c with axes := none, figure := none })\n"),
            (_P_CLOSED_FORM, "  unfold implementation_clearAxes\n  rfl"),
        ),
        "rationale": "structurally different CORRECT impl: the former-member "
                     "list is produced by one bulk positional update rather "
                     "than accumulated member-by-member, so the loop is gone "
                     "entirely. It computes the same list at the same "
                     "positions, so C0/C1/C2 all hold and it MUST verify — "
                     "else the spec would be pinned to one particular "
                     "traversal shape (SPEC-TOO-STRONG). Re-proved honestly: "
                     "the closed-form lemma's accumulator induction is "
                     "replaced by `unfold` + `rfl` for the new shape; "
                     "statement byte-identical, no new axiom/lemma, no "
                     "assumption token.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries NO precondition
    # hypothesis at all (it is `∀ artists, ...`), so nagini's
    # `admiss-readable-fields` — which asserts the per-member field permission
    # its `Requires` grants is really usable at a non-empty input — has no
    # permission to re-express. The honest analogue on this carrier is to
    # discharge the POSTCONDITION itself, by evaluation, at a normal non-empty
    # input (several members, all sharing an owner, as the F2P's several
    # co-owned members do), as a ground `have`; then close the frozen
    # obligation verbatim. Confirmed by a real build.
    # =====================================================================
    {
        "id": "admiss-ground-members",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_clearAxes\n"
            f"      {_members(_m(7, 1, 2), _m(8, 1, 2))}\n"
            "      (implementation_clearAxes\n"
            f"        {_members(_m(7, 1, 2), _m(8, 1, 2))}) := by\n"
            "    rw [impl_eq_clearAxes]\n"
            "    refine ⟨rfl, by simp, ?_⟩\n"
            "    intro i hi\n"
            "    simp only [List.length_cons, List.length_nil] at hi\n"
            "    interval_cases i <;> exact ⟨_, _, rfl, rfl, rfl, rfl, rfl⟩\n"
            + _P_INTRO),
        "rationale": "the modeled behavior is SATISFIABLE at a normal "
                     "F2P-shaped input: the postcondition is discharged by "
                     "evaluation at two members sharing both owners (the "
                     "F2P's shape — several co-owned members reset at once) as "
                     "a ground `have`, then the frozen obligation is closed "
                     "verbatim. Must verify; else the obligation would be "
                     "unsatisfiable at exactly a normal input, the analogue of "
                     "PRECOND-TOO-STRONG. Nothing is assumed: no new "
                     "declaration, statement byte-identical, the ground "
                     "instance is a `have` prepended inside the existing "
                     "tactic body. Re-expresses nagini's "
                     "admiss-readable-fields, whose permission-readability "
                     "assertion has no counterpart on a carrier with no "
                     "permissions and no precondition.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve the F2P, and (b) a witness
    # pinning the violation at one concrete input, each SEEN to hold of the
    # rival and fail on gold.
    # =====================================================================

    # ---- clear only the FIRST owner reference (nagini weak-host-only) ----
    {
        "id": "weak-first-owner-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_UPDATE,
                        "    let chld := { chld with axes := none }"),
        "refinement": "its faithful real counterpart clears only the FIRST of "
                      "the two owner references a former member carries and "
                      "leaves the second still set, so after the reset every "
                      "former member still reports the second owner as "
                      "present. The F2P walks every former member and asserts "
                      "BOTH references are absent, so it fails on the second "
                      "assertion for the very first member it checks — the "
                      "faithful patch would NOT resolve, making a verifying "
                      "rival here a true verify-does-not-imply-resolve break.",
        "rationale": "REJECT from C2b: the spec pins `a.figure = none` at every "
                     "position, but the rival never clears that reference, so "
                     "the conjunct fails at position 0 already. Refuted at a "
                     "single member whose two owner tokens DIFFER (some 1 / "
                     "some 2), so the surviving reference cannot be confused "
                     "with the cleared one.",
        "witness": _w_member(_P1_A, 0),
    },

    # ---- clear only the SECOND owner reference (nagini weak-canvas-only) ----
    {
        "id": "weak-second-owner-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _I_UPDATE,
                        "    let chld := { chld with figure := none }"),
        "refinement": "its faithful real counterpart clears only the SECOND "
                      "owner reference and leaves the FIRST still set — "
                      "exactly the behavior the issue reports, where after the "
                      "reset a former member still names the container it no "
                      "longer belongs to. The F2P asserts that first reference "
                      "is absent for every former member, so the faithful "
                      "patch would NOT resolve.",
        "rationale": "REJECT from C2a: the spec pins `a.axes = none` at every "
                     "position, but the rival never clears that reference. "
                     "Refuted at a DISTINCT single-member point from "
                     "weak-first-owner-only (payload 6, both owner tokens "
                     "some 9) — the two rivals fail on OPPOSITE sub-clauses, so "
                     "each needs its own point rather than sharing one.",
        "witness": _w_member(_P1_B, 0),
    },

    # ---- skip the FIRST member (nagini weak-skip-first) ----
    {
        "id": "weak-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial domain: correct on every member EXCEPT the first, which is
        # passed through still parented. Keyed off the accumulator being empty,
        # which is true exactly on the first iteration.
        "module": _swap(
            _BASE, _I_UPDATE,
            "    let chld := if formerChildren.isEmpty then chld"
            " else { chld with axes := none, figure := none }"),
        "refinement": "partial-domain: its faithful real counterpart "
                      "de-parents every former member EXCEPT the first (an "
                      "off-by-one that starts the walk one position in). The "
                      "F2P resets a container holding SEVERAL members and then "
                      "asserts both references absent for each of them in "
                      "order, so it fails on the very first member — the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C2 at i=0: the spec's ∀ ranges over EVERY "
                     "position, so leaving position 0 parented violates C2a and "
                     "C2b there while every later position is correct. Refuted "
                     "at a TWO-member input — a length no single-member witness "
                     "reaches, and the length at which 'skip the first' is "
                     "distinguishable from 'skip them all'.",
        "witness": _w_member(_P2_A, 0),
    },

    # ---- skip the LAST member (nagini weak-skip-last) ----
    {
        "id": "weak-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror partial domain: correct on every member except the final
        # one, which is passed through still parented.
        "module": _swap(
            _BASE, _I_UPDATE,
            "    let chld := if formerChildren.length + 1 = oldChildren.length "
            "then chld else { chld with axes := none, figure := none }"),
        "refinement": "partial-domain: its faithful real counterpart "
                      "de-parents every former member EXCEPT the last (a walk "
                      "that stops one position short). The F2P's final former "
                      "member would keep both owner references set, so the "
                      "loop asserting they are absent fails on it — the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C2 at the LAST position: the spec's ∀ covers "
                     "every position, so leaving the final one parented "
                     "violates C2a/C2b there while positions 0..n-2 are "
                     "correct. Refuted at a THREE-member input, at index 2 — "
                     "the only witness probing a non-boundary-adjacent "
                     "position, so a rival keyed to the tail rather than to "
                     "index 0 is caught on its own terms.",
        "witness": _w_member(_P3_A, 2),
    },

    # ---- no de-parenting at all: the pre-patch behavior (nagini weak-no-deparent) ----
    {
        "id": "weak-no-deparent",
        "kind": "uniqueness",
        "expect": "reject",
        # Empty the collection but hand the former members back untouched. This
        # is `Solution_prepatch.lean`'s behavior, re-expressed by deleting the
        # walk rather than by rewriting the whole impl region.
        "module": _swaps(
            _BASE,
            (_I_LOOPHEAD + "\n" + _I_UPDATE + "\n" + _I_ACCUM + "\n", ""),
            (_I_RETURN, "  formerChildren := oldChildren\n" + _I_RETURN),
        ),
        "refinement": "this is the PRE-RESET behavior itself: the collection is "
                      "emptied and the former members are handed back "
                      "untouched, each still naming both owners. It is exactly "
                      "what the issue reports and what the F2P was written to "
                      "catch, so the faithful counterpart fails the F2P "
                      "outright. `Solution_prepatch.lean` carries this "
                      "behavior and its obligation is unclosable (G-DIFF).",
        "rationale": "REJECT from C2 (both C2a and C2b) at every position: no "
                     "member's owner references are ever cleared, so the "
                     "spec's ∀ fails at position 0. Refuted at a third "
                     "DISTINCT single-member point (payload 2, owners some 3 / "
                     "some 4).",
        "witness": _w_member(_P1_C, 0),
    },

    # ---- collection not emptied (nagini weak-no-empty) ----
    {
        "id": "weak-not-emptied",
        "kind": "uniqueness",
        "expect": "reject",
        # De-parent every former member correctly, but leave the container
        # holding its old collection instead of an empty one.
        "module": _swap(_BASE, _I_FRESH,
                        "  let mut newChildren : List Artist := artists"),
        "refinement": "its faithful real counterpart de-parents the former "
                      "members but FORGETS to empty the container's "
                      "collection, so the container keeps claiming members it "
                      "has just released — and those members no longer name it "
                      "back, leaving the object graph inconsistent in the "
                      "opposite direction. Anything that re-reads or re-resets "
                      "the container afterwards sees a non-empty collection of "
                      "already-released members, so the reset's own defining "
                      "guarantee is broken and the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from C0: the spec pins `result.1 = []`, but the "
                     "rival leaves the original collection in place, which "
                     "differs from `[]` on any non-empty input. This is the "
                     "ONLY rival attacking C0, and it is refuted at a "
                     "TWO-member point distinct from every other witness "
                     "(payloads 9/8, owners some 2 / some 3).",
        "witness": _w_emptied(_P2_B),
    },

    # ---- drop a member from the former-member list (attacks C1) ----
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # No nagini counterpart: the sibling mutates members in place, so it
        # cannot lose one. On this carrier the former members are RETURNED, so
        # the length clause C1 is a real, separately-abusable obligation — the
        # rival de-parents correctly but never records the final member.
        "module": _swap(
            _BASE, _I_ACCUM,
            "    formerChildren := if formerChildren.length + 1 = "
            "oldChildren.length then formerChildren "
            "else formerChildren ++ [chld]"),
        "refinement": "its faithful real counterpart de-parents the members it "
                      "walks but loses the last one from the set it reports as "
                      "released, so that member is never accounted for: it is "
                      "dropped from the container yet never observed as "
                      "de-parented, and whichever member the caller reads at "
                      "that position is the wrong one. The F2P checks every "
                      "former member it plotted, including the last, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from C1: the spec pins "
                     "`result.2.length = artists.length`, but the rival emits "
                     "one former member too few. This is the ONLY rival "
                     "attacking C1 — a carrier-specific clause with no nagini "
                     "counterpart (see the accounting block) — refuted at a "
                     "two-member point distinct from every other witness "
                     "(payloads 11/12, owners some 7 / some 8), where the "
                     "result has length 1 ≠ 2.",
        "witness": _w_length(_P2_C),
    },

    # ---- corrupt the preserved payload (attacks the frame clause C2c) ----
    {
        "id": "weak-clobber-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # No nagini counterpart: the sibling gets frame preservation from its
        # permission discipline (it holds permission to the two back-references
        # and to nothing else, so no other field CAN be written). On this
        # carrier the frame obligation is an explicit conjunct, so a rival can
        # attack it — clear both owner references correctly AND reset the
        # payload the operation must not touch.
        "module": _swap(
            _BASE, _I_UPDATE,
            "    let chld := { chld with data := 0, axes := none, "
            "figure := none }"),
        "refinement": "its faithful real counterpart de-parents each former "
                      "member correctly but also resets state the operation "
                      "has no business touching, so a member survives the "
                      "reset with its own content silently reinitialized. The "
                      "F2P's members are constructed with real content before "
                      "the reset and are still live objects afterwards, so a "
                      "counterpart that wiped that content would corrupt every "
                      "later use of them and break the many existing tests "
                      "that reset a container and keep using its former "
                      "members — the faithful patch would NOT resolve.",
        "rationale": "REJECT from C2c (the FRAME conjunct): the spec pins "
                     "`a.data = c.data`, so every field other than the two "
                     "owner references must survive unchanged; the rival "
                     "resets it. Refuted at a fourth distinct single-member "
                     "point whose payload is NON-ZERO (13), which is what makes "
                     "the clobber to 0 observable — and note the converse, "
                     "which is why weak-payload-shift exists: this rival is "
                     "INVISIBLE at payload 0, so C2c needs a second rival to be "
                     "attacked across the whole payload domain rather than only "
                     "away from that value.",
        "witness": _w_member(_P1_D, 0),
    },

    # ---- perturb (rather than reset) the preserved payload: C2c at payload 0 ----
    {
        "id": "weak-payload-shift",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). weak-clobber-payload resets the payload to
        # the CONSTANT 0, so it agrees with gold on exactly the inputs whose
        # payload already is 0 — a rival that is correct on a sub-domain the
        # existing C2c probe cannot see. This one SHIFTS the payload instead
        # (`+ 1`), which differs from the input at EVERY payload including 0, so
        # between the two the frame clause is attacked with no blind value left.
        # Its witness is stated at payload 0 for exactly that reason: it is the
        # point at which the shipped C2c rival would have passed.
        "module": _swap(
            _BASE, _I_UPDATE,
            "    let chld := { chld with data := chld.data + 1, axes := none, "
            "figure := none }"),
        "refinement": "its faithful real counterpart de-parents each former "
                      "member correctly but perturbs state the operation must "
                      "leave alone, so every former member comes back with its "
                      "own content silently shifted. Unlike a reset-to-default "
                      "this corrupts members whose content was already the "
                      "default, so no former member escapes; the F2P's members "
                      "are still live objects after the reset and are used "
                      "again, so the faithful patch would NOT resolve.",
        "rationale": "REJECT from C2c (the FRAME conjunct), at the one point "
                     "weak-clobber-payload cannot reach: the spec pins "
                     "`a.data = c.data`, and this rival breaks it at EVERY "
                     "payload, so it is refuted at a member whose payload is 0 "
                     "— where the reset-to-0 rival coincides with gold and would "
                     "have verified. Two-member point (payloads 0/1, owners "
                     "some 4 / some 5), distinct from every other witness.",
        "witness": _w_member(_P2_D, 0),
    },

    # ---- snapshot taken after the collection was already released (C1) ----
    {
        "id": "weak-late-snapshot",
        "kind": "uniqueness",
        "expect": "reject",
        # The ordering rival that mirrors `pos-fresh-after` from the wrong side:
        # the members to be released are snapshotted only AFTER the collection
        # has been given up, so the walk sees nothing and no former member is
        # reported at all. Distinguishes the correct reorder (pos-fresh-after,
        # which must verify) from the reorder that loses the snapshot.
        "module": _swap(_BASE, _I_SNAPSHOT,
                        "  let oldChildren : List Artist := []"),
        "refinement": "its faithful real counterpart releases the container's "
                      "collection BEFORE taking the snapshot of what to "
                      "de-parent, so the walk iterates over nothing and no "
                      "former member is de-parented or reported. Observably it "
                      "is the pre-reset behavior reached by a different route: "
                      "every former member keeps both owner references, so the "
                      "F2P fails exactly as it does before the fix — the "
                      "faithful patch would NOT resolve. It is a NEAR-MISS of "
                      "the correct reorder in pos-fresh-after, which is why it "
                      "is refuted at its own input rather than sharing one.",
        "rationale": "REJECT from C1: the spec pins "
                     "`result.2.length = artists.length`, but the rival "
                     "reports NO former members, so the length is 0 on any "
                     "non-empty input. Refuted at a THREE-member point "
                     "(payloads 20/21/22, both owners some 3) — distinct from "
                     "weak-drop-last's two-member point, so the two C1 rivals "
                     "are separated by input length as well as by degree "
                     "(one member short vs. all members lost).",
        "witness": _w_length(_P3_B),
    },
]

# ---------------------------------------------------------------------------
# NAGINI -> LEAN ACCOUNTING. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness rivals) plus an EMPTY axiom lane.
# This bundle models the SAME single behavior, so every sibling case has a
# counterpart; three rivals are ADDED for clauses this carrier introduces.
#
#   sibling case               -> here                        disposition
#   ---------------------------------------------------------------------------
#   pos-rebind-after           -> pos-fresh-after             PORTED
#   pos-swap-fields            -> pos-field-order             PORTED (re-landed;
#                                                             see AUDIT NOTE on
#                                                             that case: the
#                                                             one-literal
#                                                             spelling it first
#                                                             shipped was erased
#                                                             by elaboration and
#                                                             tested nothing)
#   admiss-readable-fields     -> admiss-ground-members       RE-EXPRESSED
#   weak-host-only             -> weak-first-owner-only       PORTED
#   weak-canvas-only           -> weak-second-owner-only      PORTED
#   weak-skip-first            -> weak-skip-first             PORTED
#   weak-skip-last             -> weak-skip-last              PORTED
#   weak-no-deparent           -> weak-no-deparent            PORTED
#   weak-no-empty              -> weak-not-emptied            PORTED
#   (none)                     -> pos-bulk-update             ADDED (positive)
#   (none)                     -> weak-drop-last              ADDED (attacks C1)
#   (none)                     -> weak-clobber-payload        ADDED (attacks C2c)
#   (none)                     -> weak-late-snapshot          ADDED (attacks C1)
#   (none)                     -> pos-guarded-deparent        ADDED BY AUDIT
#                                                             (positive, attack E)
#   (none)                     -> weak-payload-shift          ADDED BY AUDIT
#                                                             (attacks C2c at
#                                                             payload 0, attack D)
#   AXIOM_TESTS (0)            -> (none)                      DROPPED (G-AX)
#
# NOTHING WAS OMITTED. Every one of the sibling's 9 SPEC cases has a counterpart
# above; no case was dropped for being hard to prove, and no soundness positive
# was abandoned because its proof would not close (all three positives and the
# admissibility case were confirmed to verify by real `lake env lean` builds).
#
# RE-EXPRESSED (admiss-ground-members): the sibling's admissibility case asserts
#   that at a non-empty input it can READ a member's two back-references, i.e.
#   that its `Requires` really grants the per-member field permission it claims.
#   The frozen obligation here is `∀ artists, ...` with NO precondition
#   hypothesis and no permission system, so there is no Requires-domain to
#   admit. The honest analogue is to show the obligation is non-vacuously
#   SATISFIABLE at a normal F2P-shaped input, by discharging the postcondition
#   by evaluation at two co-owned members, then closing the frozen obligation
#   verbatim.
#
# ADDED (pos-bulk-update): a third positive with no sibling counterpart, because
#   the sibling's carrier CANNOT express it — it mutates members in place, so a
#   bulk positional update is not a shape available there. It is the one
#   positive that changes the impl's control flow rather than just its ordering,
#   so it is the one that tests whether the spec is pinned to a particular
#   traversal.
#
# ADDED (weak-drop-last, weak-late-snapshot, weak-clobber-payload): these attack
#   the two clauses this carrier INTRODUCES, and they are not fabrications for an
#   unmodeled behavior — they are load-bearing conjuncts of the SAME modeled
#   spec. Referential transparency turns the sibling's in-place mutation into a
#   RETURNED former-member list, which (a) makes the list's LENGTH an obligation
#   the sibling's heap model did not need (a mutated member cannot go missing,
#   but a returned one can — weak-drop-last loses one, weak-late-snapshot loses
#   all of them), and (b) makes frame preservation an explicit conjunct where the
#   sibling got it from holding permission to the two back-references and
#   nothing else (weak-clobber-payload). Without these three, a rival that
#   dropped a former member or corrupted its payload would verify and the
#   battery would never notice.
#
# VACUOUS (frame/permission MUTATION as a probe): the sibling's own DEFENDED
#   SURFACE prose already records that this class does not apply to it — the
#   per-member back-references are FULL-permission inputs by design, so there is
#   no read-only input to overwrite and `has_readonly_input == False`. On this
#   referentially transparent carrier there is additionally no heap, no aliasing
#   and no fraction. No substitute permission probe is fabricated. The frame
#   OBLIGATION, by contrast, is live and attacked (weak-clobber-payload).
#
# VACUOUS (divergence / non-termination): genuinely vacuous HERE, and for the
#   carrier's reason, not the spec's. `implementation_clearAxes` is a total Lean
#   `def`, so a non-terminating rival cannot be written at all — there is no
#   impl to ship, not a rival the spec admits. This is explicitly NOT the velvet
#   disposition (the corpus-wide termination-semantics finding: under
#   `loom.semantics.termination "partial"`, 401 of 500 bundles ADMIT a diverging
#   impl vacuously while its faithful patch hangs the F2P — a known SPEC HOLE).
#   The sibling ships no divergence case either, so there was nothing to port.
#
# VACUOUS (ungrounded-oracle echo): the postcondition is grounded in constants
#   and in the input (`= none`, `= []`, lengths, a per-position equation against
#   `artists[i]?`); there is no opaque answer key to echo. Covered instead by the
#   honest positive controls, exactly as the sibling records.
#
# POINT SPREAD. The NINE reject witnesses probe nine DISTINCT ground inputs
# (pts=9), across three list LENGTHS and three refuted CLAUSE positions:
#   len 1  [7|1,2]           weak-first-owner-only   C2b   at i=0
#   len 1  [6|9,9]           weak-second-owner-only  C2a   at i=0
#   len 1  [2|3,4]           weak-no-deparent        C2a+b at i=0
#   len 1  [13|1,1]          weak-clobber-payload    C2c   at i=0
#   len 2  [3,4|5,6]         weak-skip-first         C2    at i=0
#   len 2  [9,8|2,3]         weak-not-emptied        C0    (no index)
#   len 2  [11,12|7,8]       weak-drop-last          C1    (no index)
#   len 3  [1,2,5|4,4]       weak-skip-last          C2    at i=2
#   len 3  [20,21,22|3,3]    weak-late-snapshot      C1    (no index)
#   len 2  [0,1|4,5]         weak-payload-shift      C2c   at i=0  (payload 0)
# The spec's single INPUT binder `artists` is therefore varied in all three ways
# it is load-bearing: its length (1/2/3), its per-position payload and owner
# tokens (all nine points differ), and which position the refutation reads (0, 2,
# and none). The `result` position is not a binder a reject case can vary — it is
# what the rival PRODUCES.
#
# EVERY CLAUSE ATTACKED: C0 (weak-not-emptied), C1 (weak-drop-last,
# weak-late-snapshot), C2a (weak-second-owner-only, weak-no-deparent), C2b
# (weak-first-owner-only, weak-no-deparent), C2c (weak-clobber-payload away from
# payload 0, weak-payload-shift AT payload 0 — see those two cases on why one
# rival does not cover the clause), and the ∀'s positional reach
# (weak-skip-first at the head, weak-skip-last at the tail).
# EVERY OBLIGATION DEFENDED: correct_clearAxes by FOUR soundness positives
# (reorder, reversed two-write, bulk update, guarded per-member step) plus the
# admissibility case.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job, and this bundle declares no
# `opaque` callee and consumes no `axiom` (the behavior is modeled deeply), so
# there is nothing to probe; the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
