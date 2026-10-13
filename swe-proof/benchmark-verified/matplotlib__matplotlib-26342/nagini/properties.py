# properties.py — PBT falsification battery for matplotlib__matplotlib-26342.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: edits live ONLY
# inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   install_geometry(self: GeometryCollection, new_items: List[int]) -> None
#     Requires Acc(self.items)                          <-- the held-seq ref (FULL)
#     Requires Acc(self.out_of_date)                    <-- the flag (FULL)
#     Requires Acc(list_pred(new_items), 1/2)           <-- READ-ONLY input (half perm)
#     Ensures  Acc(self.items); Acc(self.out_of_date)
#     Ensures  self.items is new_items                  <-- LOAD-BEARING (identity)
#     Ensures  self.out_of_date is True                 <-- LOAD-BEARING (flag)
#     Ensures  Acc(list_pred(new_items), 1/2)           <-- frame: caller keeps its half
#     Ensures  len(new_items) == Old(len(new_items))    <-- input untouched (length)
#     Ensures  Forall k in-bounds: new_items[k] == Old(new_items[k])  <-- (contents)
#
#   Gold impl (the two-line setter, == patch.diff `self._paths = paths;
#   self.stale = True`):
#       self.items = new_items
#       self.out_of_date = True
#
#   THE TWO LOAD-BEARING CLAUSES:
#     (1) `self.items is new_items` — Nagini reference IDENTITY. The collection
#         must store and hand back the VERY object supplied. There is no @Pure
#         answer-key / opaque oracle here: the postcondition is pinned directly to
#         the input object (`new_items`) by identity and to the input's contents
#         by Old(...) per-index. So the "ungrounded-oracle echo" class is N/A —
#         there is no wrong value an impl could echo to satisfy `x is new_items`
#         other than literally aliasing new_items (which IS the gold). The honest
#         cheapest impl IS the gold store, so the positive control is a
#         branch-reorder (see 'assessment').
#     (2) `self.out_of_date is True` — the stale flag.
#
#   THE READ-ONLY INPUT: new_items is held at Acc(list_pred(new_items), 1/2).
#   Frame-mutation (writing into new_items) is therefore the MANDATORY #1 attack
#   and is included below (reject for INSUFFICIENT PERMISSION).
#
#   No @ContractOnly axioms (meta.axioms == []). The only kind-A item is an
#   A-reference (the real post-patch Collection.set_paths store-by-reference + flag
#   primitive), already exhaustively validated == the real callee by axiom_check.py
#   (G-AX, run apply_gold=True): the F2P ContourSet subject + PathCollection
#   [override deleted -> inherits base] + bare Collection incl. the empty boundary,
#   56 observations asserting get_paths() is paths / stale True / input untouched,
#   plus a LineCollection/PolyCollection negative control and 5000 cases of the
#   environment-independent attribute-assignment primitive. That established
#   real-callee check IS the axiom lane for this instance; re-encoding it as a new
#   Docker probe would duplicate, not strengthen, it. Hence AXIOM_TESTS = []. See
#   'assessment'.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-26342"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchor INSIDE the single impl region (between # impl-start / # impl-end).
# Editing only this text keeps spec_view (hence same_spec) byte-identical.
# The whole impl body is a unique anchor.
# ===========================================================================
_IMPL_GOLD = """    self.items = new_items
    self.out_of_date = True"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: install_geometry body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify)
# Reorder the two independent assignments: set the out-of-date flag FIRST, then
# store the supplied sequence by reference. Same post-state on BOTH load-bearing
# clauses (self.items is new_items, self.out_of_date is True). No framing lemma /
# loop / fold is involved (the impl is straight-line), so there is nothing the
# verifier could fail to auto-discharge. If this faithful correct impl could NOT
# verify against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    self.out_of_date = True
    self.items = new_items"""


# ===========================================================================
# (2) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify)
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that the half-permission input is
# usable (read its length via the Acc(list_pred(new_items),1/2) Requires) AND that
# the two full-permission fields are writable, then reach the gold post-state and
# Assert both load-bearing clauses hold. If the Requires were vacuous / over-
# strong, the impl could not BOTH read new_items' length AND establish the
# postcondition => PRECOND-TOO-STRONG. Every gold obligation is still met (the
# store + flag), so a normal non-raising return is reachable on an in-domain
# input.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: the half-permission input new_items is readable (its length
    # is observable under Acc(list_pred(new_items), 1/2)) and the two full-
    # permission fields are writable; a normal return is reachable.
    Assert(len(new_items) >= 0)        # new_items half-perm readable
    self.items = new_items
    self.out_of_date = True
    Assert(self.items is new_items)    # load-bearing identity established
    Assert(self.out_of_date is True)   # load-bearing flag established"""


