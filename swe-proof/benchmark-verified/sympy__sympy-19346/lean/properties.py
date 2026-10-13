# properties.py — G-PBT falsification battery for sympy__sympy-19346 (lean).
# NOT a Lean file; a record of adversarially-reasoned cases. Each `module` is
# written to a temp Solution.lean and checked with the Lean verifier +
# markers.same_spec + variant_scope; each reject case's `witness` is checked in a
# copy with the frozen obligations removed, and must elaborate against the RIVAL
# while FAILING against the frozen solution.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read from Solution.lean / mapping.md / refinement.md)
# ---------------------------------------------------------------------------
# Two modeled obligations, each a total pure function of one list input:
#
#   theorem correct_dictRepr : ∀ entries, problem_spec_dictRepr entries
#                                          (implementation_dictRepr entries)
#     spec:  result = "{" ++ String.intercalate ", " (entries.map entryText)
#                         ++ "}"
#     where entryText p = elemRepr p.1 ++ ": " ++ elemRepr p.2
#     binder: `entries : List (SymExpr × SymExpr)`  (no precondition)
#
#   theorem correct_setRepr : ∀ elems, problem_spec_setRepr elems
#                                        (implementation_setRepr elems)
#     spec:  result = if elems.isEmpty then "set()"
#                     else "{" ++ String.intercalate ", " (elems.map elemRepr)
#                              ++ "}"
#     binder: `elems : List SymExpr`  (no precondition)
#
# The load-bearing content of both clauses is a STRUCTURAL string identity, and
# it decomposes into four independently attackable sub-claims:
#
#   (C1) every contained value is threaded through the canonical recursive
#        renderer `elemRepr` — never through the alternative textual conversion
#        `nativeRepr`. This is the discriminating clause: it holds at EVERY
#        position of EVERY entry / element, so a rival wrong at only one
#        position is still refutable.
#   (C2) within a mapping entry the key's rendering precedes `": "` precedes the
#        value's rendering — the two positions are NOT interchangeable.
#   (C3) consecutive renderings are separated by exactly `", "`.
#   (C4) the empty input's rendering: `"{}"` for a mapping, the dedicated
#        `"set()"` for an unordered collection. These are DIFFERENT literals for
#        the two obligations, and each is pinned by its own spec. The enclosing
#        delimiter pair of the NON-empty rendering is a separate point from
#        either empty literal and is attacked separately.
#   (C5) the POSITIONAL CORRESPONDENCE between the input list and the emitted
#        sequence: each clause maps over its input and intercalates the result,
#        so the i-th rendered piece is the i-th input's rendering. Independent of
#        (C1)-(C4) — a rival can satisfy every one of them and still emit the
#        right pieces in the wrong sequence, at exactly the same total length.
#        Attacked by reverse-entries-dict / reverse-elems-set, and observable
#        only at a TWO-piece input.
#
# Each of (C2)/(C3)/(C4-frame) has TWO independently attackable faces, because a
# rival can get the literal's LENGTH wrong or get its CHARACTERS wrong while
# keeping the length. The two faces need different refutations — a character
# count settles the first and cannot see the second at all — so both are
# attacked separately below (`*-literal-dict` vs the length-based rivals).
#
# ---------------------------------------------------------------------------
# MEASURED GRADING SURFACE (this instance's two shapes are NOT graded alike)
# ---------------------------------------------------------------------------
# The two modeled obligations do NOT sit on the same graded footing, and the
# difference was measured rather than assumed, by running the real graded suite
# at `base_commit` in a scratch checkout against three implementations:
#   * gold-faithful on both shapes                     -> all graded names pass
#   * gold-faithful on the MAPPING, wrong on the
#     COLLECTION (wrong delimiters + wrong empty
#     literal)                                         -> all graded names pass
#   * gold-faithful on the COLLECTION, wrong on the
#     MAPPING                                          -> a graded name FAILS
# A fourth probe, in which the collection shape's renderer raised
# unconditionally, also passed every graded name. Cause: the collection shape's
# test is named in NEITHER graded list for this instance, and the grader consults
# only the names in those two lists, so nothing it runs ever observes the
# collection rendering.
#
# Consequence for THIS battery, and it is a real limit on what a collection-side
# rejection attests to: for a mapping-side rival, "a verify here would be a
# verify-does-not-imply-resolve break" is literally true. For a COLLECTION-side
# rival it is NOT — its faithful real patch still grades resolved. Those rivals
# are retained (the frozen spec does pin those clauses, and a verify against
# them would show the modeled obligation weaker than the behaviour it declares),
# but each now carries the caveat explicitly instead of claiming a graded
# consequence the instance does not have. The five affected cases are
# wrong-native-elem-set, partial-domain-first-set, no-separator-set,
# wrong-empty-literal-set and no-braces-set.
#
# Note the carrier is largely OPAQUE: `SymExpr` is an `opaque` type and both
# `elemRepr` / `nativeRepr` are `opaque` functions with no constraining axiom, so
# `decide` computes nothing about an element's rendering. The reject lane is still
# fully expressible, by three routes that never need the callee's value:
#   * CONDITION on the carrier — assume only that the two renderings of one
#     element differ (`nativeRepr e ≠ elemRepr e`), which is exactly the
#     sub-domain where a rival substituting the wrong renderer is wrong;
#   * attack what is TRANSPARENT — the separator, the braces and the empty-input
#     literals are concrete string literals, refutable by a length count with no
#     hypothesis at all;
#   * for the position swap (C2), where no length count can separate the two
#     sides because they are permutations of the same pieces, pin the two
#     renderings to distinct concrete literals — one hypothesis per DISTINCT
#     opaque term, so the assumptions stay jointly satisfiable.
#
# ---------------------------------------------------------------------------
# PORTED FROM THE NAGINI SIBLING (nagini/properties.py) — and what was not
# ---------------------------------------------------------------------------
# Ported (the ARGUMENT, re-expressed over this carrier):
#   pos-control-set / pos-control-dict  -> pos-control-set / pos-control-dict
#   wrong-str-elem-set                  -> wrong-native-elem-set
#   wrong-str-elem-dict                 -> wrong-native-elem-dict
#   partial-domain-first-set            -> partial-domain-first-set
#   swap-key-value-dict                 -> swap-key-value-dict
#   no-separator-set                    -> no-separator-set
#   wrong-empty-literal-set             -> wrong-empty-literal-set
# Added (no nagini counterpart; closes a coverage gap this carrier exposes):
#   native-value-only-dict   — a near-miss correct on every KEY and wrong only on
#                              the VALUE position, so (C1) is demonstrated at the
#                              value position independently of the key position.
#   wrong-empty-literal-dict — (C4) for the mapping obligation. The two
#                              obligations pin DIFFERENT empty literals, and
#                              without this the mapping's empty-input point is
#                              never probed by any rival.
#   short-entry-marker-dict  — the entry marker's exact spelling inside (C2).
#                              swap-key-value-dict transposes the halves AROUND
#                              the marker and leaves the marker itself intact,
#                              so before this case that literal was pinned by
#                              the spec but demonstrated by nothing.
#   no-braces-dict           — the DELIMITER FRAME of the non-empty mapping
#                              rendering. wrong-empty-literal-dict moves only
#                              the empty mapping's literal, so every non-empty
#                              output's frame was otherwise unprobed.
#   no-separator-dict        — (C3) for the MAPPING obligation. The two
#                              obligations join through INDEPENDENT clauses (the
#                              mapping intercalates rendered ENTRIES, the
#                              collection rendered ELEMENTS), so
#                              no-separator-set left the mapping's separator
#                              demonstrated by nothing. Also the only rival that
#                              probes `entries` at a two-entry list.
#   no-braces-set            — (C4-frame) for the COLLECTION obligation, for the
#                              same independence reason: the collection's
#                              non-empty arm carries its own brace pair, which
#                              neither no-braces-dict (other obligation) nor
#                              wrong-empty-literal-set (other arm) moves.
#   wrong-delims-literal-dict, wrong-separator-literal-dict,
#   wrong-marker-literal-dict
#                            — the LENGTH-PRESERVING face of (C4-frame)/(C3)/
#                              (C2) on the mapping. Every one of the three
#                              length-based rivals above (no-braces-dict,
#                              no-separator-dict, short-entry-marker-dict) is
#                              refuted by a character count, and a count is
#                              blind to a substitution that keeps the length: it
#                              refutes `"{" ... "}"` -> bare, but not `"{" ...
#                              "}"` -> `"[" ... "]"`. So before these three
#                              cases, WHICH characters each literal contains was
#                              pinned by the spec and demonstrated by nothing —
#                              a rival emitting the right SHAPE with the wrong
#                              punctuation was refuted by no witness here. Each
#                              is refuted by pinning the two renderings to
#                              distinct concrete literals and DECIDING the
#                              resulting closed equation, the same route
#                              swap-key-value-dict needs and for the same
#                              reason (no count can separate the sides).
#   reverse-entries-dict, reverse-elems-set
#                            — the SEQUENCE ORDER of the emitted pieces, one per
#                              obligation. Every other rival moves the CONTENT of
#                              a rendering or the CHARACTERS of a literal; these
#                              two keep every rendering canonical, every literal
#                              exact and the total length IDENTICAL, and move
#                              only the order. So all four length-counting
#                              witnesses are structurally blind to them, and
#                              swap-key-value-dict does not reach the clause
#                              either (it transposes WITHIN one entry at a
#                              one-entry input, which says nothing about the
#                              order the entries are emitted in). Before these
#                              two, the positional correspondence that both spec
#                              clauses pin via `List.map` was demonstrated by
#                              nothing. Necessarily refuted at a TWO-piece input:
#                              at one piece a reversal is definitionally the
#                              identity, the same trap
#                              wrong-separator-literal-dict documents.
#   adm-f2p-points           — the admissibility lane (see section 3 for why it
#                              is non-vacuous here despite there being no
#                              precondition to attack).
# NOT ported, with the reason:
#   frame-mut-set / frame-mut-dict — nagini's fractional-permission class. This
#     backend is referentially transparent: there is no heap, both inputs are
#     immutable values, and an implementation cannot write to them at all. The
#     class is VACUOUS here, so no substitute is fabricated.
#   divergence lane — the nagini sibling carries no `diverge-*` / `nonterm-*`
#     case, so nothing was dropped in the port; recorded here as a KNOWN HOLE
#     rather than a vacuous class, because the class is NOT vacuous and the
#     shape of it is measurable. A diverging renderer CAN be written on this
#     carrier (`partial def implementation_setRepr elems := implementation_
#     setRepr elems`) and it is an admissible same-spec variant, so the lane has
#     a surface. This backend sets no termination semantics and the frozen
#     `implementation_*` is a total `def`, so such a rival does not verify — but
#     its rejection is not attributable to the spec and no witness can make it
#     so: `partial def` makes the constant IRREDUCIBLE, so the frozen script
#     fails at `unfold` (a tactic artifact, the exact failure a merely reshaped
#     CORRECT rival produces), while nothing about the impl's value is derivable
#     in either direction. Measured: a witness conditioned on the impl's value
#     elaborates against that rival AND against the frozen solution (both exit
#     0, i.e. `witness-vacuous`), and an unconditioned witness proves nothing
#     against the rival (exit 1). So the lane is a hole in what this gate can
#     attribute, not a case that was available and skipped.
#   AXIOM_TESTS — the axiom lane is G-AX's job and this gate ignores them; this
#     bundle declares no axiom at all (`axioms = []`).
#
# same_spec + obligation preservation are GUARANTEED by construction: every
# `_swap` anchor lies strictly inside an `-- impl-start`/`-- impl-end` region or
# inside a `-- proof-start`/`-- proof-end` tactic BODY. No `theorem correct_*`
# statement, no `problem_spec_*`, no `opaque` declaration and no doc comment
# outside those regions is ever touched, and nothing new is assumed.

