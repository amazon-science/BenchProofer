# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9230 (lean lane).
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over and
# the mechanics re-expressed against this backend's carrier. Each SPEC case is a
# FULL Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl
# region — and, where a positive legitimately reproves, the proof body — is
# edited), checked by variant_scope + the Lean verifier. Every expect="reject"
# case carries a refutation `witness`: a snippet that ELABORATES against the
# rival and FAILS on the frozen solution, so the rejection is attributable to the
# spec rather than to a frozen tactic script that merely stopped matching a
# reshaped impl.
#
# ============================  DEFENDED SURFACE  =============================
#
# ONE modeled function over a fully TRANSPARENT carrier (List Char / Option /
# pair), with no precondition hypothesis:
#
#   problem_spec_paramField (arg : List Char)
#       (result : Option (List Char × List Char)) : Prop :=
#     result = extractTypeName arg
#
# A single top-level clause, but `extractTypeName` is a deep model spelled out in
# the (frozen) `pure` region, so the clause decomposes into FIVE independently
# attackable behaviours — each is a distinct sub-domain of `arg` on which a rival
# can be wrong while agreeing with the spec everywhere else:
#
#   (a) WHICH separator run the pair is cut at. The name is the FINAL
#       whitespace-delimited token and the type is the whole remaining prefix —
#       so a type containing interior whitespace stays intact. A rival cutting at
#       the FIRST run instead truncates the type and lets the remainder leak into
#       the name; it agrees with the spec on every two-token input and diverges
#       from three tokens up. This is the load-bearing behaviour.
#   (b) The ORDER of the pair. Which component is the type and which is the name.
#   (c) COMPLETENESS of the type prefix. The prefix is taken whole; a rival that
#       drops one more token off its end is a truncation the spec forbids.
#   (d) The `none` GUARD. `none` exactly when fewer than two whitespace-delimited
#       tokens exist (an empty type prefix). A rival that always returns a pair
#       emits an empty type on a single-token input.
#   (e) WHITESPACE handling on the two edges: trailing whitespace of the whole
#       string is not significant, and the type keeps its leading/interior
#       whitespace but drops its own trailing whitespace. Plus the SEPARATOR SET
#       itself, which is the full `isSpace` singleton set, not just the ASCII
#       blanks.
#
# The only INPUT BINDER is `arg`, and the reject witnesses below vary it across
# seven distinct values covering token count (1 / 2 / 3), separator-run length
# (single and double), trailing-whitespace presence, and separator IDENTITY (an
# ASCII space and a non-ASCII-blank separator code point). No sub-domain of the
# decomposition is probed at only one point.
#
# ==========================  NAGINI → LEAN PORT  =============================
#
# The nagini sibling contracts a DIFFERENT abstraction of the same fix: it splits
# the observable outputs into TWO functions over an already-tokenized run
# `tokens : List[int]` (`parsed_argument_name` -> the final token;
# `parsed_argument_type` -> the ordered prefix rendered single-space), with a
# precondition of at least two tokens. This backend instead models the decomposition
# over the RAW character string as one function returning an `Option` pair, so:
#
#   * nagini's two functions collapse into this bundle's one obligation, and its
#     name-side and type-side rivals become rivals on the corresponding COMPONENT
#     of the returned pair — the arguments port, the mechanics do not;
#   * nagini's "at least two tokens" precondition becomes an in-spec `none`
#     result here, so the whole under-two-token domain is IN scope rather than
#     excluded — which makes the `none` guard attackable here (no nagini
#     counterpart, since nagini's precondition assumes it away);
#   * nagini abstracts the character level away entirely (it takes tokens, and
#     renders with a single canonical separator), so its carrier cannot express
#     whitespace-edge or separator-set rivals at all. Those are attackable here.
#
# LANES THAT DO NOT PORT:
#   * FRAME / PERMISSION-MUTATION (nagini's MANDATORY class: `tokens` is held at
#     half permission and the rival writes to it, so the permission system
#     rejects). Lean is referentially transparent — every input is an immutable
#     value, no aliasing, no fractional permission — so "write to a read-only
#     input" is not expressible and the class is VACUOUS here. Not fabricated;
#     see `assessment`.
#   * DIVERGENCE / NON-TERMINATION. On lean this is genuinely vacuous:
#     `implementation_paramField` is a total Lean `def`, so a diverging impl
#     cannot be written at all. (The nagini sibling carries none regardless.)
#   * DIVERGENCE, re-measured by the audit rather than inherited: this bundle sets
#     no `loom.semantics.termination` at all — it is a plain Lean file, and a Lean
#     `def` must be shown terminating to elaborate. The only way to write a
#     non-terminating impl is `partial def`, and that was BUILT: it fails, but for
#     a reason that attributes nothing to the spec (`unfold` cannot unfold a
#     `partial def`, so the frozen script breaks before the postcondition is
#     reached, and no witness could refute it either since the term is opaque to
#     the kernel). So the class is genuinely vacuous here — the carrier admits no
#     diverging impl of this signature — rather than a known hole in the spec.
#   * AXIOM_TESTS. Dropped — the axiom lane is G-AX's job. (meta.json axioms ==
#     []; the decomposition is modeled deeply, there is no opaque callee.)
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9230"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. `_BODY` is the frozen impl's statement block and `_HEAD + _BODY`
# the whole frozen `def`; both lie entirely inside `-- impl-start`/`-- impl-end`
# and are unique in the file, so same_spec holds by construction for every swap.
# ---------------------------------------------------------------------------

_HEAD = (
    "def implementation_paramField (arg : List Char) :\n"
    "    Option (List Char × List Char) := Id.run do\n"
)

_BODY = """  let stripped := dropTrailingSpaces arg
  let revd := stripped.reverse
  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse
  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse
  if ty.isEmpty then
    return none
  return some (ty, nm)"""

