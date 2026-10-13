# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9602 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Every SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte — only the impl region
# (and, for a positive that must reprove, the proof body) is edited, so
# markers.same_spec holds by construction and every rejection is attributable to the
# postcondition rather than to a tampered spec. No case adds an axiom, a helper
# lemma, a `sorry`/`admit`/`native_decide`, or rewrites a `theorem correct_*`
# STATEMENT.
#
# Each expect="reject" case additionally carries a refutation `witness`: a
# self-contained snippet that ELABORATES against the rival and FAILS on the frozen
# solution. That is the part with no nagini counterpart. On a tactic-proof backend
# "the build failed" is NOT evidence of a spec violation — the frozen script is
# `intro …; rfl`, tuned to the frozen impl's syntactic form, and reshaping the impl
# breaks it whether the reshape is wrong or merely different. The witness is what
# separates the two.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read off Solution.lean / mapping.md / instance.json)
#
# ONE obligation: `theorem correct_literalTypeNodes`, over
#
#   implementation_literalTypeNodes (head : List Char) (values : List LitVal)
#       : List DocNode
#
# — the inline documentation nodes rendered for a parametrised type whose arguments
# are constant values. The single postcondition is an implication chain: under the
# two domain hypotheses (`okHead head` — the head is a dotted Python type name,
# which admits the enumeration heads AND every other dotted head; and every
# argument on the modeled domain `okLit`) the emitted sequence must be EXACTLY
# `expandLiteral head values`. That oracle is fully GROUNDED in the inputs — it
# unfolds to `wrap`/`valSeq`/`argNodeCtor`/`reprVal`, all transparent — so there is
# no opaque answer-key to echo, and building the sequence IS doing the work.
# Concretely it pins, position by position, node CLASS and node TEXT:
#
#   C1  the head is a navigable cross-reference node carrying `head`
#   C2  the argument list is framed by an opening and a CLOSING bracket
#       punctuation node
#   C3  under the enumeration head (`Literal` / `typing.Literal`) each constant
#       argument is PLAIN DISPLAY TEXT — never a cross-reference (such an argument
#       is a value, not a class, so it carries no navigable reference)
#   C4  each argument's display text is its canonical source representation:
#       None for the null constant, True/False for a boolean, the decimal digits
#       for an integer, and the single-quoted form (BOTH delimiters, the apostrophe
#       glyph) for a simple string — and NOT the quoted form for a boolean or
#       integer
#   C5  adjacent arguments are separated by a comma punctuation node
#   C6  under EVERY OTHER dotted head each argument node is a navigable
#       CROSS-REFERENCE, exactly as such a head's arguments have always been —
#       the plain-text rendering is what the enumeration head SELECTS, not a
#       uniform rule, so an implementation must READ the head to decide
#   C7  the ZERO-argument spelling `head[()]` is covered too: the argument region
#       is the empty tuple's own parenthesis pair, so the sequence is the head
#       cross-reference, `[`, `(`, `)`, `]` — the argument list is NOT assumed
#       non-empty, and an implementation may not abbreviate that shape
#
# The discriminating F2P behaviour (tests/test_domain_py.py::test_parse_annotation_Literal)
# reads the rendered sequence child by child, asserting the head is a cross-reference,
# the brackets and separators are punctuation, and each enumerated value is a bare
# string — "True"/"False"/"0"/"1" for the bool/int members and "'abc'" (with both
# apostrophes) for the string member. C6 is observed by the surrounding
# annotation tests (tests/test_domain_py.py::test_parse_annotation asserts the
# `None` argument of `List[None]` IS a cross-reference, and
# ::test_pyfunction_with_union_type_operator asserts the same of the trailing
# `None` in `int | None`), which a head-independent rendering regresses. So every
# clause above is directly observed by the graded assertions, which is what makes
# each rival below a real verify-does-not-imply-resolve break rather than an
# artifact.
#
# ---------------------------------------------------------------------------
# CARRIER NARROWING vs the nagini sibling
#
# The nagini sibling contracts TWO functions over an integer-code-point carrier: a
# per-value renderer (the quoting decision) and a node-kind pipeline (a wrap fold
# then a resolution fold, as two verified loops over read-only int lists). This
# bundle models the SAME two behaviours, but FUSED into one transparent list
# equation over `List DocNode`: the rendering policy lives in `reprVal` and the
# wrap-then-resolve outcome is already expressed as the node CLASS each position
# carries (`text` for a value vs `xref` for the head). So nagini's two obligations
# collapse into one here and its per-function case split has no counterpart — the
# port attacks CLAUSES of the single fused obligation instead. Case-count parity is
# not the target; clause and binder coverage is.
#
# NAGINI CASES AND WHERE THEY LANDED
#   * pos-control-rlv-branch-reorder, pos-control-rs-resolve-reorder (soundness)
#     -> pos-inline-frame and pos-imperative-accumulate. Two structurally different
#        CORRECT impls, each reproved honestly with the obligation STATEMENT
#        byte-identical. nagini's two branch-reorder controls were per-function; the
#        fused carrier gets one shape-preserving and one genuinely imperative shape.
#   * admiss-rlv-quote-fact + admiss-rs-pipeline-fact (admissibility)
#     -> admiss-domain-pins-rendered-sequence (merged: one obligation, so nagini's
#        two per-function admissibility hooks are the same hook here).
#   * partial-domain-never-wrap, partial-domain-lit-to-xref (a value becomes a
#     cross-reference) -> r1-value-as-xref. On the fused carrier "never wrapped"
#     and "unwrapped to a cross-reference" are the SAME observable: the value
#     position carries `xref` instead of `text`. nagini kept them distinct because
#     it modeled the two pipeline stages separately; here they collapse to one
#     rival, and shipping two would be two spellings of one refutation.
#   * partial-domain-name-not-xref (the head stops being a cross-reference)
#     -> r6-head-as-text.
#   * partial-domain-rlv-one-sided-quote -> r4-one-sided-quote.
#   * partial-domain-rlv-quote-nonstring -> r3-quote-every-value.
#   * uniqueness-rlv-wrong-quote-glyph  -> r5-wrong-quote-glyph.
#   * (no nagini counterpart, added for CLAUSE coverage this carrier exposes)
#     r2-unquoted-string (C4 from the other side), r7-no-separators (C5),
#     r8-missing-closing-bracket (C2), and — added by the independent audit —
#     r9-wrong-separator-text (C5's separator TEXT, which r7 leaves unattacked
#     because removing the separators is refuted by sequence LENGTH) and
#     r10-head-target-hardcoded (C1's reference TARGET, which r6 leaves unattacked
#     because it changes the head's node CLASS instead). r10 is also the only rival
#     whose refutation is driven by the HEAD binder.
#   * (no nagini counterpart, added for the head-SELECTION clause C6, whose binder
#     the nagini sibling does not model at all — its two functions are contracted at
#     the enumeration head only) r11-head-blind-plain-text (the selection dropped
#     entirely, plain text everywhere), r12-head-matched-by-last-segment (the
#     selection made too broad) and r13-enumeration-undotted-only (too narrow).
#     r11's witness is the only one that sits OUTSIDE the enumeration head, and r12's
#     and r13's are complements, so the three together pin the selection to exactly
#     the two enumeration names. r14-null-spelling covers C4 at the null constant,
#     the argument kind every other C4 rival agrees with the contract on.
#
# LANES THAT DO NOT PORT
#   * FRAME-MUTATION (nagini's MANDATORY class: both inputs were held read-only, so
#     a rival writing back was rejected for insufficient permission). Lean is
#     referentially transparent — no aliasing, no fractional permission — so a
#     "write a read-only input" rival is not EXPRESSIBLE here. DEMONSTRATED rather
#     than asserted: the closest expressible analogue is an impl that rebinds the
#     argument in a mutable local (`let mut vs := values; vs := vs`) and renders
#     from that; the audit built it and it VERIFIES with the frozen proof body
#     (exit 0), because the rebinding is a copy that cannot be observed by any
#     caller. So there is no rejection for the class to attribute to and no
#     observable for a witness to state — the class is genuinely VACUOUS on this
#     carrier, and no substitute is fabricated. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION. Genuinely vacuous on lean:
#     `implementation_literalTypeNodes` is a total Lean `def`, so a diverging
#     implementation cannot be written at all. (The velvet situation — a
#     partial-termination bundle admitting such a rival vacuously — is a known,
#     already-escalated spec hole recorded in the corpus-wide termination-semantics finding, whose
#     scope is velvet only; lean is unaffected. Nothing to ship either way. The
#     nagini sibling's termination measures have no counterpart to attack here.)
#   * AXIOM_TESTS. Dropped — the axiom lane is G-AX's job and this gate ignores it.
#     (meta.json axioms == []: nothing is axiomatized; the value rendering and the
#     whole node sequence are deep-model references validated out-of-band.)
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9602"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Both lie ENTIRELY inside the region they name and are unique in
# the file, so the manifest breaks loudly if the frozen solution ever changes.
# ---------------------------------------------------------------------------