from pathlib import Path

INSTANCE = "sympy__sympy-19346"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Anchors. Each lies ENTIRELY inside one impl region or one proof tactic body,
# and each is unique in the frozen file.
# ===========================================================================

# --- mapping impl region ---------------------------------------------------
_D_SEP = '  let sep := ", "\n'
_D_ENTRY = '    parts := parts ++ [elemRepr p.1 ++ ": " ++ elemRepr p.2]\n'
_D_RETURN = '  return "{" ++ String.intercalate sep parts ++ "}"\n'

# --- mapping proof tactic body --------------------------------------------
_D_PROOF = """  intro entries
  unfold problem_spec_dictRepr implementation_dictRepr
  simp only [Id.run]
  rw [forIn_append_singleton_eq_map
        (fun p : SymExpr × SymExpr => elemRepr p.1 ++ ": " ++ elemRepr p.2)]
  simp only [List.nil_append]
  rfl
"""

# --- collection impl region ------------------------------------------------
_S_GUARD = '  if elems.isEmpty then return "set()"\n'
_S_ELEM = "    parts := parts ++ [elemRepr e]\n"
_S_RETURN = '  return "{" ++ String.intercalate ", " parts ++ "}"\n'

# --- collection proof tactic body -----------------------------------------
_S_PROOF = """  intro elems
  unfold problem_spec_setRepr implementation_setRepr
  by_cases h : elems.isEmpty
  · simp only [Id.run, h]; rfl
  · simp only [Id.run, h]
    rw [forIn_append_singleton_eq_map elemRepr]
    simp only [List.nil_append]
    rfl
"""


# ===========================================================================
# WITNESS BOILERPLATE
# ---------------------------------------------------------------------------
# Each witness states `¬ problem_spec_<name> <input> (implementation_<name>
# <input>)` at one concrete input. The discipline that makes the witness
# DISCRIMINATING rather than merely failing is: never name the value the rival
# happens to produce. A witness that opens by pinning the implementation to a
# hard-coded literal output (`have hl : implementation_X <input> = <that
# rival's string> := rfl`) fails against the frozen solution at that pinning
# step, BEFORE the spec claim is ever reached — so its exit code against the
# frozen solution says nothing about the claim and would be identical for the
# opposite claim. Instead each witness here:
#   (a) assumes the spec instance as a hypothesis (`intro hs`);
#   (b) NORMALISES that hypothesis with an impl-agnostic rewrite set — the
#       `Id.run do` / `forIn` desugaring plus the list-literal lemmas. The same
#       rewrite set is applied whatever the implementation is, so the step
#       cannot encode which implementation is under it. Against the frozen
#       solution the two sides coincide and the hypothesis collapses to `True`;
#       against the rival it survives as a real string equation;
#   (c) refutes the surviving equation — by cancelling the shared literal frame
#       down to the conditioned element inequality, or by counting characters
#       when the two sides cannot even have equal length.
# The failure therefore TRACKS THE CLAIM: flip the `¬` and the proof breaks
# against the rival and succeeds against the frozen solution instead.
#
# One Lean wrinkle forces the `_IC*` helpers below. `String.intercalate`
# reduces at a list literal by `rfl`, but neither `simp` nor `decide` can take
# that step, because its recursive worker is a private constant they cannot
# unfold. Each witness therefore names exactly the instance it needs as a local
# `have ... := rfl` in the SHARED vocabulary (generic in the strings, no
# implementation's value mentioned) and rewrites with it. These are local
# `have`s, not new top-level lemmas, so `variant_scope` stays satisfied.
# ===========================================================================

# (b) normalisation of the assumed spec instance, collection obligation.
# Mentions no renderer, so it runs identically on the frozen solution and on
# every rival.
_NORM_S = """  simp only [problem_spec_setRepr, implementation_setRepr, Id.run,
             pure, bind, Id.run_pure, Id.run_bind, List.forIn_cons,
             List.forIn_nil, List.nil_append, List.isEmpty_cons,
             List.isEmpty_nil, Bool.false_eq_true, if_false, if_true,
             List.map_cons, List.map_nil, List.cons_append,
             List.singleton_append] at hs
"""

# (b) the same, mapping obligation.
_NORM_D = """  simp only [problem_spec_dictRepr, implementation_dictRepr, entryText,
             Id.run, pure, bind, Id.run_pure, Id.run_bind,
             List.forIn_cons, List.forIn_nil, List.nil_append,
             List.map_cons, List.map_nil] at hs
"""

