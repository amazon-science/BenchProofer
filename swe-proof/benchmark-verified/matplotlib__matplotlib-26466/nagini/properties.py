"""PBT falsification battery for matplotlib__matplotlib-26466.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants (frozen spec, swapped impl region) checked by Nagini verify +
same_spec. This bundle has NO @ContractOnly axiom and NO consumed-axiom A-step
(meta.json axioms == [], deep_model_references == []), so AXIOM_TESTS is empty;
the retain-vs-share delta is expressed DIRECTLY via fractional permissions at
BOTH carrier levels (container and per-component location), so there is no
callee oracle to fuzz/contain (refinement.md §E, mapping.md §3).

Defended surface (TWO byte-identical functions: retain_pair_a, retain_pair_b)
-----------------------------------------------------------------------------
Each models a construction site that stores the caller's (x, y) pair. Signature
  retain_pair_X(pair: List[Slot]) -> List[Slot]

The carrier models the per-component STORAGE LOCATION explicitly: `pair` is a
length-2 list of `Slot`s, entry i being the location holding component i, and
`Slot.value` the component value there. The component VALUES are OPAQUE objects
(mapping.md §2, refinement.md R-OPQ): the modeled operation reads and re-stores
them without ANY transformation, so the carrier deliberately admits no
arithmetic on them, and the value postconditions pin them by IDENTITY.

Why the location is modeled and not abstracted away (the G-EQ/G-PANEL-1 hole
this battery now defends): the behaviour under specification is whether the
retained pair still reads its components out of storage the CALLER can overwrite
in place. On a carrier that models only the container, "the retained container
is a distinct object" and "the retained components are decoupled from the
caller's storage" are the same predicate -- and on the repo's real carrier they
are NOT: a whole-container sub-view is a distinct container object that still
presents the caller's two component locations, so the caller's later in-place
overwrite is observable through it. Modeling the location makes that difference
expressible, and the FULL-permission clauses on `Result()[i].value` are what
reject it (cases `weak-share-caller-locations-*`, `weak-subview-container-*`).

Preconditions:
  * Requires(Acc(list_pred(pair), 1 / 2))     -- READ-ONLY container (half perm).
  * Requires(Acc(pair[0].value, 1 / 2))       -- READ-ONLY component location 0:
        the caller keeps its other half, i.e. it continues to own this location
        and may overwrite it after the call (this mirrors the F2P test mutating
        `of_xy[:]=1` / `an_xy[:]=2` after construction). => has_readonly_input.
  * Requires(Acc(pair[1].value, 1 / 2))       -- READ-ONLY component location 1.
  * Requires(len(pair) == 2)
  * Requires(MustTerminate(2))                -- TOTALITY: the construction-time
        retention is a bounded, loop-free step and MUST terminate. Under
        Nagini's partial-correctness default a diverging impl would satisfy
        every other clause vacuously; the obligation rejects it (this closed
        the G-PANEL-1/G-EQ divergent-loop hole the audit found: a `while True`
        body verified under an earlier spec but its real patch hangs constructor
        calls, so the F2P suite times out and does NOT resolve).

Postconditions (load-bearing clauses):
  (P1) Ensures(Acc(list_pred(pair), 1 / 2))   -- hands the container read share
        BACK; the op did not take ownership of the caller's container.
  (P2) Ensures(Acc(pair[0].value, 1 / 2))     -- hands location 0's read share
        BACK: the op did not take ownership of the caller's component location.
  (P3) Ensures(Acc(pair[1].value, 1 / 2))     -- same for location 1.
  (P4) Ensures(len(pair) == 2)
  (P5) Ensures(Acc(list_pred(Result())))      -- the retained CONTAINER is fully
        owned. Jointly with (P1) this is satisfiable ONLY if Result() is a
        distinct object from `pair`: an alias would need 1/2 (caller) + 1
        (instance) = 3/2 > 1 total permission to one object.
  (P6) Ensures(len(Result()) == 2)
  (P7) Ensures(Acc(Result()[0].value))        -- the retained pair's component
        LOCATION 0 is fully owned. Jointly with (P2) this is satisfiable only if
        that location is NOT the caller's location 0 -- so a retained pair that
        reads component 0 back out of the caller's storage is rejected even when
        its container is a distinct fresh object. This is the clause that makes
        the delta observable per component rather than per container.
  (P8) Ensures(Acc(Result()[1].value))        -- same for component location 1.
  (P9) Ensures(Result()[0].value is pair[0].value)  -- IDENTITY pin: the value in
        retained location 0 is the very object read from input location 0, in
        order, untransformed.
  (P10) Ensures(Result()[1].value is pair[1].value) -- IDENTITY pin, component 1.

Jointly (P5)+(P7)+(P8) say the retained pair owns its container AND both of the
locations its components live in, so none of the storage it reads back from is
storage the caller can still write to; (P1)-(P3) say the caller kept all of its
own. That pair of facts is the retention property the F2P observes.

The identity pins (P9)/(P10) close the transform hole an earlier int carrier
left: over ints a value-lossy transform such as `x // 1` is the identity, so a
floor-dividing impl verified while its real patch truncates real float
coordinates (the F2P uses (.5, .5)) and does NOT resolve. On the opaque carrier
no arithmetic on the components is expressible at all, and only carrying the
SAME objects through satisfies `is` -- exactly the untransformed pass-through.

No ungrounded oracle: (P9)/(P10) are grounded in the input, NOT pinned to a
@Pure answer-key an impl could echo. The ownership/decoupling that the F2P
actually observes lives in the PERMISSION clauses (P1-P3 vs P5,P7,P8), not in a
value oracle.

Construction discipline (guarantees same_spec)
----------------------------------------------
The two functions are byte-identical in their impl region, so a bare impl-body
string is NOT unique. Every variant below is therefore built by _swap on the
WHOLE function block (def ... through # impl-end): the spec portion (pre/post +
markers) is reproduced VERBATIM and only the text strictly between # impl-start
and # impl-end changes. The frozen spec is never touched => same_spec holds
mechanically. retain_pair_a's pre/post blocks carry extra comment lines (kept
verbatim), which also makes each function block unique. `Slot` and its contract
live OUTSIDE every impl region (they are part of the frozen spec view), so no
variant can reshape the carrier itself.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26466"
FLOAT_ENCODING = None  # meta.json float_encoding is null (components are opaque objects, no float arithmetic modeled)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two frozen function blocks, VERBATIM from model.py (def -> # impl-end).
# Swapping the whole block keeps the spec portion identical and edits ONLY the
# impl body, so same_spec is guaranteed. The spec prefixes/suffix are spelled
# out so each variant reconstructs the block with only its impl body changed.
# ---------------------------------------------------------------------------
_A_SPEC = '''def retain_pair_a(pair: List[Slot]) -> List[Slot]:
    # pre-conditions-start
    # The caller owns its container and each of its two component locations, and
    # keeps a read share of all three across the call: after construction
    # returns it may overwrite either location in place.
    Requires(Acc(list_pred(pair), 1 / 2))
    Requires(len(pair) == 2)
    Requires(Acc(pair[0].value, 1 / 2))
    Requires(Acc(pair[1].value, 1 / 2))
    # Construction-time retention is a bounded step: it MUST terminate (total
    # correctness). A diverging implementation would satisfy the postconditions
    # only vacuously while construction hangs forever.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The caller keeps its read share of the input container AND of each of its
    # two component locations: the operation takes ownership of none of them and
    # may retain neither the container nor either location.
    Ensures(Acc(list_pred(pair), 1 / 2))
    Ensures(len(pair) == 2)
    Ensures(Acc(pair[0].value, 1 / 2))
    Ensures(Acc(pair[1].value, 1 / 2))
    # The retained pair is fully owned at BOTH levels: the container is the
    # constructed object's own, and so is each of the two locations its
    # components live in -- none of that storage is storage the caller still
    # holds a read share of and can overwrite in place. Each retained location
    # carries the component value present in the corresponding input location at
    # this moment, untransformed (pinned by identity on the opaque carrier).
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].value))
    Ensures(Acc(Result()[1].value))
    Ensures(Result()[0].value is pair[0].value)
    Ensures(Result()[1].value is pair[1].value)
    # post-conditions-end
    # impl-start
'''

_B_SPEC = '''def retain_pair_b(pair: List[Slot]) -> List[Slot]:
    # pre-conditions-start
    Requires(Acc(list_pred(pair), 1 / 2))
    Requires(len(pair) == 2)
    Requires(Acc(pair[0].value, 1 / 2))
    Requires(Acc(pair[1].value, 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(pair), 1 / 2))
    Ensures(len(pair) == 2)
    Ensures(Acc(pair[0].value, 1 / 2))
    Ensures(Acc(pair[1].value, 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == 2)
    Ensures(Acc(Result()[0].value))
    Ensures(Acc(Result()[1].value))
    Ensures(Result()[0].value is pair[0].value)
    Ensures(Result()[1].value is pair[1].value)
    # post-conditions-end
    # impl-start
'''

# Gold impl body (between # impl-start and # impl-end), shared by both functions.
_GOLD_BODY = '''    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''


def _A(body):
    """retain_pair_a block with the given impl body (body must end at # impl-end)."""
    return _A_SPEC + body


def _B(body):
    return _B_SPEC + body


_A_GOLD = _A(_GOLD_BODY)
_B_GOLD = _B(_GOLD_BODY)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally-DIFFERENT but CORRECT impl.
# Reads component 1 BEFORE component 0 (gold reads 0 then 1), binds differently
# named locals, and builds the two owned locations in the opposite order, then
# assembles the same pair. No loop/fold here, so there is no induction-lemma trap
# (directive 3 N/A). Owned container + owned locations + both identity pins hold.
# Applied to BOTH functions. MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS_BODY = '''    src_second = pair[1]
    second = src_second.value  # type: object
    src_first = pair[0]
    first = src_first.value  # type: object
    mine_second = Slot(second)
    mine_first = Slot(first)
    retained = [mine_first, mine_second]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# ADMISSIBILITY: keep the gold impl, but assert at entry that the precondition is
# non-vacuous and actually grants the modeled reads -- with only the 1/2 read
# share of the container AND of each component location we can READ both
# components and KNOW len==2. If a normal F2P-shaped input could not establish
# the Requires, these asserts (or the gold reads) would fail =>
# PRECOND-TOO-STRONG. Applied to BOTH functions. MUST verify.
# ---------------------------------------------------------------------------
_ADMISS_BODY = '''    Assert(len(pair) == 2)
    probe0 = pair[0]
    Assert(probe0.value is probe0.value)
    probe1 = pair[1]
    Assert(probe1.value is probe1.value)
    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# FRAME-MUTATION (uniqueness, reject): write to a READ-ONLY component location
# of the caller (held at Acc(.,1/2)) before building the result. The gold reads
# are kept verbatim AFTER the write so the rejection is attributable to the write
# itself: writing pair[0].value needs FULL permission to that location, but only
# 1/2 is held -> "insufficient permission". This is the #1 weakness class and a
# byte-fuzzer never finds it. MUST reject.
# ---------------------------------------------------------------------------
_FRAME_BODY = '''    victim = pair[0]
    other = pair[1]
    victim.value = other.value
    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# ALIAS ECHO (uniqueness, reject): return the caller's own container directly --
# the PRE-PATCH bug verbatim (model_prepatch.py / model_prepatch_2.py).
# Satisfies the identity pins trivially (Result() IS pair) but cannot satisfy
# (P5) Acc(list_pred(Result())) at FULL permission while (P1) hands back the
# caller's 1/2 share: total 3/2 > 1. MUST reject for insufficient permission.
# This is the exact behaviour the F2P observes (mutating the input later moves
# the stored pair iff the stored pair reads the caller's storage).
# ---------------------------------------------------------------------------
_ALIAS_BODY = '''    return pair
    # impl-end'''


# ---------------------------------------------------------------------------
# SHARE-CALLER-LOCATIONS (uniqueness, reject) -- THE CLASS THE AUDIT BROKE THE
# OLD SPEC WITH, in its purest form. Build a genuinely FRESH container, but fill
# it with the CALLER'S OWN two component locations. Container-level freshness
# holds (a distinct list object, so (P5) is satisfiable) and both identity pins
# hold (the values read through those locations ARE pair[i].value), yet the
# retained pair still reads its components out of storage the caller owns and can
# overwrite in place. Rejected by (P7)/(P8): full permission to Result()[0].value
# is unsatisfiable while (P2) hands the caller back its 1/2 share of that same
# location. MUST reject.
# ---------------------------------------------------------------------------
_SHARE_LOCS_BODY = '''    given0 = pair[0]
    given1 = pair[1]
    retained = [given0, given1]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# SUBVIEW CONTAINER (uniqueness, reject) -- the audit's counterexample verbatim
# in its whole-container form: hand back a sub-view of the whole input rather
# than reading the components out. A slice is a distinct container object, so on
# a container-only carrier this verified; here the view still presents the
# caller's two component locations, so (P7)/(P8) reject it. MUST reject.
# ---------------------------------------------------------------------------
_SUBVIEW_BODY = '''    retained = pair[0:2]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# ONE-LOCATION-SHARED (uniqueness, reject, partial-domain): own component 0's
# location properly but share the caller's location for component 1. Correct on
# everything the container-level clauses see and on component 0; wrong exactly
# where the caller later overwrites component 1. Rejected by (P8) alone, so it
# also demonstrates that the two location clauses are independently load-bearing
# rather than one redundant pair. MUST reject.
# ---------------------------------------------------------------------------
_ONE_SHARED_BODY = '''    given0 = pair[0]
    x = given0.value  # type: object
    kept0 = Slot(x)
    given1 = pair[1]
    retained = [kept0, given1]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# ALIASED-RETAINED-LOCATION (uniqueness, reject, boundary/same-object): build ONE
# owned location and use it for BOTH components of the retained pair. The
# container is fresh and owned, component 0's value is right, and the single
# location is genuinely the constructed object's own -- but the retained pair's
# two components are the SAME location, so writing one moves the other and the
# pair cannot hold two independent components. Rejected because (P7) and (P8)
# together demand FULL permission to each of the two retained locations, which is
# 2 x full to one location when they coincide. MUST reject.
# ---------------------------------------------------------------------------
_SAME_LOC_BODY = '''    given0 = pair[0]
    x = given0.value  # type: object
    shared = Slot(x)
    retained = [shared, shared]  # type: List[Slot]
    return retained
    # impl-end'''


# ---------------------------------------------------------------------------
# WRONG-VALUE / partial-domain rivals (owned container + owned locations whose
# CONTENTS miss the identity pins).
# ---------------------------------------------------------------------------

# (swap) retained locations carry the components transposed. Owned at both
# levels, so the permission clauses pass; fails (P9) Result()[0].value is
# pair[0].value whenever the two components are distinct objects. MUST reject.
_SWAP_VALS_BODY = '''    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(y)
    kept1 = Slot(x)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''

# (const) both retained locations carry component 0. Fails (P10)
# Result()[1].value is pair[1].value whenever the two components are distinct
# objects. MUST reject.
_DUP_FIRST_BODY = '''    given0 = pair[0]
    x = given0.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(x)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''

# (diverge) an unconditional infinite loop instead of the retention -- the
# audit's verified-but-not-resolving counterexample class (its real patch put
# `n = 0; while True: n = n + 1` in front of the buggy retention, hanging the
# constructor). The loop guard is written `n >= 0` (always true from n=0, never
# decremented) rather than the literal `True` because Nagini's mypy front-end
# rejects syntactically dead code after `while True:`, which would mask the
# obligation verdict. Under Nagini's partial-correctness default the
# never-reached exit satisfies all value/permission postconditions vacuously;
# Requires(MustTerminate(2)) must REJECT it (obligation leak: the loop has no
# termination measure). MUST reject.
_DIVERGE_BODY = '''    n = 0
    while n >= 0:
        n = n + 1
    given0 = pair[0]
    x = given0.value  # type: object
    given1 = pair[1]
    y = given1.value  # type: object
    kept0 = Slot(x)
    kept1 = Slot(y)
    retained = [kept0, kept1]  # type: List[Slot]
    return retained
    # impl-end'''


SPEC_TESTS = [
    # ---- POSITIVE CONTROL (soundness) ----------------------------------
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _A_GOLD, _A(_POS_BODY)), _B_GOLD, _B(_POS_BODY)),
        "rationale": "structurally-different CORRECT impl in BOTH functions: read "
        "component 1 before component 0, rename locals, allocate the two owned "
        "locations in the opposite order, assemble the same pair. No loop/fold => "
        "no induction-lemma trap. Owned container + owned per-component locations "
        "+ both identity pins + read-only input all hold. Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    # ---- ADMISSIBILITY -------------------------------------------------
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_swap(_BASE, _A_GOLD, _A(_ADMISS_BODY)), _B_GOLD, _B(_ADMISS_BODY)),
        "rationale": "the precondition is non-vacuous for a normal F2P-shaped "
        "length-2 input: holding only the 1/2 read share of the container and of "
        "each component location we can READ both components and know len==2 (the "
        "modeled reads succeed). Must verify; else PRECOND-TOO-STRONG.",
    },
    # ---- FRAME-MUTATION (MANDATORY: read-only input) -------------------
    {
        "id": "frame-mutation-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_FRAME_BODY)),
        "refinement": "its faithful real patch would WRITE the caller's container "
        "in place (e.g. `ref_coord[0] = ref_coord[1]` before storing) and store "
        "that. That still reads the caller's storage AND corrupts the caller's "
        "data: the F2P test_annotate_and_offsetfrom_copy_input mutates the source "
        "array after the call and compares rendered figures -- a stored pair that "
        "reads the caller's storage moves with the later mutation, so the figures "
        "differ and the test FAILS. A verifying rival here would be a true "
        "verify-not-resolve break.",
        "rationale": "rejected by the PERMISSION system: writing pair[0].value "
        "requires FULL permission to that component location but the Requires "
        "grants only Acc(.,1/2) -- 'insufficient permission'. The gold reads are "
        "kept verbatim so the rejection is attributable to the read-only-input "
        "write (frame-mutation).",
    },
    {
        "id": "frame-mutation-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_FRAME_BODY)),
        "refinement": "same frame-mutation attack at the second construction site "
        "(_AnnotationBase.__init__ / `self.xy = xy`): a patch that mutates `xy` in "
        "place keeps reading the caller's storage and corrupts caller data; the "
        "F2P FAILS. Modeled separately because the two sites are independently "
        "changed (G-DIFF has one failing prepatch variant per site).",
        "rationale": "rejected by the PERMISSION system in retain_pair_b: writing "
        "pair[0].value needs FULL permission to that location but only Acc(.,1/2) "
        "is held. Gold reads kept verbatim; rejection attributable to the write.",
    },
    # ---- ALIAS ECHO (container level) ----------------------------------
    {
        "id": "alias-return-input-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_ALIAS_BODY)),
        "refinement": "this is the PRE-PATCH bug verbatim (model_prepatch.py): "
        "`self._ref_coord = ref_coord` stores the caller's OWN container. The issue "
        "reports and the F2P observes exactly this: mutating the source array after "
        "the call moves the stored coordinate (the arrow position changes). The F2P "
        "FAILS entirely. model_prepatch.py is this skeleton and fails verification "
        "(G-DIFF).",
        "rationale": "rejected by the PERMISSION system: (P5) Acc(list_pred("
        "Result())) at FULL permission is unsatisfiable jointly with (P1) "
        "Acc(list_pred(pair),1/2) when Result() IS pair -- 3/2 > 1 total. "
        "'insufficient permission to access list_pred(Result())'.",
    },
    {
        "id": "alias-return-input-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_ALIAS_BODY)),
        "refinement": "the PRE-PATCH bug at the second site (model_prepatch_2.py): "
        "`self.xy = xy` stores the caller's container. The F2P's `annotate(xy=...)` "
        "with a later `an_xy[:]=2` mutation moves the stored point and the rendered "
        "figures differ -- the test FAILS.",
        "rationale": "rejected by the PERMISSION system in retain_pair_b: same "
        "3/2 > 1 conflict on list_pred(Result()).",
    },
    # ---- SHARE THE CALLER'S COMPONENT LOCATIONS (the audit's break class) ----
    {
        "id": "weak-share-caller-locations-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_SHARE_LOCS_BODY)),
        "refinement": "its faithful real patch builds a fresh CONTAINER around the "
        "caller's own component storage rather than reading the components out of "
        "it -- on the repo's mutable-array carrier, any arrangement that still "
        "refers into the caller's buffer. The F2P mutates the source array in place "
        "after construction (`of_xy[:]=1` / `an_xy[:]=2`); the retained pair moves "
        "with it, byte-identical observable behaviour to the pre-patch bug, so the "
        "rendered figures differ and the F2P FAILS. This is the class that broke "
        "the earlier container-only spec: container-level freshness AND both "
        "identity pins hold, so nothing but the per-location ownership clauses "
        "catches it. A verify-not-resolve break.",
        "rationale": "rejected by (P7) Acc(Result()[0].value) at FULL permission: "
        "the retained pair's component location 0 IS the caller's location 0, whose "
        "1/2 read share (P2) hands back to the caller -- 3/2 > 1 total permission "
        "to one location. 'insufficient permission to access Result()[0].value'.",
    },
    {
        "id": "weak-share-caller-locations-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_SHARE_LOCS_BODY)),
        "refinement": "the same share-the-caller's-storage rival at the second "
        "construction site: the retained point still reads the caller's array, so "
        "the later in-place mutation moves it and the F2P FAILS. Modeled per site "
        "because the two sites are independently changed.",
        "rationale": "rejected by (P7)/(P8) in retain_pair_b: full permission to a "
        "retained component location the caller still holds a read share of is "
        "unsatisfiable.",
    },
    {
        "id": "weak-subview-container-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_SUBVIEW_BODY)),
        "refinement": "the audit's recorded counterexample in its whole-container "
        "form: hand back a sub-view spanning the input's two components instead of "
        "reading them out. On the repo's mutable-array carrier such a view is a "
        "distinct container object that still addresses the caller's buffer, so "
        "after the F2P's in-place mutation the retained pair reads the NEW values "
        "and the figures differ -- the F2P FAILS while a container-only spec "
        "verified it. A verify-not-resolve break, confirmed by the audit's executed "
        "resolve run.",
        "rationale": "rejected by (P7)/(P8): the view's component locations are the "
        "caller's, so full permission to Result()[0].value is unsatisfiable "
        "alongside the read share (P2) returns to the caller. Container-level "
        "clauses (P5)/(P6) and both identity pins are satisfied, so the rejection "
        "is attributable specifically to per-component ownership.",
    },
    {
        "id": "weak-subview-container-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_SUBVIEW_BODY)),
        "refinement": "the same sub-view rival at the second construction site; the "
        "audit materialized exactly this pair of sites and its patch did NOT "
        "resolve (F2P fails, P2P 100/100).",
        "rationale": "rejected by (P7)/(P8) in retain_pair_b for the same reason.",
    },
    {
        "id": "weak-one-location-shared",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_ONE_SHARED_BODY)),
        "refinement": "its faithful real patch reads component 0 out of the caller's "
        "storage but leaves component 1 referring into it. The F2P's later in-place "
        "overwrite moves the retained y coordinate while x stays put, so the arrow "
        "endpoint is wrong and the figure comparison FAILS. Partial-domain: correct "
        "on component 0 and on every container-level clause. A verify-not-resolve "
        "break.",
        "rationale": "rejected by (P8) Acc(Result()[1].value) ALONE -- component 1's "
        "retained location is the caller's. This case is what shows the two "
        "per-location clauses are independently load-bearing rather than a "
        "redundant pair: (P7) is satisfied here.",
    },
    {
        "id": "weak-aliased-retained-locations",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_SAME_LOC_BODY)),
        "refinement": "its faithful real patch retains a pair whose two components "
        "are one and the same storage location, so the retained pair cannot hold two "
        "independent components: the y coordinate reads back as the x coordinate. "
        "The annotation renders at the wrong point and the F2P FAILS. Boundary / "
        "same-object case: the retained storage IS the object's own (nothing shared "
        "with the caller), so only the two-distinct-locations reading of (P7)+(P8) "
        "catches it.",
        "rationale": "rejected because (P7) and (P8) each demand FULL permission to "
        "the retained component location, and the two coincide -- 2 x full to one "
        "location is unsatisfiable. 'insufficient permission to access "
        "Result()[1].value'.",
    },
    # ---- WRONG-VALUE / partial-domain ----------------------------------
    {
        "id": "weak-swap-components",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_SWAP_VALS_BODY)),
        "refinement": "its faithful real patch stores a TRANSPOSED pair "
        "(`self._ref_coord = y, x`). The retained (x, y) coordinate is wrong unless "
        "x==y; the F2P renders an annotation/OffsetFrom at the swapped coordinate, "
        "so the arrow lands in the wrong place and the figure comparison FAILS. "
        "Fully owned at both levels, so it would NOT be caught by the permission "
        "system -- only by the identity pins. A verify-not-resolve break.",
        "rationale": "rejected by postcondition (P9) Result()[0].value is "
        "pair[0].value: the rival's retained location 0 carries pair[1].value, a "
        "DIFFERENT object whenever the two components are distinct "
        "(partial-domain).",
    },
    {
        "id": "weak-dup-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_DUP_FIRST_BODY)),
        "refinement": "its faithful real patch stores a pair that drops the second "
        "component and duplicates the first (`self.xy = x, x`). The y coordinate of "
        "the annotation point is wrong unless x==y; the F2P arrow endpoints are "
        "misplaced and the figure comparison FAILS. Fully owned at both levels so "
        "the permission system passes -- only the identity pin catches it. A "
        "verify-not-resolve break.",
        "rationale": "rejected by postcondition (P10) Result()[1].value is "
        "pair[1].value: both retained locations carry pair[0].value, a DIFFERENT "
        "object than pair[1].value whenever the components are distinct "
        "(partial-domain).",
    },
    # ---- NON-TERMINATION (the audit's divergent-loop class) -------------
    {
        "id": "weak-diverge-no-terminate-a",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _A_GOLD, _A(_DIVERGE_BODY)),
        "refinement": "its faithful real patch inserts an unconditional "
        "`while True:` loop before the retention (the audit's counterexample "
        "patch did exactly this in OffsetFrom.__init__): every constructor "
        "call hangs, the F2P suite times out after 300s and the patch does "
        "NOT resolve. Under partial correctness the loop satisfies all value "
        "and permission postconditions vacuously -- a true verify-not-resolve "
        "break before MustTerminate was added.",
        "rationale": "rejected by Requires(MustTerminate(2)): the diverging "
        "loop body carries no termination measure, so the caller's obligation "
        "leaks ('Obligation leak check failed. Loop might not take all "
        "unsatisfied obligations from the context') and vacuous satisfaction "
        "of the remaining clauses is not enough.",
    },
    {
        "id": "weak-diverge-no-terminate-b",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _B_GOLD, _B(_DIVERGE_BODY)),
        "refinement": "same divergent-loop attack at the second construction "
        "site (_AnnotationBase.__init__): every annotate() call hangs, the "
        "F2P suite times out, the patch does not resolve.",
        "rationale": "rejected by Requires(MustTerminate(2)) in retain_pair_b: "
        "the loop cannot discharge the termination obligation.",
    },
]

# No @ContractOnly axiom and no consumed/A-reference deep model in this bundle
# (meta.json axioms == [], deep_model_references == []). The retain-vs-share delta
# is expressed DIRECTLY via fractional permissions at both carrier levels, so
# there is no callee Requires-domain to fuzz (soundness) or contain (containment).
# G-AX is vacuous; axiom_check.py runs the REAL OffsetFrom/_AnnotationBase
# constructors end-to-end (decoupling check) but validates the model's behaviour,
# not an axiom Ensures.
AXIOM_TESTS = []
