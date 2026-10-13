# properties.py — G-PBT falsification battery for astropy__astropy-14365 (lean).
#
# NOT a Lean file; a manifest the G-PBT gate parses. Each SPEC_TESTS case is a
# FULL Solution.lean source whose SPEC (docstring, axioms, pure, post-conditions
# regions) is byte-identical to the frozen Solution.lean — only the `impl-start`/
# `impl-end` region and (for a positive that must reprove) the `proof-start`/
# `proof-end` body differ. Every `theorem correct_<name>` STATEMENT is preserved
# verbatim, so a rejection is attributable to the postcondition and never to a
# neutered obligation. Checked mechanically by variant_scope.variant_problems.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (read off Solution.lean + mapping.md + refinement.md)
# ---------------------------------------------------------------------------
# Two obligations, one per modeled behavior of a case-insensitive textual table
# syntax. Both are stated as a bare input→output equality over a single input
# binder:
#
#   correct_classify : ∀ line,
#       problem_spec_classify line (implementation_classify line)
#     where problem_spec_classify line result := result = matchCategory true line
#     Input binder: `line : List Char`. The load-bearing content is the MODE
#     SELECTOR: the result must be the category the CASE-INSENSITIVE recognizer
#     assigns to the line as written — not the case-sensitive recognizer's
#     category, and not the case-sensitive recognizer's category on some
#     case-normalized rewrite of the line.
#
#   correct_readRow : ∀ tokens,
#       problem_spec_readRow tokens (implementation_readRow tokens)
#     where problem_spec_readRow tokens result := result = tokens.map cellOfToken
#     Input binder: `tokens : List (List Char)`. This single equality carries
#     FOUR independent obligations, and each is attacked separately below:
#       (a) the per-token DECISION — `isSentinel tok`, i.e. equality with the
#           sentinel up to letter-case (not raw equality, and not a coarser test
#           that swallows neighbouring reserved spellings);
#       (b) the per-token PAYLOAD — `missing` on a sentinel token, `number
#           (parseNumber tok)` otherwise;
#       (c) the ARITY — `List.map` gives exactly one output cell per input token,
#           so no token may be dropped or duplicated;
#       (d) the ORDER — `List.map` is order-preserving.
#
# `matchCategory` and `parseNumber` are `opaque` with NO constraining axiom, so
# the classify obligation cannot be attacked at a literal input: `decide` gets
# stuck on the opaque term. It is attacked by CONDITIONING on the carrier
# instead — assuming only that the two recognizer modes disagree at one concrete
# line, which is the precise sub-domain on which the rival is wrong. That
# assumption is a single inequality between two distinct opaque terms, so it is
# satisfiable (the gate's consistency probe cannot derive `False` from it);
# nothing about the recognizer's actual values is assumed.
#
# ---------------------------------------------------------------------------
# ATTACKS
# ---------------------------------------------------------------------------
#   - MODE-SELECTION (classify): a rival selecting the case-sensitive mode, and a
#     NEAR-MISS that reaches the case-sensitive mode through a case-normalizing
#     rewrite of the line. The near-miss agrees with gold wherever the syntax is
#     spelled with upper-case reserved words, so it carries its own witness at a
#     line whose reserved spelling is lower-case-only.
#   - POINTWISE SUB-DOMAIN (classify): both mode rivals above are wrong GLOBALLY,
#     so neither shows the equality is owed at each individual line. A third rival
#     selects the right mode everywhere except at one line — the signed spelling
#     of the value grammar's non-finite literal — which it declares unrecognized.
#     This is the carrier's counterpart of the nagini sibling's signed
#     non-finite sub-domain case.
#   - PARTIAL-DOMAIN (readRow, clause (a)): a rival testing the sentinel raw
#     instead of up-to-case, and a NEAR-MISS special-casing the two literal
#     spellings the obvious probes use — refuted only at a mixed-case spelling.
#   - OVER-BROAD DECISION (readRow, clause (a)): a rival whose sentinel test also
#     swallows the other reserved token of the value grammar, which must denote a
#     number and not a missing value.
#   - STRUCTURAL (readRow, clauses (c) and (d)): a rival emitting no cell for a
#     sentinel token, and a rival building the row in reverse. Both keep the
#     per-token decision exactly right, so they isolate the arity and ordering
#     content of the equality from its value content.
#   - POSITIVE CONTROLS (soundness): structurally different CORRECT impls, each
#     with a proof that actually closes for the new shape (no weakened
#     obligation, no helper beyond the frozen set, no `sorry`). Note which of
#     these are load-bearing: `pos-classify-mut-shape` is DEFINITIONALLY the
#     frozen impl (the frozen `rfl` still closes it verbatim), so it can only
#     witness that the spec is not sensitive to surface syntax `rfl` already sees
#     through. `pos-classify-match-shape` is the one that carries the weight on
#     the classify obligation: the frozen `rfl` fails on it and the obligation has
#     to be reproven.
#   - CONSTRUCTOR PAYLOAD (classify): all three rivals above return a wholly
#     different category VALUE (a different recognizer mode, or the rejecting
#     outcome), so none of them shows that the ARGUMENT a category carries is
#     pinned. `LineCategory.data n` carries the value-column count, and a rival
#     that selects the right mode, returns the right constructor, and shifts only
#     that count isolates exactly the constructor's payload from its tag.
#   - PAYLOAD SWAP (readRow, clause (b)): a rival whose per-token decision is
#     exactly right and whose two payloads are EXCHANGED — `missing` where a
#     number is owed and vice versa. This is the only clause of the readRow
#     equality that the decision/arity/order rivals leave unattacked: each of
#     them keeps both payloads correct, so none of them shows the equality pins
#     WHICH cell a token denotes once the decision is settled.
#   - ADMISSIBILITY: the frozen impl verifies, AND — the part that carries the
#     lane's content on a total carrier — each obligation is separately
#     discharged BY EVALUATION at concrete F2P-shaped inputs, as `have`s, before
#     the frozen obligation is closed verbatim. A total obligation has no
#     precondition to be literally too strong, so the analogue of
#     PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at exactly an
#     F2P-shaped point; discharging it at those points is what tests that
#     directly, and the frozen impl verifying on its own does not (a spec
#     unsatisfiable at one concrete line would still let `rfl` close the
#     universally quantified statement if the impl echoed it).
#
# ---------------------------------------------------------------------------
# CLASSES WITH NO COUNTERPART ON THIS CARRIER (the full list is right here; this
# manifest defines no `assessment` key, so there is no other place to look)
# ---------------------------------------------------------------------------
#   - FRAME/PERMISSION MUTATION: the nagini sibling's mandatory class, resting on
#     fractional permissions over a mutable input. Lean is referentially
#     transparent — an input cannot be written — so the class is VACUOUS here,
#     not omitted. No substitute is fabricated.
#   - DIVERGENCE / NON-TERMINATION: also vacuous on this backend. Both
#     `implementation_*` are total Lean `def`s, so a diverging rival cannot be
#     written at all. (This is NOT the velvet situation, where a partial-semantics
#     bundle admits such a rival vacuously and the correct disposition is a known
#     spec hole — cf. the corpus-wide termination-semantics finding. The nagini sibling carries no
#     divergence case for this instance either.)
#   - AXIOM_TESTS: dropped by design; the axiom lane belongs to G-AX.
#
# ---------------------------------------------------------------------------
# INDEPENDENT AUDIT — probes run against the FROZEN spec and not shipped as cases
# ---------------------------------------------------------------------------
# Wrong impls this battery does NOT contain, written to look for a spec hole. All
# were REJECTED by the frozen spec (impl build exit 1), and each was additionally
# confirmed refutable by a hand-built witness that elaborated against it (exit 0)
# and failed against the frozen solution (exit 1), so the rejections are the
# spec's and not a tactic gap:
#   * readRow PAYLOAD PROVENANCE — the number parsed from the CASE-FOLDED token
#     rather than the raw one. The spec pins `parseNumber tok` on the token as
#     WRITTEN, so folding the payload's argument is caught; conditioned witness.
#   * readRow ARITY, the other direction — a numeric token contributing TWO cells
#     (the shipped arity rival only drops one).
#   * readRow EMPTY-ROW — correct on every non-empty row, one cell on the empty
#     one. The empty `tokens` is admitted with no precondition, so it is pinned.
#   * readRow EMPTY-TOKEN boundary — the empty token treated as the sentinel.
#     `isSentinel []` is `false`, and the spec sees it.
#   * classify NORMALIZING the input by dropping spaces — the right mode on a
#     rewritten line. Pins that the category is owed for the line AS WRITTEN.
#   * readRow PARTIAL DOMAIN BY LENGTH — correct on every row of length ≤ 1 and
#     all-number on longer rows. Aimed at the binder this battery moves least:
#     every readRow witness but one sits at a one-token row, so a rival tuned to
#     agree there survives all of them. Refuted at a two-sentinel row.
#   * classify SABOTAGED ON A HYPOTHESIS-DESCRIBED SUB-DOMAIN — the right mode
#     everywhere except at the lines the recognizer itself calls pure comments,
#     which it declares unrecognized. Unlike the shipped pointwise rival this
#     names its sub-domain by the recognizer's OWN outcome rather than by a
#     literal line shape, so the conditioned witness carries no line-shape guard.
#   NB the COLUMN-COUNT payload probe is no longer listed here: it was promoted
#   into the battery as `uniq-classify-constructor-payload`, since it is the only
#   attack on the argument a `LineCategory` constructor carries.
# Correct RESHAPES checked for a soundness hole (spec too strong). All VERIFIED
# (exit 0), so the spec pins the input→output relation and not an impl shape:
#   * readRow as `List.foldl` with a reproven fold lemma (no monadic loop at all).
#   * readRow as a `List.map` with the per-token decision spelled inline, closed
#     by `List.map_congr_left`.
#   * classify through an identity rewrite of the input list, and through an
#     append-nil rewrite (NOT definitionally the frozen impl — closed by `simp`).
#   * classify through a case split on the recognizer's own outcome.
#   * readRow as a cons-accumulating `List.foldl` followed by a single reverse —
#     the traversal builds the row BACKWARDS and repairs it at the end, so it is
#     the correct twin of the shipped order rival. An earlier pass recorded this
#     as INCONCLUSIVE on the ground that the rewrite would not match through the
#     `Id.run`/`forIn` bridge; that was a consequence of keeping the monadic loop.
#     Dropping the loop with the accumulator (a non-monadic `def`, as the direct
#     map positive does) removes the bridge entirely and a two-case induction
#     closes it. Measured exit 0.
#   * readRow with the per-token fold spelled via `Char.toLower`/lower-case
#     sentinel instead of `toUpper`/upper-case. An earlier pass recorded this as
#     UNRESOLVED, on the ground that the needed per-character case-fold bridge
#     (`toLower w = "no" ↔ toUpper w = "NO"`) could not be closed inside the
#     no-new-lemma variant scope. That was wrong on both counts and is corrected
#     here: the bridge follows from the ambient `Char.toUpper_toLower_eq_toUpper`
#     / `Char.toLower_toUpper_eq_toLower` by `congrArg`, and it can be carried as
#     `have`s inside the restated loop lemma, so no new top-level lemma is
#     introduced. Measured: variant build exit 0, scope check clean. One spelling
#     detail is load-bearing and worth recording, since it is what makes this
#     look unclosable: after `congrArg (List.map Char.toUpper)`, `List.map_map`
#     leaves the goal over the COMPOSITION `Char.toUpper ∘ Char.toLower`, which
#     the per-character rewrite does not match until `Function.comp_def` unfolds
#     it. Without that the rewrite silently no-ops and the `simpa` closes
#     nothing. The
#     hand-rolled `Char.toNat`/`omega` route the earlier pass tried does loop in
#     `simp`, which is presumably what it measured — a tactic dead end, not a
#     carrier limit.
from pathlib import Path