# (b) the mapping obligation at a TWO-entry input. Same set plus the two
# list-literal append lemmas the second loop iteration needs, so the accumulated
# `[e1] ++ [e2]` becomes the literal `[e1, e2]` that `_IC2` is stated at. Still
# mentions no renderer and no implementation's value, so it runs identically on
# the frozen solution and on every rival.
_NORM_D2 = """  simp only [problem_spec_dictRepr, implementation_dictRepr, entryText,
             Id.run, pure, bind, Id.run_pure, Id.run_bind,
             List.forIn_cons, List.forIn_nil, List.nil_append,
             List.map_cons, List.map_nil,
             List.cons_append, List.singleton_append] at hs
"""

# the blocked `String.intercalate` steps, supplied generically.
_IC1 = """  have ic1 : ∀ x : String, String.intercalate ", " [x] = x :=
    fun _ => rfl
"""
_IC2 = """  have ic2 : ∀ x y : String,
      String.intercalate ", " [x, y] = x ++ ", " ++ y := fun _ _ => rfl
"""
_IC2E = """  have ic2e : ∀ x y : String,
      String.intercalate "" [x, y] = x ++ "" ++ y := fun _ _ => rfl
"""
_IC0 = """  have ic0 : String.intercalate ", " ([] : List String) = "" := rfl
"""

# (c) for "the two sides differ inside a shared literal frame": push the
# equation down to `String.data`, let `simp` cancel the common list prefix and
# suffix, and re-package with `String.ext`.
_CANCEL = """  have hd := congrArg String.data hs
  simp only [String.data_append] at hd
  simp at hd
  exact String.ext hd
"""

# (c) for "the two sides cannot have equal length": count characters. No
# hypothesis about any opaque term is needed.
_LENGTH = """  have hlen := congrArg String.length hs
  simp only [String.length_append] at hlen
"""


# ===========================================================================
# 1. SOUNDNESS POSITIVES — structurally different but CORRECT, reproven.
#    Each keeps its `theorem correct_*` STATEMENT byte-identical and closes the
#    obligation honestly for the NEW implementation shape (no new lemma, no
#    weakening). A correct reshape MUST verify, else SPEC-TOO-STRONG.
# ===========================================================================

# 1a. Mapping: drop the separator local (inline the literal), and build each
#     entry by APPLYING the shared entry-rendering helper rather than spelling
#     its body out inline, then name the joined middle in a local. Same
#     observable output, a different data-flow shape, and the proof rewrites
#     with the helper itself instead of an anonymous lambda.
_pos_dict = _swap(
    _swap(
        _swap(_BASE, _D_SEP, ""),
        _D_ENTRY,
        "    parts := parts ++ [entryText p]\n",
    ),
    _D_RETURN,
    '  let joined := String.intercalate ", " parts\n'
    '  return "{" ++ joined ++ "}"\n',
)
_pos_dict = _swap(
    _pos_dict,
    _D_PROOF,
    """  intro entries
  unfold problem_spec_dictRepr implementation_dictRepr
  simp only [Id.run]
  rw [forIn_append_singleton_eq_map entryText]
  simp only [List.nil_append]
  rfl
""",
)

# 1b. Collection: invert the empty guard so the two branches appear in the
#     OPPOSITE order (non-empty handled first, the dedicated empty literal
#     returned by fall-through), and name the joined middle in a local. Same
#     observable output; the proof must now discharge the negated guard on both
#     sides of the case split.
_pos_set = _swap(
    _swap(
        _swap(
            _BASE,
            _S_GUARD + "  let mut parts : List String := []\n",
            "  if !elems.isEmpty then\n"
            "    let mut parts : List String := []\n",
        ),
        "  for e in elems do\n" + _S_ELEM,
        "    for e in elems do\n      parts := parts ++ [elemRepr e]\n",
    ),
    _S_RETURN,
    '    let joined := String.intercalate ", " parts\n'
    '    return "{" ++ joined ++ "}"\n'
    '  return "set()"\n',
)
_pos_set = _swap(
    _pos_set,
    _S_PROOF,
    """  intro elems
  unfold problem_spec_setRepr implementation_setRepr
  by_cases h : elems.isEmpty
  · simp only [Id.run, h, Bool.not_true, Bool.false_eq_true, if_false]; rfl
  · simp only [Id.run, h, Bool.not_false, if_true]
    rw [forIn_append_singleton_eq_map elemRepr]
    simp only [List.nil_append]
    rfl
""",
)


# ===========================================================================
# 2. UNIQUENESS RIVALS
# ===========================================================================

# 2a. (C1) THE discriminating rival, collection side: render every element with
#     the alternative NON-canonical textual conversion instead of the canonical
#     recursive renderer. This is the pre-patch behaviour.
_native_set = _swap(_BASE, _S_ELEM, "    parts := parts ++ [nativeRepr e]\n")

_W_NATIVE_SET = """example (e : SymExpr) (h : nativeRepr e ≠ elemRepr e) :
    ¬ problem_spec_setRepr [e] (implementation_setRepr [e]) := by
  intro hs
  apply h
""" + _NORM_S + _IC1 + "  rw [ic1, ic1] at hs\n" + _CANCEL

# 2b. (C1) the same rival on the mapping side: BOTH positions of every entry
#     rendered by the non-canonical conversion.
_native_dict = _swap(
    _BASE, _D_ENTRY,
    '    parts := parts ++ [nativeRepr p.1 ++ ": " ++ nativeRepr p.2]\n')

# Both positions are substituted here, so NEITHER half of the entry is shared
# with the frozen output and there is no common frame to cancel. The refutation
# instead counts characters: a single hypothesis saying the entry's two halves
# render to a different TOTAL length under the two conversions. That is one
# assumption about the pair, trivially satisfiable, and strictly weaker than
# pinning either rendering to a literal.
_W_NATIVE_DICT = """example (k v : SymExpr)
    (h : (nativeRepr k).length + (nativeRepr v).length
         ≠ (elemRepr k).length + (elemRepr v).length) :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
  apply h
""" + _NORM_D + _IC1 + "  rw [ic1, ic1] at hs\n" + _LENGTH + "  omega\n"

# 2c. (C1) NEAR-MISS on the mapping, value position only: every KEY is rendered
#     canonically and correctly; only the VALUE takes the non-canonical
#     conversion. Agrees with the frozen behaviour on strictly more of the
#     domain than 2b (every all-keys observation matches), so it gets its own
#     witness, conditioned on the VALUE's renderings differing.
_native_value_dict = _swap(
    _BASE, _D_ENTRY,
    '    parts := parts ++ [elemRepr p.1 ++ ": " ++ nativeRepr p.2]\n')

_W_NATIVE_VALUE_DICT = """example (k v : SymExpr) (h : nativeRepr v ≠ elemRepr v) :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
  apply h
""" + _NORM_D + _IC1 + "  rw [ic1, ic1] at hs\n" + _CANCEL

# 2d. (C1) NEAR-MISS on the collection, LEADING position only: the first element
#     takes the non-canonical conversion, every later element is rendered
#     canonically. Correct on the whole tail, so it is refuted at a TWO-element
#     input — a value-proxy that only ever looked at trailing elements would miss
#     it entirely.
_partial_set = _swap(
    _BASE,
    "  let mut parts : List String := []\n"
    "  for e in elems do\n" + _S_ELEM,
    "  let mut parts : List String := []\n"
    "  let mut later := false\n"
    "  for e in elems do\n"
    "    if later then\n"
    "      parts := parts ++ [elemRepr e]\n"
    "    else\n"
    "      parts := parts ++ [nativeRepr e]\n"
    "      later := true\n",
)

_W_PARTIAL_SET = """example (a b : SymExpr) (h : nativeRepr a ≠ elemRepr a) :
    ¬ problem_spec_setRepr [a, b] (implementation_setRepr [a, b]) := by
  intro hs
  apply h
""" + _NORM_S + _IC2 + "  rw [ic2, ic2] at hs\n" + _CANCEL

