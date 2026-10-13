"""properties.py — PBT falsification battery for matplotlib__matplotlib-20859.

NOT a Nagini module: a record of adversarially-reasoned cases the runner
(swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
model.py variants that share the FROZEN spec byte-for-byte (only the
# impl-start .. # impl-end region is edited via _swap) and are checked by Nagini
verify + markers.same_spec. The one axiom case is an A-reference deep-model
soundness+containment probe run in Docker against the real matplotlib hierarchy.

DEFENDED SURFACE (why these cases and not byte-fuzz):
  attach(parent: Parent) -> Attached  classifies a legend's parent and either
  returns the attachment outcome or raises ParentRejected. The gold dispatch is
      if is_coords_artist(parent.tag):     return Attached(True,  parent.host_canvas)
      elif in_canvas_family(parent.tag):   return Attached(False, parent.tag)
      else:                                raise ParentRejected()
  modelling the gold patch's widening of the second branch from
  isinstance(parent, Figure) to isinstance(parent, FigureBase) so a nested
  canvas region (SubFigure, TAG_NESTED) is ACCEPTED rather than rejected.

  READ-ONLY input (directive 5 / project #1 weakness): parent is passed with
  Acc(parent.tag, 1/2) and Acc(parent.host_canvas, 1/2) -- both Required AND
  Ensured. There IS a heap cell (parent.tag / parent.host_canvas) that a rival
  could try to overwrite to satisfy a postcondition vacuously, so the
  FRAME-MUTATION probe is MANDATORY and present (rival-frame-mutate): it writes
  parent.tag inside the impl and MUST be rejected for INSUFFICIENT PERMISSION.

  GROUNDED oracle (directive 2): the two helpers in the postcondition,
  is_coords_artist(tag) and in_canvas_family(tag), are @Pure functions FULLY
  GROUNDED in parent.tag -- they unfold to (tag == 0) and (tag in {1,2})
  respectively. There is NO opaque @ContractOnly answer-key to echo: the only
  way to "satisfy" the postcondition is to actually classify on the tag and
  return the matching outcome. So there is no wrong-echo attack; instead we
  carry honest positive controls (a branch-reorder and a local-variable reshape)
  plus the genuine partial-domain / control-flow / value rivals below.

  LOAD-BEARING postcondition clauses attacked:
    (P-norm)  Ensures(is_coords_artist(parent.tag) or in_canvas_family(parent.tag))
              -- normal return is permitted ONLY for a coords-or-family parent
              (attacked by rival-over-accept-foreign).
    (P-coord) Implies(is_coords_artist(parent.tag),
                      Result().is_coords and Result().canvas == parent.host_canvas)
              -- coords branch flag+canvas (attacked by rival-coord-flag-flip).
    (P-fam)   Implies(in_canvas_family(parent.tag),
                      (not Result().is_coords) and Result().canvas == parent.tag)
              -- the DISCRIMINATING clause: pinned for EVERY family member, so a
              narrow test that rejects TAG_NESTED violates it (rival-prepatch-
              narrow) and a family branch that returns the wrong canvas violates
              the canvas pin (rival-fam-wrong-canvas).
    (P-exs)   Exsures(ParentRejected, ... not is_coords_artist and not
              in_canvas_family) -- raises ONLY for a foreign parent (a narrow
              test that raises for TAG_NESTED also violates this).

AXIOM lane: axioms[] is empty (NO @ContractOnly axiom). The single non-trivial
  semantic fact is the SUBTYPE RELATION, modelled deeply by is_coords_artist /
  in_canvas_family and validated as an A-reference by G-AX (axiom_check.py). We
  carry ONE axiom-lane case (kind axiom-containment) that runs the real
  matplotlib issubclass relation in Docker and asserts the deep model agrees on
  every caller-reachable tag AND that the discriminating SubFigure-is-a-
  FigureBase-but-not-a-Figure fact holds -- i.e. the deep model is sound and the
  caller never reaches a class outside the modelled set. flag_dependency: none
  (issubclass takes no behaviour-altering flag; mapping.md S3).
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-20859"
FLOAT_ENCODING = None  # meta.float_encoding is null; integer class-family tags, no --float-encoding

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl region, anchored on its exact (unique) text so every variant
# edits ONLY inside # impl-start .. # impl-end (guarantees same_spec).
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()"""