INSTANCE = "astropy__astropy-14365"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------
# Each anchor lies ENTIRELY inside the region it names and is unique in the file.
# The `impl-end` sentinel is folded into the classify anchor because the same
# one-line application also appears (differently spaced) in the spec docstring
# region; the readRow anchors carry their `acc := acc ++ …` lines, which the
# proof region spells with `r ++ …` inside a `ForInStep.yield`.

_IMPL_CLASSIFY = "  matchCategory true line\n-- impl-end"

# The frozen classify proof body. Sliced so it breaks loudly if the proof is
# retuned; needed by the positive control whose impl is NOT definitionally the
# frozen one and therefore cannot reuse the bare `rfl`.
_PROOF_CLASSIFY = ("theorem correct_classify :\n"
                   "    ∀ line : List Char,\n"
                   "      problem_spec_classify line (implementation_classify line) := by\n"
                   "  intro line\n  rfl\n")
assert _BASE.count(_PROOF_CLASSIFY) == 1, "drift: classify proof region not unique"

_IMPL_READROW = """  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := acc ++ [Cell.missing]
    else
      acc := acc ++ [Cell.number (parseNumber v)]
  return acc
"""

# The whole frozen readRow proof region body (helper lemma + obligation). Sliced
# rather than pasted so it breaks loudly if the frozen proof is ever retuned.
_PROOF_READROW = _BASE[_BASE.index("/-- The appending `forIn`"):
                       _BASE.index("-- proof-end", _BASE.index("/-- The appending `forIn`"))]