# 2e. (C2) POSITION SWAP on the mapping: each entry written as the VALUE's
#     rendering, `": "`, then the KEY's rendering. Structurally a plausible
#     entry shape — same pieces, same separator, same length — which is exactly
#     why no character count can separate it from the frozen behaviour. The
#     witness therefore pins the two renderings to DISTINCT concrete literals
#     (one hypothesis per distinct opaque term, jointly satisfiable) and decides
#     the resulting closed string equation.
_swap_kv_dict = _swap(
    _BASE, _D_ENTRY,
    '    parts := parts ++ [elemRepr p.2 ++ ": " ++ elemRepr p.1]\n')

_W_SWAP_KV_DICT = """example (k v : SymExpr) (hk : elemRepr k = "K") (hv : elemRepr v = "V") :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
""" + _NORM_D + _IC1 + "  rw [ic1, ic1, hk, hv] at hs\n" + \
    "  exact absurd hs (by decide)\n"

# 2f. (C3) SEPARATOR DROP on the collection: consecutive renderings are
#     concatenated with nothing between them. Refutable with NO hypothesis about
#     any opaque term: the two sides differ by the two characters of the
#     separator, so they cannot have equal length whatever the renderings are.
_no_sep_set = _swap(
    _BASE, _S_RETURN,
    '  return "{" ++ String.intercalate "" parts ++ "}"\n')

_W_NO_SEP_SET = """example (a b : SymExpr) :
    ¬ problem_spec_setRepr [a, b] (implementation_setRepr [a, b]) := by
  intro hs
""" + _NORM_S + _IC2 + _IC2E + "  rw [ic2, ic2e] at hs\n" + _LENGTH + \
    '  simp only [show (", " : String).length = 2 from by decide,\n' \
    '             show ("" : String).length = 0 from by decide] at hlen\n' \
    "  omega\n"

# 2g. (C4) WRONG EMPTY LITERAL on the collection: return the brace pair for the
#     empty input instead of the dedicated literal the spec pins. Fully
#     transparent — both sides are closed string literals.
_empty_lit_set = _swap(
    _BASE, _S_GUARD, '  if elems.isEmpty then return "{}"\n')

_W_EMPTY_LIT_SET = """example : ¬ problem_spec_setRepr [] (implementation_setRepr []) := by
  intro hs
  simp only [problem_spec_setRepr, implementation_setRepr, Id.run, pure,
             Id.run_pure, List.isEmpty_nil, if_true] at hs
  exact absurd hs (by decide)
"""

# 2h. (C4) WRONG EMPTY LITERAL on the MAPPING: return the collection's dedicated
#     empty literal for an empty mapping. The two obligations pin DIFFERENT
#     empty literals, so this is a genuinely independent clause from 2g — and it
#     is the only rival that probes the mapping obligation at the empty input.
_empty_lit_dict = _swap(
    _BASE, _D_SEP, _D_SEP + '  if entries.isEmpty then return "set()"\n')

_W_EMPTY_LIT_DICT = """example : ¬ problem_spec_dictRepr [] (implementation_dictRepr []) := by
  intro hs
  simp only [problem_spec_dictRepr, implementation_dictRepr, Id.run, pure,
             bind, Id.run_pure, Id.run_bind, List.forIn_nil, List.map_nil,
             List.nil_append, List.isEmpty_nil, if_true] at hs
""" + _IC0 + "  rw [ic0] at hs\n  exact absurd hs (by decide)\n"


# 2i. (C2) ENTRY MARKER TRUNCATION on the mapping: each entry uses a one
#     character marker between the two rendered halves instead of the
#     two-character marker the spec pins. Distinct from 2e: the halves are in
#     the RIGHT order and both are canonical — only the marker between them is
#     short. Nothing else in the battery pins that literal (2e keeps it intact
#     and merely transposes around it), so without this the marker's exact
#     spelling is a clause no rival moves.
_short_marker_dict = _swap(
    _BASE, _D_ENTRY,
    '    parts := parts ++ [elemRepr p.1 ++ ":" ++ elemRepr p.2]\n')

_W_SHORT_MARKER_DICT = """example (k v : SymExpr) :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
""" + _NORM_D + _IC1 + "  simp only [ic1] at hs\n" + _LENGTH + \
    '  simp only [show (": " : String).length = 2 from by decide,\n' \
    '             show (":" : String).length = 1 from by decide] at hlen\n' \
    "  omega\n"

# 2j. (C4-frame) BRACE FRAME DROP on the mapping: the joined entries are
#     returned bare, without the enclosing brace pair. The braces are the one
#     transparent part of the non-empty mapping rendering that no other rival
#     touches — 2h moves only the EMPTY mapping's literal, leaving every
#     non-empty output's frame unprobed. Refutable with no hypothesis: the two
#     sides differ by the two frame characters.
_no_braces_dict = _swap(
    _BASE, _D_RETURN, "  return String.intercalate sep parts\n")

_W_NO_BRACES_DICT = """example (k v : SymExpr) :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
""" + _NORM_D + _IC1 + "  simp only [ic1] at hs\n" + _LENGTH + \
    '  simp only [show ("{" : String).length = 1 from by decide,\n' \
    '             show ("}" : String).length = 1 from by decide,\n' \
    '             show (": " : String).length = 2 from by decide] at hlen\n' \
    "  omega\n"

# 2k. (C3) SEPARATOR DROP on the MAPPING. no-separator-set attacks (C3) on the
#     collection only, and the two obligations join their pieces through
#     INDEPENDENT spec clauses — the mapping's `String.intercalate ", "` runs
#     over rendered ENTRIES, the collection's over rendered ELEMENTS — so a
#     rival that ran the mapping's entries together while keeping the
#     collection's separator intact was, before this case, admitted by every
#     witness in the battery. Refutable at a TWO-entry mapping with no
#     hypothesis about any opaque term: the two sides differ by exactly the
#     separator's two characters, whatever the four renderings are.
_no_sep_dict = _swap(
    _BASE, _D_RETURN,
    '  return "{" ++ String.intercalate "" parts ++ "}"\n')

_W_NO_SEP_DICT = """example (k1 v1 k2 v2 : SymExpr) :
    ¬ problem_spec_dictRepr [(k1, v1), (k2, v2)]
        (implementation_dictRepr [(k1, v1), (k2, v2)]) := by
  intro hs
""" + _NORM_D2 + _IC2 + _IC2E + "  rw [ic2, ic2e] at hs\n" + _LENGTH + \
    '  simp only [show (", " : String).length = 2 from by decide,\n' \
    '             show ("" : String).length = 0 from by decide] at hlen\n' \
    "  omega\n"

# 2l. (C4-frame) BRACE FRAME DROP on the COLLECTION. Symmetric to no-braces-dict
#     and independent of it for the same reason 2k is independent of
#     no-separator-set: the collection's non-empty arm carries its OWN brace
#     pair in its OWN spec clause. wrong-empty-literal-set moves only the empty
#     arm's dedicated literal, so a rival that returned the joined elements bare
#     on every non-empty collection — while answering the empty one correctly —
#     was refuted by nothing here. No hypothesis needed: the two sides differ by
#     exactly the frame's two characters.
_no_braces_set = _swap(
    _BASE, _S_RETURN, '  return String.intercalate ", " parts\n')

_W_NO_BRACES_SET = """example (a : SymExpr) :
    ¬ problem_spec_setRepr [a] (implementation_setRepr [a]) := by
  intro hs
""" + _NORM_S + _IC1 + "  simp only [ic1] at hs\n" + _LENGTH + \
    '  simp only [show ("{" : String).length = 1 from by decide,\n' \
    '             show ("}" : String).length = 1 from by decide] at hlen\n' \
    "  omega\n"

# 2m. (C4-frame, LENGTH-PRESERVING) WRONG DELIMITER CHARACTERS on the mapping:
#     the joined entries are enclosed in the SEQUENCE delimiter pair instead of
#     the mapping's. Distinct from no-braces-dict in exactly the way that
#     matters: that rival DELETES the frame and is caught by a character count,
#     whereas this one keeps the frame's length and only changes which two
#     characters it is, so `_LENGTH` cannot see it at all — before this case a
#     rival emitting the right shape with the wrong punctuation was admitted by
#     every witness in the battery. Refuted the way swap-key-value-dict is:
#     pin the two renderings to distinct concrete literals (one hypothesis per
#     distinct opaque term, jointly satisfiable) and decide the closed equation.
_delims_lit_dict = _swap(
    _BASE, _D_RETURN,
    '  return "[" ++ String.intercalate sep parts ++ "]"\n')

