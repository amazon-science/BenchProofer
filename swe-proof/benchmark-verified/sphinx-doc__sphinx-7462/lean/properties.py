"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-7462 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT runner executes over
the frozen `Solution.lean`. Each case edits ONLY the implementation region (and,
for the positive controls, the proof body); the spec view is untouched, so
`variant_scope.same_spec` holds by construction and every rejection is
attributable to the postcondition, never to a tampered spec.

DEFENDED SURFACE
----------------
Two INDEPENDENT renderers each assemble a parenthesised sequence from the
already-rendered pieces of its members:

    implementation_renderTupleSig  (elems : List (List SigToken)) : List SigToken
    implementation_renderTupleText (elems : List String)         : String

pinned by one equality clause each:

    result = assembleTupleSig  elems      (display-token view)
    result = assembleTupleText elems      (flat source-text view)

Both `assembleTuple*` are FULLY TRANSPARENT deep models (no opaque callee, so
every rival is refutable by `decide` at a concrete input — no carrier
conditioning is needed). Each splits the input carrier into two sub-domains:

  * NON-EMPTY (`elems ≠ []`): the members are laid out in order, each followed
    by a comma-and-space separator, with the single trailing separator dropped
    (Sig) / joined by the comma-and-space separator (Text).
  * EMPTY (`elems = []`): the special case that the fix ADDS — the display must
    be exactly the two punctuation tokens `(` then `)` (Sig) / exactly the
    two-character text `()` (Text). This is the discriminating behavior: before
    the fix the empty case fell through the non-empty path (dropping a trailing
    separator off an empty layout / joining an empty list), producing an empty
    display and, on the token view, an out-of-range removal.

The empty sub-domain carries THREE independent facts the rivals attack: the
COUNT of pieces (two, not one), their IDENTITY (the parentheses), and their
ORDER (open before close). The non-empty sub-domain is attacked from the
opposite side by a rival that renders every sequence as the empty-case output,
and (w9..w12) from INSIDE the layout: the separator's identity and the member
order, both of which are only observable once a sequence has TWO members. A
one-member sequence appends exactly one separator and then drops it, so every
non-empty witness stated at a one-member point is blind to those two facts —
which is why both non-empty witnesses now sit at a two-member point.

There is no precondition (a sequence may have zero or more members), so both
`correct_*` obligations are `∀ elems, problem_spec_* elems (implementation_*
elems)` with NO hypothesis binder.

PORTING NOTES (which nagini cases port, which are omitted, and why)
-------------------------------------------------------------------
The nagini sibling contracts the same two rendering sites (its `tuple_tokens` /
`tuple_text`), so the port is close to 1:1 rather than carrier-narrowed. The
`PSeq[PSeq[int]]` / `PSeq[int]` carrier maps to `List (List SigToken)` /
`List String`; `open_paren()`/`close_paren()`/`40`/`41` become the concrete
`SigToken.punct "("` / `SigToken.punct ")"` and the string literals; the
`join_tokens`/`join_comma` folds become the deep models `assembleTupleSig`/
`assembleTupleText`.

  * nagini `pos-reorder` (branch reorder at BOTH sites) -> `pos-reorder`: the
    empty case is tested via `!elems.isEmpty` with the non-empty layout first
    and the empty return last, at both sites; proofs re-closed. Verifies or the
    spec is over-fit to one branch order (SPEC-TOO-STRONG).
  * added `pos-functional-form`: a second correct impl in a different shape
    (pure functional `def` on `match`, no `Id.run do`/`for`/`mut`) whose cons
    branch re-derives the layout itself, closing with `cases elems <;> rfl`.
    AMENDED BY AUDIT: as ported, its body WAS the deep model
    (`assembleTuple* elems`), which made the obligation `model elems = model
    elems` and `rfl` a tautology — a positive that verifies against any spec
    and so cannot detect SPEC-TOO-STRONG. Now the layout is spelled out.
  * nagini `w1-prepatch-tok` -> `w1-prepatch-tok`: drop the empty special-case
    on the token site; attacks the EMPTY clause of `renderTupleSig`.
  * nagini `w2-prepatch-txt` -> `w2-prepatch-txt`: drop the empty special-case
    on the text site; attacks the EMPTY clause of `renderTupleText`.
  * nagini `w3-wrongtok-one-node` -> `w3-wrongtok-one-node`: empty case emits ONE
    punctuation token carrying `()`; attacks the piece-COUNT of the Sig EMPTY
    clause.
  * nagini `w4-swaptok-order` -> `w4-swaptok-order`: empty case emits `)` then
    `(`; attacks the ORDER of the Sig EMPTY clause.
  * nagini `w5-wrongtxt-one-char` -> `w5-wrongtxt-one-char`: empty case renders
    `(`; attacks the length/identity of the Text EMPTY clause.
  * nagini `w6-swaptxt-order` -> `w6-swaptxt-order`: empty case renders `)(`;
    attacks the char ORDER of the Text EMPTY clause.
  * nagini `w7-always-empty-tok` -> `w7-always-empty-tok`: emit the empty output
    for EVERY sequence on the token site; attacks the NON-EMPTY clause of
    `renderTupleSig` (the opposite side of the prepatch rivals).
  * added `w8-always-empty-txt`: emit `()` for EVERY sequence on the text site;
    attacks the NON-EMPTY clause of `renderTupleText`. Nagini attacked the
    non-empty sub-domain only on the token site (its W7); adding the text-site
    mirror ensures the non-empty binder is varied on BOTH obligations, so a
    rival mishandling the text non-empty path cannot slip by.
  * nagini `admiss-shapes` (admissibility probe) -> `admiss-ground-shapes`.
    AMENDED BY AUDIT: this case was previously OMITTED, on the ground that the
    lean obligation carries NO precondition hypothesis so there is nothing to
    over-constrain. That reason is wrong, and dropping the case removed the only
    lane that tests PRECOND-TOO-STRONG. On a TOTAL carrier the analogue of a
    too-strong precondition is the obligation being UNSATISFIABLE at exactly an
    F2P-shaped input — a spec that is contradictory there is still vacuously
    "provable" nowhere useful, and no uniqueness rival and no branch-reshape
    positive can detect it, because both only ever ask whether the ∀-statement
    closes. The probe that does detect it discharges the obligation at the
    concrete F2P-shaped inputs BY EVALUATION, as a `have` in the existing tactic
    body, before closing the frozen obligation verbatim. Landed at both sites and
    at both sub-domains (the members-absent input and a two-member input), and it
    VERIFIES (lean_verify.sh exit 0), so the modeled behavior is satisfiable at
    exactly the shapes the new tests use.
  * nagini's READ-ONLY / frame-mutation discussion has no counterpart: `elems`
    is an immutable Lean value and the result is pinned by a total equality to a
    deep model, so a "mutate the input under half-permission" attack is not
    constructible. Not vacuous-by-omission — there is no separable frame clause
    to attack beyond the result equality, which every rival already probes.
  * `AXIOM_TESTS` dropped: the axiom lane is G-AX's job and this gate ignores it
    (mapping.md records G-AX as a skip stub — the per-element renderer is left
    ∀-quantified, no callee contract is consumed).

  * added `w9-sep-nospace-tok` / `w10-revorder-tok` / `w11-sep-nospace-txt` /
    `w12-revorder-txt` (AUDIT): the interleaving rivals. Nagini's battery and
    this port both refuted every rival at either `[]` or a ONE-member sequence,
    so the separator's own text and the member order were never attacked on
    either obligation — a rival getting them wrong is correct at every point the
    battery tested. Each is refuted at a two-member sequence.

  * added `w13-keep-trailing-tok` / `w14-trailing-sep-txt` (SECOND AUDIT): the
    TRAILING-separator rivals. Every rival above gets the drop-trailing step
    right and differs elsewhere, so the "…with no trailing separator" half of
    both `assembleTuple*` was asserted by the spec but never probed: a rival that
    emits the layout WITH its trailing separator still attached was correct at
    every point the battery tested. Each is refuted at the two-member point.