# The whole impl definition (inside impl-start / impl-end). Every rival and every
# positive replaces exactly this.
_IMPL = """def implementation_literalTypeNodes
    (head : List Char) (values : List LitVal) : List DocNode :=
  let inner := valSeq (argNodeCtor head) reprVal values
  wrap head inner"""

# The frozen tactic body (inside proof-start / proof-end). Only a positive that
# needs to reprove its reshaped impl touches this; the `theorem
# correct_literalTypeNodes` STATEMENT above it is never edited.
_PROOF = """  intro head values
  unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
  intro _ _
  rfl"""

for _anchor, _what in ((_IMPL, "impl"), (_PROOF, "proof")):
    if _BASE.count(_anchor) != 1:
        raise AssertionError(f"{_what} anchor drifted")

_DEF_HEAD = """def implementation_literalTypeNodes
    (head : List Char) (values : List LitVal) : List DocNode :=
"""


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# P1 — INLINED FRAME. The frozen impl names the inner sequence and delegates the
# framing to `wrap`; this states the framed sequence directly, the way a patch that
# appended the head node, the opening bracket, the argument nodes and the closing
# bracket in place would. Behaviourally identical and definitionally equal, so the
# FROZEN proof body still closes it — the obligation is reproven, not weakened.
_POS_INLINE = _DEF_HEAD + """  DocNode.xref head :: DocNode.punct "[".toList ::
    (valSeq (argNodeCtor head) reprVal values ++ [DocNode.punct "]".toList])"""

# P2 — IMPERATIVE ACCUMULATION. A different SYNTACTIC shape: build the sequence by
# appending to a mutable accumulator (head node and opening bracket, then the
# argument nodes, then the closing bracket) instead of composing it functionally.
# This is the shape a faithful patch written imperatively takes.
#
# AUDIT NOTE (measured, not argued): this variant is still DEFINITIONALLY equal to
# the frozen impl — `Id.run do let mut … ; return` reduces away, and the appends
# reassociate by `rfl`. The frozen proof body closes it VERBATIM (built with
# `_PROOF` unchanged: exit 0). So the extra `wrap` unfold below is convenience, not
# necessity, and this case does NOT exercise "the spec accepts an impl that needs a
# real reproof". P3 is the control that does. Kept because the imperative surface
# shape is the one a patch actually takes, and a positive that stays inside `rfl`
# is still a genuine soundness control — it just proves less than P3.
_POS_IMPERATIVE = """def implementation_literalTypeNodes
    (head : List Char) (values : List LitVal) : List DocNode := Id.run do
  let mut out : List DocNode := [DocNode.xref head, DocNode.punct "[".toList]
  out := out ++ valSeq (argNodeCtor head) reprVal values
  out := out ++ [DocNode.punct "]".toList]
  return out"""