assert _BASE.count(_PROOF_READROW) == 1, "drift: readRow proof region not unique"


def _readrow_loop(cond, then_branch, else_branch):
    """A readRow impl body with the per-token branch rewritten."""
    return f"""  let mut acc : List Cell := []
  for v in tokens do
    if {cond} then
      acc := acc ++ [{then_branch}]
    else
      acc := acc ++ [{else_branch}]
  return acc
"""


# =============================================================================
# POSITIVE CONTROLS (soundness) — structurally different CORRECT impls, each
# reproven honestly for its new shape. `theorem correct_*` statements untouched.
# =============================================================================

# classify: same mode selection, threaded through mutable local state instead of
# being returned directly. Definitionally equal, so `rfl` still closes.
_POS_CLASSIFY = _swap(
    _BASE, _IMPL_CLASSIFY,
    """  Id.run do
  let mut cat : LineCategory := LineCategory.unrecognized
  cat := matchCategory true line
  return cat
-- impl-end""")

# classify: the SAME mode selection, but reached through a case split on the
# line's own shape. Unlike `_POS_CLASSIFY` this impl is NOT definitionally the
# frozen one — the frozen `rfl` does NOT close it (measured: `Tactic 'rfl'
# failed: line is not definitionally equal to implementation_classify line`), so
# the obligation is genuinely REPROVEN for the new shape (`cases line <;> rfl`)
# rather than inherited. That is what makes it a load-bearing soundness control:
# a spec pinning the impl's SYNTACTIC form would reject it.
_POS_CLASSIFY_MATCH = _swap(
    _swap(_BASE, _IMPL_CLASSIFY,
          """  match line with
  | [] => matchCategory true []
  | c :: cs => matchCategory true (c :: cs)
-- impl-end"""),
    _PROOF_CLASSIFY,
    _PROOF_CLASSIFY.replace("  intro line\n  rfl\n",
                            "  intro line\n  cases line <;> rfl\n"))

# readRow: the accumulating traversal replaced by the direct per-token map. The
# postcondition's right-hand side is FULLY GROUNDED in the input binder (the
# per-token decision is spelled out in the `pure` region; only the number
# payload is an unchanged callee), so this is the cheapest CORRECT impl, not a
# wrong echo of an answer-key oracle. It must verify — and its verifying is the
# demonstration that there is no ungrounded oracle here to exploit. The loop's
# induction lemma is no longer needed and goes with the loop; the obligation is
# reproven by `rfl`.
_POS_READROW_MAP = _swap(
    _swap(_BASE, _IMPL_READROW, "  tokens.map cellOfToken\n"),
    _PROOF_READROW,
    """theorem correct_readRow :
    ∀ tokens : List (List Char),
      problem_spec_readRow tokens (implementation_readRow tokens) := by
  intro tokens
  rfl
""")
# `:= Id.run do` no longer fits a non-monadic body.
_POS_READROW_MAP = _swap(
    _POS_READROW_MAP,
    "def implementation_readRow (tokens : List (List Char)) : List Cell := Id.run do\n",
    "def implementation_readRow (tokens : List (List Char)) : List Cell :=\n")

# readRow: same accumulating traversal, branches REORDERED (the number branch is
# tested first, via the negated condition). Keeps the loop, so the induction
# lemma is kept too — restated over the reordered branch and reproven, with the
# `correct_readRow` statement byte-identical to the frozen one.
_POS_READROW_REORDER = _swap(
    _swap(_BASE, _IMPL_READROW,
          _readrow_loop("v.map Char.toUpper ≠ ['N', 'O']",
                        "Cell.number (parseNumber v)", "Cell.missing")),
    _PROOF_READROW,
    """theorem readRow_helper (tokens : List (List Char)) (init : List Cell) :
    (Id.run (forIn tokens init (fun v r =>
        (if v.map Char.toUpper ≠ ['N', 'O']
          then ForInStep.yield (r ++ [Cell.number (parseNumber v)])
          else ForInStep.yield (r ++ [Cell.missing]) : Id (ForInStep (List Cell))))))
    = init ++ tokens.map cellOfToken := by
  induction tokens generalizing init with
  | nil => simp
  | cons a as ih =>
    rw [List.forIn_cons, List.map_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.map Char.toUpper = ['N', 'O']
    · simp only [h, ne_eq, not_true_eq_false, if_false, ih]
      simp [cellOfToken, isSentinel, h]
    · simp only [ne_eq, h, not_false_eq_true, if_true, ih]
      simp [cellOfToken, isSentinel, h]

theorem correct_readRow :
    ∀ tokens : List (List Char),
      problem_spec_readRow tokens (implementation_readRow tokens) := by
  intro tokens
  unfold problem_spec_readRow implementation_readRow
  have h2 : (Id.run (do
      let r ← forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper ≠ ['N', 'O']
          then (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.number (parseNumber v)])))
          else (do pure PUnit.unit; pure (ForInStep.yield (r ++ [Cell.missing])))
            : Id (ForInStep (List Cell)))
      pure r) : List Cell)
    = Id.run (forIn tokens ([] : List Cell) fun v r =>
        (if v.map Char.toUpper ≠ ['N', 'O']
          then ForInStep.yield (r ++ [Cell.number (parseNumber v)])
          else ForInStep.yield (r ++ [Cell.missing]) : Id (ForInStep (List Cell)))) :=
    rfl
  show (Id.run _ : List Cell) = tokens.map cellOfToken
  rw [h2, readRow_helper]
  simp
""")


