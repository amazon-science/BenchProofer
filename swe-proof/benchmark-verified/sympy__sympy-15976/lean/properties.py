"""properties.py — G-PBT falsification battery for sympy__sympy-15976 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_<name>``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed); ``expect:"reject"`` passes iff (in
scope AND it does NOT verify AND the case's refutation ``witness`` holds of the
rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a four-input domain):

  symbolMarkup (name : String) (supers subs : List String) (style : String)
      : MathNode
    result = buildSymbolMarkup name supers subs style

  A symbol is described by a base name plus two ordered collections of
  decoration strings (superscripts and subscripts) and a rendering-style flag.
  The single top-level clause pins the produced markup tree EXACTLY, and that
  tree is determined by four inseparable sub-decisions, each pinned to a distinct
  binder:

    * WHICH top-level element wraps the result — the bare name element when there
      are neither superscripts nor subscripts; a subscript element with only
      subscripts; a superscript element with only superscripts; a combined
      element with both. Pinned by the emptiness of ``supers`` and ``subs``.
    * The base identifier element carries the base name as its text. Pinned by
      ``name``.
    * WHICH decoration collection is laid out in each child slot, and in WHICH
      ORDER — for the combined element the subscript layout precedes the
      superscript layout; a single-string collection lays out as one identifier
      element, several strings as a row element. Pinned by the CONTENTS of
      ``supers`` and ``subs`` (both the multiplicity that selects row-vs-single
      and the position in the ordered child list).
    * WHETHER the bold attribute is attached to the top-level element — present
      exactly when the bold style is requested, on EVERY element kind including
      the bare name element. Pinned by ``style``.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling makes an
    input-write attack MANDATORY because its modeled name list is held at
    fractional (read-only) permission and a rival that appends to it is rejected
    for insufficient permission. Lean is referentially transparent: every input
    is a plain immutable value (``String`` / ``List String``), there is no
    half-permission to violate and no aliasing to exploit, so this class has NO
    expressible instance here. No substitute is fabricated for it.
    DEMONSTRATED, not asserted: the audit built the closest analogue — a variant
    that copies the inputs into ``let mut`` locals and appends to both (a
    character to the name, a string to the subscript collection) before building
    the tree from the ORIGINAL binders — and it VERIFIES against the frozen spec
    with the frozen ``rfl`` untouched (exit 0). That is the correct outcome and
    the reason the class is vacuous: the write cannot be observed, because the
    locals are copies and the spec relates the result to the binders. A rival
    whose appended values actually reached the tree would be an ordinary
    wrong-value rival on ``name`` / ``subs``, which ``weak-name-dropped`` and
    ``weak-layout-collapse`` already cover from the other direction.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The bundle declares NO ``opaque`` / ``axiom``
    callee (meta.json axioms == [], deep_model_references == []); the whole markup
    tree is spelled out structurally over the inputs, so there is no answer key an
    implementation could echo without doing the work. The honest analogues are
    the cheapest-correct POSITIVE CONTROLS below.

  * DIVERGENCE / NON-TERMINATION — KNOWN HOLE, not a vacuous class, and measured
    rather than assumed. The frozen solution sets no termination-semantics option
    and the modeled behavior is non-recursive, so there is no loop in the defended
    surface for a rival to strip a measure from. Two shapes were built. (1) A
    recursive helper with NO decreasing measure, written without ``partial``: the
    carrier DOES discharge a termination obligation — the file fails with
    ``unsolved goals n : ℕ ⊢ False`` on the measure goal — so such a rival is
    rejected, but it is rejected by the TERMINATION checker before the spec is
    consulted, and its witness cannot be built for the same reason (the impl never
    elaborates), so no witness can attribute that rejection to the spec. (2) A
    ``partial def`` helper, which IS in variant scope (``variant_problems == []``)
    and elaborates: the impl becomes an opaque constant, and the witness's
    refutation reduces to ``¬ spin 0 (...) = ...``, which no tactic can close
    because ``partial`` blocks reduction — witness exit 1 against the rival, so the
    case would record ``witness-unproven`` rather than a refutation. Disposition:
    HOLE (the spec does not refute an opaque non-terminating impl), not vacuity;
    nothing shippable, and no fabricated case is added for it.

  * PARTIAL-DOMAIN rivals — APPLY, and are load-bearing. Each nagini uniqueness
    rival attacks one top-level sub-decision on the sub-domain where it diverges
    from gold while agreeing everywhere else; every one ports to a wrong impl
    over this carrier and is refuted at a concrete input whose spec predicate is
    ``decide``-free (the node type carries no ``DecidableEq``, so each witness
    unfolds the spec + impl and closes with ``simp``).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen syntactic
form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at a concrete input; each was built (against the rival) and
rebuilt (against the frozen solution) to confirm it HOLDS of its rival and FAILS
on gold (so it discriminates rather than asserting a tautology).

BINDER COVERAGE. The four input binders are varied across the reject witnesses:
  * ``supers`` / ``subs`` emptiness — refuted with subs-only (``[]`` / ``["a"]``),
    supers-only (``["2"]`` / ``[]``), superscript-and-subscript both present
    (``["1"]`` / ``["1","2"]``), and both-empty (``[]`` / ``[]``), so ALL FOUR
    arms of the branch selector carry their own rival. (The supers-only arm was
    added by the audit; the port had left that arm — the first shape the F2P
    observable exercises — with no rival, so nothing attributed its top-level
    element kind to the spec.)
  * ``supers`` / ``subs`` contents — refuted at a multi-string collection
    (``["1","2"]``, row-vs-single collapse) and, in the OPPOSITE direction, at a
    single-string collection wrapped in a spurious row (``["a"]``), so BOTH halves
    of the row-vs-single clause carry a rival; and at a combined element with the
    two slots holding differently-shaped collections (order attack), so the layout
    and the child ORDER are both pinned, not just the branch. (The over-wrapping
    direction was added by the second audit; the port had probed the clause only
    from the many-to-one side.)
  * ``name`` — refuted by a rival that drops the base name text, at input
    ``name = "x"``.
  * ``style`` — refuted at ``"bold"`` on the bare-name sub-domain AND on the
    combined sub-domain (``["1"]`` / ``["2"]``), so the bold attribute is pinned
    on more than one element kind rather than on one arm only. NOT claimed: the
    subscript-only and superscript-only arms carry no bold rival of their own, so
    per-arm bold coverage is demonstrated for two of the four arms, not all four.
    (The combined-arm bold rival was added by the second audit, which found the
    battery asserting coverage of "EVERY element kind" from a single arm.)
``pts`` = 7 distinct input points. (Seven, not eight, for ten cases: the
over-wrapping layout rival is refuted at the same input point as
``weak-subs-prepatch-root`` — supers ``[]``, subs ``["a"]``, style ``"plain"`` —
because that is exactly where a single-string collection's layout is observable.
Two rivals discriminated at one shared point, not one point counted twice.)

AUDITED (second pass). A second independent audit re-derived all six then-present
witnesses against rival and gold, and additionally ran the FORGERY test on each:
building the flipped claim (the same statement with the ``¬`` dropped) against
both sides. Every flip inverted — exit 0 on gold, exit 1 on the rival with
``unsolved goals ⊢ False`` — so each gold-side exit code demonstrably tracks the
CLAIM rather than a syntactic accident, and no case is hollow. It also perturbed
the admissibility case's pinned literal three ways (tag ``msub``→``msup``, the
decoration text, and dropping the bold attribute); each perturbation FAILS
(exit 1), which is the machine check that that case pins the produced VALUE.
Two coverage defects were found and repaired — both cases of prose claiming
coverage the manifest never demonstrated — and are marked ``AUDIT NOTE (second
audit)`` at the site: no bold rival on any arm but the bare-name one (while the
docstring claimed "EVERY element kind"), and no rival on the over-wrapping half
of the row-vs-single clause. Both new rivals were measured before landing:
rejected under a generous multi-tactic proof attempt, witness exit 0 vs rival,
exit 1 with ``⊢ False`` vs gold, and the flipped claim inverting on both sides.

AUDITED. An independent adversarial audit re-derived every witness with the real
verifier (each built against its rival, exit 0, and against the frozen solution,
exit 1 with ``unsolved goals ⊢ False`` — a semantic refutation of the concrete
claim, not a missing identifier or a type error). It also probed the spec with
fresh rivals the battery does not contain (bold keyed on ``style != "plain"``
rather than ``== "bold"``; a row layout with its separator elements dropped; a
separator whose text is the empty string rather than a space; a renamed
top-level tag) — all four were REJECTED, so no spec hole was found on those
clauses — and with fresh CORRECT reshapes (branch by pattern-matching the two
lists instead of testing their lengths; ``isEmpty`` in place of ``length == 0``;
the bold attribute attached by an inline match rather than through the helper; a
local layout function replacing the shared one), all four of which VERIFY, so
the spec is not too strong on those shapes either. Two defects were found and
repaired; both are marked ``AUDIT NOTE`` at the site.

OMITTED nagini cases (see assessment): the frame/permission-mutation rival
(VACUOUS on a referentially-transparent carrier) and the AXIOM_TESTS lane (this
bundle declares no axiom / deep-model reference — G-AX skips — and the axiom lane
is not this gate's job).
"""
from pathlib import Path