_POS_IMPERATIVE_PROOF = """  intro head values
  unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral wrap
  intro _ _
  rfl"""

# P3 — SEPARATOR-INTERLEAVING BY A LIBRARY COMBINATOR. The frozen impl interleaves
# the `", "` separators with its own front-recursion (`valSeq`); this maps the values
# to text nodes first and interleaves the separators with the standard list
# combinator. Behaviourally identical on every argument list, but only
# PROPOSITIONALLY so: the two recursions have different shapes, so no amount of
# unfolding closes the goal and `rfl` does not apply. The proof body therefore
# carries a real REPROOF — an induction on the argument list. The zero-argument
# spelling is stated as its own branch, because the library combinator produces
# nothing from an empty list while the argument region there is the empty tuple's
# parenthesis pair (C7); the interleaving claim is therefore proved for a
# non-empty list, which is exactly where it applies. This is the positive control
# that shows the spec accepts a correct
# impl on the strength of its BEHAVIOUR rather than its syntactic form; without it
# every positive in the battery stays inside the frozen `rfl` (see the audit note on
# P2) and SPEC-TOO-STRONG in its interesting form is untested. No lemma is added at
# the top level (the induction lives in a `have` inside the proof body) and the
# obligation STATEMENT is byte-identical.
_POS_INTERSPERSE = _DEF_HEAD + """  match values with
  | []      => wrap head [DocNode.punct "(".toList, DocNode.punct ")".toList]
  | v :: vs => wrap head (List.intersperse (DocNode.punct ", ".toList)
      ((v :: vs).map (fun x => argNodeCtor head (reprVal x))))"""
_POS_INTERSPERSE_PROOF = """  intro head values
  have key : ∀ (mk : List Char → DocNode) (vs : List LitVal) (v : LitVal),
      valSeq mk reprVal (v :: vs)
      = List.intersperse (DocNode.punct ", ".toList)
        ((v :: vs).map (fun x => mk (reprVal x))) := by
    intro mk vs
    induction vs with
    | nil => intro v; rfl
    | cons b bs ih =>
      intro v
      show mk (reprVal v) :: DocNode.punct ", ".toList
          :: valSeq mk reprVal (b :: bs)
        = List.intersperse (DocNode.punct ", ".toList)
            ((v :: b :: bs).map (fun x => mk (reprVal x)))
      rw [ih b]
      rfl
  unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
  intro _ _
  cases values with
  | nil       => rfl
  | cons v vs => rw [key]"""


# ===========================================================================
# ADMISSIBILITY — must VERIFY.
# ===========================================================================
# Before discharging the obligation gold-verbatim, PIN the contract at a
# documented-shape argument list (a mixed integer/integer/string enumeration): show
# the two domain hypotheses are jointly SATISFIABLE there (`okLit` holds of every
# argument, and `okHead` of BOTH an enumeration head and an ordinary dotted one)
# and that the contract's own value at those points is the fully spelled-out node
# sequence — head cross-reference, brackets, comma separators, and one argument
# node per value carrying its canonical source representation, PLAIN TEXT under the
# enumeration head and a CROSS-REFERENCE under the ordinary head. If any `decide`
# could not close, the domain would be unusable => PRECOND-TOO-STRONG. Pinning both
# heads is what keeps the head-dependence clause non-vacuous: it shows the contract
# genuinely admits, and distinguishes, both branches rather than only the one the
# frozen impl was written for.
# The returned value and the theorem STATEMENT are untouched; only `have`s are
# added inside the proof body (no new lemma, no new axiom).
_ADMISS_PROOF = """  intro head values
  -- The modeled domain admits a documented mixed enumeration...
  have _admits : [LitVal.int 0, LitVal.int 1, LitVal.str "abc".toList].all okLit
      = true := by decide
  -- ...under an enumeration head AND under an ordinary dotted head...
  have _admits_lit_head : okHead "typing.Literal".toList = true := by decide
  have _admits_plain_head : okHead "List".toList = true := by decide
  -- ...and the zero-argument spelling is admitted and pinned as well (C7).
  have _admits_empty : okHead "Tuple".toList = true := by decide
  have _admits_empty_args : ([] : List LitVal).all okLit = true := by decide
  have _pinned_empty : implementation_literalTypeNodes "Tuple".toList []
      = [DocNode.xref "Tuple".toList, DocNode.punct "[".toList,
         DocNode.punct "(".toList, DocNode.punct ")".toList,
         DocNode.punct "]".toList] := by decide
  -- ...and the contract pins its rendered sequence exactly, node class and
  -- display text, position by position, differently under the two heads.
  have _pinned : implementation_literalTypeNodes "typing.Literal".toList
      [LitVal.int 0, LitVal.int 1, LitVal.str "abc".toList]
      = [DocNode.xref "typing.Literal".toList, DocNode.punct "[".toList,
         DocNode.text "0".toList, DocNode.punct ", ".toList,
         DocNode.text "1".toList, DocNode.punct ", ".toList,
         DocNode.text "'abc'".toList, DocNode.punct "]".toList] := by decide
  have _pinned_plain : implementation_literalTypeNodes "List".toList
      [LitVal.int 0, LitVal.null]
      = [DocNode.xref "List".toList, DocNode.punct "[".toList,
         DocNode.xref "0".toList, DocNode.punct ", ".toList,
         DocNode.xref "None".toList, DocNode.punct "]".toList] := by decide
  unfold problem_spec_literalTypeNodes implementation_literalTypeNodes expandLiteral
  intro _ _
  rfl"""


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK.
# ===========================================================================

# R1 — every argument rendered as a navigable cross-reference instead of plain
# display text. Attacks C3. (Fuses nagini's two pipeline-stage rivals: on this
# carrier "never marked as a value" and "resolved to a cross-reference" are the same
# observable.)
_R1_VALUE_XREF = _DEF_HEAD + """  let inner := valSeq DocNode.xref reprVal values
  wrap head inner"""