# =============================================================================
# ADMISSIBILITY — the obligation discharged AT CONCRETE F2P-SHAPED INPUTS.
# =============================================================================
# Both obligations are total over their binder, so there is no precondition
# hypothesis that could be literally too strong. The analogue on a total carrier
# is the obligation being UNSATISFIABLE at exactly an F2P-shaped point, and what
# tests that is discharging it AT those points by evaluation, as a `have`, before
# closing the frozen obligation verbatim. The frozen impl merely verifying does
# not test it: `rfl` closes the quantified statement from the impl's shape alone.
#
# The points are chosen to be the ones the modeled behaviors actually receive:
#   classify — the lower-case header command of the reported reproducer, and a
#     multi-token data line whose trailing value is the signed non-finite literal;
#   readRow — the EMPTY row (admitted with no precondition), and a mixed row
#     carrying a lower-case sentinel, a number, the signed non-finite literal and
#     an upper-case sentinel together.
# The classify `have`s close by `rfl` (the mode selection is definitional at any
# literal line); the readRow ones close by evaluating the per-token decision.
_ADMISS = _swap(
    _swap(_BASE, _PROOF_CLASSIFY,
          _PROOF_CLASSIFY.replace(
              "  intro line\n  rfl\n",
              """  have _hcmd : problem_spec_classify "read serr 1 2".toList
      (implementation_classify "read serr 1 2".toList) := by
    unfold problem_spec_classify implementation_classify
    rfl
  have _hrow : problem_spec_classify "1 -nan".toList
      (implementation_classify "1 -nan".toList) := by
    unfold problem_spec_classify implementation_classify
    rfl
  intro line
  rfl
""")),
    ("theorem correct_readRow :\n"
     "    ∀ tokens : List (List Char),\n"
     "      problem_spec_readRow tokens (implementation_readRow tokens) := by\n"
     "  intro tokens\n"),
    ("theorem correct_readRow :\n"
     "    ∀ tokens : List (List Char),\n"
     "      problem_spec_readRow tokens (implementation_readRow tokens) := by\n"
     """  have _hempty : problem_spec_readRow [] (implementation_readRow []) := by
    unfold problem_spec_readRow implementation_readRow
    simp
  have _hmixed : problem_spec_readRow
      [['n', 'o'], ['1'], ['-', 'n', 'a', 'n'], ['N', 'O']]
      (implementation_readRow
        [['n', 'o'], ['1'], ['-', 'n', 'a', 'n'], ['N', 'O']]) := by
    unfold problem_spec_readRow implementation_readRow
    simp [cellOfToken, isSentinel]
  intro tokens
"""))


# =============================================================================
# UNIQUENESS RIVALS (expect="reject"), each with a witness SEEN to discriminate:
# it elaborates against the rival and FAILS against the frozen solution.
# =============================================================================

# --- classify: the wrong mode ------------------------------------------------
_RIVAL_MODE = _swap(_BASE, _IMPL_CLASSIFY, "  matchCategory false line\n-- impl-end")

# Conditioned on the carrier: `matchCategory` is opaque, so the refutation is
# stated at a point described by hypothesis. The hypothesis is the single
# inequality that says the two modes disagree at this line — exactly the
# sub-domain where the rival is wrong, and satisfiable (two distinct opaque
# terms; nothing is assumed about either one's value).
_WIT_MODE = """example (h : matchCategory false "read serr 1 2".toList
             ≠ matchCategory true "read serr 1 2".toList) :
    ¬ problem_spec_classify "read serr 1 2".toList
        (implementation_classify "read serr 1 2".toList) := by
  unfold problem_spec_classify implementation_classify
  exact h
"""

# --- classify: NEAR-MISS — the wrong mode reached via a case-normalizing
# rewrite of the input. Agrees with gold on every line whose reserved words are
# spelled in upper case, so it needs its own witness at a line whose reserved
# spelling is lower-case-only.
_RIVAL_FOLD = _swap(_BASE, _IMPL_CLASSIFY,
                    "  matchCategory false (line.map Char.toUpper)\n-- impl-end")

_WIT_FOLD = """example (h : matchCategory false "1 NAN".toList ≠ matchCategory true "1 nan".toList) :
    ¬ problem_spec_classify "1 nan".toList
        (implementation_classify "1 nan".toList) := by
  unfold problem_spec_classify implementation_classify
  simpa using h
"""

# --- classify: the right mode, sabotaged on ONE line of the value grammar -----
# Both existing classify rivals get the MODE wrong globally. This one selects the
# case-insensitive mode correctly everywhere except at the lines whose trailing
# value is the signed spelling of the value grammar's non-finite literal, which it
# declares unrecognized. So it isolates the postcondition's per-line content from
# its mode content: the spec must pin the category AT EVERY line, not merely "the
# case-insensitive recognizer is the one consulted in general". This is the
# carrier's counterpart of the nagini sibling's signed-non-finite sub-domain case
# (`partial-reserved-drop-signed-nan`), which the port had recorded as having no
# counterpart here.
#
# AUDIT NOTE (retargeted). The first port of this case sabotaged the single line
# whose ENTIRE text is the plus-signed spelling of that literal. That rival is
# wrong and its witness did discriminate, but its `refinement` argument was false
# in two ways, and the argument is the whole point of a reject case: the standing
# fixtures carry the MINUS-signed spelling and never the plus-signed one, and they
# carry it as the trailing VALUE of a multi-token data row, never as a line equal
# to the bare literal. So the faithful patch of that rival broke no standing test
# and the refinement claim was unsupported. Retargeted to the SUFFIX form, which
# sabotages exactly the fixture-shaped line, making the refinement true. Measured:
# rival build exit 0, frozen-solution build exit 1 (`hh` reduces to `True` on gold,
# i.e. simp PROVES the equality there), consistency probe exit 1.
_RIVAL_SIGNED_NONFINITE = _swap(
    _BASE, _IMPL_CLASSIFY,
    "  if \"-nan\".toList.isSuffixOf line then LineCategory.unrecognized "
    "else matchCategory true line\n-- impl-end")