def _variant(new_impl):
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# === POSITIVE CONTROL 1 (soundness) ========================================
# Branch-REORDER: classify family membership FIRST, then the coords case in the
# else-if. The two families are mutually exclusive over the tags (is_coords =
# tag==0, family = tag in {1,2}), so reordering yields identical behaviour. No
# loop / fold is involved, so no induction lemma is needed (directive 3). Must
# verify; else SPEC-TOO-STRONG.
_POS1_IMPL = """    if in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    elif is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    else:
        raise ParentRejected()"""


# === POSITIVE CONTROL 2 (soundness) ========================================
# Local-variable reshape: build the outcome into a typed local and return it at
# the branch end, rather than returning the constructor expression inline. Same
# values, different executable shape; keeps every postcondition obligation
# discharged (the constructor's Ensures pins is_coords/canvas just as before).
# Must verify; else SPEC-TOO-STRONG.
_POS2_IMPL = """    if is_coords_artist(parent.tag):
        out = Attached(True, parent.host_canvas)  # type: Attached
        return out
    elif in_canvas_family(parent.tag):
        out2 = Attached(False, parent.tag)  # type: Attached
        return out2
    else:
        raise ParentRejected()"""


# === ADMISSIBILITY (precondition not too strong) ===========================
# Construct a concrete F2P-shaped parent (a nested canvas region, TAG_NESTED --
# exactly the SubFigure the F2P test attaches a legend to) at the top of the
# impl and assert the precondition-relevant facts: it carries the family base
# type (in_canvas_family holds) and is NOT foreign, so the family branch admits
# it. This witnesses that the Requires/dispatch accept a normal F2P input (else
# PRECOND-TOO-STRONG). The gold dispatch is kept intact after the witness.
_ADMISS_IMPL = """    # admissibility witness: a nested canvas region (the F2P SubFigure parent)
    # is a genuine canvas-surface family member and is not foreign, so the
    # family branch accepts it -- the precondition admits a normal input.
    witness = Parent(TAG_NESTED, parent.host_canvas)  # type: Parent
    Assert(in_canvas_family(witness.tag))
    Assert(not is_coords_artist(witness.tag))
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()"""


# === FRAME-MUTATION rival (uniqueness, MANDATORY) ==========================
# parent is read-only: Acc(parent.tag, 1/2). This rival WRITES parent.tag to
# TAG_TOPLEVEL before classifying -- a mutation a value abstraction can't see,
# attempting to coerce a foreign parent into the family branch and satisfy
# (P-norm)/(P-fam) vacuously. It MUST be rejected for INSUFFICIENT PERMISSION
# (only 1/2 permission is held; a write needs full permission). The rejection is
# attributable to the write because every gold dispatch line below is verbatim.
# REFINEMENT: a real patch that REASSIGNS parent (parent = Figure()) to dodge the
# type-check would attach the legend to a fabricated figure, not the actual
# SubFigure -- leg.figure would NOT be `subfig`, so the F2P test_subfigure_legend
# (asserts `leg.figure is subfig`) would FAIL. A verifying mutate => SPEC-TOO-WEAK.
_FRAME_MUTATE_IMPL = """    parent.tag = TAG_TOPLEVEL
    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()"""


# === PARTIAL-DOMAIN rival: the prepatch narrow test (uniqueness) ===========
# The actual bug. The second branch tests the NARROW top-level-canvas tag
# (parent.tag == TAG_TOPLEVEL) instead of family membership, so a nested region
# (TAG_NESTED) falls through to the raise. Correct on TAG_COORDS / TAG_TOPLEVEL /
# TAG_FOREIGN; diverges ONLY on TAG_NESTED. MUST be rejected: for TAG_NESTED,
# in_canvas_family holds so (P-fam) requires a normal return with
# canvas == parent.tag, AND (P-exs) requires `not in_canvas_family` on the raise
# path -- both violated (verifier: "Assertion (not in_canvas_family(parent.tag))
# might not hold"). REFINEMENT: this is exactly the pre-patch
# `isinstance(parent, Figure)`, which rejects a SubFigure -> the F2P
# test_subfigure_legend raises TypeError and FAILS. A verifying narrow rival =>
# SPEC-TOO-WEAK (the discriminating fix not enforced).
_PREPATCH_NARROW_IMPL = """    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif parent.tag == TAG_TOPLEVEL:
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()"""