# R2 — a string argument shown WITHOUT its delimiters (its bare characters), every
# other kind unchanged. Attacks C4 from the "no quotes at all" side.
_R2_UNQUOTED_STRING = _DEF_HEAD + """  let render : LitVal → List Char := fun v =>
    match v with
    | .str s => s
    | _      => reprVal v
  wrap head (valSeq (argNodeCtor head) render values)"""

# R3 — the delimiters applied to EVERY argument, not just to strings: the canonical
# over-application of string quoting, which would show a boolean or an integer
# delimited. Attacks C4 from the "quotes everywhere" side. Correct on strings,
# wrong on every boolean and integer — so it is refuted at a BOOLEAN point, where
# R2/R4/R5 all agree with the contract.
_R3_QUOTE_EVERY = _DEF_HEAD + """  let render : LitVal → List Char := fun v => '\\'' :: (reprVal v ++ ['\\''])
  wrap head (valSeq (argNodeCtor head) render values)"""

# R4 — a string argument shown with only its LEADING delimiter. Attacks C4: the
# closing delimiter is part of the display text.
_R4_ONE_SIDED = _DEF_HEAD + """  let render : LitVal → List Char := fun v =>
    match v with
    | .str s => '\\'' :: s
    | _      => reprVal v
  wrap head (valSeq (argNodeCtor head) render values)"""

# R5 — a string argument delimited with the WRONG glyph (the double-quote instead
# of the apostrophe). A plausible "use quotes" slip. Attacks C4's glyph.
_R5_WRONG_GLYPH = _DEF_HEAD + """  let render : LitVal → List Char := fun v =>
    match v with
    | .str s => '"' :: (s ++ ['"'])
    | _      => reprVal v
  wrap head (valSeq (argNodeCtor head) render values)"""

# R6 — the HEAD emitted as plain display text instead of a navigable
# cross-reference. Attacks C1 (the mirror image of R1: the position that MUST carry
# a reference loses it). This is the clause that keeps a parametrised type's head
# navigable while its constant arguments are not.
_R6_HEAD_TEXT = _DEF_HEAD + """  DocNode.text head :: DocNode.punct "[".toList ::
    (valSeq (argNodeCtor head) reprVal values ++ [DocNode.punct "]".toList])"""

# R7 — the arguments emitted back to back with NO separator punctuation between
# them. Attacks C5. Agrees with the contract on any single-argument list, so it is
# refuted at a MULTI-argument point.
_R7_NO_SEPARATORS = _DEF_HEAD + """  wrap head (values.map (fun v => argNodeCtor head (reprVal v)))"""

# R8 — the closing bracket omitted, so the argument list is left unclosed. Attacks
# C2 (and the length of the emitted sequence).
_R8_NO_CLOSING = _DEF_HEAD + """  DocNode.xref head :: DocNode.punct "[".toList :: valSeq (argNodeCtor head) reprVal values"""

# R9 — the separator node carries the WRONG TEXT: a bare comma with no following
# space. Attacks C5's separator TEXT, where R7 only attacks its PRESENCE — a rival
# that emits a separator of the wrong text passes every "is there a punctuation node
# between the members" check while still rendering the annotation differently, so
# the two are distinct clause facets and R7's witness does not cover this one.
# Agrees with the contract on any single-argument list, so it is refuted at a
# multi-argument point.
_R9_WRONG_SEPARATOR = _DEF_HEAD + """  wrap head (valSeq (argNodeCtor head) reprVal values
    |>.map (fun n => if n = DocNode.punct ", ".toList then DocNode.punct ",".toList else n))"""

# R10 — the head cross-reference target HARD-CODED to one of the two admitted heads
# instead of the bound argument. Attacks C1's TARGET, where R6 only attacks its node
# CLASS: this rival keeps position 0 a navigable cross-reference (so every
# "the head is a reference" check still passes) but points it at the wrong name
# whenever the other admitted head is in play. That makes it the only rival whose
# refutation is driven by the HEAD binder rather than by the argument list — it
# agrees with the contract on the whole `Literal` half of the head domain and is
# refuted on the `typing.Literal` half.
_R10_HEAD_HARDCODED = _DEF_HEAD + """  DocNode.xref "Literal".toList :: DocNode.punct "[".toList ::
    (valSeq (argNodeCtor head) reprVal values ++ [DocNode.punct "]".toList])"""

# R11 — the argument node class chosen UNIFORMLY as plain display text, with the
# head never read. Attacks C6: it is right on the enumeration head and silently
# strips the navigable reference from every constant argument of every OTHER
# parametrised type. This is the "suppress references inside brackets everywhere"
# over-reach, and the one facet no other rival reaches — R1 is its mirror (uniform
# references, wrong on the enumeration head) and both are head-BLIND, which is the
# property the contract forbids.
_R11_HEAD_BLIND_TEXT = _DEF_HEAD + """  wrap head (valSeq DocNode.text reprVal values)"""

# R12 — the enumeration head recognised by its LAST DOTTED SEGMENT rather than by
# the whole name, so any module path ending in that segment also gets plain text.
# Attacks C6 from the over-broad side: it agrees with the contract on BOTH admitted
# enumeration heads and on every head whose last segment differs, and diverges only
# on an aliased import path.
_R12_SUFFIX_HEAD = _DEF_HEAD + """  let ctor := if (headSegments head).getLast? = some "Literal".toList
             then DocNode.text else DocNode.xref
  wrap head (valSeq ctor reprVal values)"""