# Same conditioning technique as the other classify witnesses: `matchCategory` is
# opaque, so the refutation is stated at a point described by HYPOTHESIS. The
# hypothesis is one inequality between two distinct terms (the recognizer's
# category for this line is not the rejecting outcome), hence satisfiable — the
# consistency probe cannot derive `False` from it. Nothing about the recognizer's
# actual value is assumed. The rival's guard is decided (`decide`) rather than
# assumed, so the refutation is pinned to this concrete line and not to the guard.
_WIT_SIGNED_NONFINITE = """example (h : matchCategory true "1 -nan".toList ≠ LineCategory.unrecognized) :
    ¬ problem_spec_classify "1 -nan".toList
        (implementation_classify "1 -nan".toList) := by
  unfold problem_spec_classify implementation_classify
  have hs : "-nan".toList.isSuffixOf "1 -nan".toList = true := by decide
  simp only [hs, if_true]
  exact fun hh => h hh.symm
"""

# --- classify: the right mode, the right CONSTRUCTOR, the wrong ARGUMENT ------
# AUDIT NOTE (added by the independent audit). Every other classify rival returns
# a wholly different category VALUE: two select the wrong recognizer mode, and the
# third substitutes the rejecting outcome. So none of them attacks the ARGUMENT a
# category carries — `LineCategory.data ncol` carries the value-column count, and
# a spec that pinned only the constructor TAG would have been indistinguishable
# from this one under the shipped battery. This rival consults the case-insensitive
# recognizer, keeps whatever constructor it returns, and shifts only the carried
# count. The shift is by one rather than a flatten to zero on purpose: flattening
# coincides with gold on every line the recognizer already scores at zero columns,
# whereas `n + 1 ≠ n` at every `n`, so the rival is wrong on the whole `data`
# sub-domain and not merely on part of it.
#
# Measured: rival impl build exit 1; witness exit 0 against the rival and exit 1
# against the frozen solution (`unsolved goals n : ℕ, h : … ⊢ False` — a plain
# evaluation, gold's goal reduced away); consistency probe exit 1; and the
# forgery pair (assert the spec HOLDS at the same point under the same binders)
# exit 0 on gold / exit 1 on the rival, so gold's exit code tracks the claim.
_RIVAL_CONSTRUCTOR_PAYLOAD = _swap(
    _BASE, _IMPL_CLASSIFY,
    """  match matchCategory true line with
  | LineCategory.data n => LineCategory.data (n + 1)
  | c => c
-- impl-end""")

# Conditioned like the other classify witnesses, because `matchCategory` is
# opaque: the hypothesis says only that the recognizer scores this line as a data
# line with SOME column count. It binds that count as a variable rather than a
# literal, so nothing is assumed about the recognizer's actual value and the
# hypothesis is satisfiable (the probe cannot derive `False` from it). The
# refutation is then `n + 1 ≠ n`, which `simp` closes from `LineCategory.data`'s
# injectivity — no guard on the line's shape is needed at all.
_WIT_CONSTRUCTOR_PAYLOAD = """example (n : Nat) (h : matchCategory true "1 2".toList = LineCategory.data n) :
    ¬ problem_spec_classify "1 2".toList
        (implementation_classify "1 2".toList) := by
  unfold problem_spec_classify implementation_classify
  rw [h]
  simp
"""

# --- readRow (a): the per-token decision, tested raw instead of up-to-case ----
_RIVAL_RAW = _swap(_BASE, _IMPL_READROW,
                   _readrow_loop("v = ['N', 'O']",
                                 "Cell.missing", "Cell.number (parseNumber v)"))

_WIT_RAW = """example : ¬ problem_spec_readRow [['n', 'o']]
    (implementation_readRow [['n', 'o']]) := by
  unfold problem_spec_readRow implementation_readRow
  simp [cellOfToken, isSentinel]
"""

# --- readRow (a): NEAR-MISS — the two literal spellings an obvious probe uses,
# special-cased instead of folded. Agrees with gold at both `['N','O']` and
# `['n','o']`, so it is refuted only at a MIXED-case spelling.
_RIVAL_TWO_SPELLINGS = _swap(
    _BASE, _IMPL_READROW,
    _readrow_loop("v = ['N', 'O'] || v = ['n', 'o']",
                  "Cell.missing", "Cell.number (parseNumber v)"))

_WIT_TWO_SPELLINGS = """example : ¬ problem_spec_readRow [['N', 'o']]
    (implementation_readRow [['N', 'o']]) := by
  unfold problem_spec_readRow implementation_readRow
  simp [cellOfToken, isSentinel]
"""

# --- readRow (a): OVER-BROAD decision — the fold is right, but the test also
# swallows the value grammar's other reserved token, which must denote a NUMBER.
_RIVAL_OVERBROAD = _swap(
    _BASE, _IMPL_READROW,
    _readrow_loop("v.map Char.toUpper = ['N', 'O'] || v.map Char.toUpper = ['N', 'A', 'N']",
                  "Cell.missing", "Cell.number (parseNumber v)"))

# `simp` on the goal reduces the opaque number payload on the gold side into a
# shape whose `Decidable` instance will not synthesize, so the refutation is
# driven into the HYPOTHESIS instead: assume the spec holds here and simplify it
# to `False`. Against gold the same script leaves `h : True`, i.e. the spec is
# satisfied at this input, and the build fails — which is the discrimination.
_WIT_OVERBROAD = """example : ¬ problem_spec_readRow [['n', 'a', 'n']]
    (implementation_readRow [['n', 'a', 'n']]) := by
  intro h
  rw [problem_spec_readRow] at h
  simp [implementation_readRow, cellOfToken, isSentinel] at h
"""

# --- readRow (b): PAYLOAD SWAP — the per-token decision is exactly right and the
# two payloads are EXCHANGED. Every other readRow rival keeps both payloads
# correct (they attack the decision, the arity, or the order), so this is the only
# case that pins WHICH cell a token denotes once the decision is settled.
# Measured: rival build exit 1; witness exit 0 against the rival and exit 1
# against the frozen solution, with gold's failure a plain evaluation (`unsolved
# goals ⊢ False`); the flipped claim (assert the spec HOLDS at this input) builds
# exit 0 on gold and exit 1 on the rival, so gold's exit code tracks the claim.
_RIVAL_PAYLOAD_SWAP = _swap(
    _BASE, _IMPL_READROW,
    _readrow_loop("v.map Char.toUpper = ['N', 'O']",
                  "Cell.number (parseNumber v)", "Cell.missing"))

