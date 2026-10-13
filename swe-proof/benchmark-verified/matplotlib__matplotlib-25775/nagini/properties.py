"""PBT falsification battery for matplotlib__matplotlib-25775.

NOT a Nagini module: a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants (frozen spec, swapped impl region) checked by Nagini verify +
same_spec; this bundle ships NO @ContractOnly axiom and NO A-reference deep
model (meta.json axioms == [], deep_model_references == []), so AXIOM_TESTS is
empty (G-AX vacuous).

Defended surface (per-object boolean preference state)
------------------------------------------------------
Four modeled functions; carrier is a plain `bool` preference (`Glyph.pref`) +
a redraw flag (`Glyph.dirty`).  Repo binding: pref <-> Text._antialiased,
dirty <-> Text.stale, default <-> rcParams['text.antialiased'], supplied <->
the None-default `antialiased` kwarg.

  build_glyph(default: bool, supplied: Optional[bool]) -> Glyph
    no read-only INPUT param (both args are pass-by-value scalars).
    Load-bearing post:
      (B1) Implies(supplied is None,     Result().pref == default)
      (B2) Implies(supplied is not None, Result().pref == supplied)
    These two Implies clauses are the ENTIRE discriminator: B2 is exactly what
    model_prepatch.py violates (constructor ignores `supplied`, always takes
    the global default) and what F2P test_get_antialiased / test_annotation_
    antialiased observe (Text(..., antialiased=True)._antialiased is True).

  set_pref(g: Glyph, value: bool) -> None
    g.pref and g.dirty are FULL Acc (read-write) -- the gold patch writes both,
    so they are write-permitted by design; NOT a read-only frame target.
    Load-bearing post: (S1) g.pref == value ; (S2) g.dirty (stale set).
    S1 is what model_prepatch_2.py violates (no-op setter) and what F2P
    test_set_antialiased observes.

  get_pref(g: Glyph) -> bool
    PRECOND Requires(Acc(g.pref, 1/2)) -- READ-ONLY input. <== frame target.
    Load-bearing post: Acc(g.pref, 1/2) [returns the perm] and Result() == g.pref.
    A rival that WRITES g.pref to satisfy Result()==g.pref must be REJECTED for
    insufficient permission (only 1/2 held).  has_readonly_input == True;
    frame-mutation case is MANDATORY (g-frame-mut-getpref below).

  copy_state(dst: Glyph, src: Glyph) -> None
    dst.pref/dst.dirty FULL (write); src.pref is Acc(src.pref, 1/2) READ-ONLY.
    <== second frame target (src).  Load-bearing post: dst.pref == src.pref ;
    dst.dirty.  A rival that writes src.pref to "align" the values must be
    REJECTED for insufficient permission on src.

No ungrounded oracle
--------------------
Every postcondition is grounded DIRECTLY in the inputs, fully unfolded:
Result().pref == default / == supplied / g.pref == value / Result() == g.pref /
dst.pref == src.pref.  There is NO @Pure answer-key / opaque marker an impl
could echo without doing the work, so the UNGROUNDED-ORACLE-ECHO class does not
apply -- there is no "wrong echo that still verifies".  It is covered instead by
honest cheapest-impl POSITIVE CONTROLS (pos-* below): a structurally-different
CORRECT impl that must verify.

The free region is the per-function impl block (markers inclusive).  Each
variant below is built by _swap on _BASE editing ONLY text strictly inside a
single # impl-start / # impl-end block -- the frozen spec (pre/post-conditions)
is never touched, which mechanically GUARANTEES same_spec.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-25775"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The four gold impl blocks, VERBATIM from model.py (everything strictly between
# each function's # impl-start / # impl-end, inclusive of the bodies).  Swapping
# any one edits ONLY that function's free region.
# ---------------------------------------------------------------------------
_GOLD_BUILD = '''    g = Glyph(default)
    if supplied is not None:
        set_pref(g, supplied)
    return g'''

_GOLD_SET = '''    g.pref = value
    g.dirty = True'''

_GOLD_GET = '''    return g.pref'''

_GOLD_COPY = '''    dst.pref = src.pref
    dst.dirty = True'''


# ===========================================================================
# POSITIVE CONTROLS (soundness) -- structurally different but CORRECT; MUST verify
# ===========================================================================

# (P1) build_glyph: construct DIRECTLY with the resolved value (branch on
# `supplied`, no call to set_pref).  Glyph(v).pref == v by Glyph.__init__'s
# Ensures, so B1 holds in the None branch (Glyph(default)) and B2 holds in the
# else branch (Glyph(supplied)).  Structurally different (no set_pref roundtrip,
# different control shape) yet correct.  Must verify; else SPEC-TOO-STRONG.
_POS_BUILD_DIRECT = '''    if supplied is None:
        g = Glyph(default)
    else:
        g = Glyph(supplied)
    return g'''

# (P2) set_pref: write dirty FIRST, then pref (field-write order reshape).  Both
# stores still land; S1/S2 are order-independent.  Must verify; else SPEC-TOO-STRONG.
_POS_SET_REORDER = '''    g.dirty = True
    g.pref = value'''

# (P3) copy_state: set dirty FIRST, then copy pref.  Order-independent; both
# writes land.  src is read once via the held 1/2 permission.  Must verify.
_POS_COPY_REORDER = '''    dst.dirty = True
    dst.pref = src.pref'''


# ===========================================================================
# ADMISSIBILITY -- precondition admits a normal F2P-shaped input; MUST verify
# ===========================================================================

# (A1) get_pref: keep the gold body but first ASSERT we can READ g.pref under the
# 1/2 permission (proves Requires(Acc(g.pref,1/2)) is non-vacuous for a normal
# input).  A pure read assertion needs no write permission, so it must verify;
# else PRECOND-TOO-STRONG (the read-only precondition would not even grant a read).
_ADMISS_GET = '''    Assert(g.pref == g.pref)
    return g.pref'''

# (A2) build_glyph: keep gold body but assert the constructed object is readable
# (non-vacuous post).  Must verify; else PRECOND/POST mismatch on a normal input.
_ADMISS_BUILD = '''    g = Glyph(default)
    if supplied is not None:
        set_pref(g, supplied)
    Assert(g.pref == g.pref)
    return g'''


# ===========================================================================
# FRAME-MUTATION (MANDATORY: get_pref + copy_state both take a 1/2 read-only
# input).  Each must be REJECTED for INSUFFICIENT PERMISSION -- not for a wrong
# value.  The postcondition is kept verbatim (frozen spec) so the rejection is
# attributable to the illegal WRITE through a 1/2 permission.
# ===========================================================================

# (F1) get_pref: try to satisfy Result()==g.pref by FORCING g.pref to a constant
# and echoing it.  Holds only 1/2 of g.pref => the write `g.pref = True` is
# illegal (needs full permission).  REJECT for insufficient permission.
_FRAME_GET = '''    g.pref = True
    return True'''

# (F2) copy_state: instead of copying src->dst, mutate the READ-ONLY src to match
# dst, then claim dst.pref == src.pref.  src is held at 1/2 => the write
# `src.pref = dst.pref` is illegal.  REJECT for insufficient permission on src.
# dst writes are legal (full perm) and kept so the only failure is the src write.
_FRAME_COPY = '''    dst.dirty = True
    src.pref = dst.pref
    dst.pref = src.pref'''


# ===========================================================================
# UNIQUENESS / PARTIAL-DOMAIN rivals -- each MUST be REJECTED by a postcondition.
# ===========================================================================

# (W1) build_glyph: IGNORE `supplied`, always take the global default.  This is
# the PRE-PATCH bug verbatim (model_prepatch.py): the constructor reads
# rcParams['text.antialiased'] and never honours the per-object kwarg.  Fails B2.
_W_BUILD_IGNORE_SUPPLIED = '''    g = Glyph(default)
    return g'''

# (W2) build_glyph: invert -- honour `supplied` but when ABSENT return a constant
# True instead of the default (partial-domain: wrong on supplied is None when
# default is False).  Fails B1.
_W_BUILD_DEFAULT_TRUE = '''    g = Glyph(True)
    if supplied is not None:
        set_pref(g, supplied)
    return g'''

# (W3) set_pref: no-op store -- only set the redraw flag, leave pref unchanged.
# This is the PRE-PATCH-2 bug verbatim (model_prepatch_2.py).  Fails S1.
_W_SET_NOOP = '''    g.dirty = True'''

# (W4) set_pref: store the NEGATION of value (partial-domain: correct for neither
# True nor False).  Fails S1.  (Modeled "wrong setter" -- a faithful `not value`
# patch makes test_set_antialiased(True) assert _antialiased is True FAIL.)
_W_SET_NEGATE = '''    g.pref = not value
    g.dirty = True'''

# (W5) set_pref: store the value but FORGET the redraw flag (only stale-flag
# difference).  Fails S2 (g.dirty).  Faithful patch drops `self.stale = True`,
# so a set_antialiased that should mark the artist stale leaves it clean -- the
# redraw never triggers and the per-object change is not reflected on draw.
_W_SET_NO_DIRTY = '''    g.pref = value'''

# (W6) get_pref: return a CONSTANT True regardless of stored value (partial-
# domain: correct only when g.pref happens to be True).  Fails Result()==g.pref.
# Faithful patch `return True` makes get_antialiased() echo True for a glyph
# built antialiased=False -> test_get_antialiased's `get_antialiased()==
# _antialiased` FAILS.  Read-only body (no write), so the ONLY failure is the
# value postcondition, isolating it from the frame case.
_W_GET_CONST_TRUE = '''    return True'''

# (W7) copy_state: copy pref correctly but FORGET the redraw flag.  Fails dst.dirty.
# Faithful update_from that drops `self.stale = True` leaves the destination
# artist clean after adopting the source's antialiasing -> no redraw.
_W_COPY_NO_DIRTY = '''    dst.pref = src.pref'''

# (W8) copy_state: set dirty but DON'T copy pref (dst keeps its own value).
# Fails dst.pref == src.pref.  Faithful update_from that omits the new
# `self._antialiased = other._antialiased` line -> the copy does not adopt the
# source preference (the gold patch's actual added line).
_W_COPY_NO_PREF = '''    dst.dirty = True'''


SPEC_TESTS = [
    # ---- positive controls (soundness) ----
    {
        "id": "pos-build-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_BUILD, _POS_BUILD_DIRECT),
        "rationale": "structurally-different CORRECT build_glyph: branch on "
        "`supplied` and construct Glyph DIRECTLY with the resolved value (no "
        "set_pref roundtrip). Glyph(v).pref==v by Glyph.__init__ Ensures, so B1 "
        "(None->default) and B2 (supplied->supplied) both hold. Must verify; else "
        "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-set-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_SET, _POS_SET_REORDER),
        "rationale": "correct set_pref reshape: write dirty before pref. Both "
        "stores land; S1 (pref==value) and S2 (dirty) are order-independent. Must "
        "verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-copy-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_COPY, _POS_COPY_REORDER),
        "rationale": "correct copy_state reshape: set dirty before copying pref. "
        "Order-independent; src is read once via its 1/2 permission. Must verify; "
        "else SPEC-TOO-STRONG.",
    },
    # ---- admissibility ----
    {
        "id": "admiss-get-readable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_GET, _ADMISS_GET),
        "rationale": "get_pref's READ-ONLY precondition Requires(Acc(g.pref,1/2)) "
        "is non-vacuous: a pure read assertion (Assert(g.pref==g.pref)) succeeds "
        "under the half permission for a normal F2P input. Must verify; else "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "admiss-build-readable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_BUILD, _ADMISS_BUILD),
        "rationale": "build_glyph admits a normal input: after construction the "
        "result's pref is readable (Assert(g.pref==g.pref)) before return. Must "
        "verify; else PRECOND-TOO-STRONG.",
    },
    # ---- frame-mutation (MANDATORY) ----
    {
        "id": "frame-mut-getpref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_GET, _FRAME_GET),
        "refinement": "get_pref <-> Text.get_antialiased, a pure getter `return "
        "self._antialiased`. A faithful real patch CANNOT overwrite the artist's "
        "stored preference inside the getter (that would corrupt the very state "
        "test_get_antialiased reads: after Text(...,antialiased=False), "
        "get_antialiased() must still return False, not a forced True). Such a "
        "getter would FAIL the F2P. So a verifying mutate-and-echo rival here is a "
        "true verify-not-resolve break.",
        "rationale": "rejected by the PERMISSION SYSTEM: get_pref holds only "
        "Acc(g.pref,1/2); the write `g.pref = True` requires full permission and "
        "is illegal => insufficient-permission rejection. The postcondition is "
        "kept verbatim so the failure is attributable to the write, not a value "
        "mismatch.",
    },
    {
        "id": "frame-mut-copysrc",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_COPY, _FRAME_COPY),
        "refinement": "copy_state <-> Text.update_from. A faithful real patch "
        "copies other._antialiased INTO self; it must NOT write back into `other` "
        "(the source artist is not owned/modified by update_from -- mutating it "
        "would corrupt an unrelated artist and is not what the gold line "
        "`self._antialiased = other._antialiased` does). A rival that 'aligns' the "
        "values by writing src would not be a faithful update_from and would not "
        "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: copy_state holds only "
        "Acc(src.pref,1/2); the write `src.pref = dst.pref` requires full "
        "permission on src and is illegal => insufficient-permission rejection. "
        "dst writes are legal (full perm) so the sole failure is the src write.",
    },
    # ---- uniqueness / partial-domain ----
    {
        "id": "weak-build-ignore-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BUILD, _W_BUILD_IGNORE_SUPPLIED),
        "refinement": "PRE-PATCH bug verbatim (model_prepatch.py): the constructor "
        "always takes the global default and ignores the per-object `antialiased` "
        "kwarg. F2P test_get_antialiased asserts Text(...,antialiased=True)."
        "_antialiased is True, which FAILS when the kwarg is ignored. A "
        "verify-not-resolve break.",
        "rationale": "rejected by postcondition B2: Implies(supplied is not None, "
        "Result().pref == supplied) is violated (Result().pref == default "
        "regardless of supplied).",
    },
    {
        "id": "weak-build-default-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_BUILD, _W_BUILD_DEFAULT_TRUE),
        "refinement": "partial-domain: honours `supplied` but on the ABSENT branch "
        "hard-codes True instead of the global default. A faithful patch that "
        "seeds `self._antialiased = True` (rather than rcParams) makes "
        "test_get_antialiased's txt4 (no kwarg) assert get_antialiased()=="
        "rcParams['text.antialiased'] FAIL whenever the rcParam default is False. "
        "Verify-not-resolve break on the default sub-domain.",
        "rationale": "rejected by postcondition B1: Implies(supplied is None, "
        "Result().pref == default) is violated when default is False (Result().pref "
        "is True).",
    },
    {
        "id": "weak-set-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_SET, _W_SET_NOOP),
        "refinement": "PRE-PATCH-2 bug verbatim (model_prepatch_2.py): the setter "
        "only marks stale and never stores the value. F2P test_set_antialiased "
        "does txt.set_antialiased(True); assert txt._antialiased is True, which "
        "FAILS for a no-op setter. A verify-not-resolve break.",
        "rationale": "rejected by postcondition S1: g.pref == value is violated "
        "(pref is never written).",
    },
    {
        "id": "weak-set-negate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_SET, _W_SET_NEGATE),
        "refinement": "partial-domain: stores `not value`. A faithful "
        "set_antialiased that inverts its argument makes test_set_antialiased's "
        "set_antialiased(True); assert _antialiased is True FAIL (stores False). "
        "Wrong for both True and False inputs. Verify-not-resolve break.",
        "rationale": "rejected by postcondition S1: g.pref == value is violated "
        "(g.pref == not value).",
    },
    {
        "id": "weak-set-no-dirty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_SET, _W_SET_NO_DIRTY),
        "refinement": "control-flow/side-effect: stores the value correctly but "
        "DROPS `self.stale = True`. A faithful set_antialiased missing the stale "
        "flag leaves the artist not marked for redraw, so the per-object "
        "antialiasing change is not re-rendered -- the image-comparison F2P "
        "(test_text_antialiased_*_default_vs_manual) would not reflect the change. "
        "Verify-not-resolve break on the redraw effect.",
        "rationale": "rejected by postcondition S2: Acc(g.dirty) and g.dirty is "
        "violated (dirty is never set True).",
    },
    {
        "id": "weak-get-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_GET, _W_GET_CONST_TRUE),
        "refinement": "partial-domain: getter returns a constant True regardless "
        "of stored value. A faithful get_antialiased that `return True` makes "
        "test_get_antialiased's txt3 (antialiased=False) assert get_antialiased()"
        "==_antialiased (==False) FAIL. Read-only body (no write) so this is a "
        "PURE value defect, distinct from the frame case. Verify-not-resolve break.",
        "rationale": "rejected by postcondition Result() == g.pref (violated when "
        "g.pref is False; the getter returns True).",
    },
    {
        "id": "weak-copy-no-dirty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_COPY, _W_COPY_NO_DIRTY),
        "refinement": "side-effect: copies pref correctly but DROPS the redraw "
        "flag. A faithful update_from that adopts other._antialiased without "
        "setting self.stale leaves the destination artist unflagged, so the "
        "adopted preference is not re-rendered. Verify-not-resolve break on the "
        "redraw effect.",
        "rationale": "rejected by postcondition dst.dirty (violated; dirty never "
        "set True).",
    },
    {
        "id": "weak-copy-no-pref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_COPY, _W_COPY_NO_PREF),
        "refinement": "this OMITS the gold patch's actual added line "
        "`self._antialiased = other._antialiased` in update_from: dst keeps its "
        "own preference instead of adopting src's. Any path relying on update_from "
        "to propagate the per-object antialiasing (the visual-state copy) FAILS to "
        "carry it. Verify-not-resolve break on the copy clause.",
        "rationale": "rejected by postcondition dst.pref == src.pref (violated; "
        "dst.pref is never assigned from src).",
    },
]

# No @ContractOnly axiom and no A-reference deep model in this bundle
# (meta.json axioms == [], deep_model_references == []).  The changed behaviour
# is per-object boolean state modelled directly; there is no callee oracle to
# fuzz for soundness or to check for caller-domain containment.  G-AX vacuous.
AXIOM_TESTS = []