# R13 — the enumeration recognised only in its UNDOTTED spelling, so the qualified
# spelling keeps the cross-reference rendering. Attacks C3's head coverage (and C6's
# boundary) from the under-broad side: half the enumeration domain is still handled
# by the pre-change path.
_R13_UNDOTTED_ONLY = _DEF_HEAD + """  let ctor := if head = "Literal".toList then DocNode.text else DocNode.xref
  wrap head (valSeq ctor reprVal values)"""

# R14 — the NULL constant rendered as a lower-case spelling instead of its canonical
# source representation. Attacks C4 at the argument kind the surrounding annotation
# tests exercise, which no other C4 rival touches (R2/R4/R5 are string-only, R3 is
# refuted at a boolean).
_R14_NULL_SPELLING = _DEF_HEAD + """  let render : LitVal → List Char := fun v =>
    match v with
    | .null => "null".toList
    | _     => reprVal v
  wrap head (valSeq (argNodeCtor head) render values)"""


# R15 — the ZERO-argument spelling ABBREVIATED to the head cross-reference alone,
# with the whole bracket region dropped. Attacks C7, the clause no other rival
# reaches: every other rival here is refuted somewhere on a NON-empty argument
# list, and this one agrees with the contract on all of those, diverging only at
# the empty tuple. That is also the one shape whose freedom is invisible to a
# reading of the enumeration behaviour, which is why it gets its own rival.
_R15_EMPTY_ABBREVIATED = _DEF_HEAD + """  if values.isEmpty then [DocNode.xref head]
  else wrap head (valSeq (argNodeCtor head) reprVal values)"""


def _wit(head, values):
    """A refutation witness at one CONCRETE input.

    States `¬ problem_spec_literalTypeNodes head values (implementation … head
    values)` directly: discharge the two domain hypotheses by `decide` (they hold
    at this input — the point is a real one, and the head binds NOTHING, so there
    are no assumptions that could be inconsistent), then `decide` the resulting
    value equation. Elaborates against a rival whose sequence diverges from the
    contract here, and FAILS on the frozen solution, which satisfies the contract
    at every input.
    """
    args = f"{head} {values}"
    return (
        f"example : ¬ problem_spec_literalTypeNodes {args}\n"
        f"    (implementation_literalTypeNodes {args}) := by\n"
        f"  intro hspec\n"
        f"  exact absurd (hspec (by decide) (by decide)) (by decide)"
    )


