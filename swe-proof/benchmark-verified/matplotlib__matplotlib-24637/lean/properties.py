"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-24637 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves the
obligation or discharges a ground instance, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
``theorem correct_<name>`` STATEMENT stays byte-identical). ``expect="verify"``
passes iff (in scope AND the file elaborates with the obligation closed);
``expect="reject"`` passes iff (in scope AND it does NOT verify AND the case's
refutation ``witness`` holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function; one top-level equality clause):

  drawAnnotationBbox
      (visible posResolvable hasArrow : Bool) (clsName : String)
      (gid : Option String) : List RenderOp
      result = drawTrace visible posResolvable hasArrow clsName gid

  where drawTrace is, fully unfolded (grounded ENTIRELY in the inputs):

      if !visible || !posResolvable then []
      else [groupStart clsName gid]
             ++ (if hasArrow then [drawArrow] else [])
             ++ [drawPatch, drawOffsetbox]
             ++ [groupEnd clsName]

  The modeled result is the ORDERED TRACE of drawing operations the composite
  annotation-box artist emits. The single equality clause folds several
  inseparable sub-decisions, each pinned to a distinct input binder:

    * WHETHER anything is drawn — the empty trace when the artist is not visible
      or its position is unresolved, the enclosed part-draws otherwise. Pinned by
      ``visible`` and ``posResolvable``.
    * THAT the part-draws are ENCLOSED between a group-start carrying the gid and
      a matching group-end — the load-bearing structural decision (the behavior
      the issue is about). Pinned by ``gid`` (the id the group-start carries) and
      ``clsName`` (the name tagging BOTH markers, so start and end must match).
    * WHETHER the connecting-arrow op is emitted — only when the artist has one.
      Pinned by ``hasArrow``.

  drawTrace is a grounded fold over the inputs + fixed op constructors, fully
  unfoldable; NOT an opaque answer-key. The bundle declares no ``opaque`` /
  ``axiom`` (meta.json axioms == [], deep_model_references == []), so there is no
  answer key an impl could echo without producing the trace from the inputs. The
  carrier is fully TRANSPARENT — every reject witness is a bare ``decide`` at a
  concrete input; no conditioning on an opaque term is needed.

  BEHAVIOURAL DISCRIMINATOR: pre-fix, the artist drew its parts with NO
  surrounding group, so its optional id never reached the structured output; the
  F2P asserts a gid-carrying group element appears in the saved output. The
  ``no-group`` rival below IS that pre-fix behaviour; the adjacent rivals are the
  near-misses that open a group but drop the id, drop the close, mis-tag the
  close, ignore the draw guard, or ignore the arrow condition.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its modeled inputs are held at
    fractional (read-only) permission and a rival that overwrites one is rejected
    for insufficient permission. Lean is referentially transparent: the inputs
    are plain immutable values (``Bool`` / ``String`` / ``Option String`` /
    ``List RenderOp``), there is no half-permission to violate and no aliasing to
    exploit, so this class has NO expressible instance here. Nagini's two frame
    rivals (write ``gid``, write ``children``) are therefore both omitted with no
    fabricated substitute.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED (an equality
    against ``drawTrace``, a fold over the inputs and fixed op constructors,
    fully unfolded), and the bundle declares no opaque callee, so there is no
    oracle to echo. The honest analogue is the cheapest-correct POSITIVE CONTROL.

  * PARTIAL-DOMAIN (the pre-fix behaviour) — APPLIES, and is the load-bearing
    rival (``no-group``). Ported directly from nagini's pre-patch rival.

  * DROP-THE-ID / OMIT-THE-CLOSE — APPLY. Ported from nagini's drop-gid
    (empty-id) and omit-close rivals; here the id is dropped by carrying ``none``
    on the group-start and the close is dropped by omitting the group-end op.
    Nagini's rival is specifically the STRICTLY-EMPTY id, which this carrier
    keeps as a distinct value from the absent id (``some ""`` ≠ ``none``), so it
    is ported as its own ``empty-id`` rival in addition to the ``none``-carrying
    one — the two attack opposite sides of the ``gid`` binder.

  * GUARD / ARROW / CLOSE-NAME / HALF-GUARD / SWAP-PARTS rivals —
    CARRIER-SPECIFIC, not in nagini. This
    model exposes binders nagini's ``draw_grouped_output(gid, children)`` did not:
    the visibility/position guard (``visible``, ``posResolvable``), the arrow
    condition (``hasArrow``), and the class-name tag shared by both markers
    (``clsName``), and the ORDER of the enclosed part-draws. Coverage of THIS
    surface requires a rival that abuses each, so five rivals are added: ignore
    the guard entirely, honour only its visibility half (the mixed guard point),
    ignore the arrow condition, mis-tag the closing marker, and transpose the two
    part-draws. These defend binders and structure the carrier introduced; they
    are not parity-chasing for unmodeled behaviour.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation (the frozen script is tuned to the frozen form), so a
rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at a
``decide``-able concrete input; each was checked to HOLD of its rival and to FAIL
on the frozen solution (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. All five input binders are varied across the reject witnesses:
  * ``visible`` / ``posResolvable`` — ``true``/``true`` for every group-shape
    rival, ``false``/``false`` for the guard rival (the point where the draw
    guard should fire), AND the MIXED point ``true``/``false`` for the half-guard
    rival, which is what distinguishes the spec's DISJUNCTIVE guard from a
    visibility-only one. Every combination of the two guard binders that changes
    the spec's verdict is therefore witnessed.
  * ``hasArrow`` — ``false`` (no-group, close-name, arrow, half-guard, empty-id,
    swap-parts) AND ``true`` (drop-gid, omit-close), and the arrow rival is
    refuted precisely at ``hasArrow = false``.
  * ``clsName`` — a distinct string per witness, and the close-name rival is
    refuted where it differs from the empty tag it wrongly emits.
  * ``gid`` — ``some _`` (no-group, drop-gid, guard, close-name, arrow,
    half-guard, swap-parts) AND ``none`` (omit-close, empty-id). Both SIDES of
    the id binder are attacked by a dedicated rival: drop-gid is refuted where
    ``gid = some _`` (an id exists and is lost) and empty-id where ``gid = none``
    (no id exists and one is manufactured), so the binder is pinned as an
    injection rather than merely "an id is present".
The refutation points are all 9 distinct.

ORDERING. The spec's single equality also pins the ORDER of the enclosed parts,
not just which ops appear. The swap-parts rival emits exactly the right ops, with
correct markers/id/tag, transposed — so it isolates the ordering content of the
equality, which the which-ops rivals leave untested.

AXIOM lane: EMPTY. meta.json axioms == [] and deep_model_references == []; the
trace is modeled deeply and structurally over the inputs, so there is no
axiom-soundness obligation for the PBT axiom lane (that lane is G-AX's in any
case). AXIOM_TESTS is empty.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-24637"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region def, and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  -- position resolution happens here and emits no marker\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

_PROOF_BODY = (
    "  intro visible posResolvable hasArrow clsName gid\n"
    "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
    "  simp only [Id.run, bind, pure]\n"
    "  by_cases h : (!visible || !posResolvable) = true <;>\n"
    "    by_cases ha : hasArrow = true <;>\n"
    "    simp [h, ha]"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced (frozen
    proof kept — for reject cases, whose frozen script fails against the
    reshaped impl exactly as expected)."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — a
# direct functional expression (no `Id.run do` / `let mut`), with the appends
# re-associated. Same trace on every input; the frozen `simp only [Id.run …]`
# script is tuned to the `Id.run do` form, so the obligation is re-proved for
# the new shape (STATEMENT byte-identical, no new lemma/axiom).
# ---------------------------------------------------------------------------
_IMPL_POS = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp :=\n"
    "  if !visible || !posResolvable then\n"
    "    []\n"
    "  else\n"
    "    let body := (if hasArrow then [RenderOp.drawArrow] else [])\n"
    "                  ++ [RenderOp.drawPatch, RenderOp.drawOffsetbox]\n"
    "    ([RenderOp.groupStart clsName gid] ++ body) ++ [RenderOp.groupEnd clsName]"
)
_POS_PROOF = (
    "  intro visible posResolvable hasArrow clsName gid\n"
    "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
    "  by_cases h : (!visible || !posResolvable) = true <;>\n"
    "    by_cases ha : hasArrow = true <;>\n"
    "    simp [h, ha]"
)

# ADMISSIBILITY: discharge the obligation at a normal, F2P-shaped ground input
# (visible, position-resolvable, WITH an id) inside the proof region, then close
# the frozen obligation verbatim. If that ground instance could not be
# discharged the modeled behavior would be unsatisfiable at exactly the input the
# F2P exercises (the analogue of PRECOND-TOO-STRONG). The frozen theorem carries
# no precondition hypothesis (the behavior is total), so nagini's
# precondition-admission probe has no binder to attack; this is the honest
# analogue. Nothing is assumed: the STATEMENT is byte-identical, the ground
# instance is a `have`, and no new declaration/axiom/`sorry` is introduced.
_ADMISS_PROOF = (
    "  have _ground : problem_spec_drawAnnotationBbox true true true \"C\" (some \"g\")\n"
    "      (implementation_drawAnnotationBbox true true true \"C\" (some \"g\")) := by\n"
    "    unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
    "    decide\n"
    + _PROOF_BODY
)

# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl region; the spec and theorem STATEMENT
# stay byte-identical).
# ---------------------------------------------------------------------------

# NO-GROUP (= the pre-fix bug): draw the parts with NO surrounding group markers,
# so the id never appears in the trace.
_IMPL_NOGROUP = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  return trace"
)