Every reject case carries a `witness`: a Lean `example` negating the spec
predicate at one concrete input, checked in a file with the frozen obligations
removed. Each must (1) ELABORATE against the rival and (2) FAIL against the
frozen solution (a real discriminator, not a tautology). All twelve witnesses
below were built BOTH ways with scripts/lean_verify.sh (rival exit 0, gold exit
1) before shipping, and every gold-side failure was read to confirm it is a
SEMANTIC refutation — `decide` evaluating the claim and proving the negation
false — rather than an unknown identifier, a type error or a stuck reduction.
The carrier is transparent, so `decide` closes each and no witness binds a
hypothesis (nothing to be inconsistent).

AUDIT PROBES THAT FOUND NO HOLE (recorded so the next audit need not re-run
them): two further correct reshapes beyond the shipped positives — a `match`
form at each site proven by `cases elems <;> rfl` — both VERIFY, so the spec is
not over-fit to the imperative shape (no SPEC-TOO-STRONG). The four
interleaving wrong impls now shipped as w9..w12 were each REJECTED by the frozen
spec when first probed, so the separator/order gap was a battery gap, not a hole
in the spec (no SPEC-TOO-WEAK).

SECOND AUDIT — probes run and their real exit codes (SPEC-TOO-WEAK direction,
attack D). Five NEW wrong impls beyond the shipped rivals, each built against
the frozen spec: (1) the members-absent case emitting TEXT-kind pieces rather
than punctuation pieces; (2) the token layout keeping its TRAILING separator;
(3) the token layout dropping its LEADING piece instead of the trailing
separator; (4) the text join with a trailing separator appended; (5) the text
join additionally wrapped in brackets. All five were REJECTED (build exit 1) and
all five are refuted by an existing witness (witness-vs-rival exit 0), so the
spec pins every one of these facts — no spec hole. Probes (2) and (4) attacked a
clause NO shipped rival reached, so they are now shipped as w13/w14.