_W_DELIMS_LIT_DICT = """example (k v : SymExpr) (hk : elemRepr k = "K") (hv : elemRepr v = "V") :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
""" + _NORM_D + _IC1 + "  simp only [ic1] at hs\n" + \
    "  rw [hk, hv] at hs\n  exact absurd hs (by decide)\n"

# 2n. (C3, LENGTH-PRESERVING) WRONG SEPARATOR CHARACTERS on the mapping: the
#     rendered entries are joined with a semicolon-plus-space instead of the
#     comma-plus-space the spec pins. Same length, so no-separator-dict's count
#     is blind to it. Refuted at a TWO-entry mapping — necessarily, because at a
#     ONE-entry mapping this rival is definitionally EQUAL to the frozen
#     implementation (a singleton join never reaches the separator), so a
#     one-entry witness would be attacking a rival that is not wrong there.
#     Measured: at one entry the normalised hypothesis collapses to `True`
#     against this rival exactly as it does against the frozen solution.
_sep_lit_dict = _swap(_BASE, _D_SEP, '  let sep := "; "\n')

_W_SEP_LIT_DICT = """example (k1 v1 k2 v2 : SymExpr)
    (h1 : elemRepr k1 = "K") (h2 : elemRepr v1 = "V")
    (h3 : elemRepr k2 = "L") (h4 : elemRepr v2 = "W") :
    ¬ problem_spec_dictRepr [(k1, v1), (k2, v2)]
        (implementation_dictRepr [(k1, v1), (k2, v2)]) := by
  intro hs
""" + _NORM_D2 + _IC2 + """  have ic2' : ∀ x y : String,
      String.intercalate "; " [x, y] = x ++ "; " ++ y := fun _ _ => rfl
  rw [ic2, ic2', h1, h2, h3, h4] at hs
  exact absurd hs (by decide)
"""

# 2o. (C2, LENGTH-PRESERVING) WRONG ENTRY MARKER CHARACTERS on the mapping: the
#     two rendered halves are joined by a two-character arrow marker instead of
#     the colon-plus-space the spec pins. Halves canonical, halves in the right
#     order, marker the RIGHT LENGTH — so short-entry-marker-dict's count is
#     blind to it and swap-key-value-dict's transposition does not reach it
#     either. This is the third and last transparent literal in the mapping
#     rendering whose character content no rival moved.
_marker_lit_dict = _swap(
    _BASE, _D_ENTRY,
    '    parts := parts ++ [elemRepr p.1 ++ "=>" ++ elemRepr p.2]\n')

_W_MARKER_LIT_DICT = """example (k v : SymExpr) (hk : elemRepr k = "K") (hv : elemRepr v = "V") :
    ¬ problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
  intro hs
""" + _NORM_D + _IC1 + "  rw [ic1, ic1, hk, hv] at hs\n" + \
    "  exact absurd hs (by decide)\n"

# --- the SEQUENCE ORDER of the rendered pieces ------------------------------
# 2p/2q. Every rival above moves the CONTENT of a rendering or the CHARACTERS of
#     a literal; none moves the ORDER in which the pieces are emitted. Both spec
#     clauses map over the input list and intercalate the result, so the
#     positional correspondence "the i-th rendered piece is the i-th input's
#     rendering" is pinned by `List.map` in each clause — and a rival that emits
#     the same multiset of renderings in the wrong sequence keeps every other
#     property the battery checks: the pieces are all canonical, the entry marker
#     is right, the separator is right, the frame is right, and the total length
#     is IDENTICAL, so all four length-counting witnesses are blind to it.
#     swap-key-value-dict is not this clause: it transposes the two halves WITHIN
#     one entry, at a one-entry input, and says nothing about the order the
#     entries themselves are emitted in.
#     Refuted the way the other length-preserving rivals are — pin the
#     renderings to distinct concrete literals (one hypothesis per DISTINCT
#     opaque term, so jointly satisfiable) and decide the closed equation — at a
#     TWO-piece input, which is the smallest input where an order is observable
#     at all (at one piece a reversal is definitionally the identity).
_rev_entries_dict = _swap(
    _BASE, _D_RETURN,
    '  return "{" ++ String.intercalate sep parts.reverse ++ "}"\n')

_W_REV_ENTRIES_DICT = """example (k1 v1 k2 v2 : SymExpr)
    (h1 : elemRepr k1 = "K") (h2 : elemRepr v1 = "V")
    (h3 : elemRepr k2 = "L") (h4 : elemRepr v2 = "W") :
    ¬ problem_spec_dictRepr [(k1, v1), (k2, v2)]
        (implementation_dictRepr [(k1, v1), (k2, v2)]) := by
  intro hs
""" + _NORM_D2 + """  simp only [List.reverse_cons, List.reverse_nil, List.nil_append,
             List.cons_append, List.singleton_append] at hs
""" + _IC2 + "  rw [ic2, ic2, h1, h2, h3, h4] at hs\n" + \
    "  exact absurd hs (by decide)\n"

_rev_elems_set = _swap(
    _BASE, _S_RETURN,
    '  return "{" ++ String.intercalate ", " parts.reverse ++ "}"\n')

_W_REV_ELEMS_SET = """example (a b : SymExpr) (ha : elemRepr a = "A") (hb : elemRepr b = "B") :
    ¬ problem_spec_setRepr [a, b] (implementation_setRepr [a, b]) := by
  intro hs
""" + _NORM_S + """  simp only [List.reverse_cons, List.reverse_nil, List.nil_append,
             List.cons_append, List.singleton_append] at hs
""" + _IC2 + "  rw [ic2, ic2, ha, hb] at hs\n" + \
    "  exact absurd hs (by decide)\n"


# ===========================================================================
# 3. ADMISSIBILITY POSITIVE
# ---------------------------------------------------------------------------
# Neither obligation carries a precondition — both binders are plain `List`
# types with no hypothesis — so the classical PRECOND-TOO-STRONG shape (an
# admissible input the precondition excludes) has no surface to attack: there
# is no precondition to strengthen. The lane is NOT vacuous for a different
# reason, though, and this case covers it: an obligation can be closed by a
# route that never touches the input shapes the graded suite actually
# exercises. So this variant discharges the obligation AT the concrete
# F2P-shaped inputs first — empty mapping, one-entry mapping, empty
# collection, two-element collection — as `have`s proven by evaluation, and
# only then closes the frozen obligations verbatim. If either obligation were
# unsatisfiable at exactly those points while still closable in general, these
# `have`s would fail. Must verify.
_adm_points = _swap(
    _swap(
        _BASE, _D_PROOF,
        """  have f2p_empty : problem_spec_dictRepr [] (implementation_dictRepr []) := by
    unfold problem_spec_dictRepr implementation_dictRepr
    simp only [Id.run]
    rfl
  have f2p_one : ∀ k v : SymExpr,
      problem_spec_dictRepr [(k, v)] (implementation_dictRepr [(k, v)]) := by
    intro k v
    unfold problem_spec_dictRepr implementation_dictRepr entryText
    simp only [Id.run]
    rfl
  have f2p_two : ∀ k1 v1 k2 v2 : SymExpr,
      problem_spec_dictRepr [(k1, v1), (k2, v2)]
        (implementation_dictRepr [(k1, v1), (k2, v2)]) := by
    intro k1 v1 k2 v2
    unfold problem_spec_dictRepr implementation_dictRepr entryText
    simp only [Id.run]
    rfl
""" + _D_PROOF),
    _S_PROOF,
    """  have f2p_empty : problem_spec_setRepr [] (implementation_setRepr []) := by
    unfold problem_spec_setRepr implementation_setRepr
    simp only [Id.run]
    rfl
  have f2p_two : ∀ a b : SymExpr,
      problem_spec_setRepr [a, b] (implementation_setRepr [a, b]) := by
    intro a b
    unfold problem_spec_setRepr implementation_setRepr
    simp only [Id.run, List.isEmpty_cons, Bool.false_eq_true, if_false]
    rw [forIn_append_singleton_eq_map elemRepr]
    simp only [List.nil_append]
    rfl
""" + _S_PROOF)