# === CONTROL-FLOW / VALUE rival: family branch returns the WRONG canvas ====
# In the family branch return the parent's host_canvas instead of the parent
# itself. (not is_coords) still holds, shape ok, but (P-fam) pins
# canvas == parent.tag, which is violated for a family parent (host_canvas is an
# unrelated identity). MUST be rejected. REFINEMENT: this models
# `self.set_figure(parent.figure)` in the FigureBase branch instead of
# `self.set_figure(parent)`; for a SubFigure parent leg.figure would be the
# parent's owning canvas, NOT the SubFigure itself -> the F2P assertion
# `leg.figure is subfig` FAILS. A verifying rival => SPEC-TOO-WEAK on the canvas
# pin.
_FAM_WRONG_CANVAS_IMPL = """    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.host_canvas)
    else:
        raise ParentRejected()"""


# === VALUE rival: coords branch flips the coordinates flag (uniqueness) =====
# In the coords branch return is_coords=False (and the wrong canvas to match the
# not-coords convention). (P-coord) pins Result().is_coords True for a coords
# parent, so this MUST be rejected. REFINEMENT: a real patch that set
# self.isaxes=False for an Axes parent would mis-classify every axes legend (the
# legend would not know its axes), breaking the P2P axes-parent tests
# (test_legend_remove, test_legend_text_axes, ... pass an Axes parent through
# the first branch). A verifying flag-flip => SPEC-TOO-WEAK on the coords flag.
_COORD_FLAG_FLIP_IMPL = """    if is_coords_artist(parent.tag):
        return Attached(False, parent.host_canvas)
    elif in_canvas_family(parent.tag):
        return Attached(False, parent.tag)
    else:
        raise ParentRejected()"""


# === OVER-ACCEPT rival: never reject a foreign parent (uniqueness) =========
# Drop the raise: classify family vs coords, and for anything else still return
# a not-coords attachment (treat a FOREIGN parent as a canvas-family member).
# For TAG_FOREIGN neither is_coords_artist nor in_canvas_family holds, so the
# normal-return guard (P-norm) `is_coords_artist or in_canvas_family` is FALSE
# on the returned path -> MUST be rejected. REFINEMENT: a real patch that
# accepted ANY object as parent (dropping the `else: raise TypeError`) would let
# `Legend(Line2D(...))` silently build a broken legend instead of raising the
# documented TypeError -- the rejection-of-foreign behaviour the dispatch must
# keep. A verifying over-accept => SPEC-TOO-WEAK on the foreign-reject guard.
_OVER_ACCEPT_IMPL = """    if is_coords_artist(parent.tag):
        return Attached(True, parent.host_canvas)
    else:
        return Attached(False, parent.tag)"""