if _BASE.count(_HEAD + _BODY) != 1:
    raise AssertionError("frozen impl region drifted")

# The frozen obligation STATEMENT, lifted verbatim (everything up to the
# proof-introducing `:=`). Reusing the frozen text rather than retyping it is
# what keeps variant_scope's statement-identity check honest: a reproving
# positive may rewrite the tactic body freely, but the statement must stay
# byte-identical, and copying it cannot drift.
_STMT_AT = _BASE.index("theorem correct_paramField")
_STMT = _BASE[_STMT_AT:_BASE.index(":=", _STMT_AT)].rstrip()


def _with_proof(src, tactics):
    """`src` with its whole proof region replaced by the frozen obligation
    statement plus a new tactic body. No new theorem/lemma, no assumption
    token — only the tactic script changes."""
    a = src.index("-- proof-start")
    b = src.index("-- proof-end") + len("-- proof-end")
    return (src[:a] + "-- proof-start\n" + _STMT + " := by\n"
            + tactics.rstrip() + "\n-- proof-end" + src[b:])


# ===========================================================================
# (1) POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify, else
# SPEC-TOO-STRONG. Three shapes, deliberately at two different strengths.
# ===========================================================================

# CHEAP: drop the `Id.run do` / early-return scaffold for a direct
# `if … then … else` expression. Definitionally equal to the frozen impl, so the
# frozen `by_cases`+`rfl` script would still close it; the body is simplified to a
# bare `rfl` since no case split is needed once the monadic wrapper is gone.
# Honest about what it tests: that the spec is not tied to the do-notation
# spelling. It exercises no obligation the frozen file did not already discharge.
_POS_PURE = _with_proof(
    _swap(_BASE, _HEAD + _BODY,
          "def implementation_paramField (arg : List Char) :\n"
          "    Option (List Char × List Char) :=\n"
          "  let stripped := dropTrailingSpaces arg\n"
          "  let revd := stripped.reverse\n"
          "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
          "  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
          "  if ty.isEmpty then none else some (ty, nm)"),
    """  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName
  rfl""")

# LOAD-BEARING: fuse the two edge-trims into one traversal. Instead of trimming
# the trailing whitespace and then reversing, reverse FIRST and trim from the
# front — the same value on every input (the two operations commute through the
# reversal), but NOT definitionally the frozen term, so the frozen tactic body
# does NOT close it. Confirmed: carrying the frozen proof onto this impl fails
# with `Tactic 'rfl' failed`. Reproven from the SAME byte-identical statement via
# `List.reverse_reverse`.
_POS_REVREV = _with_proof(
    _swap(_BASE, _BODY,
          "  let revd := arg.reverse.dropWhile isSpace\n"
          "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
          "  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
          "  if ty.isEmpty then\n"
          "    return none\n"
          "  return some (ty, nm)"),
    """  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName dropTrailingSpaces
  simp only [Id.run, List.reverse_reverse]
  split <;> rfl""")

# LOAD-BEARING: compute the name/prefix cut with a SINGLE pass that returns both
# halves at once, instead of two separate scans over the same string. Same value,
# different term, so the obligation is reproven from
# `List.span_eq_takeWhile_dropWhile`.
_POS_SPAN = _with_proof(
    _swap(_BASE, _BODY,
          "  let revd := (dropTrailingSpaces arg).reverse\n"
          "  let sp := revd.span (fun c => !isSpace c)\n"
          "  let nm := sp.1.reverse\n"
          "  let ty := dropTrailingSpaces sp.2.reverse\n"
          "  if ty.isEmpty then\n"
          "    return none\n"
          "  return some (ty, nm)"),
    """  intro arg
  unfold problem_spec_paramField implementation_paramField extractTypeName
  simp only [Id.run, List.span_eq_takeWhile_dropWhile]
  split <;> rfl""")


# ===========================================================================
# (2) RIVALS (uniqueness) — one per attackable behaviour (a)…(e). Each keeps the
# frozen spec and the frozen obligation statement; each carries a witness at a
# concrete input, verified to elaborate against the rival and to FAIL on gold.
# ===========================================================================

# (a) Cut at the FIRST separator run instead of the last: the type becomes the
# leading token only and the name absorbs the whole remainder. Correct on every
# two-token input; wrong from three tokens up.
_RIV_FIRSTCUT = _swap(_BASE, _BODY,
                      "  let s := arg.dropWhile isSpace\n"
                      "  let ty := s.takeWhile (fun c => !isSpace c)\n"
                      "  let nm := (s.dropWhile (fun c => !isSpace c)).dropWhile isSpace\n"
                      "  if ty.isEmpty || nm.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")

# (b) Pair components exchanged on the two-token sub-domain only (where the type
# part carries no interior whitespace) — a NEAR-MISS that agrees with gold on
# every input whose type has interior whitespace, so it needs its own witness at
# a two-token point.
_RIV_SWAPPED = _swap(_BASE, _BODY,
                     "  let stripped := dropTrailingSpaces arg\n"
                     "  let revd := stripped.reverse\n"
                     "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                     "  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                     "  if ty.isEmpty then\n"
                     "    return none\n"
                     "  if !(ty.any isSpace) then\n"
                     "    return some (nm, ty)\n"
                     "  return some (ty, nm)")

# (c) Off-by-one truncation: the prefix is computed correctly and then ONE MORE
# trailing token is dropped from it.
_RIV_OFFBYONE = _swap(_BASE, _BODY,
                      "  let stripped := dropTrailingSpaces arg\n"
                      "  let revd := stripped.reverse\n"
                      "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                      "  let full := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty := dropTrailingSpaces (full.reverse.dropWhile (fun c => !isSpace c)).reverse\n"
                      "  if ty.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")