# ===========================================================================
# Shared refinement preamble. Every rival below is a rendering that a real
# printer could plausibly emit and that the frozen spec pins against. Whether
# its faithful real patch is additionally rejected by the GRADED suite depends
# on which container shape it is wrong about, and that split was measured (see
# MEASURED GRADING SURFACE at the top of this file), so it is stated per case
# rather than asserted uniformly: `_R_GRADED` for the mapping shape, whose
# rendering the graded suite does assert, and `_R_UNGRADED_SHAPE` for the
# collection shape, whose rendering no graded name observes.
# ===========================================================================

_R_NON_CANONICAL = (
    "the faithful real patch renders the container's contents through each "
    "value's own plain textual conversion rather than through the canonical "
    "recursive representation function. That is precisely the pre-existing "
    "behaviour the change was written to eliminate: the desired behaviour is "
    "the reconstructible canonical spelling of every contained value, and the "
    "plain textual form of a symbolic value is a different string. "
)

# Mapping shape: measured to be graded. A rival that VERIFIED here would be a
# genuine verify-does-not-imply-resolve break rather than a modeling artifact.
_R_GRADED = (
    "The graded suite asserts this container shape's rendering directly — "
    "measured: an implementation faithful everywhere EXCEPT this shape fails a "
    "graded name — so the faithful real patch of this rival does NOT resolve "
    "the instance, and a verify here would be a true "
    "verify-does-not-imply-resolve break. "
)

# Collection shape: measured NOT to be graded. Recorded honestly rather than
# claiming a consequence the instance does not have.
_R_UNGRADED_SHAPE = (
    "CAVEAT, measured rather than assumed: this rival is wrong about the "
    "unordered-collection shape only, and for THIS instance that shape's test "
    "is named in neither graded list, so the grader never observes its "
    "rendering — an implementation wrong here and faithful on the mapping shape "
    "still grades resolved (measured on the real suite at base_commit, "
    "including a probe whose collection renderer raised unconditionally). So a "
    "verify against this rival would NOT by itself be a "
    "verify-does-not-imply-resolve break; it would show the modeled obligation "
    "admitting behaviour its own declared postcondition forbids. The case is "
    "retained on that narrower ground — the frozen spec does pin this clause, "
    "and a spec that fails to pin what it states is a defect independently of "
    "which names the harness happens to run — and NOT on a graded-test "
    "argument, which the measurement does not support. "
)


