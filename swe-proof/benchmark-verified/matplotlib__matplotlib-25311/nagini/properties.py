"""PBT falsification battery for matplotlib__matplotlib-25311.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants (frozen spec, swapped impl region) checked by Nagini verify +
same_spec; this bundle has NO @ContractOnly axiom and NO consumed-axiom A-step
(meta.json axioms == []), so AXIOM_TESTS holds only the A-reference deep-model
soundness/containment probes that the bundle's own axiom_check.py performs.

Defended surface (build_helper_state -> List[int])
--------------------------------------------------
The model abstracts the live runtime objects a draggable helper touches to
distinct int OBJECT IDENTITIES, and the helper's serialisable __dict__ to a
List[int] of held identities. The change under specification: the canvas (the
drawing surface) moves from a stored instance attribute (in __dict__, hence
pickled) to a class-level property (never in __dict__). The model captures this
as "surface is ABSENT from Result() while every genuine attribute is PRESENT".

Parameters: surface, element_id, drag_flag, blit_flag, cid_pick, cid_release
all : int (object identities, passed BY VALUE). There is NO reference-typed
parameter and NO Acc(x, 1/2) read-only INPUT in the precondition -- the only
permission in the postcondition is Acc(list_pred(Result())) (ownership of the
returned list). So has_readonly_input == False and the FRAME-MUTATION weakness
class (overwrite a half-permission read-only input to satisfy a postcondition
vacuously) DOES NOT APPLY: there is no aliased input object the impl could write
through. A "mutate the input" rival here is impossible to even spell (the inputs
are ints); the canonical frame-mutation probe is N/A for this spec and is
justified-omitted (see 'assessment'). We instead include a permission-level
negative control below (a rival that drops the result-ownership obligation) so
the permission lane is still exercised.

Precondition (the ONLY constraints on inputs):
  Requires(surface != element_id), != drag_flag, != blit_flag,
           != cid_pick, != cid_release
  -> the drawing surface is a DISTINCT object from each genuine retained value.
     (No constraint forces the five genuine values to differ from one another;
     they may legitimately collide -- e.g. two callbacks abstracted identically.)

Postcondition (load-bearing clauses):
  (P0) Acc(list_pred(Result()))                 -- ownership of the result list.
  (P1) read_surface(surface) == surface         -- A2: read access preserved.
        read_surface is the IDENTITY @Pure helper, so P1 is a function of the
        INPUT alone (true for ANY impl). It is grounded, not an answer-key the
        impl could "echo" to dodge work -- there is no wrong echo of P1. It is
        the faithfulness guard (the read still yields the surface), not the
        discriminator.
  (P2) not contains(ToSeq(Result()), surface)   -- THE DISCRIMINATOR (A4): the
        drawing surface identity is ABSENT from the serialisable state. This is
        exactly the F2P observable ("FigureCanvasAgg" not in the figure pickle
        stream) and exactly what model_prepatch.py (canvas appended to state)
        violates (G-DIFF).
  (P3..P7) contains(ToSeq(Result()), x) for x in {element_id, drag_flag,
        blit_flag, cid_pick, cid_release}        -- the genuine attributes are
        RETAINED. These stop a "return [] / drop everything" cheat from
        satisfying P2 vacuously: the result must be the real instance state.

No ungrounded oracle: contains is a genuine front-recursive membership over the
ACTUAL Result() and read_surface is identity on the input; neither is an opaque
answer-key an impl can echo without producing the right list. UNGROUNDED-ORACLE
is therefore covered by an honest cheapest-impl positive control (the structural
variants below) rather than a wrong-echo reject -- stated per directive 2.

Region surgery: every variant is built by _swap on _BASE, replacing ONLY the
gold impl BODY (the text strictly between # impl-start / # impl-end). The frozen
spec (axioms/pure/pre/post-conditions + signatures) is never touched, which
mechanically GUARANTEES same_spec for every spec case.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25311"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The gold impl BODY, verbatim from model.py: everything strictly between
# `# impl-start` and `# impl-end`. Swapping this whole block edits ONLY the free
# (impl) region, so same_spec is guaranteed.
_GOLD = '''    # The serialisable state holds the genuine helper attributes; the drawing
    # surface is obtained on demand (read_surface) rather than stored.
    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    # The sequence view of the literal state, spelled out so the front-recursive
    # membership predicate unfolds one element per step.
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == element_id)
    Assert(s[1] == drag_flag)
    Assert(s[2] == blit_flag)
    Assert(s[3] == cid_pick)
    Assert(s[4] == cid_release)
    Assert(s.drop(1)[0] == drag_flag)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == cid_pick)
    Assert(s.drop(4)[0] == cid_release)
    Assert(len(s.drop(5)) == 0)
    # The drawing surface is absent: prove `not contains(..., surface)` from the
    # empty tail upward, each step discharging `head != surface` from the
    # distinctness preconditions.
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    # Each genuine attribute IS present: prove `contains` at its position by
    # unfolding to the element it sits at.
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s.drop(2), cid_release))
    Assert(contains(s.drop(1), cid_release))
    Assert(contains(s, cid_release))
    return state'''


# ===========================================================================
# POSITIVE CONTROL 1 (soundness): local-variable reshape. Build the SAME
# 5-element list through an intermediate local (different executable shape) and
# keep every gold proof obligation verbatim. A correct impl that differs only in
# construction surface MUST verify; else SPEC-TOO-STRONG. (Directive: change the
# executable shape, keep the gold invariants/asserts -- this preserves the
# front-recursive contains proof exactly.)
# ===========================================================================
_POS_RESHAPE = '''    # Structurally different construction: assemble the genuine attributes into
    # a local tuple of names first, then materialise the SAME serialisable state.
    e = element_id  # type: int
    d = drag_flag   # type: int
    b = blit_flag   # type: int
    p = cid_pick    # type: int
    r = cid_release # type: int
    state = [e, d, b, p, r]  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == element_id)
    Assert(s[1] == drag_flag)
    Assert(s[2] == blit_flag)
    Assert(s[3] == cid_pick)
    Assert(s[4] == cid_release)
    Assert(s.drop(1)[0] == drag_flag)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == cid_pick)
    Assert(s.drop(4)[0] == cid_release)
    Assert(len(s.drop(5)) == 0)
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s.drop(2), cid_release))
    Assert(contains(s.drop(1), cid_release))
    Assert(contains(s, cid_release))
    return state'''


# ===========================================================================
# POSITIVE CONTROL 2 (soundness): genuine REORDER. Emit the serialisable state
# with the five genuine attributes in a DIFFERENT order
# [cid_release, cid_pick, blit_flag, drag_flag, element_id] -- a structurally
# different state that still OMITS the surface and RETAINS every genuine value.
# __dict__ ordering is irrelevant to picklability, so the real helper's state is
# order-free; a faithful correct impl in any genuine order must verify. The full
# proof chain is re-derived for the new positions (no dropped framing asserts;
# directive 2). MUST verify; else SPEC-TOO-STRONG.
# ===========================================================================
_POS_REORDER = '''    # The genuine attributes in a different serialisation order; the surface is
    # still absent and every genuine value is still present.
    state = [cid_release, cid_pick, blit_flag,
             drag_flag, element_id]  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == cid_release)
    Assert(s[1] == cid_pick)
    Assert(s[2] == blit_flag)
    Assert(s[3] == drag_flag)
    Assert(s[4] == element_id)
    Assert(s.drop(1)[0] == cid_pick)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == drag_flag)
    Assert(s.drop(4)[0] == element_id)
    Assert(len(s.drop(5)) == 0)
    # surface absent: tail-up unfolding (head != surface from the distinctness
    # preconditions at every step).
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    # each genuine attribute present at its new position.
    Assert(contains(s.drop(4), element_id))
    Assert(contains(s.drop(3), element_id))
    Assert(contains(s.drop(2), element_id))
    Assert(contains(s.drop(1), element_id))
    Assert(contains(s, element_id))
    Assert(contains(s.drop(3), drag_flag))
    Assert(contains(s.drop(2), drag_flag))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s, cid_release))
    return state'''


# ===========================================================================
# ADMISSIBILITY: keep the gold impl, but at entry assert that a normal
# F2P-shaped input is admitted -- i.e. the precondition (surface distinct from
# each genuine value) is non-vacuous and the genuine values may legitimately
# COLLIDE with one another (only `surface` is constrained distinct). We assert
# the read accessor is establishable on a representative input. If a normal
# in-domain input could not establish the Requires this would fail =>
# PRECOND-TOO-STRONG. MUST verify.
# ===========================================================================
_ADMISS = '''    # The precondition admits a normal F2P-shaped input: surface is distinct
    # from each genuine value (Requires), while the genuine values themselves
    # carry NO mutual-distinctness constraint (they may collide). The read
    # accessor is establishable for any such input.
    Assert(surface != element_id)
    Assert(surface != cid_release)
    Assert(read_surface(surface) == surface)
''' + _GOLD


# ===========================================================================
# UNIQUENESS rivals (each MUST be rejected by a postcondition / permission).
# ===========================================================================

# (a) DISCRIMINATOR ATTACK = the pre-patch bug: APPEND the surface to the
#     serialisable state (store self.canvas as an instance attribute). All
#     genuine attrs present, but surface now leaks. This is exactly
#     model_prepatch.py's skeleton. The proof tries to discharge P2 over the
#     6-element list; P2 (not contains(..., surface)) is FALSE (surface sits at
#     index 5) so no proof can complete -> rejected by P2.
_W_LEAK_SURFACE = '''    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release, surface]  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 6)
    Assert(contains(s.drop(5), surface))
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s, cid_release))
    return state'''

# (b) VALUE-LEVEL DOUBLE-MASK / substitution: store `element_id` in the slot
#     where the surface would go (return the GENUINE state but with the surface
#     "encoded" as a copy of element_id). The genuine attrs are present and the
#     surface is absent -- BUT this rival's intent is to test whether P2 can be
#     dodged by aliasing the surface to a genuine value. It CANNOT: the surface
#     is a distinct identity (precondition), so this impl is in fact CORRECT and
#     MUST verify -- it is folded into the positive-control reasoning. (See
#     'assessment'.) Not emitted as a reject; documented here for completeness.

# (c) PARTIAL-DOMAIN (drop a genuine attribute): omit `cid_release` from the
#     serialisable state -- surface still absent, but one genuine connection id
#     is missing. Its faithful real patch forgets to register / retain one of
#     the two _connect_picklable callback ids in self.cids, so the helper's
#     state is incomplete. Rejected by P7 (contains(..., cid_release)).
_W_DROP_CID_RELEASE = '''    state = [element_id, drag_flag, blit_flag,
             cid_pick]  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 4)
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s, cid_pick))
    return state'''

# (d) PARTIAL-DOMAIN (drop the FIRST genuine attribute): omit `element_id`
#     (the ref_artist identity). Surface absent, every other genuine attr
#     present, but the reference element is missing from the serialisable
#     state. Its faithful real patch drops `self.ref_artist` from the helper's
#     retained state -- the helper cannot be reconstructed on unpickle (the
#     P2P round-trip / draggable rebind fails). Rejected by P3
#     (contains(..., element_id)).
_W_DROP_ELEMENT = '''    state = [drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 4)
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s, cid_release))
    return state'''

# (e) "DROP EVERYTHING" cheat: return the empty serialisable state. This is the
#     vacuous way to satisfy P2 (surface trivially absent from []). It MUST be
#     rejected because P3..P7 (the genuine attributes are retained) fail -- the
#     faithfulness guard. Its faithful real patch would null out the helper's
#     entire __dict__, breaking every P2P that relies on a functioning
#     DraggableBase. Rejected by P3..P7.
_W_EMPTY = '''    state = []  # type: List[int]
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 0)
    Assert(not contains(s, surface))
    return state'''

# (f) PERMISSION negative control (drops the result-ownership obligation): build
#     the correct serialisable state but DO NOT return it -- return a fresh,
#     unframed empty list instead, so the caller does not receive list_pred over
#     the genuine state. Stands in for the permission lane (frame-mutation is
#     N/A: no read-only input). P3..P7 fail on the returned [] (and the returned
#     list is not the genuine state). Rejected by the postcondition over
#     Result(). Its faithful real patch hands the caller a state object that is
#     not the helper's real __dict__, so the round-trip is broken.
_W_RETURN_FRESH_EMPTY = '''    correct = [element_id, drag_flag, blit_flag,
               cid_pick, cid_release]  # type: List[int]
    Assert(len(ToSeq(correct)) == 5)
    decoy = []  # type: List[int]
    s = ToSeq(decoy)  # type: PSeq[int]
    Assert(len(s) == 0)
    Assert(not contains(s, surface))
    return decoy'''


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_RESHAPE),
        "rationale": "structurally-different CORRECT impl: assemble the SAME "
        "5-element serialisable state through intermediate locals (different "
        "executable construction) while keeping every gold proof obligation "
        "verbatim (the front-recursive contains unfold chain). Must verify; else "
        "SPEC-TOO-STRONG -- the spec would reject a faithful correct construction "
        "variant.",
    },
    {
        "id": "pos-genuine-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _POS_REORDER),
        "rationale": "correct reshape: emit the genuine attributes in a different "
        "serialisation order [cid_release, cid_pick, blit_flag, drag_flag, "
        "element_id]. __dict__/state ordering is irrelevant to picklability (the "
        "F2P only inspects membership of the canvas in the pickle stream), so any "
        "genuine order is correct. The full contains proof chain is re-derived "
        "for the new positions (no dropped framing asserts). Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fts-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD, _ADMISS),
        "rationale": "the precondition admits a normal F2P-shaped input: surface "
        "distinct from each genuine value (Requires), genuine values otherwise "
        "unconstrained, and the read accessor read_surface(surface)==surface "
        "establishable. Asserts these at entry then runs the gold body. Must "
        "verify; else PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-leak-surface",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_LEAK_SURFACE),
        "refinement": "this is the PRE-PATCH bug verbatim: keep "
        "`self.canvas = self.ref_artist.figure.canvas` as a stored instance "
        "attribute, so the canvas identity lands in __dict__ and is emitted into "
        "the figure pickle stream. The F2P test_complete asserts "
        "'FigureCanvasAgg' not in pickletools.genops(pkl); with the canvas stored "
        "this FAILS. model_prepatch.py is exactly this skeleton (canvas appended "
        "to state) and fails this same clause (G-DIFF). A verifying rival here "
        "would be a true verify-not-resolve break.",
        "rationale": "rejected by postcondition P2 (not contains(ToSeq(Result()), "
        "surface)): the surface identity sits at index 5 of the returned state, "
        "so contains(..., surface) is true and P2 is violated.",
    },
    {
        "id": "weak-drop-cid-release",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_DROP_CID_RELEASE),
        "refinement": "partial-domain: its faithful real patch retains only one "
        "of the two _connect_picklable callback ids in self.cids (drops the "
        "button_release_event connection from the retained state). The helper "
        "reconstructed on unpickle is missing a callback id, so the P2P pickle "
        "round-trip tests that exercise the rebound draggable (and the helper's "
        "own invariant that both cids are retained) break. A verify-not-resolve "
        "break.",
        "rationale": "rejected by postcondition P7 (contains(ToSeq(Result()), "
        "cid_release)): cid_release is absent from the returned 4-element state.",
    },
    {
        "id": "weak-drop-element",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_DROP_ELEMENT),
        "refinement": "partial-domain at the FIRST genuine attribute: its faithful "
        "real patch omits self.ref_artist from the helper's retained state. The "
        "draggable cannot identify the artist it repositions after an unpickle, "
        "so the round-trip-reconstructed figure's draggable is non-functional and "
        "the P2P suite (which reloads and redraws) breaks. A verify-not-resolve "
        "break.",
        "rationale": "rejected by postcondition P3 (contains(ToSeq(Result()), "
        "element_id)): element_id is absent from the returned state.",
    },
    {
        "id": "weak-empty-state",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_EMPTY),
        "refinement": "the vacuous cheat: return an EMPTY serialisable state, "
        "which trivially satisfies P2 (surface absent from []) without doing the "
        "work. Its faithful real patch nulls the helper's entire __dict__, so the "
        "DraggableBase has no ref_artist/cids/flags and every P2P that constructs "
        "or rebinds a draggable fails. This is the exact 'drop everything to "
        "satisfy absence vacuously' attack the P3..P7 retention guards defend "
        "against.",
        "rationale": "rejected by postconditions P3..P7 "
        "(contains(ToSeq(Result()), x) for each genuine x): the empty state "
        "contains none of element_id/drag_flag/blit_flag/cid_pick/cid_release.",
    },
    {
        "id": "weak-return-fresh-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD, _W_RETURN_FRESH_EMPTY),
        "refinement": "permission/ownership lane (frame-mutation is N/A here -- "
        "all inputs are ints, no read-only Acc(.,1/2) input to overwrite). The "
        "impl computes the correct state locally but RETURNS a different, empty "
        "list, so the caller is handed a state object that is NOT the helper's "
        "real __dict__. Its faithful real patch builds the right attributes but "
        "exposes the wrong object as the serialisable state, breaking the pickle "
        "round-trip. A verify-not-resolve break.",
        "rationale": "rejected by postconditions P3..P7 over Result(): the "
        "RETURNED list is empty (the locally-correct list is discarded), so none "
        "of the genuine attributes are members of ToSeq(Result()).",
    },
]


# ===========================================================================
# AXIOM lane: this bundle has NO @ContractOnly axiom (meta.json axioms == []).
# The single deep_model_reference is an A-REFERENCE (build_helper_state /
# read_surface / contains modelling the real DraggableBase set-up + canvas
# accessor), validated against the real matplotlib by the bundle's own
# axiom_check.py / G-AX. We persist that validation as two PBT axiom probes,
# embedding axiom_check.py's HOST-side source into each probe string (the runner
# mounts ONLY the probe at /work, so axiom_check.py is not in-container -- it is
# read on the host at manifest-load time and inlined). apply_gold=True: the
# obligations describe POST-FIX behaviour (canvas is a property, absent from
# __dict__).
#
#   ax-sound-deepmodel    (axiom-soundness):     run the real DraggableBase
#       (structural check) and assert the deep model's three claims hold --
#       (1) helper.canvas IS ref_artist.figure.canvas (read preserved),
#       (2) the canvas is ABSENT from vars(helper) (the serialisable state),
#       (3) every genuine attr (ref_artist/got_artist/_use_blit/cids) is present.
#       Plus the end-to-end F2P observable: no FigureCanvas class name in the
#       pickle stream of a figure with a draggable legend. Exit 0 iff sound.
#
#   ax-cover-deepmodel    (axiom-containment):   the model's Requires lets
#       build_helper_state be reached with ANY six int identities where surface
#       differs from each genuine value. The deep model must hold for the real
#       library on the inputs the model can reach. The only caller-reachable
#       shape is a real DraggableBase over a real figure artist (the surface is
#       always a distinct object from ref_artist/flags/cids at runtime -- the
#       Requires distinctness is satisfied). We CONFIRM containment by checking
#       the runtime distinctness the model's Requires encodes actually holds on
#       a real helper (the canvas identity differs from every genuine retained
#       identity), so no caller-reachable input lies outside the modelled
#       domain. Exit 0 iff every reachable input is covered.
# ===========================================================================

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


_PROBE_SOUNDNESS = '''# -*- coding: utf-8 -*-
"""axiom-soundness probe for matplotlib__matplotlib-25311 (A-reference deep
model). Runs the bundle's own axiom_check.py logic against the REAL, post-fix
matplotlib DraggableBase in-container. Exit 0 iff the deep model's three claims
(read preserved, canvas absent from serialisable state, genuine attrs retained)
AND the end-to-end F2P observable (no FigureCanvas in the figure pickle stream)
all hold. Embeds axiom_check.py source (read on the host; not mounted)."""
import sys

_SRC = ''' + repr(_AXIOM_CHECK_SRC) + '''

ns = {"__name__": "_axiom_check_embedded"}
exec(compile(_SRC, "axiom_check.py", "exec"), ns)

try:
    ns["check_structural"]()
    ns["check_end_to_end"]()
except AssertionError as exc:
    print("AXIOM-UNSOUND: deep model disagrees with real DraggableBase: %r" % (exc,))
    sys.exit(1)
except Exception as exc:
    print("AXIOM probe error: %r" % (exc,))
    sys.exit(1)
print("axiom-soundness OK: deep model matches real matplotlib DraggableBase "
      "(read preserved, canvas absent from serialisable state, genuine attrs "
      "retained; no FigureCanvas in figure pickle stream).")
sys.exit(0)
'''


_PROBE_CONTAINMENT = '''# -*- coding: utf-8 -*-
"""axiom-containment probe for matplotlib__matplotlib-25311. The model's
Requires reaches build_helper_state with six int OBJECT IDENTITIES where the
surface identity differs from each genuine retained value. We confirm that EVERY
caller-reachable shape (a real DraggableBase over a real figure artist) actually
satisfies that runtime distinctness -- i.e. the canvas object identity differs
from each genuine retained identity (ref_artist, got_artist, _use_blit, the cids)
-- so no reachable input lies OUTSIDE the modelled precondition domain. If a
reachable input violated the distinctness the model assumes, the deep model
would be mis-scoped (AXIOM-TOO-WEAK-FOR-CALLER)."""
import sys


def main():
    try:
        import matplotlib
    except Exception as exc:
        print("containment SKIP: matplotlib not importable: %r" % (exc,))
        return 0
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.offsetbox import DraggableBase

    fig = plt.figure()
    ax = fig.add_subplot(111)
    (line,) = ax.plot([0, 1, 2, 3, 4], [40, 43, 45, 47, 48], label="speed")
    helper = DraggableBase(line, use_blit=False)
    canvas_id = id(helper.canvas)

    # The genuine retained values the model abstracts (ref_artist, got_artist,
    # _use_blit, and the two cids). The model's Requires demands the surface
    # (canvas) identity differs from each. Confirm the real runtime honours it.
    genuine = {
        "ref_artist": id(helper.ref_artist),
        "got_artist": id(helper.got_artist),
        "_use_blit": id(helper._use_blit),
    }
    for idx, cid in enumerate(helper.cids):
        genuine["cid_%d" % idx] = id(cid)

    violations = [name for name, ident in genuine.items() if ident == canvas_id]
    if violations:
        print("AXIOM-TOO-WEAK-FOR-CALLER: canvas identity coincides with a "
              "genuine retained value (%r) -- a caller-reachable input violates "
              "the modelled distinctness precondition." % (violations,))
        plt.close(fig)
        return 1

    # And the canvas (surface) is genuinely a distinct, live object -- so the
    # precondition distinctness is non-vacuous and every reachable input is in
    # the modelled domain.
    assert helper.canvas is fig.canvas
    plt.close(fig)
    print("axiom-containment OK: on a real DraggableBase the canvas identity "
          "differs from every genuine retained identity (%d genuine values "
          "checked), so every caller-reachable input satisfies the model's "
          "distinctness precondition -- no reachable input is uncovered."
          % (len(genuine),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodel",
        "axiom": "build_helper_state/read_surface/contains (A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_SOUNDNESS,
        "rationale": "the A-reference deep model must equal the real matplotlib "
        "DraggableBase under the caller's runtime config (post-fix: canvas is a "
        "class-level property). Runs the bundle's axiom_check.py structural + "
        "end-to-end checks; any disagreement (canvas read changed, canvas present "
        "in __dict__, a genuine attr missing, or a FigureCanvas in the pickle "
        "stream) => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-deepmodel",
        "axiom": "build_helper_state/read_surface/contains (A-reference)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _PROBE_CONTAINMENT,
        "rationale": "every caller-reachable input (a real DraggableBase over a "
        "real figure artist) must satisfy the model's Requires (surface identity "
        "distinct from each genuine retained value). Confirms the canvas identity "
        "differs from ref_artist/got_artist/_use_blit/cids on the real helper; a "
        "reachable input where they coincided would put it outside the modelled "
        "domain (AXIOM-TOO-WEAK-FOR-CALLER).",
    },
]