# (d) Guard dropped: always return a pair, so a single-token input yields an
# EMPTY type component instead of `none`.
_RIV_NOGUARD = _swap(_BASE, _BODY,
                     "  let stripped := dropTrailingSpaces arg\n"
                     "  let revd := stripped.reverse\n"
                     "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                     "  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                     "  return some (ty, nm)")

# (e1) The type prefix keeps the separator run that divided it from the name:
# its own trailing whitespace is never trimmed.
_RIV_KEEPSEP = _swap(_BASE, _BODY,
                     "  let stripped := dropTrailingSpaces arg\n"
                     "  let revd := stripped.reverse\n"
                     "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                     "  let ty := (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                     "  if ty.isEmpty then\n"
                     "    return none\n"
                     "  return some (ty, nm)")

# (e2) Trailing whitespace of the WHOLE string treated as significant, so a
# string ending in a separator yields an empty name and a type that swallows the
# real name.
_RIV_TRAILING = _swap(_BASE, _BODY,
                      "  let revd := arg.reverse\n"
                      "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                      "  if ty.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")

# (e3) Separator set narrowed to the three ASCII blanks, so every other
# separator code point is treated as an ordinary character and no cut is made
# there at all. Structure otherwise identical to the frozen impl.
_RIV_ASCIISEP = _swap(_BASE, _BODY,
                      "  let plain : Char → Bool := fun c => c == ' ' || c == '\\t' || c == '\\n'\n"
                      "  let stripped := ((arg.reverse.dropWhile plain).reverse)\n"
                      "  let revd := stripped.reverse\n"
                      "  let nm := (revd.takeWhile (fun c => !plain c)).reverse\n"
                      "  let pre := (revd.dropWhile (fun c => !plain c)).reverse\n"
                      "  let ty := (pre.reverse.dropWhile plain).reverse\n"
                      "  if ty.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")

# (e4) ADDED BY AUDIT. The type's LEADING whitespace stripped as well as its
# trailing whitespace. The frozen decomposition is asymmetric on the two edges —
# the type keeps its leading and interior blanks and drops only its own trailing
# ones — and every rival above attacks the trailing edge or the cut position, so
# nothing in the shipped set held the LEADING edge. This rival agrees with gold
# on every input whose type part does not begin with a separator, which is every
# other witness point in the battery, so it needs its own point.
_RIV_LEADTRIM = _swap(_BASE, _BODY,
                      "  let stripped := dropTrailingSpaces arg\n"
                      "  let revd := stripped.reverse\n"
                      "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty0 := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty := ty0.dropWhile isSpace\n"
                      "  if ty.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")

# (e5) ADDED BY AUDIT. The type's INTERIOR whitespace deleted rather than
# preserved: the prefix is cut at the right place and kept whole, but its blanks
# are squeezed out. This is the residual of behaviour (a) that the first-cut
# rival does not cover — that one truncates the prefix, this one keeps every
# non-blank character of it and only loses the separators — so a rival can be
# wrong here while getting the cut position, the pair order, the prefix extent,
# the guard and both edges right. Agrees with gold on every single-token type,
# which is every other multi-token witness point in the battery.
_RIV_INTERIOR = _swap(_BASE, _BODY,
                      "  let stripped := dropTrailingSpaces arg\n"
                      "  let revd := stripped.reverse\n"
                      "  let nm := (revd.takeWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty0 := dropTrailingSpaces (revd.dropWhile (fun c => !isSpace c)).reverse\n"
                      "  let ty := ty0.filter (fun c => !isSpace c)\n"
                      "  if ty.isEmpty then\n"
                      "    return none\n"
                      "  return some (ty, nm)")


# ---------------------------------------------------------------------------
# Witness scaffold. The carrier is fully transparent — `List Char`, `Option` and
# the pair all decide equality — so every witness states the spec predicate at a
# CONCRETE ground literal and closes by `decide` after unfolding. No witness
# binds a hypothesis, so there is nothing that could be inconsistent and the
# gate's satisfiability probe is a no-op. Checked in a file whose frozen
# obligation is elided, so no tactic script can mask the verdict; against gold
# the same `decide` refutes the negation (`decide proved that the proposition …
# is false`) and the build fails, which is the discrimination half.
# ---------------------------------------------------------------------------

def _wit(lit):
    return (f"example : ¬ problem_spec_paramField {lit}\n"
            f"    (implementation_paramField {lit}) := by\n"
            "  unfold problem_spec_paramField implementation_paramField extractTypeName\n"
            "  decide")


# ---------------------------------------------------------------------------
# ADMISSIBILITY, added by audit. The frozen obligation carries NO precondition
# hypothesis, so the crude reading ("nothing can be PRECOND-TOO-STRONG here") is
# what the earlier accounting recorded — and it is the wrong analogue on a total
# carrier. The real risk this lane exists to catch is an obligation that is
# UNSATISFIABLE, or satisfiable only away from the shape the failing test
# exercises: `∀ arg, result = extractTypeName arg` would still be discharged by
# the frozen script if `extractTypeName` were degenerate at exactly the input the
# harness feeds it, because the spec pins `result` to a term over the same input
# and `rfl` closes that without ever exhibiting WHICH pair comes out.
#
# So the positive below discharges the frozen obligation VERBATIM (frozen tactic
# body, byte-identical statement, no new declaration, nothing assumed) and adds
# ONE `have` in front of it that EVALUATES the modeled decomposition, by `decide`,
# at the concrete shape the failing test's field argument has: a bracketed
# multi-token type followed by a one-token name. The `have` names the concrete
# pair, so it pins the admission to the branch that returns a pair whose type
# component retains its interior blank — not merely to "some equation holds".
#
# Measured load-bearing, which is the whole point of stating it as an evaluation
# rather than as `rfl`: built as a standalone `example` against this battery's own
# rivals, it FAILS (exit 1) on the first-cut, the separator-run-keeping and the
# off-by-one rivals, and it is the leading/interior-edge rivals below that the
# remaining ones answer. A `have` that passed against every impl would be
# decoration; this one distinguishes.
_ADM_LIT = "['M', 'a', 'p', '[', 'k', ',', ' ', 'v', ']', ' ', 'a', 'r', 'g']"
_ADM_TY = "['M', 'a', 'p', '[', 'k', ',', ' ', 'v', ']']"
_ADM_NM = "['a', 'r', 'g']"

_POS_ADMISSIBLE = _with_proof(
    _BASE,
    "  intro arg\n"
    f"  have _reachable : implementation_paramField {_ADM_LIT}\n"
    f"      = some ({_ADM_TY}, {_ADM_NM}) := by\n"
    "    unfold implementation_paramField\n"
    "    decide\n"
    "  unfold problem_spec_paramField implementation_paramField extractTypeName\n"
    "  simp only [Id.run]\n"
    "  by_cases h : (dropTrailingSpaces\n"
    "      ((dropTrailingSpaces arg).reverse.dropWhile (fun c => !isSpace c)).reverse).isEmpty\n"
    "  · simp only [h, if_true]; rfl\n"
    "  · simp only [h]; rfl")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS. In every case the frozen `theorem correct_paramField`
    # STATEMENT stays byte-identical (variant_scope enforces it); only the
    # tactic body may differ. No new axiom, no new theorem/lemma, no assumption
    # token.
    # =====================================================================
    {
        "id": "pos-pure-conditional",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": "correct reshape: the mutable-do / early-return scaffold is "
                     "replaced by a direct `if … then none else some (ty, nm)` "
                     "expression, computing the same pair on every input. It must "
                     "satisfy problem_spec_paramField — else SPEC-TOO-STRONG. Proof: "
                     "definitionally the frozen term once the monadic wrapper is gone, "
                     "so a bare `rfl` closes the same statement. CHEAP end of the "
                     "lane: it shows the spec is not tied to the do-notation spelling, "
                     "and exercises no obligation the frozen file did not already "
                     "discharge — do not read it as evidence the spec admits a "
                     "genuinely new proof.",
    },
    {
        "id": "pos-fused-edge-trim",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_REVREV,
        "rationale": "correct reshape that FUSES the two edge trims: instead of "
                     "trimming the string's trailing separators and then reversing, it "
                     "reverses first and trims from the front. Same value on every "
                     "input (the trim commutes through the reversal), so it must "
                     "satisfy problem_spec_paramField — else SPEC-TOO-STRONG. NOT "
                     "definitionally the frozen impl: carrying the frozen tactic body "
                     "onto it fails with `Tactic 'rfl' failed`, so the obligation is "
                     "genuinely REPROVEN (via List.reverse_reverse, then a case split "
                     "on the empty-prefix guard) from the byte-identical statement. "
                     "This and pos-single-pass-cut are the load-bearing positives.",
    },
    {
        "id": "pos-single-pass-cut",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_SPAN,
        "rationale": "correct reshape that computes the name and the remaining prefix "
                     "in ONE pass returning both halves, instead of two separate scans "
                     "over the same string. Same pair on every input, so it must "
                     "satisfy problem_spec_paramField — else SPEC-TOO-STRONG. Not "
                     "definitionally the frozen term (the single-pass split is a "
                     "different function), so the obligation is reproven from "
                     "List.span_eq_takeWhile_dropWhile plus the guard's case split, "
                     "statement unchanged.",
    },

    # =====================================================================
    # ADMISSIBILITY (added by audit). See _POS_ADMISSIBLE.
    # =====================================================================
    {
        "id": "admiss-reachable-shape-evaluates",
        "kind": "admissibility",
        "expect": "verify",
        "module": _POS_ADMISSIBLE,
        "rationale": "the frozen obligation must be discharged AND be non-degenerate "
                     "at the shape the failing test's field argument actually has: a "
                     "bracketed multi-token type followed by a one-token name. This "
                     "case closes the frozen obligation verbatim (byte-identical "
                     "statement, frozen tactic body, no new declaration, nothing "
                     "assumed) with one `have` in front of it that EVALUATES the "
                     "modeled decomposition at that concrete input by `decide` and "
                     "names the resulting pair — so the admission is pinned to the "
                     "branch returning a pair whose type component keeps its interior "
                     "blank, not merely to `rfl` on a term over the same input. If the "
                     "obligation were satisfiable only away from that shape, this case "
                     "would fail: PRECOND-TOO-STRONG in the form the analogue takes on "
                     "a total carrier, where there is no precondition hypothesis to "
                     "weaken. Load-bearing rather than decorative — measured: the same "
                     "`have`, built standalone against this battery's own rivals, "
                     "fails on the first-cut, separator-run-keeping and off-by-one "
                     "impls.",
    },

    # =====================================================================
    # RIVALS. Behaviour (a) — WHICH separator run the pair is cut at. This is the
    # load-bearing behaviour of the frozen spec.
    # =====================================================================
    {
        "id": "uniq-cut-at-first-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRSTCUT,
        "refinement": "cutting at the FIRST separator run makes the type the leading "
                      "token alone and lets the rest of the intended type leak into the "
                      "name. On the field argument the FAIL_TO_PASS test adds — a type "
                      "with interior whitespace followed by a name — the type is "
                      "truncated at its first blank and the leftover becomes part of the "
                      "name, which is exactly the mis-rendering the issue reports "
                      "(reported as the truncated type and a name carrying the "
                      "remainder). test_info_field_list asserts both the rendered "
                      "parameter name and the full cross-referenced type sequence, so a "
                      "faithful patch cutting at the first run does NOT resolve.",
        "rationale": "REJECT from result = extractTypeName arg, whose name component is "
                     "the FINAL whitespace-delimited token and whose type component is "
                     "the WHOLE remaining prefix. On a three-token `arg` the first-cut "
                     "rival returns the leading token as the type and a two-token name, "
                     "while the spec demands a two-token type and a one-token name. "
                     "Attacks behaviour (a); witness at a three-token `arg`.",
        "witness": _wit("['a', ' ', 'b', ' ', 'c']"),
    },

    # Behaviour (b) — the ORDER of the returned pair.
    {
        "id": "uniq-pair-order-swapped-two-token",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SWAPPED,
        "refinement": "exchanging the two components records the name as the type and "
                      "vice versa. Restricted to the sub-domain where the type part "
                      "carries no interior whitespace — which is exactly the shape of the "
                      "single-token inline-type field the F2P text opens with, and of the "
                      "inline-type variable field a PASS_TO_PASS test asserts on. On both, "
                      "the pair comes back reversed, so each such parameter is rendered "
                      "under its type name while its actual name is emitted as a "
                      "cross-referenced class. Those are node-level assertions naming both "
                      "components, so a faithful patch doing this fails the F2P AND a "
                      "declared P2P — it does NOT resolve. (Grounded on the F2P text's own "
                      "field arguments, not hypothetically: the two-token ones diverge, "
                      "the multi-token one does not, which is why this rival needs its own "
                      "witness at a two-token point.)",
        "rationale": "REJECT from result = extractTypeName arg, which fixes WHICH "
                     "component is the type (the prefix) and which is the name (the "
                     "final token). On a two-token `arg` the rival returns the "
                     "components in the opposite order. A NEAR-MISS deliberately given "
                     "its own witness: it agrees with gold on every input whose type "
                     "part contains interior whitespace, so the three-token point used "
                     "by uniq-cut-at-first-separator would NOT refute it. Attacks "
                     "behaviour (b); witness at a two-token `arg`.",
        "witness": _wit("['a', ' ', 'b']"),
    },

    # Behaviour (c) — COMPLETENESS of the type prefix.
    {
        "id": "uniq-type-prefix-truncated",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OFFBYONE,
        "refinement": "dropping one further trailing token from the type prefix is an "
                      "off-by-one that renders a multi-token type with its last chunk "
                      "missing — the truncated-type symptom the issue reports — and "
                      "collapses every TWO-token field argument to the no-pair case, so "
                      "the inline type syntax stops recording a type there at all. Both "
                      "effects land on the F2P text's own field arguments: its multi-token "
                      "inline type loses its final chunk (the F2P asserts the complete "
                      "cross-referenced type sequence) and its single-token inline type "
                      "degrades to no type at all. The inline-type variable field of a "
                      "declared P2P degrades the same way. A faithful patch truncating the "
                      "prefix therefore does NOT resolve, and breaks a P2P besides.",
        "rationale": "REJECT from result = extractTypeName arg: the type component is "
                     "the ENTIRE remaining prefix, so removing a further token from its "
                     "end violates the equality for every `arg` with two or more "
                     "tokens. Attacks behaviour (c). Witness deliberately placed at a "
                     "three-token `arg` whose FIRST separator is a two-character run: "
                     "that point also varies the separator-run length, which no other "
                     "witness in this battery does at a multi-token input.",
        "witness": _wit("['a', ' ', ' ', 'b', ' ', 'c']"),
    },

    # Behaviour (d) — the `none` guard.
    {
        "id": "uniq-no-pair-guard-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NOGUARD,
        "refinement": "HONEST NEGATIVE — this rival's faithful patch DOES resolve the "
                      "declared F2P, so it is NOT a verify-does-not-imply-resolve "
                      "candidate; it is shipped as the only defence of the no-pair "
                      "clause. Measured, not argued: a real patch that always returns a "
                      "pair records a bogus empty type for every field written with a "
                      "bare name, but in the F2P text every such field is FOLLOWED by a "
                      "separate field supplying its type, and that later field "
                      "assigns over the same key in the same collected mapping — so the "
                      "bogus entry is overwritten before rendering and the F2P still "
                      "passes (all 45 tests in the F2P's own file pass). The rival IS "
                      "genuinely wrong repo behavior — it produces an empty parenthesised "
                      "type where a real type belongs, and breaks 5 tests elsewhere in "
                      "the suite (a translation test whose fields have no type companion, "
                      "and four type-annotation-description tests whose synthesised "
                      "fields likewise have none) — but those tests are outside this "
                      "instance's declared F2P/P2P sets, so no resolve-level claim is "
                      "made here. The spec rejects it because the spec models the real "
                      "no-pair behavior faithfully, which is the property this case "
                      "measures.",
        "rationale": "REJECT from result = extractTypeName arg, which is `none` EXACTLY "
                     "when the string has fewer than two whitespace-delimited tokens "
                     "(equivalently, an empty type prefix). On a single-token `arg` the "
                     "spec demands `none` and the rival returns a pair with an empty "
                     "type component. Attacks behaviour (d) — the only rival probing the "
                     "under-two-token sub-domain, which nagini's precondition assumes "
                     "away entirely; witness at a one-token `arg`.",
        "witness": _wit("['a']"),
    },

    # Behaviour (e) — whitespace on the two edges, and the separator set.
    {
        "id": "uniq-type-keeps-separator-run",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_KEEPSEP,
        "refinement": "leaving the dividing separator run attached to the type means "
                      "every recorded type carries trailing blanks. MEASURED by building "
                      "and running the faithful real patch (cut at the last separator, "
                      "but keep the type's trailing blank): the recorded type text is "
                      "tokenized by a delimiter split that neither anchors nor strips, so "
                      "the blank survives into the emitted node AND into the "
                      "cross-reference target. The F2P assertion on the single-token "
                      "inline type fails on the rendered text (it sees the type with a "
                      "trailing blank where the bare token is asserted), the multi-token "
                      "case additionally emits its closing bracket token with the blank "
                      "attached, and a PASS_TO_PASS assertion on a variable field written "
                      "with the inline type syntax fails the same way. So the faithful "
                      "patch does NOT resolve, and it breaks a declared P2P as well — the "
                      "strongest-grounded rival in this battery after the first-cut one.",
        "rationale": "REJECT from result = extractTypeName arg, whose type component has "
                     "its OWN trailing whitespace removed (while leading and interior "
                     "whitespace are preserved). The rival returns the untrimmed prefix, "
                     "so the type components differ whenever a pair exists. Attacks "
                     "behaviour (e); witness at a two-token `arg` whose separator is a "
                     "two-character run, so the surplus is visible and the run length is "
                     "varied against the single-separator witnesses.",
        "witness": _wit("['a', ' ', ' ', 'b']"),
    },
    {
        "id": "uniq-trailing-whitespace-significant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_TRAILING,
        "refinement": "HONEST NEGATIVE on reachability — no resolve-level claim. "
                      "Treating the string's own trailing whitespace as significant makes "
                      "the final token EMPTY for any field argument ending in a "
                      "separator, so the type swallows the real name and the field is "
                      "re-keyed under the empty string, losing the parameter's name in "
                      "the rendering. That IS wrong repo behavior, but it is UNREACHABLE "
                      "through the declared tests, and by construction rather than by "
                      "accident: the surrounding markup parser's own field-marker pattern "
                      "carries a lookbehind that REJECTS a field name ending in a blank, "
                      "so such a line does not parse as a field at all (verified: it "
                      "yields an ordinary paragraph). A grep of the whole test tree at "
                      "the base commit finds no field argument with a trailing blank. So "
                      "the faithful patch would pass F2P and P2P, and this case is "
                      "shipped for what it does measure: the spec pins the trailing-edge "
                      "behavior over the FULL input domain, not merely over the sub-domain "
                      "the markup layer happens to deliver — which is the right strength, "
                      "since the modeled function is specified over arbitrary strings.",
        "rationale": "REJECT from result = extractTypeName arg, which ignores the whole "
                     "string's trailing whitespace before splitting. On an `arg` ending "
                     "in a separator the spec's name is the last non-blank token and its "
                     "type is the prefix before it, whereas the rival returns an empty "
                     "name and a type covering both tokens. Attacks the other half of "
                     "behaviour (e); witness at the only trailing-separator input in the "
                     "battery.",
        "witness": _wit("['a', ' ', 'b', ' ']"),
    },
    {
        "id": "uniq-separator-set-narrowed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ASCIISEP,
        "refinement": "HONEST NEGATIVE on reachability — no resolve-level claim. "
                      "Narrowing the separator set to the three common ASCII blanks means "
                      "every other whitespace code point is treated as an ordinary "
                      "character, so a field argument divided by one of them is not split "
                      "and no type is recorded. That IS wrong repo behavior — the "
                      "library's own whitespace split honours the full set — but the "
                      "declared tests only ever separate with an ASCII blank (grep over "
                      "the test tree at the base commit finds no non-ASCII separator in "
                      "any field argument), so a faithful patch hand-rolling an "
                      "ASCII-only split would still resolve the F2P and keep the P2P "
                      "green. Shipped anyway because the divergence is MEASURED and was "
                      "load-bearing for this bundle: an earlier ASCII-only separator "
                      "model was rejected during construction for exactly this "
                      "unfaithfulness, and this case is what keeps that decision under "
                      "test — it defends the separator-set half of the spec, which no "
                      "test-reachable input constrains.",
        "rationale": "REJECT from result = extractTypeName arg, whose separator "
                     "predicate is the FULL set of whitespace code points, not the ASCII "
                     "blanks alone. On an `arg` divided by a non-ASCII-blank separator "
                     "the spec returns a pair and the rival returns `none` (it sees one "
                     "token). Attacks the separator-set half of behaviour (e) — the only "
                     "witness in the battery that varies the separator IDENTITY rather "
                     "than its position or count; nagini's tokenized carrier cannot "
                     "express this rival at all.",
        "witness": _wit("['q', '\\x1c', 'r']"),
    },
    {
        "id": "uniq-type-leading-edge-trimmed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_LEADTRIM,
        "refinement": "HONEST NEGATIVE on reachability — no resolve-level claim, and it "
                      "is the reachability rather than the wrongness that is limited. "
                      "Stripping the type's leading blanks as well as its trailing ones "
                      "loses a leading blank the library's own whitespace split "
                      "preserves, so it is wrong repo behavior; but a field argument "
                      "whose type part begins with a blank does not survive the markup "
                      "layer that delivers it (the field-marker syntax does not carry a "
                      "leading blank into the argument text), so no declared test "
                      "observes it. Shipped for what it does measure: the frozen "
                      "decomposition is ASYMMETRIC on the type's two edges, and this is "
                      "the only case in the battery that holds the leading one. Every "
                      "other rival attacks the trailing edge or the cut position, so "
                      "without this case a spec that trimmed both edges would be "
                      "attacked by nothing.",
        "rationale": "REJECT from result = extractTypeName arg, whose type component "
                     "keeps its LEADING and interior whitespace and drops only its own "
                     "trailing whitespace. The rival additionally strips the leading "
                     "blanks, so the type components differ on exactly the inputs whose "
                     "type part starts with a separator. A NEAR-MISS: it agrees with "
                     "gold at every other witness point in this battery, which is why "
                     "it carries its own — a two-token `arg` led by a TAB, which also "
                     "varies the separator identity a third way (neither the plain "
                     "space of the other points nor the non-ASCII code point of the "
                     "separator-set case).",
        "witness": _wit("['\\t', 'x', ' ', 'y']"),
    },
    {
        "id": "uniq-type-interior-whitespace-squeezed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INTERIOR,
        "refinement": "cutting in the right place but SQUEEZING the blanks out of the "
                      "type renders a multi-token type with its parts run together. On "
                      "the field argument the FAIL_TO_PASS test adds — a bracketed type "
                      "with an interior blank followed by a name — the recorded type "
                      "loses that blank, so the assertion on the full "
                      "cross-referenced type sequence sees the wrong token text and the "
                      "faithful patch does NOT resolve. Distinct from the first-cut "
                      "rival in what it gets right: the cut position, the prefix extent, "
                      "the pair order, the guard and both edges are all correct here, so "
                      "this is the narrowest wrong impl in the battery and the one whose "
                      "rejection isolates interior-blank preservation by itself.",
        "rationale": "REJECT from result = extractTypeName arg: the type component is "
                     "the remaining prefix VERBATIM, interior whitespace included. The "
                     "rival deletes every separator inside it, so the type components "
                     "differ on exactly the inputs whose type part has more than one "
                     "token — the residual of behaviour (a) that the first-cut rival "
                     "does not cover, since that one truncates the prefix instead of "
                     "keeping all of its non-blank characters. Witness at the "
                     "F2P-shaped input: a bracketed multi-token type plus a one-token "
                     "name, the same point the admissibility positive evaluates at, so "
                     "the battery attacks and admits at the same concrete shape.",
        "witness": _wit(_ADM_LIT),
    },
]


# ===========================================================================
# Nagini → lean accounting
#
#   nagini case                        -> here
#   ---------------------------------------------------------------------
#   pos-control-name                   -> pos-pure-conditional        RE-EXPRESSED
#     (nagini reshapes locals on the name side; the lean counterpart is the
#     scaffold-free conditional. Cheap/definitional in both.)
#   pos-control-type                   -> pos-fused-edge-trim,
#                                         pos-single-pass-cut         RE-EXPRESSED
#     (nagini keeps the backward loop and reorders branches, because a forward
#     construction would need a fold lemma its verifier will not auto-discharge.
#     The lean carrier has no loop to reorder — the impl is a chain of
#     traversals — so the equivalent "different shape, same value, real reproof"
#     positives are the fused edge trim and the single-pass cut. Both genuinely
#     reprove: the frozen tactic body fails on each.)
#   prepatch-name-split-remainder      -> uniq-cut-at-first-separator PORTED (merged)
#   prepatch-type-first-token          -> uniq-cut-at-first-separator PORTED (merged)
#     (nagini needs two cases because it models the name side and the type side
#     as two separate functions; here they are the two components of ONE returned
#     pair, so the single first-cut rival IS both. Merging is carrier narrowing,
#     not a dropped case: one rival exhibits both wrong components at once, and
#     its witness refutes them jointly.)
#   partial-domain-name-n2             -> uniq-pair-order-swapped-two-token
#                                                                     RE-EXPRESSED
#     (nagini's rival returns the FIRST token as the name on the two-token
#     sub-domain. On this carrier the first token of a two-token string IS the
#     type component, so the faithful re-expression is the pair-order swap
#     restricted to that same sub-domain — same sub-domain, same argument.)
#   partial-domain-type-offbyone       -> uniq-type-prefix-truncated   PORTED
#   frame-mut-name                     -> (none)  VACUOUS (no heap, no permissions)
#   frame-mut-type                     -> (none)  VACUOUS (no heap, no permissions)
#   admiss-name                        -> admiss-reachable-shape-evaluates
#                                                                     RE-EXPRESSED
#     (CORRECTED BY AUDIT. The earlier accounting recorded this as N/A because the
#     frozen obligation has no precondition hypothesis to weaken. That is the
#     wrong analogue on a total carrier: the shippable form is a positive that
#     discharges the obligation at a concrete F2P-shaped input BY EVALUATION,
#     as a `have`, before closing the frozen obligation verbatim — which tests
#     that the obligation is satisfiable at the shape the harness actually feeds,
#     not merely satisfiable somewhere. It was landed, it verifies, and the `have`
#     is load-bearing: standalone, it fails against three of this battery's own
#     rivals.)
#   AXIOM_TESTS (empty)                -> (none)  DROPPED (G-AX's lane)
#
# ADDED beyond the nagini set (surface this backend models but nagini elided —
# nagini takes an already-tokenized run with at least two tokens, so none of
# these is expressible there):
#   * uniq-no-pair-guard-dropped        — the `none` / under-two-token domain,
#     which nagini's precondition excludes.
#   * uniq-type-keeps-separator-run     — per-character whitespace on the type's
#     trailing edge; nagini renders with one canonical separator.
#   * uniq-trailing-whitespace-significant — the whole string's trailing edge.
#   * uniq-separator-set-narrowed       — the separator SET; nagini's carrier has
#     no characters to classify.
#
# SPEC-TOO-WEAK probes run during the port and NOT shipped, each because it is
# NOT WRONG on this carrier (the frozen spec does not distinguish it, so no
# witness could discriminate — and a reject case whose witness does not
# discriminate is exactly the corrupt artifact this lane exists to avoid):
#   * trimming the type prefix's trailing whitespace via a reversed traversal
#     rather than the shared helper — observationally identical, so it belongs in
#     the positive lane, not the reject lane (it is essentially pos-fused-edge-
#     trim);
#   * returning the pair as a two-element structure rather than a Lean pair —
#     not expressible without editing the frozen spec's result type, which
#     same_spec forbids.
#
# REFINEMENT STRENGTH — which rivals carry a resolve-level claim, MEASURED by
# building each faithful real patch and running the tests, not argued from the
# spec. Recorded here because the three tiers carry different evidential weight
# and a reader should not have to infer which is which:
#
#   TIER 1 — faithful patch fails the declared F2P (a true verify-does-not-imply-
#   resolve candidate if the spec ever admitted it):
#     uniq-cut-at-first-separator        (this IS the pre-change behavior)
#     uniq-pair-order-swapped-two-token  (also breaks a declared P2P)
#     uniq-type-prefix-truncated         (also breaks a declared P2P)
#     uniq-type-keeps-separator-run      (also breaks a declared P2P; the
#       trailing blank survives the downstream delimiter split, which neither
#       anchors nor strips, into both the rendered node and the xref target)
#
#   TIER 2 — genuinely wrong repo behavior, but the declared F2P/P2P sets do not
#   observe it, so NO resolve-level claim is made:
#     uniq-no-pair-guard-dropped — the bogus empty type is overwritten before
#       rendering, because every bare-name field in the F2P text is followed by a
#       field supplying its type, which assigns over the same key. Breaks 5 tests
#       elsewhere in the suite (fields with no type companion), all outside the
#       declared sets. Shipped as the ONLY defence of the no-pair clause.
#
#   TIER 3 — wrong behavior on inputs the markup layer never delivers, so
#   unreachable through ANY test:
#     uniq-trailing-whitespace-significant — the field-marker pattern's own
#       lookbehind rejects a field name ending in a blank, so such a line does not
#       parse as a field at all; no test-tree field argument has a trailing blank.
#     uniq-separator-set-narrowed — no test-tree field argument uses a non-ASCII
#       separator.
#
# Tiers 2 and 3 are shipped deliberately, and their `refinement` fields say so
# in as many words. They defend clauses of the frozen spec that NO
# test-reachable input constrains — the no-pair result, the trailing edge, and
# the separator set — and the spec is specified over arbitrary strings, so those
# clauses are load-bearing for `verify ⟹ correct` even where the harness is
# blind to them. Dropping them would leave three clauses of the postcondition
# attacked by nothing at all. What they are NOT is evidence of a
# verify-does-not-imply-resolve break; only tier 1 could be that.
#
# BINDER / POINT COVERAGE. The spec has exactly one input binder, `arg`, and the
# seven reject witnesses probe SEVEN DISTINCT values of it, chosen so that no
# sub-domain of the decomposition is measured at a single point:
#   ['a']                          1 token                     — the `none` guard
#   ['a',' ','b']                  2 tokens, 1-char separator   — pair order
#   ['a',' ',' ','b']              2 tokens, 2-char separator   — type trailing edge
#   ['a',' ','b',' ']              2 tokens + trailing blank    — string trailing edge
#   ['a',' ','b',' ','c']          3 tokens, 1-char separators   — which run is cut
#   ['a',' ',' ','b',' ','c']      3 tokens, mixed run lengths   — prefix completeness
#   ['q','\x1c','r']               2 tokens, non-ASCII separator — separator set
# plus the two points the audit added:
#   ['\t','x',' ','y']             2 tokens, LEADING tab          — type leading edge
#   ['M','a','p','[','k',',',' ','v',']',' ','a','r','g']
#                                  F2P-shaped: multi-token type   — interior blanks
#     (also the point the admissibility positive evaluates at, so the battery
#      attacks and admits at the same concrete shape)
# Token count takes 1/2/3, separator-run length 1 and 2, trailing-whitespace
# presence both ways, leading whitespace of the type part both ways, and separator
# identity three values (space, tab, a non-ASCII code point). `arg` is therefore
# varied along every dimension the frozen decomposition branches on.
#
# ============================  AUDIT RECORD  =================================
#
# An independent audit re-derived every case with real builds. What it found:
#
#   * Statement integrity: all 10 shipped `theorem correct_paramField` statements
#     were byte-identical to the frozen one. Nothing neutered.
#   * Witness discrimination: all 7 reject witnesses rebuilt by hand — rival 0,
#     gold 1, every gold-side failure a plain `decide` EVALUATION (`Tactic
#     `decide` proved that the proposition ¬(...)`), i.e. the kernel computed the
#     claim rather than getting stuck. Forgery test run on all 7 anyway: flipping
#     the claim (dropping the `¬`, so the witness asserts gold is CORRECT there)
#     BUILDS CLEAN on gold, exit 0, for every one. Gold's exit code therefore
#     tracks the claim and none of the rejections is hollow.
#   * Rival wrongness: each of the 7 rivals was simulated against the frozen
#     decomposition exhaustively over a 5-symbol alphabet up to length 5. Every
#     one differs from gold on hundreds of inputs, so none is a mere reshape.
#     Both load-bearing positives differ on ZERO inputs over the same sweep,
#     confirming they are faithful reshapes and the lane is a real soundness test.
#   * SPEC-TOO-WEAK probe: the two rivals added above were written as NEW attacks
#     on the clauses the shipped set left unguarded (the type's leading edge, and
#     its interior blanks). Both are REJECTED by the frozen spec, with witnesses
#     that discriminate. No wrong impl was found that the spec admits.
#   * SPEC-TOO-STRONG probe: a further correct reshape not shipped here — the
#     empty-prefix guard written as a `match` on the prefix rather than an
#     `isEmpty` test — was proven against the frozen statement (`rcases` on the
#     prefix, then `simp`), so the spec admits it. No soundness hole. Two other
#     tactic spellings of that same reshape did NOT close (`split` cannot split
#     the `match`; a bare `cases … <;> rfl` leaves the guard unreduced), which is
#     a proof-engineering fact about the reshape, not a property of the spec — it
#     is not shipped only because the two positives above already cover the lane.