# ===========================================================================
# (3) FRAME-MUTATION — write into the read-only input new_items (reject). MANDATORY.
# install_geometry holds only Acc(list_pred(new_items), 1/2). A WRITE into the
# supplied list — guarded so the index is in-bounds (len > 0) and value-NEUTRAL
# (new_items[0] = new_items[0]) — needs FULL permission to list_pred(new_items).
# With only the half-permission the Requires grants, Nagini rejects for
# INSUFFICIENT PERMISSION. The gold store + flag are kept verbatim AFTER the write
# so the rejection is attributable solely to the write, not to a spec/value
# change. A byte-fuzzer never thinks to mutate a read-only input — this is the
# project's #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    self.items = new_items
    self.out_of_date = True
    # FRAME MUTATION: write back into the read-only half-permission input.
    # Value-neutral and guarded in-bounds, so the ONLY reason it fails is that
    # writing a list element needs FULL permission to list_pred(new_items) while
    # the Requires grants only 1/2.
    if len(new_items) > 0:
        new_items[0] = new_items[0]"""


# ===========================================================================
# (4) COPY-NOT-IDENTITY — store a COPY of new_items, not the object (reject).
# This is the canonical uniqueness attack for THIS spec (refinement.md D.1): a
# copy stores a NEW list with identical elements. It would render the same
# geometry and mark the artist stale, so it PASSES the @check_figures_equal F2P
# test and all P2P — yet it FAILS the load-bearing identity clause
# `self.items is new_items` because list(new_items) is a fresh object, not the
# supplied one. expect=reject: if it verified, the spec would admit a non-gold
# (copy) algorithm => SPEC-TOO-WEAK relative to the gold by-identity store.
# (The flag is kept correct so the ONLY failing clause is the identity clause.)
# ===========================================================================
_IMPL_COPY = """    copied = list(new_items)  # type: List[int]
    self.items = copied
    self.out_of_date = True"""


# ===========================================================================
# (5) SKIP-THE-FLAG — store the object but leave out_of_date unset/false (reject).
# Stores EXACTLY the supplied object (identity clause holds) but does NOT mark the
# collection out of date. Fails the load-bearing `self.out_of_date is True`
# clause. (We assign False explicitly so the field is initialised — leaving it
# unassigned would fail to typecheck/frame, masking the spec reason.)
# ===========================================================================
_IMPL_NOFLAG = """    self.items = new_items
    self.out_of_date = False"""


# ===========================================================================
# (6) WRONG-OBJECT / INSTALL-EMPTY — store a fresh empty list (reject).
# Mirrors the pre-patch "install nothing" failure mode at the value level: store
# a brand-new empty list instead of the supplied sequence. Fails the identity
# clause (a fresh [] is not new_items) AND the contents/length clauses whenever
# new_items is non-empty. This is the partial-domain miss on the dominant F2P
# input (a non-empty contour path set). The flag is set correctly so the failure
# is squarely the identity / length / contents clauses, not the flag.
# ===========================================================================
_IMPL_EMPTY = """    fresh = []  # type: List[int]
    self.items = fresh
    self.out_of_date = True"""


SPEC_TESTS = [
    {
        "id": "pos-control-reorder-assignments",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the two independent "
                     "assignments are swapped (set the out-of-date flag first, then "
                     "store the supplied sequence by reference). The post-state is "
                     "identical on BOTH load-bearing clauses (self.items is new_items, "
                     "self.out_of_date is True). The impl is straight-line, so no "
                     "framing lemma / loop invariant the verifier must auto-discharge "
                     "is involved. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-input-and-fields",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that the half-permission input new_items is "
                     "usable (its length is observable under Acc(list_pred(new_items), "
                     "1/2)) and the two full-permission fields are writable, then "
                     "reaches the gold post-state and Asserts both load-bearing clauses "
                     "hold for an in-domain (F2P-shaped) input. If any Requires were "
                     "vacuous or over-strong the impl could not both read new_items and "
                     "establish the postcondition => PRECOND-TOO-STRONG. Source: the "
                     "three Requires (Acc(self.items), Acc(self.out_of_date), "
                     "Acc(list_pred(new_items),1/2)).",
    },
    {
        "id": "frame-mutation-write-new-items",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which Collection.set_paths wrote back "
                      "into the supplied paths list (e.g. paths[0] = paths[0], "
                      "paths.sort(), or any in-place rewrite) would mutate the SAME "
                      "list object the caller still holds. The F2P test "
                      "test_contour_set_paths does cs_test.set_paths(cs_ref.get_paths()) "
                      "— it installs cs_ref's OWN paths list onto cs_test by reference; "
                      "a setter that rewrote that list would corrupt cs_ref's geometry "
                      "(same object) and the @check_figures_equal render comparison "
                      "would differ, so the mutating patch would NOT resolve the F2P. "
                      "The gold setter only stores the reference and never touches the "
                      "list contents.",
        "rationale": "install_geometry holds only Acc(list_pred(new_items), 1/2). The "
                     "write new_items[0] = new_items[0] is value-neutral and guarded "
                     "in-bounds (len > 0), so the ONLY reason it fails is that writing "
                     "a list element needs FULL permission to list_pred(new_items) "
                     "while the Requires grants 1/2 => Nagini rejects for INSUFFICIENT "
                     "PERMISSION. Source: the permission system + the "
                     "Acc(list_pred(new_items),1/2) Requires. The gold store + flag are "
                     "kept verbatim so the rejection is attributable to the write.",
    },
    {
        "id": "copy-not-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_COPY),
        "refinement": "A faithful real patch self._paths = list(paths) (store a COPY) "
                      "would render IDENTICAL geometry and still set self.stale = True, "
                      "so the @check_figures_equal F2P (which observes render equality "
                      "+ redraw, NOT CPython object identity) and all P2P would PASS — "
                      "yet gold is the by-identity store self._paths = paths. The copy "
                      "is a DIFFERENT algorithm (refinement.md D.1): it breaks the "
                      "stored-reference contract (a caller that prepares a sequence and "
                      "expects that very object used, and any later in-place edit to "
                      "the supplied list, would not be reflected). It is the textbook "
                      "verify-without-faithfully-resolving rival the identity clause "
                      "exists to exclude.",
        "rationale": "self.items = list(new_items) binds a FRESH list object, so "
                     "self.items is new_items is FALSE (Nagini reference identity). The "
                     "load-bearing postcondition self.items is new_items therefore "
                     "fails. The flag is kept True so the ONLY failing clause is the "
                     "identity clause. Source: the postcondition self.items is "
                     "new_items (clause A3).",
    },
    {
        "id": "skip-out-of-date-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_NOFLAG),
        "refinement": "A faithful real patch that did self._paths = paths but OMITTED "
                      "self.stale = True (left the artist not-stale) would not mark the "
                      "collection for redraw. The F2P test_contour_set_paths is a "
                      "@check_figures_equal oracle that renders cs_test after the "
                      "setter; without stale = True the artist's cached rendering is "
                      "not invalidated, so the figure does not redraw with the newly "
                      "installed paths and the render comparison FAILS — the patch does "
                      "not resolve the F2P.",
        "rationale": "self.out_of_date = False leaves the load-bearing clause "
                     "self.out_of_date is True FALSE, so the postcondition fails. The "
                     "store is kept correct (identity holds) so the ONLY failing clause "
                     "is the flag. Source: the postcondition self.out_of_date is True "
                     "(clause A4).",
    },
    {
        "id": "install-empty-wrong-object",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_EMPTY),
        "refinement": "A faithful real patch that stored a fresh empty list "
                      "(self._paths = []) instead of the supplied paths reproduces the "
                      "pre-patch 'install nothing' failure at the value level: "
                      "get_paths() returns an empty path set, so cs_test renders no "
                      "geometry and the @check_figures_equal comparison against cs_ref "
                      "(which DOES draw its contour paths) FAILS — the patch does not "
                      "resolve the F2P. This is the partial-domain miss on the dominant "
                      "non-empty F2P input.",
        "rationale": "self.items = [] (a fresh object) makes self.items is new_items "
                     "FALSE, and for any non-empty input also makes "
                     "len(new_items) == Old(len(new_items)) hold only on new_items "
                     "(unchanged) while the stored list disagrees in length/contents "
                     "with new_items — but the load-bearing clause that fails first is "
                     "the identity self.items is new_items. Source: the postcondition "
                     "self.items is new_items (and the length/contents clauses). The "
                     "flag is set correctly so the failure is the object clauses.",
    },
]

# No Docker AXIOM_TESTS: meta.axioms == [] (no @ContractOnly axiom; the axioms
# region is empty). The only kind-A item is an A-reference — the real post-patch
# Collection.set_paths store-by-reference + stale-flag primitive — already
# validated == the real callee by axiom_check.py (G-AX, run apply_gold=True): 56
# observations over the F2P ContourSet subject + PathCollection [its identical
# override is deleted by the patch -> inherits the base] + a bare Collection incl.
# the empty-sequence boundary, asserting get_paths() is paths (identity), stale is
# True, and the supplied list left untouched; a LineCollection/PolyCollection
# negative control (their set_paths overrides rebuild self._paths and are OUTSIDE
# the modeled base-setter scope); plus 5000 cases of the environment-independent
# attribute-assignment primitive. That IS the real-callee axiom lane for this
# instance; re-encoding it as a new Docker probe would duplicate, not strengthen,
# it. See 'assessment' in the structured return.
AXIOM_TESTS = []