SPEC_TESTS = [

    # ---------------------------------------------------------------- positives
    {
        "id": "pos-inline-frame",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS_INLINE),
        "rationale": (
            "CORRECT structural variant: the frozen impl names the inner argument "
            "sequence and delegates the framing; this states the framed sequence "
            "directly (head cross-reference, opening bracket, argument nodes, "
            "closing bracket), which is a shape a faithful patch could equally "
            "take. Every clause C1–C5 is still satisfied, so the FROZEN proof body "
            "closes it unchanged and the `theorem correct_literalTypeNodes` "
            "STATEMENT is byte-identical. If it FAILS => SPEC-TOO-STRONG (a "
            "faithful, structurally different correct impl rejected)."
        ),
    },
    {
        "id": "pos-imperative-accumulate",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL, _POS_IMPERATIVE), _PROOF, _POS_IMPERATIVE_PROOF),
        "rationale": (
            "CORRECT variant with a genuinely different SHAPE: the sequence is built "
            "by appending to a mutable accumulator rather than composed "
            "functionally — the shape an imperatively written patch takes. The "
            "frozen `rfl` no longer applies through the accumulation, so the proof "
            "body is REPROVEN (the framing is additionally unfolded); no lemma is "
            "added, nothing is assumed, and the obligation STATEMENT is unchanged. "
            "This is the control that shows the spec accepts a reshaped correct "
            "impl and not merely the frozen syntax. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-intersperse-separators",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL, _POS_INTERSPERSE),
            _PROOF, _POS_INTERSPERSE_PROOF),
        "rationale": (
            "CORRECT variant that is only PROPOSITIONALLY equal to the frozen impl, "
            "not definitionally: the separators are interleaved by the standard list "
            "combinator instead of by the contract's own front-recursion, so the two "
            "recursions have different shapes, no unfolding closes the goal, and the "
            "frozen `rfl` does NOT apply. The proof body carries a real REPROOF (an "
            "induction on the argument list, inside a `have` — no top-level lemma, no "
            "axiom, obligation STATEMENT byte-identical). This is the control that "
            "shows the spec accepts a correct impl on the strength of its BEHAVIOUR "
            "rather than its syntactic form; the other two positives are both "
            "closable by the frozen tactic body and so cannot show that. If it FAILS "
            "=> SPEC-TOO-STRONG."
        ),
    },

    # ------------------------------------------------------------ admissibility
    {
        "id": "admiss-domain-pins-rendered-sequence",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF, _ADMISS_PROOF),
        "rationale": (
            "PORT of nagini's two per-function admissibility hooks, merged (one "
            "obligation here). The returned value is gold-verbatim; the proof body "
            "first pins that the two domain hypotheses are jointly SATISFIABLE at "
            "a documented mixed enumeration (two integers and a simple string, all "
            "`okLit`) and that the contract's value there is the fully spelled-out "
            "sequence — head cross-reference, brackets, comma separators, one plain "
            "text node per value carrying its canonical source representation — and "
            "that the ZERO-argument spelling is admitted and pinned to the head "
            "reference framed around the empty tuple's parenthesis pair (C7). If "
            "either `decide` could not close, the domain would be unusable => "
            "PRECOND-TOO-STRONG. No new lemma or axiom; only `have`s inside the "
            "proof body, obligation STATEMENT byte-identical."
        ),
    },

    # ---------------------------------------------------------------- uniqueness
    {
        "id": "r1-value-as-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R1_VALUE_XREF),
        "refinement": (
            "this IS the pre-change behaviour, and the issue itself: each enumerated "
            "constant is turned into a navigable class reference, so a boolean "
            "member is reported as a missing class and a strict documentation build "
            "fails. Its faithful real counterpart is the unpatched renderer. The F2P "
            "test asserts each enumerated member is a BARE string in the rendered "
            "sequence, not a cross-reference node; a rival that emits references "
            "there fails exactly those assertions, so it does NOT resolve — a "
            "verifying rival here would be a true verify-does-not-imply-resolve "
            "break. (Fuses nagini's partial-domain-never-wrap and "
            "partial-domain-lit-to-xref: on this carrier both surface as the value "
            "position carrying a reference instead of plain text.)"
        ),
        "rationale": (
            "REJECTED by C3 (each constant argument is PLAIN DISPLAY TEXT, never a "
            "cross-reference): the contract pins `DocNode.text (reprVal v)` at every "
            "argument position, the rival puts `DocNode.xref` there. Refuted at a "
            "two-boolean enumeration under the `Literal` head. If it VERIFIES => "
            "SPEC-TOO-WEAK on the node-class clause — the very clause the issue is "
            "about."
        ),
        # head="Literal", values=[bool true, bool false]  (the issue's own shape):
        # contract => text "True", text "False"; rival => xref "True", xref "False".
        "witness": _wit('"Literal".toList', "[LitVal.bool true, LitVal.bool false]"),
    },
    {
        "id": "r2-unquoted-string",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R2_UNQUOTED_STRING),
        "refinement": (
            "a patch that showed a string constant by its bare characters rather "
            "than its canonical source form renders the string member as `abc`. The "
            "F2P test asserts that member's text is `'abc'` — WITH both delimiters — "
            "so the assertion fails and it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C4 (a simple string's display text is its single-quoted "
            "form): the contract pins `reprVal (.str s) = '\\'' :: s ++ ['\\'']`, the "
            "rival pins `s`. Correct on booleans and integers, wrong on every "
            "string, so it is refuted at a STRING argument (under the "
            "`typing.Literal` head)."
        ),
        # head="typing.Literal", values=[str "abc"]:
        # contract => text "'abc'"; rival => text "abc".
        "witness": _wit('"typing.Literal".toList', '[LitVal.str "abc".toList]'),
    },
    {
        "id": "r3-quote-every-value",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R3_QUOTE_EVERY),
        "refinement": (
            "the canonical over-application of string delimiting: a patch that "
            "delimited EVERY constant, not just strings, renders the boolean and "
            "integer members as `'True'`/`'False'`/`'0'`/`'1'`. The F2P test asserts "
            "those members are the bare strings `True`/`False`/`0`/`1`, so it fails "
            "them and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C4 from the other side (a boolean shows as True/False and "
            "an integer as its bare decimal digits — no delimiters): the rival wraps "
            "every argument's text in apostrophes. Refuted at a BOOLEAN point, which "
            "is where R2/R4/R5 all AGREE with the contract, so this witness reaches a "
            "sub-domain none of theirs does. (The converse does not hold and is not "
            "claimed: this rival diverges on every argument kind, so R1's boolean "
            "witness also refutes it — measured. What the boolean point buys is that "
            "the C4-over-application clause is attacked where the C4-under-"
            "application rivals are silent.)"
        ),
        # head="Literal", values=[bool true]:
        # contract => text "True"; rival => text "'True'".
        "witness": _wit('"Literal".toList', "[LitVal.bool true]"),
    },
    {
        "id": "r4-one-sided-quote",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R4_ONE_SIDED),
        "refinement": (
            "a patch that emitted only the LEADING delimiter renders the string "
            "member as `'abc` instead of `'abc'`. The F2P test compares that text "
            "exactly, so the assertion fails and it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C4 (BOTH delimiters are part of a string's display text): "
            "the trailing apostrophe is absent. A NEAR-MISS of R2/R5 in the sense "
            "that it renders the same argument KIND wrongly for a different reason "
            "(a missing trailing delimiter, vs no delimiters at all in R2 and the "
            "wrong glyph in R5); it is given its own string point (a distinct string "
            "content, under the other head) so each near-miss is refuted at an input "
            "of its own. Note the witnesses are NOT mutually exclusive: any string "
            "argument diverges for all three rivals, so R2's/R4's/R5's witnesses each "
            "also refute the other two rivals (measured). What distinguishes these "
            "three cases is the RIVAL, not the witness point."
        ),
        # head="typing.Literal", values=[str "xy"]:
        # contract => text "'xy'"; rival => text "'xy".
        "witness": _wit('"typing.Literal".toList', '[LitVal.str "xy".toList]'),
    },
    {
        "id": "r5-wrong-quote-glyph",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R5_WRONG_GLYPH),
        "refinement": (
            "the canonical source form of a short simple string uses the APOSTROPHE, "
            "not the double quote. A patch that framed the value in double quotes "
            "renders the string member as `\"abc\"`; the F2P test asserts the exact "
            "text `'abc'`, so it fails and does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C4's glyph: the contract pins the apostrophe (U+0027) as "
            "the delimiter, the rival uses the double quote (U+0022). Refuted at the "
            "same string content as R2 but under the OTHER head, so the head binder "
            "varies across the string-clause rivals. The two rivals fail for "
            "different reasons (no delimiter vs the wrong delimiter), but their "
            "witness POINTS are interchangeable — every string argument diverges for "
            "both, and each witness was measured to refute the other's rival too. "
            "The distinct point is for binder coverage, not because either "
            "sub-domain is out of the other's reach."
        ),
        # head="Literal", values=[str "abc"]:
        # contract => text "'abc'"; rival => text "\"abc\"".
        "witness": _wit('"Literal".toList', '[LitVal.str "abc".toList]'),
    },
    {
        "id": "r6-head-as-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R6_HEAD_TEXT),
        "refinement": (
            "the mirror-image over-correction: a patch that stopped emitting a "
            "navigable reference for the parametrised type's HEAD (while correctly "
            "leaving the constant arguments as plain text) renders the head as bare "
            "text. The F2P test asserts the first child IS a cross-reference node "
            "carrying `Literal` / `typing.Literal`, and the surrounding annotation "
            "tests assert ordinary type names stay navigable, so it fails them and "
            "does NOT resolve. This is the over-shoot a naive fix for the issue "
            "invites — suppressing references everywhere inside the brackets."
        ),
        "rationale": (
            "REJECTED by C1 (the head is a navigable cross-reference node): the "
            "contract pins `DocNode.xref head` at position 0, the rival puts "
            "`DocNode.text head`. If it VERIFIES => SPEC-TOO-WEAK on the head "
            "clause, i.e. the spec would not notice a fix that killed ALL references "
            "rather than only the constants'."
        ),
        # head="typing.Literal", values=[int 0]:
        # contract => xref "typing.Literal" first; rival => text "typing.Literal".
        "witness": _wit('"typing.Literal".toList', "[LitVal.int 0]"),
    },
    {
        "id": "r7-no-separators",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R7_NO_SEPARATORS),
        "refinement": (
            "a patch that emitted the argument nodes without the separator "
            "punctuation between them renders a multi-argument enumeration as its "
            "values run together, with no `, ` nodes. The F2P test reads the "
            "sequence child by child and asserts a punctuation node between "
            "consecutive members, so those positions do not line up and it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by C5 (adjacent arguments are separated by a comma "
            "punctuation node) and the resulting sequence length: `valSeq` "
            "interleaves separators, the rival maps straight over the values. It "
            "AGREES with the contract on every single-argument list, so it is "
            "refuted at a THREE-argument mixed enumeration — the input shape the "
            "F2P test itself uses."
        ),
        # head="typing.Literal", values=[int 0, int 1, str "abc"]:
        # contract => 8 nodes with two ", " separators; rival => 5 nodes, none.
        "witness": _wit('"typing.Literal".toList',
                        '[LitVal.int 0, LitVal.int 1, LitVal.str "abc".toList]'),
    },
    {
        "id": "r8-missing-closing-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R8_NO_CLOSING),
        "refinement": (
            "a patch that framed the argument list on the opening side only leaves "
            "the rendered annotation unclosed. The F2P test asserts a final closing "
            "punctuation child, which is simply absent, so it fails and does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by C2 (the argument list is framed by an opening AND a closing "
            "bracket punctuation node): the contract's `wrap` appends the closing "
            "node, the rival omits it, so the emitted sequence is one node short at "
            "the end. Refuted at a single-integer enumeration under the `Literal` "
            "head — the smallest point at which the framing clause alone is at "
            "stake, and an integer value distinct from every other witness's."
        ),
        # head="Literal", values=[int 7]:
        # contract => [..., text "7", punct "]"]; rival => [..., text "7"].
        "witness": _wit('"Literal".toList', "[LitVal.int 7]"),
    },
    {
        "id": "r9-wrong-separator-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R9_WRONG_SEPARATOR),
        "refinement": (
            "a patch that separated the arguments with a bare comma and no following "
            "space renders a multi-argument enumeration with its members run up "
            "against the commas. The F2P test compares each separator child's text "
            "against `, ` exactly — space included — so the assertion fails and it "
            "does NOT resolve. Distinct from the no-separator case: here a separator "
            "node IS present at every expected position and carries the right node "
            "class, so only its text is wrong."
        ),
        "rationale": (
            "REJECTED by C5's separator TEXT: the contract pins "
            "`DocNode.punct \", \"` between adjacent arguments, the rival emits "
            "`DocNode.punct \",\"`. This is the clause facet R7 leaves unattacked — "
            "R7 removes the separators, so it is refuted by the sequence LENGTH and "
            "would not notice a separator of the wrong text at the right position. "
            "Agrees with the contract on every single-argument list, so it is refuted "
            "at a TWO-argument integer enumeration."
        ),
        # head="Literal", values=[int 0, int 1]:
        # contract => punct ", " between the members; rival => punct ",".
        "witness": _wit('"Literal".toList', "[LitVal.int 0, LitVal.int 1]"),
    },
    {
        "id": "r10-head-target-hardcoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R10_HEAD_HARDCODED),
        "refinement": (
            "a patch that emitted a fixed name as the parametrised type's reference "
            "target instead of the head it actually read renders the dotted spelling "
            "of the annotation with the undotted target. The F2P test asserts the "
            "first child is a cross-reference carrying `typing.Literal` for the "
            "dotted annotation, so the assertion fails and it does NOT resolve — "
            "while the undotted annotation still passes, which is what makes this a "
            "half-domain break rather than an obvious one."
        ),
        "rationale": (
            "REJECTED by C1's TARGET: the contract pins `DocNode.xref head` — the "
            "reference target is the head that was READ — and the rival pins a "
            "constant. This is the clause facet R6 leaves unattacked: R6 changes the "
            "head's node CLASS (text instead of a reference), so a rival that keeps "
            "the reference but points it at the wrong name passes every check R6's "
            "witness makes. It is also the only rival refuted by the HEAD binder "
            "rather than by the argument list: it agrees with the contract on the "
            "entire `Literal` half of the admitted head domain, so it is refuted "
            "under `typing.Literal`. If it VERIFIES => SPEC-TOO-WEAK on the head "
            "target, i.e. the spec would not pin the reference to the observed head."
        ),
        # head="typing.Literal", values=[int 0]:
        # contract => xref "typing.Literal"; rival => xref "Literal".
        "witness": _wit('"typing.Literal".toList', "[LitVal.int 0]"),
    },
    {
        "id": "r11-head-blind-plain-text",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R11_HEAD_BLIND_TEXT),
        "refinement": (
            "a change that made every constant argument plain display text without "
            "consulting the head renders `List[None]` with its `None` argument as "
            "bare text, and the trailing `None` of a union annotation likewise. Those "
            "arguments are asserted to be navigable cross-reference nodes by "
            "tests/test_domain_py.py::test_parse_annotation and "
            "::test_pyfunction_with_union_type_operator, so both fail and it does NOT "
            "resolve — even though the enumeration test it was aimed at passes. This "
            "is the single most likely over-reach: the enumeration behaviour read as "
            "a uniform rule instead of a head-selected one."
        ),
        "rationale": (
            "REJECTED by C6 (under every other dotted head each argument node is a "
            "navigable CROSS-REFERENCE): the contract pins `argNodeCtor head`, which "
            "is `DocNode.text` only on the enumeration head, and the rival pins "
            "`DocNode.text` everywhere. Refuted at the null constant under an "
            "ordinary container head — a point that lies OUTSIDE every other rival's "
            "witness, all of which sit on the enumeration head. If it VERIFIES => "
            "SPEC-TOO-WEAK on the head-selection clause, i.e. the spec would not "
            "notice a change that regressed every non-enumerated annotation."
        ),
        # head="List", values=[null]:
        # contract => xref "None"; rival => text "None".
        "witness": _wit('"List".toList', "[LitVal.null]"),
    },
    {
        "id": "r12-head-matched-by-last-segment",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R12_SUFFIX_HEAD),
        "refinement": (
            "a change that recognised the enumeration by the trailing component of "
            "the dotted name would also strip the references from the arguments of "
            "any other module's same-named parametrised type reached through an "
            "aliased import. The rendered sequence for such a head is asserted to "
            "carry cross-reference arguments by the surrounding annotation tests, so "
            "it does NOT resolve. It is a HALF-domain break: both spellings the issue "
            "names still render correctly."
        ),
        "rationale": (
            "REJECTED by C6 on the over-broad side: the contract's selection is "
            "equality against the two whole names, the rival's is a suffix match. It "
            "agrees with the contract on BOTH enumeration heads and on every head "
            "whose last segment is something else, so it is refuted at an aliased "
            "dotted head — a sub-domain neither R11 (uniform text) nor R13 (undotted "
            "only) reaches. If it VERIFIES => SPEC-TOO-WEAK on WHICH heads select the "
            "plain rendering."
        ),
        # head="t.Literal", values=[int 0]:
        # contract => xref "0"; rival => text "0".
        "witness": _wit('"t.Literal".toList', "[LitVal.int 0]"),
    },
    {
        "id": "r13-enumeration-undotted-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R13_UNDOTTED_ONLY),
        "refinement": (
            "a change applied only to the bare spelling of the enumeration leaves the "
            "qualified spelling on the pre-change path, so its members are still "
            "reported as missing classes — exactly the complaint in the issue, which "
            "names the qualified spelling too. The F2P test asserts the qualified "
            "annotation's members are bare strings, so it fails and it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by C3 across the WHOLE enumeration head domain (and C6's "
            "boundary from the under-broad side): the rival selects plain text for one "
            "spelling only. It agrees with the contract on the undotted enumeration "
            "head AND on every non-enumeration head, so it is refuted under the "
            "qualified enumeration head — the complement of R12's witness, which is "
            "why the two together pin the selection to exactly the two names."
        ),
        # head="typing.Literal", values=[bool true]:
        # contract => text "True"; rival => xref "True".
        "witness": _wit('"typing.Literal".toList', "[LitVal.bool true]"),
    },
    {
        "id": "r14-null-spelling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R14_NULL_SPELLING),
        "refinement": (
            "a change that spelled the null constant in lower case renders that "
            "argument's text as `null`. The annotation tests compare that argument's "
            "text against `None` exactly, so the assertion fails and it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by C4 at the NULL constant: the contract pins `None` as its "
            "canonical source representation. This is the argument kind no other C4 "
            "rival attacks — R2/R4/R5 diverge only on strings and R3 is refuted at a "
            "boolean, so all three AGREE with the contract at a null argument. "
            "Refuted at a single null under the enumeration head."
        ),
        # head="Literal", values=[null]:
        # contract => text "None"; rival => text "null".
        "witness": _wit('"Literal".toList', "[LitVal.null]"),
    },
    {
        "id": "r15-empty-argument-abbreviated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _R15_EMPTY_ABBREVIATED),
        "refinement": (
            "a change that emitted only the head reference when the argument list "
            "has no elements renders the zero-argument annotation `Tuple[()]` as a "
            "lone cross-reference, with no brackets and no parenthesis pair. "
            "tests/test_domain_py.py::test_parse_annotation reads that annotation's "
            "rendered children and asserts the five-node sequence — reference, `[`, "
            "`(`, `)`, `]` — so the assertion fails and it does NOT resolve, even "
            "though the enumeration behaviour it was aimed at is untouched."
        ),
        "rationale": (
            "REJECTED by C7 (the zero-argument spelling is covered, and its "
            "argument region is the empty tuple's parenthesis pair): the contract "
            "pins `wrap head (valSeq … [])`, a five-node sequence, and the rival "
            "emits one node. It AGREES with the contract on every non-empty "
            "argument list, so it is refuted at the empty one — a sub-domain no "
            "other rival in this battery reaches. If it VERIFIES => SPEC-TOO-WEAK "
            "on the argument-list domain, i.e. the contract would impose no "
            "obligation at all on a shape the graded suite observes."
        ),
        # head="Tuple", values=[]:
        # contract => 5 nodes (xref, "[", "(", ")", "]"); rival => 1 node.
        "witness": _wit('"Tuple".toList', "([] : List LitVal)"),
    },
]


# ===========================================================================
# AXIOM_TESTS — dropped by design (the axiom lane is G-AX's job; this gate
# ignores it). The bundle declares no axiom and no opaque callee: the value
# rendering and the whole emitted node sequence are modeled DEEPLY as transparent
# definitions, which is also why every witness above closes by `decide` rather
# than having to condition on an opaque term.
# ===========================================================================
AXIOM_TESTS = []