INSTANCE = "sympy__sympy-15976"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every
# replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

_PROOF_BODY = (
    '  intro name supers subs style\n'
    '  rfl'
)

# sanity: the frozen anchors are present exactly once
assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival / reshaped impl bodies (each a full impl region; only the impl changes,
# so the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# POSITIVE CONTROL (soundness): a structurally different but CORRECT impl — the
# four cases are branched on the SUBSCRIPT emptiness first (the frozen impl
# branches on the superscript emptiness first), landing on the identical tree in
# every case. The frozen `rfl` no longer closes the reshaped `if`; the tactic
# body is retuned (unfold + split on both branches + `rfl`), statement
# byte-identical, no new lemma/axiom/assumption token.
_POS_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if subs.length == 0 then\n'
    '      if supers.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '    else\n'
    '      if supers.length == 0 then\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)
_POS_PROOF = (
    '  intro name supers subs style\n'
    '  unfold problem_spec_symbolMarkup implementation_symbolMarkup buildSymbolMarkup\n'
    '  simp only [Id.run, Id.pure_eq, Id.bind_eq]\n'
    '  split <;> split <;> rfl'
)

# ADMISSIBILITY: the frozen impl + frozen proof, with the spec predicate
# discharged at an F2P-shaped ground input (subscript-only, single part, bold)
# against a LITERAL result tree, and the frozen impl separately shown to compute
# that same literal — so the pair pins WHAT the modeled behavior produces there,
# not merely that it produces something.
#
# AUDIT NOTE. This case previously read
#     have _ground : problem_spec_symbolMarkup "x" [] ["2"] "bold"
#         (implementation_symbolMarkup "x" [] ["2"] "bold") := by rfl
# which is a literal INSTANCE of the frozen `∀`-obligation closed two lines
# later by the same `rfl`. It could not fail while the frozen theorem passed, so
# it attested nothing beyond the theorem itself, and it pinned no value — the
# nagini sibling's analogue asserts the produced tag and bold marker
# (`node_tag(r) == TAG_MSUB`, `node_bold(r) == False`), a value claim this port
# had dropped. Both `have`s below name the full expected tree explicitly, so a
# spec or impl that computed a DIFFERENT tree at this input would fail here even
# though the `∀` obligation still held of it.
_ADMISS_PROOF = (
    '  have _ground : problem_spec_symbolMarkup "x" [] ["2"] "bold"\n'
    '      (MathNode.elem "msub" [("mathvariant", "bold")]\n'
    '        [MathNode.elem "mi" [] [MathNode.text "x"],\n'
    '         MathNode.elem "mi" [] [MathNode.text "2"]]) := by\n'
    '    simp [problem_spec_symbolMarkup, buildSymbolMarkup, joinPieces,\n'
    '      MathNode.setAttr]\n'
    '  have _ground_impl : implementation_symbolMarkup "x" [] ["2"] "bold"\n'
    '      = MathNode.elem "msub" [("mathvariant", "bold")]\n'
    '        [MathNode.elem "mi" [] [MathNode.text "x"],\n'
    '         MathNode.elem "mi" [] [MathNode.text "2"]] := by\n'
    '    simp [implementation_symbolMarkup, joinPieces, MathNode.setAttr]\n'
    + _PROOF_BODY
)

# PARTIAL-DOMAIN (subs-only branch reverts to the pre-fix skeleton): on the
# subscript-only sub-domain the top-level element stays the bare-name element and
# wraps the subscript element as its single child (the pre-fix nesting), instead
# of BEING the subscript element. Correct on every other branch.
_PREPATCH_ROOT_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "mi" [] [MathNode.elem "msub" [] [mname, joinPieces subs]]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (supers-only branch reverts to the pre-fix skeleton): the mirror
# of the case above on the OTHER single-decoration branch — with superscripts only,
# the top-level element stays the bare-name element and wraps the superscript
# element as its single child, instead of BEING the superscript element. Correct
# on every other branch, including the subscript-only one.
#
# AUDIT NOTE. Added by the audit. The battery pinned the extra-wrapper regression
# only on the subscript-only branch; the superscript-only branch — a distinct
# `if` arm of the modeled assembly, and the FIRST shape the F2P observable
# exercises — had no rival at all, so nothing attributed that arm's top-level
# element kind to the spec.
_PREPATCH_SUP_ROOT_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "mi" [] [MathNode.elem "msup" [] [mname, joinPieces supers]]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (decoration layout collapse): every decoration collection is
# laid out as a single identifier element carrying the first string, dropping the
# multi-string row layout. Agrees with gold on single-string collections;
# diverges on multi-string ones.
_LAYOUT_COLLAPSE_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, MathNode.elem "mi" [] [MathNode.text (subs.headD "")]]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, MathNode.elem "mi" [] [MathNode.text (supers.headD "")]]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, MathNode.elem "mi" [] [MathNode.text (subs.headD "")], MathNode.elem "mi" [] [MathNode.text (supers.headD "")]]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (combined child ORDER swap): on the combined element the
# subscript and superscript layouts are placed in the wrong slots — superscript
# first, then subscript. Agrees with gold when the two collections lay out to the
# identical tree; diverges when they differ.
_ORDER_SWAP_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces supers, joinPieces subs]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (bold drop on the bare-name sub-domain): the bold attribute is
# attached only when there are superscripts or subscripts, silently dropped on
# the bare-name element. Agrees with gold on every scripted branch.
_BOLD_DROP_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" && !(supers.length == 0 && subs.length == 0) then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (bold drop on the COMBINED sub-domain): the bold attribute is
# attached on every arm EXCEPT the combined one, where it is silently dropped.
# Agrees with gold on the bare-name, subscript-only and superscript-only arms.
#
# AUDIT NOTE (second audit). Added. The battery claimed — in its own docstring and
# in `weak-bold-drop-bare`'s rationale — that the bold attribute is pinned "on
# EVERY element kind, not only the scripted ones". Only the bare-name arm actually
# carried a bold rival, so the three SCRIPTED arms had no case attributing their
# bold attachment to the spec, and the claim of per-kind coverage was prose the
# manifest did not demonstrate. This rival attacks the arm the previous bold case
# leaves unattacked and is refuted at supers `["1"]`, subs `["2"]`, style `"bold"`.
_BOLD_DROP_COMBINED_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" && !(supers.length != 0 && subs.length != 0) then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (layout always a row): every decoration collection is laid out as
# a ROW element, even a single-string one, which must lay out as a lone identifier
# element. The exact mirror of `weak-layout-collapse`, which attacks the
# row-vs-single boundary from the other side (collapsing several strings to one
# element); this over-wraps one string into a row.
#
# AUDIT NOTE (second audit). Added. The row-vs-single decision was probed in one
# direction only: every existing rival either agrees with gold on single-string
# collections or collapses multi-string ones. Nothing rejected an impl that
# WRAPPED a single string in a row element, so the "a single string becomes one
# identifier element" half of the layout clause carried no rival at all. Refuted
# at subs `["a"]`, where gold lays out one identifier element and the rival a row.
_ALWAYS_ROW_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let jp : List String -> MathNode := fun its =>\n'
    '    MathNode.elem "mrow" [] (joinSep its)\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text name]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, jp subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, jp supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, jp subs, jp supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)

