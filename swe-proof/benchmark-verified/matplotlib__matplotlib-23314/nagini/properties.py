# properties.py — PBT falsification battery for matplotlib__matplotlib-23314.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps RESULT on. Spec cases are full
# model.py variants that share the FROZEN spec (region-surgery: every edit lives
# ONLY inside the # impl-start / # impl-end region, which spec_view elides — so
# same_spec holds by construction) and are checked by Nagini verify; axiom cases
# are real-callee probes checked in Docker.
#
# DEFENDED SURFACE (what this spec protects — see model.py / refinement.md):
#
#   render(self: Container, sink: Sink) -> None       [the single modeled site]
#     Requires Acc(self.visible, 1/2)                 <-- READ-ONLY input (half perm)
#     Requires Acc(self.content, 1/2)                 <-- READ-ONLY input (half perm)
#     Requires self.content >= 0
#     Requires Acc(sink.work)                          <-- the ONLY writable field
#     Ensures  Acc(self.visible, 1/2) and self.visible  == Old(self.visible)    [frame]
#     Ensures  Acc(self.content, 1/2) and self.content  == Old(self.content)    [frame]
#     Ensures  Acc(sink.work)
#     Ensures  Implies(not self.visible, sink.work == Old(sink.work))           [clause 1]
#     Ensures  Implies(self.visible,     sink.work == Old(sink.work) + content) [clause 2]
#
#   The two LOAD-BEARING clauses are GROUNDED ENTIRELY in the inputs: clause 1
#   pins sink.work to Old(sink.work) when invisible; clause 2 pins it to
#   Old(sink.work) + self.content (the body's full work) when visible. There is
#   NO @Pure answer-key / opaque marker an impl could echo without doing the work
#   — the postcondition is an arithmetic identity in (visible, content,
#   Old(sink.work)). The ungrounded-oracle-echo class is therefore N/A
#   (see 'assessment'); the cheapest honest impl IS essentially the gold guard +
#   add, so its positive control is a branch-reorder, not an echo.
#
#   The BEHAVIOURAL DISCRIMINATOR (the bug fix, matplotlib #23306): an Axes3D
#   flagged not-visible must draw NOTHING. The pre-patch Axes3D.draw had no
#   `if not self.get_visible(): return` guard and ran the whole body
#   unconditionally — so an invisible 3D axes still drew (the F2P bug). Clause 1
#   senses exactly that: when invisible the sink must be unchanged. The
#   partial-domain / overshoot rivals below ARE that pre-patch behaviour
#   (model_prepatch.py).
#
#   READ-ONLY inputs present (self.visible, self.content at Acc(...,1/2)) => the
#   FRAME-MUTATION probe is MANDATORY and is included below (case "frame-...").
#
#   No @ContractOnly axioms (meta.axioms == []). The deep model — that the real
#   Axes3D.draw honours get_visible() (invisible emits 0 draw primitives, visible
#   emits > 0) and that get_visible() returns exactly the stored flag — is an
#   A-reference, validated against the REAL matplotlib code in-container by
#   axiom_check.py (G-AX). Because that A-reference is the entire grounding of
#   clauses (1)/(2), we DO re-run it as a Docker axiom-soundness probe under the
#   gold patch (apply_gold=True) so the PBT battery itself re-confirms the
#   real-callee behaviour the refinement leans on. See AXIOM_TESTS.
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23314"
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
# Editing only this keeps spec_view (hence same_spec) byte-identical.
# ===========================================================================
_IMPL_GOLD = """    if not self.visible:
        return
    sink.work = sink.work + self.content
    return"""

assert _IMPL_GOLD in _BASE, "impl anchor drift: render body not verbatim"