SPEC_TESTS = [
    # ----- soundness / positive controls (must verify) --------------------
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS1_IMPL),
        "rationale": (
            "branch-REORDER positive control: family membership classified "
            "first, coords in the else-if. The families are mutually exclusive "
            "over the tags, so behaviour is identical. No loop/fold => no "
            "induction lemma needed (directive 3). Must verify; else "
            "SPEC-TOO-STRONG (a correct restructured dispatch would be rejected)."
        ),
    },
    {
        "id": "pos-local-var-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _variant(_POS2_IMPL),
        "rationale": (
            "local-variable reshape positive control: build the Attached outcome "
            "into a typed local then return it, instead of returning the "
            "constructor inline. Same values, different executable shape; the "
            "constructor Ensures still pins is_coords/canvas so every "
            "postcondition obligation is discharged. Must verify; else "
            "SPEC-TOO-STRONG."
        ),
    },
    # ----- admissibility (precondition not too strong) --------------------
    {
        "id": "admiss-nested-parent",
        "kind": "admissibility",
        "expect": "verify",
        "module": _variant(_ADMISS_IMPL),
        "rationale": (
            "constructs a concrete F2P-shaped nested-region parent (TAG_NESTED, "
            "the SubFigure the F2P attaches a legend to) and asserts it is a "
            "family member and not foreign, so the family branch admits it. "
            "Witnesses that the precondition/dispatch accept a normal input; if "
            "it fails to verify, PRECOND-TOO-STRONG."
        ),
    },
    # ----- uniqueness / frame-mutation / partial-domain (must be rejected) -
    {
        "id": "rival-frame-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FRAME_MUTATE_IMPL),
        "refinement": (
            "a faithful real patch that REASSIGNED the parent (parent = Figure()) "
            "to coerce the type-check would attach the legend to a fabricated "
            "figure, so `leg.figure is subfig` would be False and the F2P "
            "test_subfigure_legend would FAIL -- the rival does not resolve."
        ),
        "rationale": (
            "FRAME-MUTATION (mandatory; parent is read-only, Acc(parent.tag,1/2)). "
            "Writes parent.tag inside the impl; must be rejected for INSUFFICIENT "
            "PERMISSION (only 1/2 held). The rejection is attributable to the "
            "write because the gold dispatch lines below are verbatim. A "
            "verifying mutate => SPEC-TOO-WEAK (the permission system failed to "
            "protect the read-only input)."
        ),
    },
    {
        "id": "rival-prepatch-narrow",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_PREPATCH_NARROW_IMPL),
        "refinement": (
            "this is the pre-patch `isinstance(parent, Figure)` test (narrow "
            "top-level-canvas only). It rejects a SubFigure (TAG_NESTED), so the "
            "F2P test_subfigure_legend raises TypeError and FAILS -- the exact "
            "bug the gold patch fixes. The rival does not resolve."
        ),
        "rationale": (
            "PARTIAL-DOMAIN: correct on TAG_COORDS/TAG_TOPLEVEL/TAG_FOREIGN, "
            "diverges ONLY on TAG_NESTED. For TAG_NESTED in_canvas_family holds, "
            "so (P-fam) requires a normal return with canvas==parent.tag and "
            "(P-exs) requires `not in_canvas_family` on the raise path -- both "
            "violated (verifier: 'Assertion (not in_canvas_family(parent.tag)) "
            "might not hold'). A verifying narrow rival => SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "rival-fam-wrong-canvas",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_FAM_WRONG_CANVAS_IMPL),
        "refinement": (
            "models `set_figure(parent.figure)` in the FigureBase branch instead "
            "of `set_figure(parent)`; for a SubFigure parent leg.figure would be "
            "the parent's owning canvas, NOT the SubFigure -> the F2P assertion "
            "`leg.figure is subfig` FAILS. The rival does not resolve."
        ),
        "rationale": (
            "CONTROL-FLOW/VALUE: family branch returns host_canvas instead of the "
            "parent itself. (P-fam) pins canvas==parent.tag for a family parent, "
            "violated here. A verifying rival => SPEC-TOO-WEAK on the canvas pin."
        ),
    },
    {
        "id": "rival-coord-flag-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_COORD_FLAG_FLIP_IMPL),
        "refinement": (
            "a real patch setting self.isaxes=False for an Axes parent would "
            "mis-classify every axes legend (it would not know its owning axes), "
            "breaking the P2P axes-parent tests (test_legend_remove, "
            "test_legend_text_axes, ...). The rival does not resolve."
        ),
        "rationale": (
            "VALUE: coords branch flips is_coords to False. (P-coord) pins "
            "Result().is_coords True for a coords parent, violated here. A "
            "verifying flag-flip => SPEC-TOO-WEAK on the coords flag."
        ),
    },
    {
        "id": "rival-over-accept-foreign",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _variant(_OVER_ACCEPT_IMPL),
        "refinement": (
            "a real patch dropping the `else: raise TypeError` would let "
            "`Legend(Line2D(...))` silently build a broken legend instead of "
            "raising the documented TypeError; the dispatch must REJECT a foreign "
            "parent. The rival does not resolve (wrong behaviour on a foreign "
            "parent)."
        ),
        "rationale": (
            "OVER-ACCEPT: never raises -- treats a FOREIGN parent (TAG_FOREIGN) "
            "as a family member. (P-norm) `is_coords_artist or in_canvas_family` "
            "is FALSE on the returned path for TAG_FOREIGN, so the normal-return "
            "guard rejects it. A verifying over-accept => SPEC-TOO-WEAK on the "
            "foreign-reject guard."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane: NO @ContractOnly axiom (axioms[] empty). The single semantic fact
# is the A-reference subtype relation modelled by is_coords_artist /
# in_canvas_family. We carry ONE axiom-containment probe that EXECUTES the real
# matplotlib issubclass relation in Docker (NOT regex over source; directive 4)
# and asserts: (a) the deep model agrees with the real relation on every
# caller-reachable tag [soundness], (b) every modelled tag maps to a real class
# the caller can actually reach and no reachable class falls outside the modelled
# set [containment], and (c) the discriminating SubFigure-is-a-FigureBase-but-
# not-a-Figure facts hold. The probe embeds axiom_check.py's logic (read on the
# HOST at load time so it is self-contained in-container; directive 6) and opens
# nothing on disk, so directive 5 (utf-8) is moot.
# ---------------------------------------------------------------------------

_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

_CONTAINMENT_PROBE = r'''
import sys

import matplotlib
matplotlib.use("Agg")  # headless

from matplotlib.axes import Axes
from matplotlib.figure import Figure, FigureBase, SubFigure
from matplotlib.lines import Line2D

# --- model.py reference encodings (kept in lock-step with model.py) ----------
TAG_COORDS = 0
TAG_TOPLEVEL = 1
TAG_NESTED = 2
TAG_FOREIGN = 3

# Exactly the tags the modeled function can reach (its Parent.tag domain) ->
# the representative real class each stands for (mapping.md S3). Containment:
# the caller never produces a tag outside this set, and each maps to a real
# class whose membership the deep model must reproduce.
REACHABLE = {
    TAG_COORDS: Axes,
    TAG_TOPLEVEL: Figure,
    TAG_NESTED: SubFigure,
    TAG_FOREIGN: Line2D,
}

def model_is_coords_artist(tag):
    return tag == TAG_COORDS

def model_in_canvas_family(tag):
    return tag == TAG_TOPLEVEL or tag == TAG_NESTED

def real_is_coords_artist(cls):
    return issubclass(cls, Axes)

def real_in_canvas_family(cls):
    # the gold second branch, reached only after the Axes branch did not fire
    return issubclass(cls, FigureBase) and not issubclass(cls, Axes)

# (a)+(b): SOUNDNESS over the caller-reachable domain (containment-by-construction:
# we enumerate EXACTLY the tags the model can pass; each is a real class).
for tag, cls in REACHABLE.items():
    m_c = model_is_coords_artist(tag)
    r_c = real_is_coords_artist(cls)
    m_f = model_in_canvas_family(tag)
    r_f = real_in_canvas_family(cls)
    print("tag=%d (%s): coords model=%r real=%r ; family model=%r real=%r"
          % (tag, cls.__name__, m_c, r_c, m_f, r_f))
    if m_c != r_c:
        print("UNSOUND is_coords_artist for %s" % cls.__name__); sys.exit(1)
    if m_f != r_f:
        print("UNSOUND in_canvas_family for %s" % cls.__name__); sys.exit(1)
    # mutual exclusion: no class is both coords and family
    if r_c and r_f:
        print("%s is BOTH coords and family" % cls.__name__); sys.exit(1)

# (c): the discriminating facts the whole fix turns on.
if not issubclass(SubFigure, FigureBase):
    print("SubFigure must be a FigureBase (nested region accepted)"); sys.exit(1)
if issubclass(SubFigure, Figure):
    print("SubFigure must NOT be a Figure (pre-patch narrow check rejected it)"); sys.exit(1)
if not issubclass(Figure, FigureBase):
    print("Figure must be a FigureBase"); sys.exit(1)
if issubclass(Axes, FigureBase):
    print("Axes must not be in the canvas-surface family"); sys.exit(1)
if issubclass(Line2D, FigureBase) or issubclass(Line2D, Axes):
    print("a foreign artist must be in neither family"); sys.exit(1)

print("CONTAINMENT+SOUNDNESS OK: deep model == real matplotlib subtype relation "
      "over %d caller-reachable classes; SubFigure is a FigureBase but not a "
      "Figure (the discriminating fact)." % len(REACHABLE))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-subtype-containment",
        "axiom": "in_canvas_family / is_coords_artist (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _CONTAINMENT_PROBE,
        "rationale": (
            "No @ContractOnly axiom exists; the subtype relation is the only "
            "opaque semantic fact and is modelled deeply (A-reference). This "
            "probe EXECUTES the real matplotlib issubclass relation in Docker "
            "(directive 4: run the callee, never regex source) and asserts the "
            "deep model agrees on EXACTLY the caller-reachable tags "
            "{Axes, Figure, SubFigure, Line2D} (containment: the model never "
            "reaches a class outside this set), the two families are mutually "
            "exclusive, and the discriminating SubFigure-is-a-FigureBase-not-a-"
            "Figure fact holds. A real class outside the modelled set or a "
            "disagreement => AXIOM-TOO-WEAK-FOR-CALLER / unsound deep model. "
            "Mirrors axiom_check.py / G-AX, embedded self-contained (directive 6)."
        ),
    },
]