# PARTIAL-DOMAIN (base name dropped): the base identifier element carries the
# empty string instead of the actual base name, doing no work on the `name`
# input. Diverges wherever the base name is nonempty.
_NAME_DROP_IMPL = (
    'def implementation_symbolMarkup (name : String) (supers subs : List String)\n'
    '    (style : String) : MathNode := Id.run do\n'
    '  let mname := MathNode.elem "mi" [] [MathNode.text ""]\n'
    '  let mut x :=\n'
    '    if supers.length == 0 then\n'
    '      if subs.length == 0 then\n'
    '        mname\n'
    '      else\n'
    '        MathNode.elem "msub" [] [mname, joinPieces subs]\n'
    '    else\n'
    '      if subs.length == 0 then\n'
    '        MathNode.elem "msup" [] [mname, joinPieces supers]\n'
    '      else\n'
    '        MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]\n'
    '  if style == "bold" then\n'
    '    x := x.setAttr "mathvariant" "bold"\n'
    '  return x'
)


def _witness(name, supers, subs, style, tac):
    return (
        f'example : ¬ problem_spec_symbolMarkup "{name}" {supers} {subs} "{style}"\n'
        f'    (implementation_symbolMarkup "{name}" {supers} {subs} "{style}") := by\n'
        '  unfold problem_spec_symbolMarkup implementation_symbolMarkup buildSymbolMarkup\n'
        f'{tac}'
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl
    # that MUST verify. If a faithful correct reshape cannot satisfy the frozen
    # obligation the spec is SPEC-TOO-STRONG. The theorem STATEMENT is
    # byte-identical; only the tactic body is retuned to the reshaped `if` (the
    # frozen `rfl` no longer closes it). No helper lemma, axiom, or assumption
    # token is introduced.
    # =====================================================================
    {
        "id": "pos-subs-first-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_IMPL), _PROOF_BODY, _POS_PROOF),
        "rationale": (
            "a correct reshape that branches on the subscript collection first "
            "(the frozen impl branches on the superscript collection first), "
            "landing on the identical markup tree in all four cases, must satisfy "
            "`result = buildSymbolMarkup name supers subs style`; if it cannot, "
            "the spec is SPEC-TOO-STRONG. Proof: after `unfold`, `split <;> split "
            "<;> rfl` closes each of the four reshaped branches; no new "
            "declaration, axiom, or assumption token."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input rather than only in the abstract. The
    # frozen theorem carries NO precondition hypothesis (the behavior is total, so
    # `∀` is unguarded), so nagini's precondition-admission probe has no binder to
    # attack; the honest analogue is to discharge the spec predicate at the F2P
    # ground input inside the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF),
        "rationale": (
            "the spec predicate is discharged at an F2P-shaped ground input "
            "(subscript-only, single part, bold style) against an EXPLICIT "
            "literal result tree — the subscript element carrying the bold "
            "attribute, with the name identifier and the single-string layout as "
            "its children — and the frozen impl is separately shown to compute "
            "that same literal, both as `have`s before the frozen obligation is "
            "closed verbatim. Verifies (else the spec is unsatisfiable at the "
            "normal input, the analogue of PRECOND-TOO-STRONG). Because the "
            "expected tree is named rather than written as "
            "`implementation_... applied to the same arguments`, the case pins "
            "the produced VALUE at this input and would fail if the modeled "
            "behavior computed a different tree there, instead of restating an "
            "instance of the `∀` obligation. Nothing is assumed: the theorem "
            "STATEMENT is byte-identical and no new declaration/axiom/`sorry` "
            "is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each carries (a) the refinement argument that its faithful
    # real patch would NOT resolve the F2P, so a verifying rival would be a true
    # verify-does-not-imply-resolve break rather than an artifact, and (b) a
    # refutation witness pinning the violation at one concrete input.
    # =====================================================================
    {
        "id": "weak-subs-prepatch-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_ROOT_IMPL),
        "refinement": (
            "this IS the pre-fix behavior on the subscript-only sub-domain: the "
            "top-level element stays the bare-name identifier element wrapping the "
            "subscript element as its single child, instead of being the "
            "subscript element itself. The F2P observable for a single-subscript "
            "symbol demands a subscript-element root with children [name, layout], "
            "but this yields an identifier-element root with a single "
            "subscript-element child — exactly the extra-wrapper regression the "
            "F2P catches. A real patch doing this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[]`, subs "
            "`[\"a\"]`, the spec's top-level element is the subscript element with "
            "children [name-element, single-string layout], but the rival's is the "
            "identifier element wrapping that subscript element. If it verifies, "
            "the spec does not pin the top-level element kind on the "
            "subscript-only branch (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("x", "[]", '["a"]', "plain", "  simp [joinPieces]\n"),
    },
    {
        "id": "weak-supers-prepatch-root",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_SUP_ROOT_IMPL),
        "refinement": (
            "the mirror of the case above on the superscript-only sub-domain: the "
            "top-level element stays the bare-name identifier element wrapping the "
            "superscript element as its single child, instead of being the "
            "superscript element itself. The F2P observable for a "
            "single-superscript symbol demands a superscript-element root with "
            "children [name, layout] — it reads the root's own element kind and "
            "then that root's direct children — but this yields an "
            "identifier-element root whose only child is the superscript element, "
            "so every one of those reads lands one level off. A real patch that "
            "removed the extra wrapper on the subscript branch only, leaving it "
            "here, would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[\"2\"]`, "
            "subs `[]`, the spec's top-level element is the superscript element "
            "with children [name-element, single-string layout], but the rival's "
            "is the identifier element wrapping that superscript element. This "
            "attacks the branch selector's OTHER single-decoration arm, which no "
            "other case in this battery varies: `weak-subs-prepatch-root` pins the "
            "subscript-only arm and the remaining rivals hit the both-empty, "
            "both-present, or layout sub-domains, all of which this rival gets "
            "right. If it verifies, the spec does not pin the top-level element "
            "kind on the superscript-only branch (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("x", '["2"]', "[]", "plain", "  simp [joinPieces]\n"),
    },
    {
        "id": "weak-layout-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LAYOUT_COLLAPSE_IMPL),
        "refinement": (
            "collapses the multi-string decoration layout to a single identifier "
            "element carrying the first string, dropping the row layout that "
            "several strings must produce. On a multi-part subscript the F2P "
            "observable demands a row element holding the separated identifier "
            "elements, but this yields a bare identifier element — a visibly "
            "different DOM subtree. A real patch doing this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[]`, subs "
            "`[\"1\",\"2\"]`, the spec's subscript child is the row layout of two "
            "strings, but the rival emits a single identifier element carrying "
            "only the first. Refuted on the multi-string sub-domain — varying the "
            "CONTENTS of `subs` — so the layout multiplicity is pinned, not just "
            "the branch. If it verifies, the spec does not pin the row-vs-single "
            "layout (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("y", "[]", '["1","2"]', "plain", "  simp [joinPieces, joinSep]\n"),
    },
    {
        "id": "weak-combined-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ORDER_SWAP_IMPL),
        "refinement": (
            "on the combined element the subscript and superscript layouts are "
            "placed in the wrong ordered slots (superscript first). The combined "
            "element is positional: the first decoration child is the subscript, "
            "the second the superscript. On a symbol whose two collections lay out "
            "to different subtrees (one single-string, one multi-string) this "
            "places the wrong subtree in each slot — a different ordered child "
            "list the F2P observable rejects. A real patch doing this would not "
            "resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[\"1\"]`, subs "
            "`[\"1\",\"2\"]`, the spec's combined children are [name, subs-layout "
            "(a row), supers-layout (a single element)], but the rival swaps the "
            "last two. Refuted where the two collections differ in shape, "
            "exercising the ordered child list with BOTH collections nonempty. If "
            "it verifies, the spec does not pin the child ORDER (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("z", '["1"]', '["1","2"]', "plain", "  simp [joinPieces, joinSep]\n"),
    },
    {
        "id": "weak-bold-drop-bare",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOLD_DROP_IMPL),
        "refinement": (
            "attaches the bold attribute only when there are superscripts or "
            "subscripts, silently dropping it on the bare-name element. A bold "
            "plain symbol (no decorations) would then lose its bold styling — the "
            "bold-on-root path the F2P observable exercises. A real patch doing "
            "this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[]`, subs "
            "`[]`, style `\"bold\"`, the spec attaches the bold attribute to the "
            "bare-name element, but the rival leaves it unattached. Refuted with "
            "style `\"bold\"` on the bare-name sub-domain — varying `style` and "
            "hitting the both-empty branch the other witnesses do not — so the "
            "bold attribute is pinned on EVERY element kind. If it verifies, the "
            "spec does not pin bold on the bare-name branch (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("w", "[]", "[]", "bold", "  simp [joinPieces, MathNode.setAttr]\n"),
    },
    {
        "id": "weak-bold-drop-combined",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BOLD_DROP_COMBINED_IMPL),
        "refinement": (
            "attaches the bold attribute on every arm except the combined one, "
            "where a symbol carrying BOTH a superscript and a subscript silently "
            "loses its bold styling. The bold request is a property of the whole "
            "rendered symbol, so the attribute belongs on whichever top-level "
            "element the decorations selected; an impl that special-cases the "
            "combined element renders a bold doubly-decorated symbol unbolded. A "
            "real patch doing this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[\"1\"]`, subs "
            "`[\"2\"]`, style `\"bold\"`, the spec attaches the bold attribute to the "
            "combined element, but the rival leaves that one arm unattached. This "
            "is the arm `weak-bold-drop-bare` does not reach: that case pins bold "
            "on the bare-name element only, so without this rival the battery's "
            "claim that bold is pinned on EVERY element kind rested on one arm. If "
            "it verifies, the spec does not pin bold on the combined branch "
            "(SPEC-TOO-WEAK)."
        ),
        "witness": _witness(
            "x", '["1"]', '["2"]', "bold",
            "  simp [joinPieces, joinSep, MathNode.setAttr]\n"),
    },
    {
        "id": "weak-layout-always-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ALWAYS_ROW_IMPL),
        "refinement": (
            "lays out EVERY decoration collection as a row element, so a "
            "single-string collection — which must render as a lone identifier "
            "element — is wrapped in a spurious row. The mirror of the collapse "
            "rival: same clause, opposite direction. A single-part subscript would "
            "gain a row wrapper the required markup does not have, a visibly "
            "different subtree. A real patch doing this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at supers `[]`, subs "
            "`[\"a\"]`, the spec's subscript child is a lone identifier element "
            "carrying `\"a\"`, but the rival emits a row element wrapping it. "
            "`weak-layout-collapse` attacks the row-vs-single boundary only from "
            "the many-to-one side; nothing in the battery rejected over-wrapping a "
            "single string, so the 'a single string becomes one identifier element' "
            "half of the layout clause was unattacked. If it verifies, the spec "
            "does not pin the single-string layout (SPEC-TOO-WEAK)."
        ),
        "witness": _witness(
            "x", "[]", '["a"]', "plain",
            "  simp [joinPieces, joinSep, MathNode.setAttr]\n"),
    },
    {
        "id": "weak-name-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NAME_DROP_IMPL),
        "refinement": (
            "the base identifier element carries the empty string instead of the "
            "actual base name, doing no work on the `name` input. Every rendered "
            "symbol would lose its base name text — a wrong DOM leaf the F2P "
            "observable rejects. A real patch doing this would not resolve."
        ),
        "rationale": (
            "REJECT from `result = buildSymbolMarkup ...`: at name `\"x\"`, supers "
            "`[]`, subs `[]`, the spec's result is the identifier element carrying "
            "the text `\"x\"`, but the rival's carries the empty string. Refuted by "
            "varying the `name` binder off the empty value, confirming the base "
            "name text is pinned. If it verifies, the spec does not pin the base "
            "name into the identifier element (SPEC-TOO-WEAK)."
        ),
        "witness": _witness("x", "[]", "[]", "plain", "  simp [joinPieces]\n"),
    },
]


# No consumed axioms and no deep-model references: the markup tree is modeled
# directly over the inputs (meta.json axioms == [], deep_model_references == []),
# so there is no in-model axiom obligation for the PBT axiom lane to re-discharge.
AXIOM_TESTS = []