# ===========================================================================
# (1) POSITIVE CONTROL — structurally different but CORRECT (verify).
# Reorder the control flow into the positive (visible) form instead of the
# negative early-return guard: do the work ONLY when visible, otherwise fall
# through to the shared return. Same observable effect (clause 1: nothing added
# when invisible; clause 2: + content when visible), no loop / fold lemma, no
# dropped framing obligation (the frame clauses are auto-discharged because no
# read-only field is written either way). If a faithful correct impl could NOT
# verify against this spec => SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS = """    if self.visible:
        sink.work = sink.work + self.content
    return"""

# ===========================================================================
# (2) POSITIVE CONTROL #2 — local-variable reshape (verify).
# Stage the delivered work through a named local (delivered = self.content when
# visible else 0) and add it unconditionally. Same value as the gold guard;
# proves the spec admits a flat (guardless control flow) but correct shape too.
# Must verify, else SPEC-TOO-STRONG.
# ===========================================================================
_IMPL_POS2 = """    if self.visible:
        delivered = self.content  # type: int
    else:
        delivered = 0
    sink.work = sink.work + delivered
    return"""

# ===========================================================================
# (3) ADMISSIBILITY — the precondition admits a normal F2P-shaped input (verify).
# Cannot add a top-level caller (that leaves the impl region and breaks
# same_spec). Instead, in-region: re-derive that BOTH read-only half-permission
# inputs are usable (read self.visible and self.content), that the writable
# sink.work permission is usable, and reach a normal non-raising return — exactly
# the gold behaviour with extra read-asserts. If the Requires were vacuous /
# over-strong the impl could not both consume the permissions and return =>
# PRECOND-TOO-STRONG.
# ===========================================================================
_IMPL_ADMISS = """    # admissibility: both half-permission inputs are readable and the writable
    # sink permission is usable; a normal (non-raising) return is reachable for an
    # in-domain (F2P-shaped) Container/Sink.
    Assert(self.content >= 0)                 # content half-perm readable + invariant
    Assert(self.visible or not self.visible)  # visible half-perm readable (total bool)
    if not self.visible:
        Assert(sink.work == Old(sink.work))
        return
    sink.work = sink.work + self.content
    Assert(sink.work == Old(sink.work) + self.content)
    return"""

# ===========================================================================
# (4) FRAME-MUTATION — write to the read-only input self.content (reject).
# MANDATORY: self.content and self.visible are held at only Acc(...,1/2). The
# write `self.content = self.content` is VALUE-NEUTRAL (it would still satisfy
# self.content == Old(self.content) if it had permission) — yet a field WRITE
# needs FULL permission. With only the half-permission the Requires grants,
# Nagini rejects for INSUFFICIENT PERMISSION. Everything else is the gold body,
# so the rejection is attributable to the write, not to a spec change. A
# byte-fuzzer never thinks to mutate a read-only input — this is the project's
# #1 weakness class.
# ===========================================================================
_IMPL_FRAME = """    if not self.visible:
        return
    # FRAME MUTATION: write back into the read-only half-permission input.
    self.content = self.content
    sink.work = sink.work + self.content
    return"""

# ===========================================================================
# (5) PARTIAL-DOMAIN / overshoot-when-invisible — reject. THIS IS THE PRE-PATCH
# BUG (model_prepatch.py): drop the visibility guard and run the body
# unconditionally. It AGREES with the gold on the visible sub-domain (and on the
# invisible+content==0 corner), but on an invisible container with content > 0 it
# adds content to the sink. Clause 1 (Implies(not self.visible, sink.work ==
# Old(sink.work))) then fails: an invisible pass delivered work. This is exactly
# the F2P test_invisible_axes[png] scenario (an invisible 3D axes must draw
# nothing).
# ===========================================================================
_IMPL_OVERSHOOT = """    sink.work = sink.work + self.content
    return"""

# ===========================================================================
# (6) PARTIAL-DOMAIN / underdeliver-when-visible — reject. The mirror miss: keep
# the guard (invisible correct) but do NO work when visible (leave the sink as on
# entry). Agrees with gold on the invisible sub-domain and on visible+content==0,
# but on a visible container with content > 0 it under-delivers. Clause 2
# (Implies(self.visible, sink.work == Old(sink.work) + self.content)) then fails:
# a visible pass must deliver the FULL body. A faithful real patch where draw()
# returned early even when visible would draw nothing for a normal (visible) 3D
# axes, breaking every P2P rendering test (the figure would come back blank), so
# it would NOT resolve.
# ===========================================================================
_IMPL_UNDERDELIVER = """    return"""

# ===========================================================================
# (7) UNIQUENESS / overdeliver-double — reject. When visible, add 2*self.content
# instead of content (a value-level over-count: the body delivered twice the
# work). Agrees with gold only on content==0; diverges for every content > 0.
# Clause 2 pins sink.work == Old(sink.work) + self.content exactly, so the
# doubled tally fails. A faithful real patch that drew the body twice (or doubled
# the emitted primitives) would produce a doubled / corrupted figure and fail the
# P2P image-comparison tests — it would NOT resolve.
# ===========================================================================
_IMPL_DOUBLE = """    if not self.visible:
        return
    sink.work = sink.work + self.content + self.content
    return"""


SPEC_TESTS = [
    {
        "id": "pos-control-positive-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS),
        "rationale": "Structurally different but correct: the negative early-return "
                     "guard (`if not self.visible: return; work += content`) is "
                     "rewritten in positive form (`if self.visible: work += content`) "
                     "with a single shared return. Same observable effect on the sink "
                     "(clause 1: nothing added when invisible; clause 2: + content when "
                     "visible) and no read-only field is written, so the frame clauses "
                     "auto-discharge. No loop / fold lemma needed. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_POS2),
        "rationale": "Second correct shape: stage the delivered work through a named "
                     "local (`delivered = self.content if visible else 0`) and add it "
                     "unconditionally. Same value as the gold guard; a flat "
                     "(guard-less) control flow. Proves the spec is not over-fitted to "
                     "the gold's exact early-return shape. Must verify, else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-readonly-and-sink",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_ADMISS),
        "rationale": "Re-derives in-region that both half-permission inputs are usable "
                     "(reads self.content via the >=0 invariant and self.visible via a "
                     "total-bool assert) and that the writable sink.work permission is "
                     "usable, then reaches a normal non-raising return for an in-domain "
                     "(F2P-shaped) Container/Sink. If any Requires were vacuous or "
                     "over-strong the impl could not both consume the permissions and "
                     "return => PRECOND-TOO-STRONG. Source: the Acc(...,1/2) Requires + "
                     "Acc(sink.work) Requires.",
    },
    {
        "id": "frame-mutation-write-content",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_FRAME),
        "refinement": "A faithful real patch in which Axes3D.draw wrote back into the "
                      "Axes3D state it only reads (e.g. reassigning self._visible or a "
                      "drawable-content field) to satisfy its obligation would mutate "
                      "the Axes3D the caller (Figure.draw and every other holder) still "
                      "owns. The gold guard only READS self.get_visible() and never "
                      "writes the axes; Figure.draw iterates its axes and relies on each "
                      "axes' state being untouched between draws, so a self-mutating "
                      "draw would corrupt subsequent passes and the cached state the "
                      "image-comparison F2P/P2P tests render from — it would NOT "
                      "faithfully resolve test_invisible_axes (nor the P2P suite).",
        "rationale": "render holds only Acc(self.content, 1/2). The write "
                     "self.content = self.content is value-neutral (would still satisfy "
                     "self.content == Old(self.content)) but a field WRITE needs FULL "
                     "permission => Nagini rejects for INSUFFICIENT PERMISSION. Source: "
                     "the permission system + the Acc(self.content, 1/2) Requires. The "
                     "rest is the gold body verbatim, so the rejection is attributable "
                     "to the write, not a spec change.",
    },
    {
        "id": "partial-domain-overshoot-invisible",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_OVERSHOOT),
        "refinement": "This IS the pre-patch behaviour (model_prepatch.py): Axes3D.draw "
                      "with NO `if not self.get_visible(): return` guard, running the "
                      "whole render body unconditionally. For the F2P scenario "
                      "(test_invisible_axes[png]: an invisible 3D axes compared against "
                      "an empty reference figure) it still draws the body, so the "
                      "rendered figure is non-empty and the image comparison FAILS — "
                      "the faithful (guardless) patch does NOT resolve. This is exactly "
                      "the bug matplotlib #23306 fixes.",
        "rationale": "Body runs unconditionally, so for an invisible container with "
                     "content > 0 the sink gains content. Clause 1 "
                     "Implies(not self.visible, sink.work == Old(sink.work)) then "
                     "fails. Source: the invisible-case postcondition clause (the new "
                     "guard the gold patch adds).",
    },
    {
        "id": "partial-domain-underdeliver-visible",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_UNDERDELIVER),
        "refinement": "A faithful real patch where draw() returned early even when the "
                      "axes IS visible (e.g. an over-broad guard `if True: return` or "
                      "inverting the condition) would draw NOTHING for a normal visible "
                      "3D axes — every P2P 3D rendering test (and the visible half of "
                      "the surrounding image-comparison suite) would come back blank, "
                      "so the patch would NOT resolve.",
        "rationale": "Impl does no work in any case. Agrees with gold on the invisible "
                     "sub-domain and on visible+content==0, but on a visible container "
                     "with content > 0 the sink is left at Old(sink.work) while clause 2 "
                     "Implies(self.visible, sink.work == Old(sink.work) + self.content) "
                     "requires + content. Source: the visible-case postcondition clause.",
    },
    {
        "id": "uniqueness-overdeliver-double",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_GOLD, _IMPL_DOUBLE),
        "refinement": "A faithful real patch that ran the render body twice (or doubled "
                      "the primitives delivered to the renderer) on a visible axes would "
                      "produce a doubled / over-drawn figure, failing the P2P "
                      "image-comparison tests against the single-pass reference — it "
                      "would NOT resolve. Supporting value-level over-count case.",
        "rationale": "When visible the impl adds 2*self.content. Clause 2 pins "
                     "sink.work == Old(sink.work) + self.content EXACTLY, so the doubled "
                     "tally fails for every content > 0 (it agrees only at content==0). "
                     "Source: the exact-equality visible-case postcondition clause.",
    },
]

# ===========================================================================
# AXIOM lane — no @ContractOnly axiom (meta.axioms == []), but ONE A-reference
# deep model grounds the whole spec: that the REAL Axes3D.draw honours
# get_visible() (invisible => 0 draw primitives = clause 1; visible => > 0 =
# clause 2) and that get_visible() returns exactly the stored flag. We re-run the
# bundle's established G-AX check (axiom_check.py) as a Docker axiom-soundness
# probe UNDER THE GOLD PATCH (apply_gold=True): the post-patch invisible 3D axes
# must emit 0 primitives and the visible one > 0, on the real matplotlib in the
# instance image. If the real callee disagreed with clauses (1)/(2), the
# A-reference (hence the whole abstraction) would be UNSOUND.
#
# AVOID-bug #4: the probe CALLS the real Axes3D.draw onto a recording renderer
# (never regex-scrapes source). AVOID-bug #6: the probe is fully self-contained —
# it embeds the axiom_check.py logic verbatim (the runner mounts only the probe
# script; model.py / axiom_check.py are NOT in-container). The probe imports only
# matplotlib (the package under test) + stdlib and exits 0 iff every obligation
# holds.
# ===========================================================================
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-axes3d-draw-honours-visible",
        "axiom": "self.visible (boolean field read) and the content-delivery body",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness: run the REAL Axes3D.draw (gold patch "
                     "applied) onto a recording renderer in the instance image. An "
                     "invisible 3D axes must emit 0 draw primitives (clause 1: sink "
                     "unchanged) and a visible one with content must emit > 0 (clause 2: "
                     "the body delivers work); plus get_visible() must return exactly "
                     "the stored flag (set_visible(b) => get_visible()==b). If the real "
                     "callee violated this, the deep-model A-reference grounding clauses "
                     "(1)/(2) would be AXIOM-UNSOUND. Reuses the bundle's G-AX logic "
                     "(axiom_check.py) embedded verbatim.",
    },
]