SPEC_TESTS = [
    # --- soundness positives ------------------------------------------------
    {
        "id": "pos-control-dict",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_dict,
        "rationale": "structurally different but observationally identical "
        "mapping renderer: the separator local is inlined, each entry is built "
        "by APPLYING the shared entry-rendering helper instead of spelling its "
        "body out inline, and the joined middle is named in a local. The "
        "`theorem correct_dictRepr` STATEMENT is byte-identical and the "
        "obligation is reproven honestly for the new shape (the loop/fold "
        "rewrite is instantiated at the helper itself rather than at an "
        "anonymous lambda); no new lemma, no weakening, no `sorry`. Must "
        "verify — a correct reshape that the spec rejected would be "
        "SPEC-TOO-STRONG on the mapping clause.",
    },
    {
        "id": "pos-control-set",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_set,
        "rationale": "structurally different but observationally identical "
        "collection renderer: the empty guard is NEGATED so the two branches "
        "appear in the opposite order (non-empty handled first, the dedicated "
        "empty literal returned by fall-through) and the joined middle is named "
        "in a local. The `theorem correct_setRepr` STATEMENT is byte-identical; "
        "the reproof discharges the negated guard on both arms of the case "
        "split. Must verify — else SPEC-TOO-STRONG on the collection clause, "
        "whose two arms are order-independent.",
    },
    # --- (C1) the discriminating clause -------------------------------------
    {
        "id": "wrong-native-elem-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _native_set,
        "refinement": _R_NON_CANONICAL
        + "This rival is that patch on the collection shape. "
        + _R_UNGRADED_SHAPE,
        "rationale": "attacks clause (C1) on the collection obligation: the "
        "spec pins EVERY element of a non-empty collection to the canonical "
        "recursive renderer, and this rival substitutes the alternative "
        "non-canonical conversion at every position. The two are distinct "
        "opaque carriers related by nothing, so on the sub-domain where an "
        "element's two renderings differ the spec is false of this output. A "
        "verify here => SPEC-TOO-WEAK: the spec would admit the pre-existing "
        "behaviour outright.",
        "witness": _W_NATIVE_SET,
    },
    {
        "id": "wrong-native-elem-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _native_dict,
        "refinement": _R_NON_CANONICAL
        + "This rival is that patch on the mapping shape. "
        + _R_GRADED,
        "rationale": "attacks clause (C1) on the mapping obligation: the spec "
        "pins BOTH positions of every entry to the canonical recursive "
        "renderer, and this rival substitutes the non-canonical conversion at "
        "both. Because BOTH halves move, no part of the entry is shared with "
        "the frozen output and there is no common frame to cancel, so the "
        "witness counts characters instead: one hypothesis, that the entry's "
        "two halves render to a different total length under the two "
        "conversions. A verify => SPEC-TOO-WEAK.",
        "witness": _W_NATIVE_DICT,
    },
    {
        "id": "native-value-only-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _native_value_dict,
        "refinement": _R_NON_CANONICAL
        + "This rival applies it to the value position only — a real patch "
        "that recursed correctly on each key but emitted the plain textual "
        "form of each value. It still prints a non-reconstructible value "
        "spelling on the right of every entry, so the graded assertion's "
        "expected mapping string does not match. "
        + _R_GRADED,
        "rationale": "NEAR-MISS against wrong-native-elem-dict, and it needs "
        "its own witness: it agrees with the frozen behaviour on strictly more "
        "of the domain — every KEY is rendered canonically and correctly, so "
        "any probe that only inspected keys would see no difference. Its "
        "witness is therefore conditioned on the VALUE's renderings differing, "
        "which demonstrates that clause (C1) is pinned at the value position "
        "INDEPENDENTLY of the key position. A verify => SPEC-TOO-WEAK on the "
        "value position of the entry format.",
        "witness": _W_NATIVE_VALUE_DICT,
    },
    {
        "id": "partial-domain-first-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_set,
        "refinement": _R_NON_CANONICAL
        + "This rival applies it to the LEADING element only — a real patch "
        "that fell back to the plain textual form for the first element it "
        "emitted and recursed correctly on the rest. The rendered collection "
        "then carries one non-canonical spelling in front, which the shape's "
        "desired rendering does not contain. "
        + _R_UNGRADED_SHAPE,
        "rationale": "NEAR-MISS against wrong-native-elem-set: correct on the "
        "whole TAIL and wrong only at the leading position, so it is refuted "
        "at a TWO-element input rather than a singleton — a distinct point in "
        "the `elems` binder, and one that shows clause (C1) is pinned at every "
        "position rather than merely 'somewhere'. A value-proxy that inspected "
        "only trailing elements would miss this rival entirely. A verify => "
        "SPEC-TOO-WEAK on the leading-element sub-domain.",
        "witness": _W_PARTIAL_SET,
    },
    # --- (C2) entry position ordering --------------------------------------
    {
        "id": "swap-key-value-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_kv_dict,
        "refinement": "the faithful real patch formats each mapping entry with "
        "its two rendered halves in the opposite order — the value's "
        "representation, the `\": \"` marker, then the key's representation. "
        "Both halves ARE canonical, so this passes any check that only asks "
        "'was the recursive renderer used'; but the graded assertion pins an "
        "exact mapping string in which each key precedes its own value, so a "
        "transposed entry does not match it. " + _R_GRADED,
        "rationale": "attacks clause (C2), the only clause about POSITION "
        "rather than content: the spec's entry rendering places the key's "
        "representation before `\": \"` and the value's after. This rival is a "
        "permutation of exactly the same pieces with exactly the same total "
        "length, so no character count can separate it from the frozen output "
        "and the witness must reach the content: it pins the two renderings to "
        "distinct concrete literals — ONE hypothesis per DISTINCT opaque term, "
        "so the assumptions are jointly satisfiable (any two values whose "
        "canonical spellings are those literals) — and decides the resulting "
        "closed equation. A verify => SPEC-TOO-WEAK on entry ordering.",
        "witness": _W_SWAP_KV_DICT,
    },
    # --- (C3) separator ----------------------------------------------------
    {
        "id": "no-separator-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_sep_set,
        "refinement": "the faithful real patch joins the rendered elements with "
        "nothing between them instead of with the two-character separator the "
        "spec pins. Every element is still rendered canonically, so the fix's "
        "own discriminating change is present; but the shape's desired "
        "rendering separates consecutive elements, so the run-together output "
        "is not it. " + _R_UNGRADED_SHAPE,
        "rationale": "attacks clause (C3): consecutive renderings must be "
        "separated by exactly the two-character separator. Refuted at a "
        "two-element collection with NO hypothesis about any opaque term at "
        "all — the two sides differ by exactly the separator's two characters, "
        "so they cannot have equal length whatever the renderings are, which "
        "makes this the strongest form the refutation can take. A verify => "
        "SPEC-TOO-WEAK on the separator.",
        "witness": _W_NO_SEP_SET,
    },
    # --- (C4) the empty-input literals, one per obligation ------------------
    {
        "id": "wrong-empty-literal-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _empty_lit_set,
        "refinement": "the faithful real patch returns the brace pair for an "
        "empty unordered collection instead of that shape's dedicated empty "
        "literal. Every non-empty rendering is untouched, so the container "
        "recursion fix is fully present; but that shape's desired rendering of "
        "the empty case is the dedicated literal, not the brace pair. "
        + _R_UNGRADED_SHAPE,
        "rationale": "attacks clause (C4) on the collection obligation, i.e. "
        "the empty arm of its conditional — the ONLY clause reached at the "
        "empty input, and one no non-empty witness can touch. Both sides are "
        "closed string literals, so the refutation needs no hypothesis and "
        "`decide` settles it. This is also the reject witness that probes "
        "`elems` at the empty list, so the binder is varied across three "
        "distinct shapes (empty / one element / two elements). A verify => "
        "SPEC-TOO-WEAK on the empty-collection literal.",
        "witness": _W_EMPTY_LIT_SET,
    },
    {
        "id": "wrong-empty-literal-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _empty_lit_dict,
        "refinement": "the faithful real patch special-cases the empty mapping "
        "and returns the OTHER container shape's dedicated empty literal for "
        "it. Every non-empty mapping is rendered correctly, so the recursion "
        "fix is present; but the graded assertion covers the empty mapping's "
        "own rendering explicitly, so it fails. " + _R_GRADED,
        "rationale": "attacks clause (C4) on the MAPPING obligation. This is a "
        "genuinely independent clause from wrong-empty-literal-set, not a "
        "restatement: the two obligations pin DIFFERENT empty literals, and "
        "the rival emits the collection's literal where the mapping's is "
        "required. It is also the only rival that probes `entries` at the empty "
        "list — without it the mapping's empty input is a point no witness "
        "moves, and a rival that mishandled only the empty mapping would "
        "verify unnoticed. Closed literals on both sides, so `decide` settles "
        "it with no hypothesis. A verify => SPEC-TOO-WEAK on the empty-mapping "
        "literal.",
        "witness": _W_EMPTY_LIT_DICT,
    },
    {
        "id": "short-entry-marker-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _short_marker_dict,
        "refinement": "the faithful real patch separates each entry's two "
        "rendered halves with a bare colon instead of the colon-plus-space "
        "marker the spec pins. Both halves ARE rendered canonically and are in "
        "the right order, so the container-recursion behaviour is fully "
        "correct; but the graded assertion pins an exact mapping string "
        "containing the two-character marker, so a one-character marker does "
        "not match. " + _R_GRADED,
        "rationale": "attacks the exact spelling of the entry marker inside "
        "clause (C2) — a clause no other rival moves. swap-key-value-dict "
        "transposes the two halves AROUND the marker but keeps the marker "
        "itself intact, so before this case the marker's literal content was "
        "pinned by the spec but never demonstrated to be pinned. Refuted at a "
        "one-entry mapping with NO hypothesis about any opaque term: the two "
        "sides differ by exactly one character, so they cannot have equal "
        "length whatever the renderings are. A verify => SPEC-TOO-WEAK on the "
        "entry marker.",
        "witness": _W_SHORT_MARKER_DICT,
    },
    {
        "id": "no-braces-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_braces_dict,
        "refinement": "the faithful real patch returns the joined entries "
        "without the enclosing delimiter pair. Every entry is rendered "
        "canonically and correctly joined, so the container-recursion behaviour "
        "is present; but the graded assertion pins an exact mapping string that "
        "is delimited, so the bare join does not match. " + _R_GRADED,
        "rationale": "attacks the DELIMITER FRAME of the non-empty mapping "
        "rendering. wrong-empty-literal-dict moves only the EMPTY mapping's "
        "literal, so before this case every non-empty output's frame was a part "
        "of the spec no rival probed — an implementation that dropped the "
        "delimiters on non-empty mappings while keeping the empty literal right "
        "would have verified unnoticed. Refuted at a one-entry mapping with no "
        "hypothesis: the two sides differ by exactly the frame's two "
        "characters. A verify => SPEC-TOO-WEAK on the mapping's delimiters.",
        "witness": _W_NO_BRACES_DICT,
    },
    {
        "id": "no-separator-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_sep_dict,
        "refinement": "the faithful real patch joins the rendered ENTRIES of a "
        "mapping with nothing between them instead of with the two-character "
        "separator the spec pins. Both halves of every entry are still rendered "
        "canonically and in the right order, so the container-recursion "
        "behaviour is fully present; but the graded assertion pins an exact "
        "mapping string for a multi-entry mapping in which consecutive entries "
        "are separated, so the run-together output does not match. "
        + _R_GRADED,
        "rationale": "attacks clause (C3) on the MAPPING obligation. This is "
        "NOT a restatement of no-separator-set: the two obligations join through "
        "independent spec clauses — the mapping intercalates rendered ENTRIES, "
        "the collection rendered ELEMENTS — so before this case a rival that "
        "ran a mapping's entries together while keeping the collection's "
        "separator intact was refuted by no witness in the battery. It is also "
        "the only rival that probes `entries` at a TWO-entry list, so that "
        "binder is now varied across three shapes (empty / one / two entries) "
        "as `elems` already was. Refuted with NO hypothesis about any opaque "
        "term: the two sides differ by exactly the separator's two characters. "
        "A verify => SPEC-TOO-WEAK on the mapping's separator.",
        "witness": _W_NO_SEP_DICT,
    },
    {
        "id": "no-braces-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _no_braces_set,
        "refinement": "the faithful real patch returns a non-empty collection's "
        "joined elements without the enclosing delimiter pair. Every element is "
        "rendered canonically and correctly joined, and the empty collection's "
        "dedicated literal is untouched, so the container-recursion fix is "
        "present; but that shape's desired rendering of a non-empty collection "
        "is delimited, so the bare join is not it. " + _R_UNGRADED_SHAPE,
        "rationale": "attacks the DELIMITER FRAME of the non-empty COLLECTION "
        "rendering, which is a separate clause from the mapping's frame that "
        "no-braces-dict attacks — the collection's non-empty arm carries its own "
        "brace pair in its own spec clause — and a separate point from the "
        "empty arm that wrong-empty-literal-set moves. Before this case a rival "
        "that dropped the delimiters on every non-empty collection while "
        "answering the empty one correctly would have verified unnoticed. "
        "Refuted at a one-element collection with no hypothesis: the two sides "
        "differ by exactly the frame's two characters. A verify => "
        "SPEC-TOO-WEAK on the collection's delimiters.",
        "witness": _W_NO_BRACES_SET,
    },
    # --- the LENGTH-PRESERVING face of (C4-frame)/(C3)/(C2) ------------------
    # Every rival above that attacks a transparent literal is refuted by a
    # character COUNT, which is blind to any substitution that keeps the length.
    # These three attack the same three literals in the length-preserving
    # direction, so what is demonstrated is WHICH characters each one contains
    # and not merely how many.
    {
        "id": "wrong-delims-literal-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _delims_lit_dict,
        "refinement": "the faithful real patch encloses a mapping's joined "
        "entries in the SEQUENCE delimiter pair rather than the mapping's own. "
        "Every entry is rendered canonically, correctly ordered and correctly "
        "joined, and the output is still delimited and still the same length, so "
        "every structural property except the delimiters' identity is right; but "
        "the graded assertion pins an exact mapping string whose outer "
        "characters are the mapping's delimiters, so this does not match. "
        + _R_GRADED,
        "rationale": "attacks the CHARACTER CONTENT of the non-empty mapping's "
        "delimiter frame, which is a strictly different point from the frame's "
        "PRESENCE that no-braces-dict attacks. That rival deletes the frame and "
        "is refuted by counting characters; this one preserves the length "
        "exactly, so `_LENGTH` cannot see it and no witness in the battery could "
        "refute it before this case — the spec pinned which two characters the "
        "frame is, and nothing demonstrated it. The refutation therefore takes "
        "the swap-key-value-dict route: pin the two renderings to distinct "
        "concrete literals (ONE hypothesis per DISTINCT opaque term, so jointly "
        "satisfiable) and `decide` the resulting closed string equation. A "
        "verify => SPEC-TOO-WEAK on the identity of the mapping's delimiters.",
        "witness": _W_DELIMS_LIT_DICT,
    },
    {
        "id": "wrong-separator-literal-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _sep_lit_dict,
        "refinement": "the faithful real patch joins a mapping's rendered "
        "entries with a semicolon-plus-space instead of the comma-plus-space the "
        "spec pins. Entries canonical, ordered, delimited, and the joined output "
        "the same length as the desired one; only the separator's characters "
        "differ. The graded assertion pins an exact multi-entry mapping string "
        "using the comma separator, so this does not match. " + _R_GRADED,
        "rationale": "attacks the CHARACTER CONTENT of clause (C3) on the "
        "mapping, the length-preserving face that no-separator-dict's character "
        "count is blind to. Necessarily refuted at a TWO-entry mapping: at a "
        "ONE-entry mapping this rival is DEFINITIONALLY EQUAL to the frozen "
        "implementation, because a singleton join never reaches the separator — "
        "measured, the normalised hypothesis collapses to `True` against this "
        "rival at one entry exactly as it does against the frozen solution, so a "
        "one-entry witness would be attesting to a tactic mismatch and not to "
        "the spec. At two entries the two sides are closed strings of equal "
        "length differing in one character, refuted by pinning the four "
        "renderings to distinct literals and deciding. A verify => "
        "SPEC-TOO-WEAK on the identity of the mapping's separator.",
        "witness": _W_SEP_LIT_DICT,
    },
    {
        "id": "wrong-marker-literal-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _marker_lit_dict,
        "refinement": "the faithful real patch joins each entry's two rendered "
        "halves with a two-character arrow marker instead of the "
        "colon-plus-space the spec pins. Both halves canonical, in the right "
        "order, and the entry the right total length; only the marker's "
        "characters differ. The graded assertion pins an exact mapping string "
        "containing the colon-plus-space marker, so this does not match. "
        + _R_GRADED,
        "rationale": "attacks the CHARACTER CONTENT of the entry marker inside "
        "clause (C2), and it is the third distinct attack on that one literal: "
        "swap-key-value-dict transposes the halves AROUND the marker and leaves "
        "it intact, short-entry-marker-dict changes its LENGTH and is refuted by "
        "a count — so a rival that kept the marker's length and changed its "
        "characters slipped between the two and was refuted by nothing. Decided "
        "from two distinct pinned renderings, the only route available when the "
        "sides have equal length. A verify => SPEC-TOO-WEAK on the identity of "
        "the entry marker.",
        "witness": _W_MARKER_LIT_DICT,
    },
    # --- the SEQUENCE ORDER of the emitted pieces ---------------------------
    {
        "id": "reverse-entries-dict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rev_entries_dict,
        "refinement": "the faithful real patch emits a mapping's rendered "
        "entries in the reverse of the order the mapping enumerates them. Every "
        "entry is rendered canonically, in the right internal order, joined by "
        "the right separator and enclosed in the right delimiters, and the "
        "output has exactly the same length as the desired one — only the "
        "sequence of the entries differs. CAVEAT, measured rather than assumed, "
        "and it is narrower than the other mapping-side cases: the graded "
        "assertion for a two-entry mapping accepts EITHER enumeration order (it "
        "tests membership in a tuple of two acceptable strings, because the "
        "container's own enumeration order is not guaranteed), so a real patch "
        "that reversed the entries would still grade resolved on that assertion. "
        "This case is therefore retained on the narrower and true ground that "
        "the frozen spec DOES pin the positional correspondence — its clause "
        "maps over the entry list and intercalates the result, so the i-th "
        "rendered piece is the i-th entry's rendering — and a spec that fails to "
        "pin what it states is a defect independently of which orders the "
        "harness happens to accept. NOT retained on a graded-test argument, "
        "which the measurement does not support.",
        "rationale": "attacks the positional correspondence between the input "
        "list and the emitted sequence, on the mapping obligation — a clause no "
        "other rival in this battery moves. Every other rival changes the "
        "CONTENT of a rendering or the CHARACTERS of a literal; this one keeps "
        "every rendering canonical, every literal exact, and the total length "
        "IDENTICAL, so all four length-counting witnesses here are structurally "
        "blind to it. It is also distinct from swap-key-value-dict, which "
        "transposes the two halves WITHIN a single entry at a one-entry input "
        "and so says nothing about the order the entries themselves are emitted "
        "in. Refuted at a TWO-entry mapping — necessarily, since at one entry a "
        "reversal is definitionally the IDENTITY (measured: `String.intercalate "
        "sep [x] = String.intercalate sep [x].reverse` closes by `rfl`, so a "
        "one-entry witness would be attacking a rival that is not wrong there) — "
        "by pinning the four renderings to distinct literals and deciding the "
        "closed equation. A verify => SPEC-TOO-WEAK on entry ordering.",
        "witness": _W_REV_ENTRIES_DICT,
    },
    {
        "id": "reverse-elems-set",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rev_elems_set,
        "refinement": "the faithful real patch emits a non-empty collection's "
        "rendered elements in the reverse of the order the collection "
        "enumerates them. Every element is rendered canonically, the separator "
        "and delimiters are exact, the empty case is untouched, and the output "
        "length is unchanged. " + _R_UNGRADED_SHAPE,
        "rationale": "the same positional-correspondence clause on the "
        "COLLECTION obligation, and independent of reverse-entries-dict for the "
        "reason the other paired cases are independent: the two obligations map "
        "and intercalate through their OWN clauses, over rendered ELEMENTS here "
        "and rendered ENTRIES there, so a rival that reversed one while keeping "
        "the other in order was refuted by nothing. Refuted at a two-element "
        "collection — the smallest input where an order is observable at all — "
        "by pinning the two renderings to distinct literals and deciding the "
        "closed equation. A verify => SPEC-TOO-WEAK on element ordering.",
        "witness": _W_REV_ELEMS_SET,
    },
    # --- admissibility ------------------------------------------------------
    {
        "id": "adm-f2p-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _adm_points,
        "rationale": "the admissibility lane on this backend. Neither "
        "obligation has a precondition — both binders are unconstrained `List` "
        "types — so there is no precondition to over-strengthen and the "
        "classical PRECOND-TOO-STRONG attack has no surface. What this case "
        "rules out instead is the residual risk that survives that "
        "observation: an obligation closable in general but UNSATISFIABLE at "
        "the very input shapes the graded suite exercises. It discharges each "
        "obligation at those concrete points first — the empty mapping, a "
        "one-entry mapping, a TWO-entry mapping (the shape the graded "
        "multi-entry assertion exercises, and the smallest one that reaches the "
        "mapping's separator clause at all, so an obligation unsatisfiable only "
        "once a join actually happens would surface here and at no other point "
        "in this lane), the empty collection, a two-element collection — as "
        "`have`s proven by evaluation, and only then closes the frozen "
        "obligations verbatim, with both `theorem correct_*` STATEMENTS "
        "byte-identical and no new lemma or axiom. Must verify; a failure here "
        "would mean the spec is unsatisfiable at a graded input, which no "
        "soundness positive over the ∀-statement alone would surface.",
    },
]