_WIT_PAYLOAD_SWAP = """example : ¬ problem_spec_readRow [['N', 'O']]
    (implementation_readRow [['N', 'O']]) := by
  unfold problem_spec_readRow implementation_readRow
  simp [cellOfToken, isSentinel]
"""

# --- readRow (c): ARITY — the decision and both payloads are exactly right, but
# a sentinel token contributes no cell, so the row is short.
_RIVAL_DROP = _swap(_BASE, _IMPL_READROW, """  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := acc
    else
      acc := acc ++ [Cell.number (parseNumber v)]
  return acc
""")

_WIT_DROP = """example : ¬ problem_spec_readRow [['N', 'O']]
    (implementation_readRow [['N', 'O']]) := by
  unfold problem_spec_readRow implementation_readRow
  simp [cellOfToken, isSentinel]
"""

# --- readRow (d): ORDER — every cell is individually correct and the arity is
# right; the row is built back to front. Refuted only at a MULTI-token input, so
# this witness also varies the length of the input binder.
_RIVAL_REVERSE = _swap(_BASE, _IMPL_READROW, """  let mut acc : List Cell := []
  for v in tokens do
    if v.map Char.toUpper = ['N', 'O'] then
      acc := Cell.missing :: acc
    else
      acc := Cell.number (parseNumber v) :: acc
  return acc
""")

_WIT_REVERSE = """example : ¬ problem_spec_readRow [['N', 'O'], ['1']]
    (implementation_readRow [['N', 'O'], ['1']]) := by
  unfold problem_spec_readRow implementation_readRow
  simp [cellOfToken, isSentinel]
"""