# DROP-THE-ID: open a WELL-FORMED group, but carry `none` as the id instead of
# the artist's `gid`.
_IMPL_DROPGID = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName none]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

# OMIT-THE-CLOSE: emit the id-carrying group-start and the parts, but never the
# matching group-end.
_IMPL_NOCLOSE = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  return trace"
)

# IGNORE-THE-GUARD: always draw (and emit the group markers) even when the
# artist is not visible or its position is unresolved.
_IMPL_GUARD = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

# IGNORE-THE-ARROW-CONDITION: emit the arrow op unconditionally, regardless of
# whether the artist has one.
_IMPL_ARROW = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

# MISTAG-THE-CLOSE: tag the group-end with the empty name instead of the same
# class name that tagged the group-start (unbalanced markers).
_IMPL_WRONGNAME = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd \"\"]\n"
    "  return trace"
)

# HALF-GUARD: check ONLY visibility and skip the position-resolution half of the
# guard, so a visible artist whose position is unresolved still draws. Added by
# audit: every other rival is refuted with the two guard binders EQUAL (both
# `true`, or both `false` for the guard rival), so a rival that keeps one half of
# the guard and drops the other was unattacked.
_IMPL_HALFGUARD = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

# EMPTY-ID: always carry a PRESENT id, substituting the empty string when the
# artist has none. Added by audit: this is the near-miss on the `none` side of
# the `gid` binder (drop-the-id attacks the `some _` side), and it is the exact
# shape of nagini's empty-id rival.
_IMPL_EMPTYID = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName (some (gid.getD \"\"))]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)

# SWAP-THE-PARTS: emit a well-formed, correctly-tagged, id-carrying group around
# the right SET of part-draws, but in the wrong relative ORDER. Added by audit:
# every other rival changes WHICH ops are emitted, so the spec's ORDERING of the
# enclosed parts (as opposed to the enclosure itself) was untested.
_IMPL_SWAPPARTS = (
    "def implementation_drawAnnotationBbox\n"
    "    (visible posResolvable hasArrow : Bool) (clsName : String) (gid : Option String) :\n"
    "    List RenderOp := Id.run do\n"
    "  if !visible || !posResolvable then\n"
    "    return []\n"
    "  let mut trace : List RenderOp := []\n"
    "  trace := trace ++ [RenderOp.groupStart clsName gid]\n"
    "  if hasArrow then\n"
    "    trace := trace ++ [RenderOp.drawArrow]\n"
    "  trace := trace ++ [RenderOp.drawOffsetbox]\n"
    "  trace := trace ++ [RenderOp.drawPatch]\n"
    "  trace := trace ++ [RenderOp.groupEnd clsName]\n"
    "  return trace"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct impl cannot satisfy the frozen
    # obligation, the spec is SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-functional-reassoc",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_IMPL_POS), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that drops the mutable-accumulator `Id.run do` form "
            "and builds the same trace as one functional `if/else` expression with "
            "the appends re-associated (`([groupStart clsName gid] ++ body) ++ "
            "[groupEnd clsName]`). Same value on every input, so it must satisfy "
            "`result = drawTrace visible posResolvable hasArrow clsName gid`; if it "
            "cannot, the spec is SPEC-TOO-STRONG. Proof: after `unfold`, case-split "
            "on the guard and on `hasArrow` and `simp` closes each — no new "
            "declaration, axiom, or assumption token; the STATEMENT is byte-identical."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped ground input, not only
    # provable in the abstract.
    # =====================================================================
    {
        "id": "admiss-visible-resolvable-with-id-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the obligation is discharged at the F2P-shaped ground input (visible, "
            "position-resolvable, WITH a group id: `true true true \"C\" (some "
            "\"g\")`), where the spec requires the parts be enclosed between an "
            "id-carrying group-start and a matching group-end, by `decide`; then the "
            "frozen obligation is closed verbatim. Verifies (else the modeled "
            "behavior would be unsatisfiable at the normal input, the analogue of "
            "PRECOND-TOO-STRONG). Nothing assumed: the STATEMENT is byte-identical, "
            "the ground instance is a `have` inside the existing tactic body, and no "
            "new declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P (so a verifying rival would be
    # a true verify-does-not-imply-resolve break, not an artifact) and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-no-group",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_NOGROUP),
        "refinement": (
            "this IS the pre-fix behaviour: the artist drew its parts with NO "
            "surrounding group element, so its optional id never entered the "
            "structured output. Its faithful real patch is the pre-patch code, whose "
            "output contains no id-carrying group element at all; the F2P asserts a "
            "gid-carrying group element appears in the saved output, so the entry is "
            "absent and the patch does NOT resolve — exactly the bug the fix repairs."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: with a visible, "
            "position-resolvable artist the spec demands the trace OPEN with "
            "`groupStart clsName gid` and CLOSE with `groupEnd clsName`, but the "
            "rival emits only the part-draws (no group markers). Refuted at "
            "`hasArrow = false` so the traces differ only in the missing markers."
        ),
        "witness": (
            "-- The parts are drawn with no enclosing group, so the id-carrying\n"
            "-- group-start (and its close) the spec requires are absent.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true false \"A\" (some \"g\")\n"
            "    (implementation_drawAnnotationBbox true true false \"A\" (some \"g\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-drop-the-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_DROPGID),
        "refinement": (
            "a faithful real patch that opened a group but FORGOT to carry the id "
            "would emit a group element with no id (or a class-name-derived one), "
            "NOT the artist's own id. The F2P looks for the artist's id on the group "
            "element specifically, so the id still would not reach the output as the "
            "group's id and the patch does NOT resolve — this is nagini's drop-gid "
            "(empty-id) rival on this carrier (the id is carried as `none`)."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec's group-start "
            "carries `gid`, but the rival's carries `none`. At `gid = some \"x\"` "
            "the two group-start ops differ, so the traces differ. Refuted where "
            "`gid = some _` — the sub-domain where an id exists to be lost — varying "
            "the `gid` binder off the `none` value the omit-close rival uses."
        ),
        "witness": (
            "-- A group is opened but carries no id where one exists (`some \"x\"`),\n"
            "-- so the emitted group-start differs from the id-carrying one.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true true \"B\" (some \"x\")\n"
            "    (implementation_drawAnnotationBbox true true true \"B\" (some \"x\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-omit-the-close",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_NOCLOSE),
        "refinement": (
            "a faithful real patch that opened the id-carrying group but omitted the "
            "matching close would leave an unbalanced group open in the structured "
            "output, malforming it (the group is never closed before the document "
            "end) and regressing the pre-existing output-structure tests — so it "
            "would not resolve while keeping the suite green. The id still appears, "
            "so a naive 'does the id show up' check would miss it; the full "
            "structural equality catches the missing close. Ported from nagini's "
            "omit-close rival."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec's trace ends "
            "with `groupEnd clsName`, but the rival stops after the part-draws. The "
            "traces differ in the trailing close op. Refuted with `gid = none` "
            "(varying that binder off `some _`) and `hasArrow = true`."
        ),
        "witness": (
            "-- The id-carrying group is opened but never closed, so the trailing\n"
            "-- group-end the spec requires is missing.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true true \"C\" none\n"
            "    (implementation_drawAnnotationBbox true true true \"C\" none) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-the-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_GUARD),
        "refinement": (
            "a faithful real patch that emitted the group markers/part-draws WITHOUT "
            "first checking visibility and position resolution would draw (and emit "
            "an id-carrying group for) an artist that should draw nothing, producing "
            "output ops where the pre-existing not-drawn behaviour expects none — "
            "regressing those tests. It would not resolve while keeping the suite "
            "green. This attacks the guard binders the carrier models (nagini pinned "
            "the drawn branch by a precondition rather than in-spec)."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: when `!visible || "
            "!posResolvable`, the spec demands the empty trace, but the rival emits "
            "the full group. Refuted at `visible = false, posResolvable = false` — "
            "the sole point where the guard should fire, varying BOTH guard binders "
            "off `true`."
        ),
        "witness": (
            "-- A not-visible, unresolved artist must emit nothing, but the rival\n"
            "-- ignores the guard and emits the full id-carrying group.\n"
            "example : ¬ problem_spec_drawAnnotationBbox false false false \"D\" (some \"y\")\n"
            "    (implementation_drawAnnotationBbox false false false \"D\" (some \"y\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-ignore-the-arrow-condition",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_ARROW),
        "refinement": (
            "a faithful real patch that emitted the connecting-arrow draw "
            "unconditionally would attempt to draw an arrow the artist does not "
            "have, adding a draw op (or raising) where none belongs; the "
            "pre-existing behaviour for an artist without an arrow expects no arrow "
            "op, so it would regress and not resolve. This attacks the `hasArrow` "
            "binder the carrier models."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec emits the arrow "
            "op only `if hasArrow`, but the rival emits it always. At `hasArrow = "
            "false` the spec's trace omits the arrow op while the rival includes it, "
            "so the traces differ. Refuted precisely at `hasArrow = false`."
        ),
        "witness": (
            "-- With no arrow, the spec omits the arrow op, but the rival emits it\n"
            "-- unconditionally.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true false \"F\" (some \"w\")\n"
            "    (implementation_drawAnnotationBbox true true false \"F\" (some \"w\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-mistag-the-close",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_WRONGNAME),
        "refinement": (
            "a faithful real patch that closed the group with a name different from "
            "the one that opened it would emit mis-nested group markers, malforming "
            "the structured output's nesting and regressing the pre-existing "
            "output-structure tests — so it would not resolve. This attacks the "
            "`clsName` binder, which the spec requires tag BOTH the start and the "
            "end identically."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec closes with "
            "`groupEnd clsName`, matching the name on the start, but the rival closes "
            "with `groupEnd \"\"`. At `clsName = \"E\"` (≠ the empty tag) the close "
            "ops differ, so the traces differ. Refuted where `clsName` is a non-empty "
            "string distinct from the mis-emitted empty tag."
        ),
        "witness": (
            "-- The group is closed with the empty name instead of the class name\n"
            "-- that opened it, so the closing op is mis-tagged.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true false \"E\" (some \"z\")\n"
            "    (implementation_drawAnnotationBbox true true false \"E\" (some \"z\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-half-guard-visible-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_HALFGUARD),
        "refinement": (
            "a faithful real patch that consulted only the visibility half of the "
            "draw guard and dropped the position-resolution half would draw (and "
            "emit an id-carrying group for) an artist whose position could not be "
            "resolved — a case the pre-existing not-drawn behaviour expects to "
            "produce no ops at all, and which the unresolved-position path exists "
            "precisely to skip. It would emit output ops where none belong, "
            "regressing those tests, so it would not resolve while keeping the "
            "suite green."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec's guard is the "
            "DISJUNCTION `!visible || !posResolvable`, so the empty trace is required "
            "when EITHER half fires, but the rival returns early only on `!visible`. "
            "Refuted at the MIXED guard point `visible = true, posResolvable = "
            "false` — the sub-domain no other rival's witness reaches, since every "
            "other one holds the two guard binders EQUAL (both `true`, or both "
            "`false` for the guard rival). That mixed point is what distinguishes the "
            "spec's disjunctive guard from a visibility-only one."
        ),
        "witness": (
            "-- The position is unresolved though the artist is visible, so nothing\n"
            "-- must be drawn; the rival checks only visibility and emits the full group.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true false false \"H\" (some \"q\")\n"
            "    (implementation_drawAnnotationBbox true false false \"H\" (some \"q\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-manufacture-empty-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_EMPTYID),
        "refinement": (
            "a faithful real patch that coerced a missing id into a present, empty "
            "one would tag every un-idded artist's group with an empty id attribute "
            "instead of omitting the attribute, changing the structured output for "
            "every artist that carries no id and regressing the pre-existing "
            "output-content tests. This is nagini's empty-id rival on this carrier, "
            "on the `none` side of the id binder."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec's group-start "
            "carries the artist's `gid` VERBATIM, including `none` when there is no "
            "id, but the rival always carries `some _`. At `gid = none` the spec "
            "requires `groupStart clsName none` while the rival emits `groupStart "
            "clsName (some \"\")`, so the traces differ. Refuted at `gid = none` — "
            "the complementary sub-domain to drop-the-id, which attacks the `some _` "
            "side; the two together pin the id binder as an injection rather than "
            "merely 'an id is present'."
        ),
        "witness": (
            "-- With no id at all, the spec's group-start carries `none`; the rival\n"
            "-- manufactures a present-but-empty id instead.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true false \"G\" none\n"
            "    (implementation_drawAnnotationBbox true true false \"G\" none) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
    {
        "id": "weak-swap-the-part-draws",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_SWAPPARTS),
        "refinement": (
            "a faithful real patch that drew the wrapped offset box before the "
            "background box would paint the background OVER the content it is "
            "supposed to sit behind, inverting the z-order of the composite artist's "
            "parts in every rendered output — a visible regression of the "
            "pre-existing image-comparison tests, so it would not resolve while "
            "keeping the suite green."
        ),
        "rationale": (
            "REJECT from the clause `result = drawTrace …`: the spec pins the trace "
            "as an ORDERED sequence whose enclosed parts run background box then "
            "wrapped offset box, but the rival emits them in the opposite order. The "
            "group markers, the id, the class tag and the multiset of emitted ops are "
            "all correct, so this attacks the ORDERING the equality carries, which "
            "every other rival leaves untested (they each change WHICH ops appear). "
            "Refuted at `hasArrow = false` so the two traces differ in nothing but "
            "the transposed pair."
        ),
        "witness": (
            "-- The two part-draws are emitted in the wrong relative order.\n"
            "example : ¬ problem_spec_drawAnnotationBbox true true false \"I\" (some \"g\")\n"
            "    (implementation_drawAnnotationBbox true true false \"I\" (some \"g\")) := by\n"
            "  unfold problem_spec_drawAnnotationBbox implementation_drawAnnotationBbox drawTrace\n"
            "  decide\n"
        ),
    },
]


# No consumed axioms and no deep-model references: the trace is modeled deeply
# and structurally over the inputs (meta.json axioms == [], deep_model_references
# == []), so there is no in-model axiom obligation for the PBT axiom lane to
# re-discharge (and that lane belongs to G-AX regardless).
AXIOM_TESTS = []