SECOND AUDIT — probes run (SPEC-TOO-STRONG direction, attack E). Two further
correct reshapes: a `foldr`-based token assembly guarded by `elems.length = 0`
(rather than `isEmpty`), and a text assembly guarded by `elems == []` whose join
runs over `elems.reverse.reverse`. Both VERIFY (exit 0), so neither the guard
spelling nor the accumulation direction is over-fit — no soundness hole. Recorded
because the first attempt at the `foldr` reshape FAILED, and the failure was the
prober's own `simp` normalization (`e ++ [sep] ++ acc` vs `e ++ sep :: acc`), NOT
the spec: re-proving the same reshape with an explicit `rw [List.foldr_cons, ih]`
closed it. A failed reshape proof is not evidence of a spec hole until the proof
itself has been ruled out.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7462"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of a region substring; assert it actually
    matched and is unique so silent drift (Solution.lean edited) fails loudly."""
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — each lies ENTIRELY inside the impl region (impls) or the
# proof region (theorem bodies) of Solution.lean and is unique across the file.
# ---------------------------------------------------------------------------

# The two frozen impl bodies (Id.run do blocks).
_SIG_IMPL = (
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct "(", SigToken.punct ")"]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result.dropLast"
)

_TXT_IMPL = (
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return "()"\n'
    '  return String.intercalate ", " elems'
)

# The two frozen proof bodies (theorem statement + tactics), byte-identical to
# the file so a positive control can re-emit the STATEMENT and swap only the
# tactic body (variant_scope permits proof-body edits, requires the statement).
_SIG_CORR = (
    "theorem correct_renderTupleSig :\n"
    "    ∀ (elems : List (List SigToken)),\n"
    "      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by\n"
    "  intro elems\n"
    "  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig\n"
    "  by_cases h : elems.isEmpty\n"
    "  · simp [h, Id.run, pure]\n"
    "  · simp only [h, Id.run]\n"
    "    have hbridge :\n"
    "        (do\n"
    "          pure PUnit.unit\n"
    "          let r ← forIn elems ([] : List SigToken) fun elem r => do\n"
    "              pure PUnit.unit\n"
    '              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))\n'
    "          pure r.dropLast : Id (List SigToken))\n"
    "        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>\n"
    '            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl\n'
    "    rw [hbridge, helper_renderTupleSig]\n"
    "    simp [pure]"
)

_TXT_CORR = (
    "theorem correct_renderTupleText :\n"
    "    ∀ (elems : List String),\n"
    "      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by\n"
    "  intro elems\n"
    "  unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText\n"
    "  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]"
)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — expect "verify"
# ===========================================================================

# (pos-functional-form) A structurally different CORRECT impl at BOTH sites: a
# pure functional `def` driven by `match` on the carrier (no imperative
# do-block / for / mut), which SPELLS OUT the layout rather than delegating to
# the spec's own model. If it fails to verify the spec is over-fit to the
# imperative shape => SPEC-TOO-STRONG.
#
# AUDIT NOTE (why the body is not `assembleTupleSig elems`): this case
# previously set each impl to the deep model itself, so `problem_spec_* elems
# (implementation_* elems)` was `assembleTupleSig elems = assembleTupleSig
# elems` and `rfl` closed a TAUTOLOGY. Such a positive verifies for free no
# matter how the spec is shaped, and therefore cannot detect SPEC-TOO-STRONG —
# it is exactly the "impl is trivially the frozen model" evasion. The `match`
# form below re-derives the non-empty layout independently (its cons branch
# writes the map/flatten/dropLast pipeline over `e :: rest`), so `rfl` has real
# definitional work to do and the case can actually fail if the spec is
# over-fit. Both sites re-verified after the change (lean_verify.sh exit 0).
_POS_FUNC_SIG_IMPL = (
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken :=\n"
    "  match elems with\n"
    '  | [] => [SigToken.punct "(", SigToken.punct ")"]\n'
    "  | e :: rest =>\n"
    '      (((e :: rest).map (fun x => x ++ [SigToken.punct ", "])).flatten).dropLast'
)
_POS_FUNC_TXT_IMPL = (
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String :=\n"
    "  match elems with\n"
    '  | [] => "()"\n'
    '  | _ => String.intercalate ", " elems'
)
_POS_FUNC_SIG_CORR = (
    "theorem correct_renderTupleSig :\n"
    "    ∀ (elems : List (List SigToken)),\n"
    "      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by\n"
    "  intro elems\n"
    "  cases elems <;> rfl"
)
_POS_FUNC_TXT_CORR = (
    "theorem correct_renderTupleText :\n"
    "    ∀ (elems : List String),\n"
    "      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by\n"
    "  intro elems\n"
    "  cases elems <;> rfl"
)
POS_FUNCTIONAL = _swap(
    _swap(
        _swap(
            _swap(_BASE, _SIG_IMPL, _POS_FUNC_SIG_IMPL),
            _TXT_IMPL, _POS_FUNC_TXT_IMPL),
        _SIG_CORR, _POS_FUNC_SIG_CORR),
    _TXT_CORR, _POS_FUNC_TXT_CORR)

# (pos-reorder) The same executable meaning at both sites but with the NON-EMPTY
# layout tested first (`if !elems.isEmpty`) and the empty return last. Proof
# re-closed (same bridge; the branch-condition negation is discharged by
# `Bool.not_false`/`if_true`). If it fails to verify the spec is over-fit to one
# branch order => SPEC-TOO-STRONG.
_POS_RE_SIG_IMPL = (
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if !elems.isEmpty then\n"
    "    let mut result : List SigToken := []\n"
    "    for elem in elems do\n"
    "      result := result ++ elem\n"
    '      result := result ++ [SigToken.punct ", "]\n'
    "    return result.dropLast\n"
    '  return [SigToken.punct "(", SigToken.punct ")"]'
)
_POS_RE_TXT_IMPL = (
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if !elems.isEmpty then\n"
    '    return String.intercalate ", " elems\n'
    '  return "()"'
)
_POS_RE_SIG_CORR = (
    "theorem correct_renderTupleSig :\n"
    "    ∀ (elems : List (List SigToken)),\n"
    "      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by\n"
    "  intro elems\n"
    "  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig\n"
    "  by_cases h : elems.isEmpty\n"
    "  · simp [h, Id.run, pure, bind]\n"
    "  · simp only [h, Bool.not_false, Id.run, if_true]\n"
    "    have hbridge :\n"
    "        (do\n"
    "          let r ← forIn elems ([] : List SigToken) fun elem r => do\n"
    "              pure PUnit.unit\n"
    '              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))\n'
    "          pure r.dropLast : Id (List SigToken))\n"
    "        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>\n"
    '            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl\n'
    "    rw [hbridge, helper_renderTupleSig]\n"
    "    simp [pure]"
)
_POS_RE_TXT_CORR = (
    "theorem correct_renderTupleText :\n"
    "    ∀ (elems : List String),\n"
    "      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by\n"
    "  intro elems\n"
    "  unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText\n"
    "  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]"
)
POS_REORDER = _swap(
    _swap(
        _swap(
            _swap(_BASE, _SIG_IMPL, _POS_RE_SIG_IMPL),
            _TXT_IMPL, _POS_RE_TXT_IMPL),
        _SIG_CORR, _POS_RE_SIG_CORR),
    _TXT_CORR, _POS_RE_TXT_CORR)


# ===========================================================================
# ADMISSIBILITY (added by audit) — expect "verify"
#
# The PRECOND-TOO-STRONG lane. Both frozen obligations are `∀ elems, …` with no
# hypothesis binder, so there is no Requires to over-constrain — but that is NOT
# the same as the lane being vacuous, and treating it as vacuous is what this
# port previously did. On a total carrier the analogue of a too-strong
# precondition is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input: a spec that cannot be discharged there is not detectable by any
# uniqueness rival (they ask only whether the ∀-statement fails to close) nor by
# any reshape positive (they re-close the same ∀-statement a different way).
#
# The probe that DOES detect it discharges each obligation at the concrete
# F2P-shaped inputs by EVALUATION, as a `have` prepended to the existing tactic
# body, and only then closes the frozen obligation verbatim. Both representative
# shapes are grounded at both sites: the MEMBERS-ABSENT input (the sub-domain the
# new tests add) and a TWO-MEMBER input (the smallest shape where the
# interleaving is observable). If either `have` could not close, the modeled
# behavior would be contradictory at a normal input while the ∀-obligation still
# "verified" — the total-carrier PRECOND-TOO-STRONG signal.
#
# Scope: no new declaration, no new axiom/assumption token, and BOTH theorem
# statements stay byte-identical (the `have`s live inside the existing proof
# region, which variant_scope permits). Built with lean_verify.sh: exit 0.
_ADMISS_SIG_HAVE = (
    "  have _ground_empty : problem_spec_renderTupleSig ([] : List (List SigToken))\n"
    "      (implementation_renderTupleSig ([] : List (List SigToken))) := by\n"
    "    unfold problem_spec_renderTupleSig implementation_renderTupleSig\n"
    "    decide\n"
    "  have _ground_two : problem_spec_renderTupleSig\n"
    '      [[SigToken.text "a"], [SigToken.text "b"]]\n'
    '      (implementation_renderTupleSig [[SigToken.text "a"], [SigToken.text "b"]]) := by\n'
    "    unfold problem_spec_renderTupleSig implementation_renderTupleSig\n"
    "    decide\n"
)
_ADMISS_TXT_HAVE = (
    "  have _ground_empty : problem_spec_renderTupleText ([] : List String)\n"
    "      (implementation_renderTupleText ([] : List String)) := by\n"
    "    unfold problem_spec_renderTupleText implementation_renderTupleText\n"
    "    decide\n"
    '  have _ground_two : problem_spec_renderTupleText ["a", "b"]\n'
    '      (implementation_renderTupleText ["a", "b"]) := by\n'
    "    unfold problem_spec_renderTupleText implementation_renderTupleText\n"
    "    decide\n"
)
ADMISS_GROUND = _swap(
    _swap(_BASE,
          _SIG_CORR,
          _SIG_CORR.replace("  intro elems\n", _ADMISS_SIG_HAVE + "  intro elems\n", 1)),
    _TXT_CORR,
    _TXT_CORR.replace("  intro elems\n", _ADMISS_TXT_HAVE + "  intro elems\n", 1))


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# Each edits ONLY one impl body; the frozen proofs are left in place (they no
# longer close against the reshaped impl, which is exactly why a witness is
# required to attribute the rejection to the spec).
# ===========================================================================

# (w1-prepatch-tok) Token site, drop the empty special-case and assemble
# unconditionally. Correct on every non-empty sequence; on the empty sequence it
# lays out an empty list and drops a (non-existent) trailing separator, yielding
# the empty display instead of `(` `)`.
_W1 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result.dropLast")

# (w2-prepatch-txt) Text site, drop the empty special-case and join
# unconditionally. Correct on every non-empty sequence; on the empty sequence it
# joins the empty list, yielding "" instead of "()".
_W2 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    '  return String.intercalate ", " elems')

# (w3-wrongtok-one-node) Token site, empty case emits ONE punctuation token
# carrying the two-character text `()` rather than the two separate `(` `)`
# tokens. Correct on every non-empty sequence; wrong only on empty, in piece
# COUNT (length 1 vs length 2).
_W3 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct "()"]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result.dropLast")

# (w4-swaptok-order) Token site, empty case emits `)` then `(` (close before
# open). Correct on every non-empty sequence; wrong only on empty, in ORDER.
_W4 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct ")", SigToken.punct "("]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result.dropLast")

# (w5-wrongtxt-one-char) Text site, empty case renders the single character `(`
# instead of `()`. Correct on every non-empty sequence; wrong only on empty, by
# a missing `)`.
_W5 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return "("\n'
    '  return String.intercalate ", " elems')

# (w6-swaptxt-order) Text site, empty case renders `)(` instead of `()`. Correct
# on every non-empty sequence; wrong only on empty, in character ORDER.
_W6 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return ")("\n'
    '  return String.intercalate ", " elems')

# (w7-always-empty-tok) Token site, emit the empty-case output for EVERY
# sequence (drop the member layout entirely). Correct on the empty sub-domain;
# wrong on every non-empty sequence. Attacks the NON-EMPTY clause.
_W7 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    '  return [SigToken.punct "(", SigToken.punct ")"]')

# (w8-always-empty-txt) Text site mirror of w7: render `()` for EVERY sequence.
# Correct on the empty sub-domain; wrong on every non-empty sequence. Attacks the
# NON-EMPTY clause of the OTHER obligation (varies the non-empty text binder,
# which w7 does not touch).
_W8 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    '  return "()"')

# ---------------------------------------------------------------------------
# MULTI-MEMBER rivals (added by audit) — the INTERLEAVING sub-domain.
#
# Every rival above is refuted at either `[]` or a ONE-member sequence, and a
# one-member sequence does not observe the interleaving at all: the loop appends
# exactly one separator and `dropLast` immediately removes it, so the separator's
# own identity and the member ORDER are both invisible there. A rival that gets
# the separator text or the member order wrong is therefore correct on 100% of
# the points the battery previously tested, and the SEPARATOR clause of both
# `assembleTuple*` was unattacked. These four rivals close that, each refuted at
# a TWO-member sequence (the smallest point where interleaving is observable).
# All four were built both ways before shipping (rival exit 0, gold exit 1) and
# each gold-side failure is a semantic `decide` refutation, not a tactic gap.
# ---------------------------------------------------------------------------

# (w9-sep-nospace-tok) Token site, separator token carries `,` instead of `, `.
# Correct on empty AND on every one-member sequence; wrong from two members up.
_W9 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct "(", SigToken.punct ")"]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ","]\n'
    "  return result.dropLast")

# (w10-revorder-tok) Token site, members laid out in REVERSE order. Correct on
# empty AND on every one-member sequence; wrong from two members up.
_W10 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct "(", SigToken.punct ")"]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems.reverse do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result.dropLast")

# (w11-sep-nospace-txt) Text site, join separator is `,` instead of `, `.
# Correct on empty AND on every one-member sequence; wrong from two members up.
_W11 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return "()"\n'
    '  return String.intercalate "," elems')

# (w12-revorder-txt) Text site, member texts joined in REVERSE order. Correct on
# empty AND on every one-member sequence; wrong from two members up.
_W12 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return "()"\n'
    '  return String.intercalate ", " elems.reverse')


# ---------------------------------------------------------------------------
# TRAILING-SEPARATOR rivals (added by the second audit).
#
# Every rival above gets the drop-trailing step RIGHT and differs somewhere else
# (the members-absent output, the separator's text, the member order). So the
# "…with the single trailing separator dropped" / "joined by" half of both
# `assembleTuple*` — a fact the spec genuinely asserts — was never probed: a
# rival that emits the layout with its trailing separator still attached was
# correct at every point the battery tested. Both are refuted at the two-member
# point, and both were REJECTED by the frozen spec when probed (build exit 1)
# with their witness elaborating against the rival (exit 0).
# ---------------------------------------------------------------------------

# (w13-keep-trailing-tok) Token site, return the layout WITHOUT dropping the
# trailing separator. Correct on the members-absent input; wrong on every
# non-empty sequence by one extra trailing separator piece.
_W13 = _swap(
    _BASE, _SIG_IMPL,
    "def implementation_renderTupleSig\n"
    "    (elems : List (List SigToken)) : List SigToken := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return [SigToken.punct "(", SigToken.punct ")"]\n'
    "  let mut result : List SigToken := []\n"
    "  for elem in elems do\n"
    "    result := result ++ elem\n"
    '    result := result ++ [SigToken.punct ", "]\n'
    "  return result")

# (w14-trailing-sep-txt) Text site mirror: join correctly, then append a trailing
# separator. Correct on the members-absent input; wrong on every non-empty
# sequence by a trailing comma-and-space.
_W14 = _swap(
    _BASE, _TXT_IMPL,
    "def implementation_renderTupleText\n"
    "    (elems : List String) : String := Id.run do\n"
    "  if elems.isEmpty then\n"
    '    return "()"\n'
    '  return String.intercalate ", " elems ++ ", "')


# --- witnesses (checked with the frozen obligations removed) ---------------
# Each negates the spec predicate at one concrete input. The carrier is
# transparent, so `decide` closes and no witness binds a hypothesis.

def _wit_sig(elems: str) -> str:
    return (
        "example : ¬ problem_spec_renderTupleSig\n"
        f"    {elems}\n"
        f"    (implementation_renderTupleSig {elems}) := by\n"
        "  unfold problem_spec_renderTupleSig implementation_renderTupleSig\n"
        "  decide")


def _wit_txt(elems: str) -> str:
    return (
        "example : ¬ problem_spec_renderTupleText\n"
        f"    {elems}\n"
        f"    (implementation_renderTupleText {elems}) := by\n"
        "  unfold problem_spec_renderTupleText implementation_renderTupleText\n"
        "  decide")


# EMPTY sub-domain, token site: gold => [`(`, `)`], the prepatch/one-node/
# swapped rivals differ (empty list / one node / reversed order).
_WIT_SIG_EMPTY = _wit_sig("([] : List (List SigToken))")
# NON-EMPTY sub-domain, token site, at a TWO-member sequence: gold => the two
# member layouts interleaved with ONE `, ` and no trailing separator, w7 => the
# empty-case output.
#
# AUDIT NOTE (why two members and not one): this witness used to refute at the
# one-member point `[[text "a"]]`, which discriminates w7 correctly but is the
# WEAKEST non-empty point on the carrier — with one member the loop appends a
# single separator and `dropLast` removes it again, so the separator token and
# the member order are unobservable there. Refuting at two members exercises the
# surviving separator and the member order as well, and it still discriminates
# w7 (rival exit 0, gold exit 1, gold failing by semantic `decide` refutation).
# It is also the point the new w9/w10 interleaving rivals need.
_WIT_SIG_NONEMPTY = _wit_sig('[[SigToken.text "a"], [SigToken.text "b"]]')
# EMPTY sub-domain, text site: gold => "()", the prepatch/one-char/swapped rivals
# differ ("" / "(" / ")(").
_WIT_TXT_EMPTY = _wit_txt("([] : List String)")
# NON-EMPTY sub-domain, text site, at a TWO-member sequence: gold => "a, b"
# (members joined by exactly one `, `), w8 => "()". Strengthened from the
# one-member point `["a"]` for the reason recorded above: `["a"]` renders as "a"
# with no separator at all, so it cannot see a wrong separator or a wrong order.
_WIT_TXT_NONEMPTY = _wit_txt('["a", "b"]')


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-functional-form", "kind": "soundness", "expect": "verify",
     "module": POS_FUNCTIONAL,
     "rationale": "a structurally-different but correct impl at BOTH sites: a pure "
                  "functional `def` driven by `match` on the carrier (no imperative "
                  "do-block / for / mut), whose cons branch SPELLS OUT the "
                  "interleave/flatten/drop-trailing layout instead of delegating to "
                  "the spec's model, so `cases elems <;> rfl` has real definitional "
                  "work to do. If it fails to verify the spec is over-fit to the "
                  "imperative shape => SPEC-TOO-STRONG. Amended by audit: the "
                  "earlier version of this case set each impl to `assembleTuple* "
                  "elems` — the deep model itself — so the obligation reduced to "
                  "`assembleTupleSig elems = assembleTupleSig elems` and `rfl` "
                  "closed a tautology that would verify against ANY shape of spec, "
                  "detecting nothing. Re-built after the change with lean_verify.sh "
                  "(exit 0)."},
    {"id": "pos-reorder", "kind": "soundness", "expect": "verify",
     "module": POS_REORDER,
     "rationale": "a second correct impl at both sites with the NON-EMPTY layout "
                  "tested first (`if !elems.isEmpty`) and the empty return last — "
                  "same executable meaning, different source. The equality clause is "
                  "agnostic to branch order; proof re-closed (same accumulator "
                  "bridge, branch-condition negation discharged by "
                  "Bool.not_false/if_true). If it fails to verify the spec is "
                  "over-fit to one branch order => SPEC-TOO-STRONG. Built with "
                  "lean_verify.sh (exit 0)."},

    # ---- admissibility (must VERIFY) — added by audit ----
    {"id": "admiss-ground-shapes", "kind": "admissibility", "expect": "verify",
     "module": ADMISS_GROUND,
     "rationale": "the PRECOND-TOO-STRONG lane, restored by audit (it had been "
                  "dropped as vacuous). Neither obligation carries a precondition "
                  "hypothesis, so there is no Requires to over-constrain — but the "
                  "analogue on this TOTAL carrier is the obligation being "
                  "UNSATISFIABLE at exactly an F2P-shaped input, which no rival and "
                  "no reshape positive can see (both only ask whether the "
                  "∀-statement closes). This case discharges each obligation at the "
                  "concrete F2P-shaped inputs BY EVALUATION — as `have`s prepended "
                  "to the existing tactic body — and only then closes the frozen "
                  "obligation verbatim. Both sub-domains are grounded at BOTH sites: "
                  "the members-absent input (the sub-domain the new tests add) and a "
                  "two-member input (the smallest interleaving-observable shape). If "
                  "a `have` could not close, the modeled behavior would be "
                  "contradictory at a normal input while the ∀-obligation still "
                  "verified. Nothing is assumed: no new declaration, no new "
                  "assumption token, both theorem statements byte-identical. Built "
                  "with lean_verify.sh (exit 0)."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "w1-prepatch-tok", "kind": "uniqueness", "expect": "reject",
     "module": _W1, "witness": _WIT_SIG_EMPTY,
     "refinement": "its faithful real patch is the pre-fix token assembly with no "
                   "guard for the members-absent case: it lays out an empty member "
                   "list and removes a trailing separator that is not there, which "
                   "on the members-absent input errors out at run time instead of "
                   "emitting the two bracket pieces. The F2P that adds the "
                   "members-absent case asserts two separate bracket pieces are "
                   "emitted; the patch errors and does NOT resolve — so a verifying "
                   "rival here is a true verify-does-not-imply-resolve break.",
     "rationale": "attacks the EMPTY clause of renderTupleSig: on `elems = []` gold "
                  "=> [`(`, `)`] while the rival lays out nothing and returns the "
                  "empty display. Witness at `[]`. Built both ways (rival exit 0, "
                  "gold exit 1)."},
    {"id": "w2-prepatch-txt", "kind": "uniqueness", "expect": "reject",
     "module": _W2, "witness": _WIT_TXT_EMPTY,
     "refinement": "its faithful real patch is the pre-fix text assembly with no "
                   "guard for the members-absent case: it joins an empty member list "
                   "and yields the empty string instead of the two-character bracket "
                   "text. The F2P that adds the members-absent case asserts the "
                   "two-character bracket text; the patch yields the empty string and "
                   "does NOT resolve.",
     "rationale": "attacks the EMPTY clause of renderTupleText: on `elems = []` gold "
                  '=> "()" while the rival joins nothing and returns "". Witness at '
                  "`[]`. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "w3-wrongtok-one-node", "kind": "uniqueness", "expect": "reject",
     "module": _W3, "witness": _WIT_SIG_EMPTY,
     "refinement": "its faithful real patch emits ONE punctuation piece carrying "
                   "the two-character bracket text instead of two separate bracket "
                   "pieces. The F2P asserts exactly two separate punctuation pieces "
                   "positionally; one combined piece fails that assertion and does "
                   "NOT resolve.",
     "rationale": "attacks the piece-COUNT of the EMPTY clause of renderTupleSig: "
                  "gold => a length-2 token list, the rival => a length-1 token list. "
                  "Witness at `[]`. Built both ways (rival exit 0, gold exit 1)."},
    {"id": "w4-swaptok-order", "kind": "uniqueness", "expect": "reject",
     "module": _W4, "witness": _WIT_SIG_EMPTY,
     "refinement": "its faithful real patch emits the two bracket pieces in the "
                   "reversed order (close before open). The F2P asserts the opening "
                   "bracket BEFORE the closing one positionally; the reversed order "
                   "fails that assertion and does NOT resolve.",
     "rationale": "attacks the ORDER of the EMPTY clause of renderTupleSig: gold => "
                  "[open, close], the rival => [close, open]. Witness at `[]`. Built "
                  "both ways (rival exit 0, gold exit 1)."},
    {"id": "w5-wrongtxt-one-char", "kind": "uniqueness", "expect": "reject",
     "module": _W5, "witness": _WIT_TXT_EMPTY,
     "refinement": "its faithful real patch renders the members-absent case as the "
                   "single opening-bracket character, producing malformed output. The "
                   "F2P asserts exactly the two-character bracket text; the "
                   "single-character output fails it and does NOT resolve.",
     "rationale": "attacks the length/identity of the EMPTY clause of "
                  'renderTupleText: gold => "()" (length 2), the rival => "(" '
                  "(length 1). Witness at `[]`. Built both ways (rival exit 0, gold "
                  "exit 1)."},
    {"id": "w6-swaptxt-order", "kind": "uniqueness", "expect": "reject",
     "module": _W6, "witness": _WIT_TXT_EMPTY,
     "refinement": "its faithful real patch renders the members-absent case as the "
                   "reversed bracket pair. The F2P asserts the two-character bracket "
                   "text in open-then-close order; the reversed text fails it and "
                   "does NOT resolve.",
     "rationale": "attacks the character ORDER of the EMPTY clause of "
                  'renderTupleText: gold => "()", the rival => ")(". Witness at `[]`. '
                  "Built both ways (rival exit 0, gold exit 1)."},
    {"id": "w7-always-empty-tok", "kind": "uniqueness", "expect": "reject",
     "module": _W7, "witness": _WIT_SIG_NONEMPTY,
     "refinement": "its faithful real patch unconditionally emits the two bracket "
                   "pieces and drops the member layout, so every sequence renders as "
                   "a bare bracket pair losing all members. The existing "
                   "non-empty-sequence tests assert the member pieces; the "
                   "member-losing output fails them and does NOT resolve.",
     "rationale": "attacks the NON-EMPTY clause of renderTupleSig (the opposite side "
                  "of the prepatch rivals): a fixed 2-piece output != the member "
                  "layout for any non-empty sequence. Witness at "
                  "`[[text \"a\"], [text \"b\"]]`: gold => the two members "
                  "interleaved, the rival => the bracket pair. (Corrected by audit: "
                  "this rationale still named the one-member point `[[text \"a\"]]` "
                  "after the shared non-empty witness was strengthened to two "
                  "members.) Built both ways (rival exit 0, gold exit 1)."},
    {"id": "w8-always-empty-txt", "kind": "uniqueness", "expect": "reject",
     "module": _W8, "witness": _WIT_TXT_NONEMPTY,
     "refinement": "its faithful real patch unconditionally returns the "
                   "two-character bracket text and drops the member join, so every "
                   "sequence renders as bare brackets losing all members. The "
                   "existing non-empty-sequence tests assert the joined member texts; "
                   "the member-losing output fails them and does NOT resolve.",
     "rationale": "attacks the NON-EMPTY clause of renderTupleText — the text-site "
                  "mirror of w7, added so the non-empty binder is varied on BOTH "
                  'obligations. Witness at `["a", "b"]`: gold => "a, b", the rival '
                  '=> "()". Built both ways (rival exit 0, gold exit 1).'},

    # ---- multi-member / interleaving rivals (added by audit) ----
    {"id": "w9-sep-nospace-tok", "kind": "uniqueness", "expect": "reject",
     "module": _W9, "witness": _WIT_SIG_NONEMPTY,
     "refinement": "its faithful real patch emits the member separator without its "
                   "trailing space, so a multi-member sequence renders with the "
                   "members run up against the separator instead of spaced. The "
                   "existing multi-member display test asserts the separator piece "
                   "by its exact text (comma AND space) positionally between the "
                   "members; a comma-only piece fails that assertion and does NOT "
                   "resolve. Note this rival is correct on the members-absent input "
                   "the new tests add, so it is invisible to those and is caught "
                   "only by the pre-existing multi-member case.",
     "rationale": "attacks the SEPARATOR identity in the NON-EMPTY clause of "
                  "renderTupleSig — a clause no other rival reaches, because every "
                  "other non-empty witness sits at a ONE-member sequence where the "
                  "lone separator is appended and immediately dropped, making its "
                  'text unobservable. Witness at `[[text "a"], [text "b"]]` (the '
                  "smallest point where a separator survives): gold => the members "
                  "interleaved with a comma-and-space piece, the rival => "
                  "comma-only. Built both ways (rival exit 0, gold exit 1; gold "
                  "fails by semantic `decide` refutation)."},
    {"id": "w10-revorder-tok", "kind": "uniqueness", "expect": "reject",
     "module": _W10, "witness": _WIT_SIG_NONEMPTY,
     "refinement": "its faithful real patch walks the members in reverse, so a "
                   "multi-member sequence renders its members backwards. The "
                   "existing multi-member display test asserts the member pieces in "
                   "source order positionally; the reversed layout fails it and does "
                   "NOT resolve. Like w9 this rival is correct on the members-absent "
                   "input, so the newly added tests do not see it.",
     "rationale": "attacks member ORDER in the NON-EMPTY clause of renderTupleSig, "
                  "which is unobservable at every one-member point the other rivals "
                  'use. Witness at `[[text "a"], [text "b"]]`: gold => a-then-b, the '
                  "rival => b-then-a. Built both ways (rival exit 0, gold exit 1; "
                  "gold fails by semantic `decide` refutation)."},
    {"id": "w11-sep-nospace-txt", "kind": "uniqueness", "expect": "reject",
     "module": _W11, "witness": _WIT_TXT_NONEMPTY,
     "refinement": "its faithful real patch joins the member texts on a comma with "
                   "no following space, so a multi-member sequence renders unspaced. "
                   "The existing multi-member source-text case asserts the joined "
                   "text with comma-and-space exactly; the unspaced text fails it "
                   "and does NOT resolve.",
     "rationale": "attacks the SEPARATOR identity in the NON-EMPTY clause of "
                  "renderTupleText (the text-site mirror of w9). Witness at "
                  '`["a", "b"]`: gold => "a, b", the rival => "a,b". Built both ways '
                  "(rival exit 0, gold exit 1; gold fails by semantic `decide` "
                  "refutation)."},
    {"id": "w12-revorder-txt", "kind": "uniqueness", "expect": "reject",
     "module": _W12, "witness": _WIT_TXT_NONEMPTY,
     "refinement": "its faithful real patch joins the member texts in reverse, so a "
                   "multi-member sequence renders its members backwards. The "
                   "existing multi-member source-text case asserts the members in "
                   "source order; the reversed join fails it and does NOT resolve.",
     "rationale": "attacks member ORDER in the NON-EMPTY clause of renderTupleText "
                  "(the text-site mirror of w10). Witness at `[\"a\", \"b\"]`: gold "
                  '=> "a, b", the rival => "b, a". Built both ways (rival exit 0, '
                  "gold exit 1; gold fails by semantic `decide` refutation)."},

    # ---- trailing-separator rivals (added by the second audit) ----
    {"id": "w13-keep-trailing-tok", "kind": "uniqueness", "expect": "reject",
     "module": _W13, "witness": _WIT_SIG_NONEMPTY,
     "refinement": "its faithful real patch lays the members out with a separator "
                   "after each one and then forgets to remove the LAST one, so a "
                   "multi-member sequence renders with a dangling separator piece "
                   "after its final member. The existing multi-member display test "
                   "asserts the piece sequence positionally and exhaustively; a "
                   "trailing separator piece is one piece too many and fails that "
                   "assertion, so it does NOT resolve. Note this rival is correct on "
                   "the members-absent input the new tests add, so those tests do "
                   "not see it — only the pre-existing multi-member case does.",
     "rationale": "attacks the DROP-TRAILING half of the NON-EMPTY clause of "
                  "renderTupleSig, a fact the spec asserts that no other rival "
                  "probes: every other rival performs the drop correctly and differs "
                  "elsewhere (members-absent output, separator text, member order). "
                  'Witness at `[[text "a"], [text "b"]]`: gold => the members '
                  "interleaved with ONE separator and none trailing, the rival => the "
                  "same plus a trailing separator. Built both ways (rival exit 0, "
                  "gold exit 1; gold fails by semantic `decide` refutation)."},
    {"id": "w14-trailing-sep-txt", "kind": "uniqueness", "expect": "reject",
     "module": _W14, "witness": _WIT_TXT_NONEMPTY,
     "refinement": "its faithful real patch joins the member texts correctly and "
                   "then appends one more separator, so a multi-member sequence "
                   "renders with a dangling comma-and-space at its end. The existing "
                   "multi-member source-text case asserts the joined text exactly; "
                   "the trailing separator fails it and does NOT resolve. Like w13 "
                   "this rival is correct on the members-absent input.",
     "rationale": "attacks the JOIN half of the NON-EMPTY clause of renderTupleText "
                  "from the trailing side (the text-site mirror of w13) — the one "
                  "non-empty fact no other text rival reaches. Witness at "
                  '`["a", "b"]`: gold => "a, b", the rival => "a, b" with a trailing '
                  "comma-and-space. Built both ways (rival exit 0, gold exit 1; gold "
                  "fails by semantic `decide` refutation)."},
]


# The axiom lane (G-AX) is a skip stub for this bundle: the per-element renderer
# is left universally quantified (arbitrary `elems`), so no callee opaque/axiom
# contract is consumed and there is nothing for the axiom lane to run.
AXIOM_TESTS = []