SPEC_TESTS = [
    # ---- POSITIVE CONTROLS (soundness) -----------------------------------
    {
        "id": "pos-classify-mut-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLASSIFY,
        "rationale": "structurally different but CORRECT classify: the same "
                     "case-insensitive mode selection, threaded through a mutable "
                     "local instead of returned directly. `problem_spec_classify "
                     "line result := result = matchCategory true line` holds "
                     "definitionally, and the frozen `correct_classify` statement is "
                     "reproven (`rfl` still closes). Must verify, else "
                     "SPEC-TOO-STRONG: the spec would be pinning an impl SHAPE "
                     "rather than the input→output relation it states. CAVEAT on how "
                     "much this case proves: the mutable-local body is "
                     "DEFINITIONALLY the frozen one, so the frozen `rfl` closes it "
                     "unchanged and the obligation is inherited rather than reproven. "
                     "It therefore cannot detect a spec that pins the impl's "
                     "syntactic form; `pos-classify-match-shape` is the control that "
                     "can, and it is the one to read as this obligation's real "
                     "soundness evidence.",
    },
    {
        "id": "pos-classify-match-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_CLASSIFY_MATCH,
        "rationale": "structurally different but CORRECT classify, and — unlike "
                     "`pos-classify-mut-shape` — NOT definitionally the frozen impl: "
                     "the same case-insensitive mode selection reached through a case "
                     "split on the line's own shape. The frozen `rfl` does NOT close "
                     "this impl (measured: `rfl failed: line is not definitionally "
                     "equal to implementation_classify line`), so `correct_classify` is "
                     "genuinely REPROVEN for the new shape by `cases line <;> rfl` "
                     "rather than inherited unchanged. That is what makes it "
                     "load-bearing: the mutable-local positive is defeq to gold and so "
                     "cannot detect a spec that pins the impl's syntactic form, whereas "
                     "this one can. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-readrow-direct-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_READROW_MAP,
        "rationale": "structurally different but CORRECT readRow: the accumulating "
                     "traversal replaced by the direct per-token map, and "
                     "`correct_readRow` reproven by `rfl` (the loop's induction lemma "
                     "goes with the loop; no new lemma is introduced, no obligation "
                     "weakened). This is also the GROUNDED-ECHO control: the "
                     "postcondition's right-hand side is `tokens.map cellOfToken`, "
                     "fully grounded in the input binder (the per-token decision is "
                     "spelled out in the `pure` region; only the number payload is an "
                     "unchanged callee), so writing that term IS the cheapest correct "
                     "impl rather than an echo of an ungrounded answer-key. Its "
                     "verifying is the evidence that there is no wrong echo to build.",
    },
    {
        "id": "pos-readrow-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_READROW_REORDER,
        "rationale": "structurally different but CORRECT readRow: the accumulating "
                     "traversal is kept and its per-token branches are REORDERED (the "
                     "number branch tested first via the negated condition). The "
                     "induction lemma is restated over the reordered branch and "
                     "reproven; the `correct_readRow` statement is byte-identical. "
                     "Must verify, else SPEC-TOO-STRONG.",
    },
    # ---- ADMISSIBILITY ---------------------------------------------------
    {
        "id": "admiss-f2p-shaped-inputs",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "each obligation is discharged AT CONCRETE F2P-SHAPED INPUTS — as "
                     "`have`s proven by evaluation — before the frozen obligation is "
                     "closed verbatim. Both obligations are total over their binder, so "
                     "no precondition hypothesis can be literally too strong; the "
                     "analogue of PRECOND-TOO-STRONG on a total carrier is the "
                     "obligation being UNSATISFIABLE at exactly the shape of input the "
                     "modeled behavior receives, and discharging it at those points is "
                     "what tests that directly. The frozen impl merely verifying does "
                     "NOT: `rfl` closes the quantified statement from the impl's shape "
                     "alone, so a spec unsatisfiable at one concrete line would still "
                     "pass. Points pinned: classify at the lower-case header command of "
                     "the reported reproducer and at a multi-token data line whose "
                     "trailing value is the signed non-finite literal; readRow at the "
                     "EMPTY row (admitted with no precondition) and at a mixed row "
                     "carrying a lower-case sentinel, a number, the signed non-finite "
                     "literal and an upper-case sentinel together. Must verify, else "
                     "PRECOND-TOO-STRONG.",
    },
    # ---- UNIQUENESS: classify, the mode selector -------------------------
    {
        "id": "uniq-classify-case-sensitive-mode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_MODE,
        "rationale": "attacks the ONLY clause of `problem_spec_classify`: `result = "
                     "matchCategory true line`. The rival selects the case-sensitive "
                     "mode, so its result is `matchCategory false line`, which the "
                     "postcondition equality forbids at every line where the two modes "
                     "disagree. Binder varied: `line`, at a header line written in "
                     "lower case.",
        "refinement": "a faithful patch built this way keeps recognition "
                      "case-sensitive, which is precisely the reported defect: the "
                      "issue's own reproducer — a file whose header command is written "
                      "in lower case — is still rejected as an unrecognized line, and "
                      "the F2P round-trip over the all-lower-case rendering of the "
                      "fixture aborts at line classification before any value is ever "
                      "read. It does not resolve.",
        "witness": _WIT_MODE,
    },
    {
        "id": "uniq-classify-normalize-then-case-sensitive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FOLD,
        "rationale": "NEAR-MISS against the same clause: the rival reaches the "
                     "case-sensitive mode through a case-normalizing rewrite of the "
                     "line, so it AGREES with gold on every line whose reserved words "
                     "are spelled in upper case — including the input that refutes "
                     "`uniq-classify-case-sensitive-mode`. Hence its own witness, at a "
                     "line containing the value grammar's lower-case-only reserved "
                     "spelling, which the rewrite destroys. The postcondition demands "
                     "the category of the line AS WRITTEN under the case-insensitive "
                     "mode, not the category of a rewritten line under the "
                     "case-sensitive one. Binder varied: `line`, at a data line whose "
                     "reserved token is case-sensitive in the grammar.",
        "refinement": "a faithful patch built this way (normalize the line's case, "
                      "then match case-sensitively) does accept lower-case header and "
                      "table-break lines, so it would look like a fix for the reported "
                      "reproducer. But the recognized syntax mixes reserved words that "
                      "are spelled upper-case with one that is spelled lower-case, so "
                      "normalizing the line breaks recognition of the latter: a data "
                      "row containing the non-finite value literal becomes "
                      "unrecognized and raises. That literal appears in the standing "
                      "P2P fixtures (a hardness-ratio row, and the worked example "
                      "whose non-finite cell is asserted on), so the patch would turn "
                      "passing tests red and does not resolve.",
        "witness": _WIT_FOLD,
    },
    {
        "id": "uniq-classify-signed-nonfinite-line",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SIGNED_NONFINITE,
        "rationale": "attacks `result = matchCategory true line` POINTWISE rather than "
                     "at the mode selector. Both other classify rivals get the mode "
                     "wrong globally, so neither shows the equality is required at each "
                     "individual line; this rival selects the case-insensitive mode "
                     "correctly EVERYWHERE except at lines whose trailing value is the "
                     "signed spelling of the value grammar's non-finite literal, which "
                     "it declares unrecognized. The postcondition is an equality at "
                     "every line, so a single sabotaged line violates it. Binder varied: "
                     "`line`, at a MULTI-token data line whose trailing value is the "
                     "signed non-finite literal — a point no other case in this battery "
                     "reaches, and (unlike the bare literal the first port of this case "
                     "used) the shape the standing fixtures actually contain.",
        "refinement": "a faithful patch built this way recognizes the syntax "
                      "case-insensitively — so the reported reproducer reads — yet "
                      "rejects a data row whose trailing value is the signed spelling of "
                      "the non-finite literal, raising on a line the value grammar "
                      "admits. The standing P2P fixtures contain exactly such a row (a "
                      "hardness-ratio block whose final cell is that signed spelling, "
                      "read by the multi-table reader test), so the patch turns a "
                      "passing test red. It does not resolve. NB the sign matters: the "
                      "fixtures carry the MINUS-signed spelling and never the "
                      "plus-signed one, so a rival sabotaging only the plus-signed form "
                      "would leave every standing test green and could not carry this "
                      "argument — which is why this case is stated at the minus-signed "
                      "suffix.",
        "witness": _WIT_SIGNED_NONFINITE,
    },
    {
        "id": "uniq-classify-constructor-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_CONSTRUCTOR_PAYLOAD,
        "rationale": "attacks the ARGUMENT a category carries rather than which "
                     "category is returned. The other three classify rivals all "
                     "return a wholly different value — two pick the wrong "
                     "recognizer mode, one substitutes the rejecting outcome — so "
                     "under those alone a spec pinning only the constructor TAG "
                     "would look identical to this one. This rival consults the "
                     "case-insensitive recognizer, keeps whatever constructor it "
                     "returns, and shifts only the value-column count of "
                     "`LineCategory.data ncol`. `result = matchCategory true line` "
                     "is an equality of category VALUES, so the carried count is "
                     "pinned too. The shift is by one rather than a flatten to "
                     "zero deliberately: flattening agrees with gold wherever the "
                     "recognizer already scores zero columns, while `n + 1 ≠ n` at "
                     "every `n`. Binder varied: `line`, at a multi-token data line, "
                     "and the witness additionally varies the CARRIED COUNT as a "
                     "bound variable rather than fixing it to a literal.",
        "refinement": "a faithful patch built this way recognizes the syntax "
                      "case-insensitively — so the reported reproducer's header "
                      "command reads — but reports one more value column than a "
                      "data row actually has. The column count is what the reader "
                      "uses to bind a row's values to the table's columns, so "
                      "every data row is read one column wider than it is: the "
                      "declared error columns no longer line up with the values "
                      "behind them, and a row whose count is checked against the "
                      "header's is rejected outright. The F2P round-trip compares "
                      "the re-read table's columns against the original's and "
                      "asserts on a specific error column's contents, so it fails "
                      "on the comparison; the standing P2P tests that read a "
                      "fixed-width worked example and assert individual cells fail "
                      "with it. It does not resolve.",
        "witness": _WIT_CONSTRUCTOR_PAYLOAD,
    },
    # ---- UNIQUENESS: readRow, clause (a) — the per-token decision --------
    {
        "id": "uniq-readrow-raw-sentinel-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_RAW,
        "rationale": "attacks clause (a) of `problem_spec_readRow`: the per-token "
                     "decision must be `isSentinel tok`, i.e. equality with the "
                     "sentinel UP TO LETTER-CASE. The rival compares raw, so on a "
                     "lower-case spelling of the sentinel it emits a number cell where "
                     "`tokens.map cellOfToken` demands `missing`. Binder varied: "
                     "`tokens`, at a one-token row whose token is the lower-case "
                     "sentinel spelling.",
        "refinement": "a faithful patch built this way leaves the missing-value test "
                      "case-sensitive, so a lower-case sentinel token falls through to "
                      "number parsing and raises on a token that is not a number. The "
                      "F2P round-trip over the all-lower-case rendering of the fixture "
                      "— whose data rows carry exactly such tokens — fails while "
                      "reading values. It does not resolve.",
        "witness": _WIT_RAW,
    },
    {
        "id": "uniq-readrow-two-literal-spellings",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_TWO_SPELLINGS,
        "rationale": "NEAR-MISS against clause (a): the rival special-cases the two "
                     "all-upper and all-lower spellings, so it agrees with gold at "
                     "both — including the input that refutes "
                     "`uniq-readrow-raw-sentinel-test`. Its witness therefore sits at a "
                     "MIXED-case spelling, where a genuine fold still says `missing` "
                     "and the special-case says `number`. This is what shows the spec "
                     "pins the fold itself and not a finite list of spellings the "
                     "battery happens to probe. Binder varied: `tokens`, at a "
                     "one-token row whose token is a mixed-case sentinel spelling.",
        "refinement": "a faithful patch built this way enumerates two spellings "
                      "instead of comparing up to case, so a hand-written file using a "
                      "mixed-case spelling of the missing-value token still falls "
                      "through to number parsing and raises — the very class of "
                      "hand-written input the issue is about. The stated desired "
                      "behavior is case-insensitivity of the syntax, not tolerance of "
                      "two extra spellings, so this is an incomplete fix that leaves "
                      "the reported failure reachable.",
        "witness": _WIT_TWO_SPELLINGS,
    },
    {
        "id": "uniq-readrow-overbroad-sentinel-test",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_OVERBROAD,
        "rationale": "attacks clause (a) from the OTHER side: the rival's fold is "
                     "correct but its test is too coarse — it also matches the value "
                     "grammar's other reserved token, which the postcondition requires "
                     "to denote `number (parseNumber tok)` and not `missing`. So the "
                     "spec pins the decision's boundary in both directions, not merely "
                     "that the sentinel is recognized. Binder varied: `tokens`, at a "
                     "one-token row whose token is the non-finite value literal.",
        "refinement": "a faithful patch built this way conflates a legitimate "
                      "non-finite VALUE with the MISSING-value sentinel, so such a "
                      "cell round-trips as missing instead of as the number it is. The "
                      "standing P2P fixtures assert exactly this distinction — one "
                      "checks the non-finite cell of a read table is non-finite, and "
                      "the round-trip comparison separates missing cells from "
                      "non-finite ones — so the patch turns passing tests red. It does "
                      "not resolve.",
        "witness": _WIT_OVERBROAD,
    },
    # ---- UNIQUENESS: readRow, clause (b) — the per-token payload ---------
    {
        "id": "uniq-readrow-payload-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_PAYLOAD_SWAP,
        "rationale": "attacks clause (b), the per-token PAYLOAD: the rival's decision "
                     "is exactly `isSentinel tok` and its arity and order are exactly "
                     "right, but the two payloads are EXCHANGED — it emits `number "
                     "(parseNumber tok)` on a sentinel token and `missing` on a numeric "
                     "one. Every other readRow rival in this battery keeps both payloads "
                     "correct (they attack the decision, the arity, or the order), so "
                     "this is the only case showing the equality pins WHICH cell a token "
                     "denotes once the decision is settled. Binder varied: `tokens`, at "
                     "a one-token row whose token is the upper-case sentinel spelling.",
        "refinement": "a faithful patch built this way inverts the two outcomes of the "
                      "value loop: a missing-value token is handed to the number parser "
                      "(which raises on a token that is not a number) while a legitimate "
                      "numeric cell is recorded as missing. Every standing fixture with "
                      "an all-sentinel row hits the first half, and the round-trip "
                      "comparison that separates missing cells from numeric ones hits "
                      "the second, so the patch turns passing tests red as well as "
                      "failing the F2P. It does not resolve.",
        "witness": _WIT_PAYLOAD_SWAP,
    },
    # ---- UNIQUENESS: readRow, structural clauses (c) and (d) -------------
    {
        "id": "uniq-readrow-drop-sentinel-cell",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP,
        "rationale": "attacks clause (c), ARITY: the rival's per-token decision and "
                     "both payloads are exactly right, but a sentinel token "
                     "contributes NO cell. `tokens.map cellOfToken` fixes one output "
                     "cell per input token, so the shorter row violates the equality "
                     "even though every cell it does produce is correct. Isolates the "
                     "structural content of the postcondition from its value content. "
                     "Binder varied: `tokens`, at a one-token row whose token is the "
                     "upper-case sentinel spelling.",
        "refinement": "a faithful patch built this way silently omits a value from a "
                      "row that contains a missing-value token, so the row has fewer "
                      "entries than the table has columns and the read fails (or "
                      "misaligns the remaining values into the wrong columns). The "
                      "fixture the F2P reads has rows with an embedded missing-value "
                      "token as well as all-sentinel rows, so the round-trip fails on "
                      "row construction. It does not resolve.",
        "witness": _WIT_DROP,
    },
    {
        "id": "uniq-readrow-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_REVERSE,
        "rationale": "attacks clause (d), ORDER: every cell is individually correct "
                     "and the arity is right, but the row is built back to front. "
                     "`List.map` is order-preserving, so the equality is violated. "
                     "This is the only rival refuted at a MULTI-token input — it "
                     "varies the LENGTH and the composition of the `tokens` binder as "
                     "well as its contents, so no single-token witness could stand in "
                     "for it. Binder varied: `tokens`, at a two-token row mixing a "
                     "sentinel token with a numeric one.",
        "refinement": "a faithful patch built this way reverses each data row, so "
                      "every value lands under the wrong column. The F2P round-trip "
                      "compares the re-read table's columns against the original's "
                      "values and asserts on a specific error column's contents, so it "
                      "fails on the value comparison; the standing P2P tests that "
                      "check individual cells fail too. It does not resolve.",
        "witness": _WIT_REVERSE,
    },
]


# =============================================================================
# AXIOM_TESTS — out of scope for this lane by design (the axiom lane is G-AX's
# job and this gate ignores the key). Recorded empty rather than omitted so the
# disposition is explicit: the frozen bundle consumes NO property axiom (both
# callees are `opaque` declarations with no `axiom`), and their behavioral
# properties are validated against the real callees by axiom_check.py.
# =============================================================================
AXIOM_TESTS = []
