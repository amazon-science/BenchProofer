# properties.py — G-PBT falsification battery for sympy__sympy-16886 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   encodeMorse : List Char → List Char → List Char
#   Renders a message into its dot/dash encoding. The message is read as a series
#   of WORDS separated by ASCII word breaks. Within a word, the code words of the
#   supported characters appear in input order joined by ONE copy of the separator;
#   a character the standard alphabet does not support contributes nothing and no
#   separator; a word that retains no supported character is absent entirely.
#   Encoded words are joined by TWO copies of the separator, and a message ending
#   in a word break contributes one further doubled separator. The separator is a
#   caller-chosen character SEQUENCE of any length, excluding only a single
#   character that already has a code word or is the space. The SINGLE
#   postcondition pins the whole result to (sep, msg); no output component is left
#   free. The load-bearing content is the standard code-word table (the
#   discriminator this instance fixes is one digit's code word) plus five
#   structural clauses — word segmentation, the pass-over of unsupported
#   characters, the dropping of empty words, the one-vs-two separator levels, and
#   the trailing word break. The table is modeled DEEPLY (a total function of the
#   character, spelled out entry by entry), so there is no opaque answer-key oracle
#   to echo — computing the answer IS doing the work — and the carrier (List Char,
#   the separator sequence, the joins) is fully transparent and decidable at
#   concrete inputs.
#
# CARRIER NOTE: nagini contracted TWO functions (a whole-message encoder + a
# per-symbol table builder) over List[int] code points behind fractional
# permissions, and expressed the encoding as a front-recursive fold pinned via
# ToSeq. This backend collapses the modeled behaviour into ONE total Lean `def`
# `encodeMorse` over a transparent `List Char` carrier, with the code-word table
# modeled DEEPLY as `codeMorse`/`codeOf` (an A-reference, validated == the real
# table by G-AX). Every splice — the per-character table lookup, the word
# segmentation, the traversal order, and both separator levels — is therefore
# transparently attackable here at concrete literal inputs.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY #1 class: `msg` was read-only Acc(.,1/2) and
#     the mandatory rival WROTE `msg[0] = dash()` into the input in place, rejected
#     for insufficient permission). Lean is referentially transparent — no aliasing,
#     no fractional permissions — so a "write-back into a read-only input" rival is
#     not expressible and the whole lane is VACUOUS here. See 'assessment'.
#   * AXIOM_TESTS. Validating the deep-model table == the real callee is G-AX's job;
#     this gate ignores them.
#
# LANES THAT DO PORT, RE-DERIVED (an earlier revision of this file recorded the
# first two as not porting; both are in fact expressible on this carrier and are
# now carried as cases):
#   * ADMISSIBILITY (ports nagini's admiss-default-sep). The lean obligation carries
#     TWO precondition hypotheses, `∀ c ∈ msg, isModeledChar c` and
#     `isUsableSep sep = true`. It is NOT true that the pos-functional-map positive
#     discharges them: that positive closes with `fun sep msg _ _ => main sep msg`,
#     DISCARDING both
#     without ever exhibiting an input that satisfies them, so it attests nothing
#     about satisfiability. The analogue of PRECOND-TOO-STRONG on a total carrier is
#     the obligation being unsatisfiable at exactly an F2P-shaped input, which
#     admiss-f2p-word tests directly (see that case).
#   * WRONG-SEPARATOR-AT-ONE-POSITION (ports nagini's
#     rival-wrong-separator-first-step). Carried as rival-sep-first-step.
#   * DIVERGENCE / NON-TERMINATION (nagini's fold consumed a MustTerminate
#     obligation). An earlier revision recorded this lane as VACUOUS on the stated
#     ground that "a diverging implementation cannot be written at all". That is
#     MEASURED FALSE: `partial def spinForever (n : Nat) : List Char :=
#     spinForever (n + 1)` is accepted by Lean (`partial` is not an assumption
#     token, adds no axiom/sorry, and leaves the `theorem correct_encodeMorse`
#     statement byte-identical, so `variant_scope` returns no problems), and the
#     resulting variant is REJECTED by the verifier. What is true is only the
#     narrower fact that a PLAIN `def` with no decreasing measure is refused —
#     `fail to show termination for loopy / no parameters suitable for structural
#     recursion` (measured). So the class is a real reject lane, now carried as
#     rival-diverge-argument-independent. The witness cannot be a literal-input
#     `decide`: against the opaque `partial` term `decide` gets STUCK on the RIVAL
#     side (measured: "reduction got stuck at the `Decidable` instance
#     (spinForever …).hasDecEq"), which is the half that must succeed. Nor can it
#     condition on the result — a hypothesis-conditioned witness
#     `(h : implementation… ≠ …)` was measured to elaborate against BOTH the rival
#     and the frozen solution (exit 0 / exit 0), i.e. vacuous. The shape that
#     discriminates is FUNCTIONALITY: a diverging impl ignores its arguments, so it
#     returns ONE value at two inputs the spec forces apart. See that case.
import re
from pathlib import Path

INSTANCE = "sympy__sympy-16886"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _region(tag):
    """The body of Solution.lean's `-- <tag>-start` / `-- <tag>-end` region."""
    m = re.search(rf"-- {tag}-start\n(.*?)\n-- {tag}-end", _BASE, re.S)
    if m is None:
        raise AssertionError(f"Solution.lean has no {tag} region")
    return m.group(1)


# ---------------------------------------------------------------------------
# impl-region anchors. Each lies ENTIRELY inside impl-start/impl-end and is unique
# in the file, so editing it cannot perturb the spec view.
#
# The two WHOLE-BLOCK anchors (the impl body and the proof body) are located
# POSITIONALLY, from the region markers, rather than spelled out as literals. A
# literal spelling makes the file refuse to load after any edit to the impl,
# including a purely cosmetic one — a re-indent or a new comment — and a battery
# that cannot load is a gate that reaches no verdict on a spec nobody has shown to
# be weak. What the variants actually depend on is not the impl's SPELLING but the
# constructs they reshape or abuse, so those are asserted individually below: a
# semantic rewrite of the impl still fails loudly (which is the point of the
# original literals), while a reformat does not.
# ---------------------------------------------------------------------------

# The program's own code-word table block (the whole `codeMorse` definition, from
# its doc-comment up to the `codeOf` doc-comment). The individual table ARMS are NOT
# unique in the file — the authoritative spec table has byte-identical arms — so the
# per-character rivals edit one arm INSIDE this block and swap the whole block,
# which is unique to the impl region.
_CM_START = _BASE.index("/-- The program's own code-word table")
_CM_END = _BASE.index("/-- The encoder's total per-character lookup. -/")
_CODEMORSE = _BASE[_CM_START:_CM_END]
assert _BASE.count(_CODEMORSE) == 1, "codeMorse-block anchor drifted / not unique"

# The full impl body (the `implementation_encodeMorse` definition to the end of the
# impl region). The functional-map positive and the two whole-body rivals swap it.
_IMPL_REGION = _region("impl")
_IMPL_BODY = _IMPL_REGION[
    _IMPL_REGION.index("def implementation_encodeMorse"):].rstrip("\n")
assert _BASE.count(_IMPL_BODY) == 1, "impl-body anchor not unique"

# The frozen proof body (the tactic block after `:= by`). The functional-map
# positive reproves the SAME `theorem correct_encodeMorse` statement with a proof
# that closes for its shape; the admissibility positive PREPENDS to it and then
# closes the frozen obligation verbatim, so neither depends on its content.
_PROOF_REGION = _region("proof")
_PROOF_BODY = _PROOF_REGION[
    _PROOF_REGION.index(":= by\n") + len(":= by\n"):].rstrip("\n")
assert _BASE.count(_PROOF_BODY) == 1, "proof-body anchor not unique"

# The five impl constructs the cases below reshape or abuse, each a unique line of
# the impl region. Every one is a distinct clause of the postcondition, and a rival
# built on a fragment that has moved would attack nothing: asserting them here is
# what makes "the impl was rewritten" a loud load failure rather than a battery
# whose rivals quietly stop discriminating.
_WORD_LOOP = "  for w in wordRuns msg do\n"
_KEEP_SUPPORTED = "    let supported := w.filter (fun c => (codeMorse c).isSome)\n"
_KEEP_NONEMPTY = "    kept := kept ++ (if supported ≠ [] then [supported] else [])\n"
_RENDER_WORD = "    encoded := encoded ++ [List.intercalate sep (w.map codeOf)]\n"
_JOIN_WORDS = "  return List.intercalate (sep ++ sep) encoded\n"
_TRAILING_BREAK = "           ++ (if endsInWordBreak msg then sep ++ sep else [])"
for _frag in (_WORD_LOOP, _KEEP_SUPPORTED, _KEEP_NONEMPTY, _RENDER_WORD,
              _JOIN_WORDS, _TRAILING_BREAK):
    if _BASE.count(_frag) != 1:
        raise AssertionError(f"impl construct anchor drifted / not unique: {_frag!r}")

# The parameter list of the impl, so a rival can shadow an argument it abuses.
_IMPL_SIG = "(sep : List Char) (msg : List Char) : List Char := Id.run do"
assert _BASE.count(_IMPL_SIG) == 1, "impl signature anchor drifted"


# ---------------------------------------------------------------------------
# Witness helper. States `¬ problem_spec_encodeMorse sep msg (implementation …)` at
# one concrete (sep, msg) input over literal Chars, closed by `decide`. It ELABORATES
# against a rival whose result diverges from the spec at that point, and FAILS on the
# frozen solution (which satisfies the spec everywhere in its domain). All inputs are
# concrete literals — no opaque terms, no hypotheses — so there are no assumptions
# that could be inconsistent.
#
# Every witness point is chosen INSIDE the frozen obligation's domain, which is what
# makes refuting the rival there a statement about THIS spec: `msg` is drawn from
# printable ASCII and the blanks (`isModeledChar`), and `sep` satisfies
# `isUsableSep` — so a single-character separator is drawn from the characters the
# alphabet gives NO code word to and that are not the space ('#', '%', '&', '~'
# below). A separator that already has a code word (the '/' and ':' and ';' an
# earlier revision of this battery used) is OUTSIDE the domain, and a rival refuted
# only there would not be refuted against the guarded obligation at all. The pipe is
# avoided so the coverage reader — which treats a bare `'|'` as a match-arm
# delimiter — can read the probed input point.
# ---------------------------------------------------------------------------
def _lit(cs):
    return "[" + ", ".join("'%s'" % c for c in cs) + "]"


def _wit(sep, msg):
    s, m = _lit(sep), _lit(msg)
    return (
        f"example : ¬ problem_spec_encodeMorse {s} {m}\n"
        f"    (implementation_encodeMorse {s} {m}) := by\n"
        f"  unfold problem_spec_encodeMorse implementation_encodeMorse\n"
        f"  decide"
    )


# The two `have`s every reproved positive needs: the program's table IS the
# authoritative table, pointwise (`codeOf_eq`), and its support predicate IS the
# authoritative one (`tblf`). Both are proved by cases on the character, so neither
# is an assumption.
_TABLE_HAVES = (
    '  have codeOf_eq : codeOf = morseOf := by\n'
    '    funext c\n'
    '    unfold codeOf morseOf\n'
    '    cases c using Char.rec with\n'
    '    | _ => rfl\n'
    '  have tblf : (fun c => (codeMorse c).isSome) = (fun c => (charMorse c).isSome) := by\n'
    '    funext c\n'
    '    cases c using Char.rec with\n'
    '    | _ => rfl\n'
)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY (with a reproved obligation).
# ---------------------------------------------------------------------------

# pos-functional-map: replace BOTH imperative accumulator loops with the pointwise
# expression they compute. Behaviourally IDENTICAL on every input — the first loop
# builds the filtered, non-empty words and the second maps the within-word render
# over them, which is exactly `supportedWords`-shaped composition of `map` and
# `filter`. The `theorem correct_encodeMorse` statement is kept byte-identical; the
# proof is reproved (the two front-recursive `forIn` lemmas are no longer needed, so
# the reproof drops them and closes by rewriting the table facts). If this CORRECT
# impl failed to verify, the spec would be over-fit to the imperative-loop code
# shape => SPEC-TOO-STRONG.
_POS_MAP_IMPL = (
    'def implementation_encodeMorse\n'
    '    (sep : List Char) (msg : List Char) : List Char :=\n'
    '  List.intercalate (sep ++ sep)\n'
    '      ((((wordRuns msg).map (fun w => w.filter (fun c => (codeMorse c).isSome))).filter\n'
    '          (fun w => w ≠ [])).map (fun w => List.intercalate sep (w.map codeOf)))\n'
    '    ++ (if endsInWordBreak msg then sep ++ sep else [])'
)
_POS_MAP_PROOF = _TABLE_HAVES + (
    '  have main : ∀ (sep : List Char) (msg : List Char),\n'
    '      problem_spec_encodeMorse sep msg (implementation_encodeMorse sep msg) := by\n'
    '    intro sep msg\n'
    '    unfold problem_spec_encodeMorse implementation_encodeMorse supportedWords\n'
    '    rw [codeOf_eq, tblf]\n'
    '  refine ⟨fun sep msg _ _ => main sep msg, fun sep c _ => main sep [c],\n'
    '          ?_, ?_, ?_⟩\n'
    '  · intro p hp\n'
    '    fin_cases hp <;> rfl\n'
    '  · intro c w h\n'
    '    unfold charMorse at h\n'
    '    split at h <;> first | (injection h with h; subst h; decide) | simp at h\n'
    '  · intro c w _ h\n'
    '    unfold codeMorse at h\n'
    '    split at h <;> first | (injection h with h; subst h; decide) | simp at h'
)
_POS_MAP = _swap(_swap(_BASE, _IMPL_BODY, _POS_MAP_IMPL), _PROOF_BODY, _POS_MAP_PROOF)


# ---------------------------------------------------------------------------
# ADMISSIBILITY (PRECOND-TOO-STRONG) — must VERIFY.
# ---------------------------------------------------------------------------
# The frozen obligation is guarded by TWO hypotheses: `∀ c ∈ msg, isModeledChar c`
# (the message lies in the alphabet the encoding is specified over) and
# `isUsableSep sep = true` (the separator is one the encoding is defined for). On a
# total carrier the PRECOND-TOO-STRONG analogue is: are those guards jointly
# SATISFIABLE, and is the obligation dischargeable, at exactly an F2P-shaped input?
# The impl region is untouched; the proof body gains three leading `have`s that
# answer both halves at the concrete all-digit word with a usable separator, then
# closes the frozen obligation VERBATIM:
#   * `_hdom` exhibits a message that satisfies the domain guard;
#   * `_hsep` exhibits a separator that satisfies the usability guard;
#   * `_ground` discharges the whole spec predicate at that input by evaluation.
# None is assumed: no new theorem/lemma/axiom, no assumption token, and the
# `theorem correct_encodeMorse` statement stays byte-identical (all three live
# inside the existing tactic body). If either guard admitted NOTHING, or the
# obligation were unsatisfiable at the very input shape the F2P exercises, this
# positive would FAIL => PRECOND-TOO-STRONG.
_ADMISS_MSG = _lit("12345")
_ADMISS_SEP = _lit("#")
_ADMISS_PROOF = (
    f"  have _hdom : ∀ c ∈ {_ADMISS_MSG}, isModeledChar c := by\n"
    f"    intro c hc\n"
    f"    fin_cases hc <;> rfl\n"
    f"  have _hsep : isUsableSep {_ADMISS_SEP} = true := by decide\n"
    f"  have _ground : problem_spec_encodeMorse {_ADMISS_SEP} {_ADMISS_MSG}\n"
    f"      (implementation_encodeMorse {_ADMISS_SEP} {_ADMISS_MSG}) := by\n"
    f"    unfold problem_spec_encodeMorse implementation_encodeMorse\n"
    f"    decide\n"
) + _PROOF_BODY
_ADMISS = _swap(_BASE, _PROOF_BODY, _ADMISS_PROOF)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the frozen
# spec exactly, edits only the impl region, and carries a discriminating witness.
# The twelve fall into two families: three abuse the TABLE (a digit entry, a second
# digit entry, a letter entry), and nine abuse one of the structural clauses — the
# traversal (skip, reverse), the separator (ignored, garbled at one position,
# single-level between words), the pass-over of unsupported characters, the dropping
# of empty words, the trailing word break, and termination.
# ---------------------------------------------------------------------------

# rival-wrong-digit1: the program's table maps the character '1' to the four-signal
# code `----` instead of the standard five-signal `.----`. This IS the pre-change
# behaviour this instance fixes.
_RIVAL_D1 = _swap(
    _BASE, _CODEMORSE,
    _CODEMORSE.replace(
        '  | \'1\' => some ".----".toList',
        '  | \'1\' => some "----".toList', 1),
)

# rival-wrong-digit0: the program's table maps '0' to a WRONG but same-length code
# `....-` (the code word of a different digit) instead of `-----`. Correct on every
# other character; the LENGTH is right, so a length-only check would miss it.
_RIVAL_D0 = _swap(
    _BASE, _CODEMORSE,
    _CODEMORSE.replace(
        '  | \'0\' => some "-----".toList',
        '  | \'0\' => some "....-".toList', 1),
)

# rival-wrong-letterE: the program's table maps the LETTER 'E' to a dash instead of
# the standard single dot. The other two table rivals abuse a DIGIT entry, so
# without this one the whole letter half of the table — 26 of the 52 arms, and the
# part the P2P assertions exercise — is unprobed by any case.
_RIVAL_LETTERE = _swap(
    _BASE, _CODEMORSE,
    _CODEMORSE.replace(
        '  | \'E\' => some ".".toList',
        '  | \'E\' => some "-".toList', 1),
)

# rival-skip-first: the encoder segments `msg.drop 1` instead of `msg`, so the
# message's first character never reaches a code word. It diverges on every message
# whose leading character is supported.
_RIVAL_SKIP = _swap(_BASE, _WORD_LOOP,
                    "  for w in wordRuns (msg.drop 1) do\n")

# rival-reverse-order: within each word the code words come out in REVERSE. A true
# PERMUTATION of the within-word traversal: it keeps every code word and the exact
# separator count and total length, so only the ORDER content of the clause can
# reject it (rival-skip-first drops a word, a divergence a length check alone would
# catch).
_RIVAL_REVERSE = _swap(
    _BASE, _RENDER_WORD,
    "    encoded := encoded ++ [List.intercalate sep (w.reverse.map codeOf)]\n")

# rival-ignore-sep: the encoder ignores the caller's separator and hardcodes a fixed
# one, by shadowing the parameter on the first line of the body. Correct whenever
# the caller's separator happens to be that constant; diverges for any other — a
# genuine sub-domain, and the only rival that abuses the `sep` binder wholesale.
_RIVAL_SEP = _swap(
    _BASE, _IMPL_SIG,
    _IMPL_SIG + "\n  let sep := ['%']   -- discards the caller's separator")

# rival-sep-first-step: the encoder honours the caller's separator at every
# within-word join EXCEPT the first, where it emits a fixed '.' instead. A strictly
# WEAKER abuse of `sep` than rival-ignore-sep (which discards the argument
# everywhere): here the argument IS consulted, and is honoured at every join but
# one, so the divergence is confined to a single position and only for words with at
# least two code words. Ports nagini's rival-wrong-separator-first-step.
_RIVAL_SEP1 = _swap(
    _BASE, _RENDER_WORD,
    "    encoded := encoded ++ [match w.map codeOf with\n"
    "                           | [] => []\n"
    "                           | [x] => x\n"
    "                           | x :: y :: rest =>\n"
    "                             x ++ ['.'] ++ List.intercalate sep (y :: rest)]\n")

# rival-keep-unsupported: the encoder does NOT pass over a character the table has
# no entry for — it renders it as the empty code word, which still consumes a
# separator slot. The output therefore carries a separator where the spec says the
# character contributes nothing at all. Attacks the pass-over clause, which no other
# rival reaches.
_RIVAL_KEEP_UNSUPPORTED = _swap(_BASE, _KEEP_SUPPORTED,
                                "    let supported := w\n")

# rival-keep-empty-words: the encoder keeps a word that retained NO supported
# character, so that word contributes an empty rendering and, with it, a doubled
# separator the spec says is absent. Attacks the empty-word clause; distinct from
# rival-keep-unsupported, which keeps the unsupported CHARACTER inside a word that
# survives either way.
_RIVAL_KEEP_EMPTY = _swap(_BASE, _KEEP_NONEMPTY,
                          "    kept := kept ++ [supported]\n")

# rival-single-word-sep: the encoder joins WORDS with one copy of the separator
# instead of two, collapsing the encoding's two levels into one. Correct on any
# message of at most one represented word; diverges as soon as there are two.
# Attacks the doubled-separator clause.
_RIVAL_WORD_SEP = _swap(_BASE, _JOIN_WORDS,
                        "  return List.intercalate sep encoded\n")

# rival-drop-trailing-break: the encoder omits the extra doubled separator a message
# ending in a word break contributes. Correct on every message that does not end in
# a break, which is most of them — a narrow sub-domain rival, and the only case that
# probes the trailing clause.
_RIVAL_DROP_TRAILING = _swap(_BASE, _JOIN_WORDS + _TRAILING_BREAK,
                             _JOIN_WORDS.rstrip("\n"))

# rival-diverge-argument-independent: the encoder DIVERGES — `spinForever` recurses
# with no decreasing measure, so the result is an irreducible term at every input.
# Expressible because `partial def` is accepted (see LANES note above); rejected
# because the frozen obligation must still pin the result to the joins, which an
# opaque non-terminating term does not.
_RIVAL_DIVERGE = _swap(
    _BASE, _IMPL_BODY,
    'partial def spinForever (n : Nat) : List Char := spinForever (n + 1)\n'
    '\n'
    'def implementation_encodeMorse\n'
    '    (sep : List Char) (msg : List Char) : List Char := spinForever 0')

# Witness for the diverging rival. A literal-input `decide` is NOT usable: against
# the opaque `partial` term `decide` gets stuck on the RIVAL side (the half that
# must succeed), and a hypothesis-conditioned witness was measured VACUOUS
# (elaborates against the frozen solution too). This one refutes by FUNCTIONALITY
# instead: a diverging impl ignores its arguments, so `implementation… ['E']` and
# `implementation… ['T']` are literally the SAME term (`rfl`), while the spec pins
# them to `.` and `-` respectively. The diverging term is never unfolded, which is
# why an irreducible body is still attackable. Against the frozen solution the
# `rfl` step is a type mismatch — the two results are NOT the same term — so the
# witness fails there.
_WIT_DIVERGE = (
    "example : ¬ (problem_spec_encodeMorse ['#'] ['E']\n"
    "      (implementation_encodeMorse ['#'] ['E'])\n"
    "    ∧ problem_spec_encodeMorse ['#'] ['T']\n"
    "      (implementation_encodeMorse ['#'] ['T'])) := by\n"
    "  rintro ⟨h1, h2⟩\n"
    "  unfold problem_spec_encodeMorse at h1 h2\n"
    "  rw [show implementation_encodeMorse ['#'] ['T']\n"
    "      = implementation_encodeMorse ['#'] ['E'] from rfl, h1] at h2\n"
    "  exact absurd h2 (by decide)")


SPEC_TESTS = [
    # ---- positive control (must VERIFY) -----------------------------------
    {
        "id": "pos-functional-map",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_MAP,
        "rationale": (
            "structurally-different but CORRECT impl: both imperative accumulator "
            "loops are replaced by the pointwise `map`/`filter` composition they "
            "compute, identical on every input. The frozen `theorem "
            "correct_encodeMorse` statement is kept byte-identical and reproved for "
            "the new shape (the two front-recursive `forIn` lemmas are no longer "
            "needed, so the reproof drops them and closes by rewriting the two table "
            "facts). It discharges the sole postcondition clause — the two-level "
            "separator-joined rendering of the supported words, plus the trailing "
            "word break — exactly as gold. If it FAILED to verify, the spec would be "
            "over-fit to the imperative-loop code shape => SPEC-TOO-STRONG. (Ported "
            "from nagini's pos-encode-local-reshape / pos-mlist-branch-reorder "
            "positives, collapsed into one for this single-function carrier.)"
        ),
    },
    # ---- admissibility (must VERIFY) --------------------------------------
    {
        "id": "admiss-f2p-word",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "PRECOND-TOO-STRONG probe. The frozen obligation is guarded by two "
            "hypotheses — `∀ c ∈ msg, isModeledChar c` and `isUsableSep sep = true`. "
            "This case shows they are jointly SATISFIABLE, and the obligation "
            "dischargeable, at exactly an F2P-shaped input: three leading `have`s in "
            "the proof body exhibit the all-digit word with a usable separator "
            "(`_hdom` for the message guard, `_hsep` for the separator guard, "
            "`_ground` discharging the whole spec predicate there by evaluation) and "
            "then the frozen obligation is closed VERBATIM. The impl region is "
            "untouched, no theorem/lemma/axiom is added, no assumption token is "
            "introduced, and the `theorem correct_encodeMorse` statement is "
            "byte-identical. Note this is NOT already covered by pos-functional-map, "
            "which closes with `fun sep msg _ _ => main sep msg` and DISCARDS both "
                        "hypotheses without ever "
            "exhibiting an input satisfying them. If either guard admitted nothing, "
            "or the obligation were unsatisfiable at the input shape the F2P "
            "exercises, this would FAIL => PRECOND-TOO-STRONG. (Ports nagini's "
            "admiss-default-sep.)"
        ),
    },
    # ---- uniqueness rivals (must be REJECTED) -----------------------------
    {
        "id": "rival-wrong-digit1",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_D1,
        "refinement": (
            "the program's code-word table maps the character '1' to the four-signal "
            "`----` — EXACTLY the pre-change table entry this instance fixes (the "
            "standard code word is the five-signal `.----`). Its faithful real "
            "counterpart is the unchanged repo table; under it the FAIL_TO_PASS input "
            "'12345' renders with `----` for its first character instead of `.----`, "
            "so the exact-string assertion `encode_morse('12345') == "
            "'.----|..---|...--|....-|.....'` FAILS. It does NOT resolve the F2P — this "
            "is precisely the bug the patch fixes — so a verifying rival here would be "
            "a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause (the result is the "
            "separator-joined rendering of the per-character STANDARD code words "
            "`morseOf`): the rival's table returns `----` for '1' where `morseOf '1'` "
            "is `.----`, so the rendering diverges wherever '1' occurs (both wrong "
            "length and wrong value). Attacks the '1' entry of the table over the "
            "`msg` binder. If it VERIFIES => SPEC-TOO-WEAK (admits the pre-change "
            "bug)."
        ),
        # msg = ['1'] isolates the fixed character; sep = ['#'] (no code word, not
        # the space, so `isUsableSep` holds and the point is inside the domain).
        "witness": _wit("#", "1"),
    },
    {
        "id": "rival-wrong-digit0",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_D0,
        "refinement": (
            "the program's table maps '0' to a wrong but same-LENGTH code `....-` (a "
            "different digit's word) instead of `-----`; correct on every other "
            "character. Its faithful real counterpart is a table whose '0' entry is "
            "wrong; under it the FAIL_TO_PASS input '67890' ends in `....-` instead of "
            "`-----`, so `encode_morse('67890') == '-....|--...|---..|----.|-----'` "
            "FAILS. It does NOT resolve the F2P."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause: `morseOf '0'` is `-----`, so a "
            "table returning `....-` for '0' makes the rendering diverge wherever '0' "
            "occurs. The LENGTH is right (5 signals), so this specifically targets the "
            "VALUE pinned by the clause, on a table entry distinct from digit '1'. "
            "Attacks the '0' entry over the `msg` binder. If it VERIFIES => "
            "SPEC-TOO-WEAK (a wrong same-length code slips through)."
        ),
        # msg = ['0'] isolates a DIFFERENT abused table entry than digit1; a
        # different usable separator, so no two witnesses share an input point.
        "witness": _wit("%", "0"),
    },
    {
        "id": "rival-wrong-letterE",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_LETTERE,
        "refinement": (
            "the program's table maps the letter 'E' to a dash instead of the "
            "standard single dot; correct on every other character. Its faithful "
            "real counterpart is a table whose 'E' entry is wrong. Under it the "
            "PASS_TO_PASS assertion `encode_morse('ABC') == '.-|-...|-.-.'` still "
            "holds (no 'E'), but any message containing 'E' renders a dash where a "
            "dot belongs — e.g. the documented `encode_morse('ATTACK RIGHT FLANK')` "
            "example — so a table-wide assertion over the letter half FAILS. It does "
            "NOT resolve the F2P either (it does not touch the digit entry the F2P "
            "pins), so it is a pure SPEC-TOO-WEAK probe."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause: `morseOf 'E'` is the "
            "single-dot code, so a table returning a dash for 'E' makes the rendering "
            "diverge wherever 'E' occurs. Attacks a LETTER entry of the table — the "
            "other table rivals abuse a digit ('0'/'1'), so without this case 26 of "
            "the table's 52 arms are unprobed by any case and the battery would "
            "attest only that the digit half is pinned. If it VERIFIES => "
            "SPEC-TOO-WEAK (the letter half of the table is unpinned)."
        ),
        # msg = ['E'] isolates the abused letter entry.
        "witness": _wit("&", "E"),
    },
    {
        "id": "rival-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SKIP,
        "refinement": (
            "the encoder segments `msg.drop 1` instead of `msg`, dropping the first "
            "character's code word. Its faithful real counterpart is an encoder that "
            "skips the leading input symbol (e.g. iterating over `msg[1:]`); under it "
            "'12345' emits '..---|...--|....-|.....' (missing the leading '.----|'), so "
            "the F2P exact-string assertion FAILS. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which pins the result to the "
            "rendering of ALL of `msg` in order: dropping the head renders "
            "`msg.drop 1`, which differs from `msg` for any message whose first two "
            "code words differ. Attacks the ORDER-preserving, whole-message traversal "
            "over the `msg` binder (a structural clause the table rivals do not "
            "reach). If it VERIFIES => SPEC-TOO-WEAK (drops the first symbol)."
        ),
        # msg = ['1','2'] (length 2, distinct code words) — a distinct input point
        # from the singleton rivals; the dropped head '1' makes the rendering differ.
        "witness": _wit("~", "12"),
    },
    {
        "id": "rival-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_REVERSE,
        "refinement": (
            "within each word the encoder emits the code words in reverse order. Its "
            "faithful real counterpart is an encoder that iterates a word's "
            "characters backwards (e.g. over `word[::-1]`); under it "
            "`encode_morse('12345')` emits '.....|....-|...--|..---|.----' — the right "
            "code words in the wrong order — so the F2P exact-string assertion "
            "`encode_morse('12345') == '.----|..---|...--|....-|.....'` FAILS. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which pins each word to its "
            "code words IN ORDER. This is a true PERMUTATION: the output keeps every "
            "code word and the exact same separator count and total length, so unlike "
            "rival-skip-first (which drops a word, a divergence a length check alone "
            "would catch) only the ORDER content of the clause can reject it. Attacks "
            "the order clause over the `msg` binder at a two-letter point no other "
            "witness probes. If it VERIFIES => SPEC-TOO-WEAK (the within-word order "
            "is unpinned)."
        ),
        # msg = ['A','B'] — distinct code words of DIFFERENT lengths, so reversing is
        # observable; the first witness point drawn from the letter half.
        "witness": _wit("#", "AB"),
    },
    {
        "id": "rival-ignore-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SEP,
        "refinement": (
            "the encoder ignores the caller's separator and hardcodes a fixed one. "
            "Its faithful real counterpart is an encoder that joins with a constant "
            "separator rather than the argument; under it a call with any other "
            "separator (the F2P suite exercises non-default ones) emits the constant "
            "instead, so the corresponding exact-string assertion FAILS. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which pins BOTH join levels "
            "to the `sep` ARGUMENT: substituting a constant makes the result differ "
            "whenever `sep` is not that constant and the message has at least two "
            "code words. Attacks the `sep` binder wholesale — the only rival that "
            "discards it everywhere — so the battery demonstrates the spec's "
            "dependence on `sep`, not just on `msg`. If it VERIFIES => SPEC-TOO-WEAK "
            "(the separator is unpinned)."
        ),
        # sep = ['&'] (≠ the hardcoded constant), msg = ['1','2'] (two code words so
        # the join token is observable) — varies the `sep` binder away from the
        # constant, an input point no other witness probes.
        "witness": _wit("&", "12"),
    },
    {
        "id": "rival-sep-first-step",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_SEP1,
        "refinement": (
            "the encoder honours the caller's separator at every within-word join "
            "EXCEPT the first, where it emits a fixed '.' instead. Its faithful real "
            "counterpart is an encoder that garbles the join token at one position (a "
            "stray hardcoded signal between the first two code words); under it "
            "`encode_morse('12345')` emits '.----...---|...--|....-|.....' — a '.' "
            "where the separator belongs between the 1st and 2nd code words — so the "
            "F2P exact-string assertion "
            "`encode_morse('12345') == '.----|..---|...--|....-|.....'` FAILS. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which interleaves `sep` at "
            "EVERY adjacent pair within a word: substituting '.' at one position "
            "makes the result differ whenever a word has at least two code words. "
            "This is a strictly WEAKER abuse of the `sep` binder than "
            "rival-ignore-sep, and that is the point — there the argument is "
            "discarded everywhere, here it is genuinely consulted and honoured at "
            "every join but one, so the case tests that the clause pins the separator "
            "POSITIONWISE rather than merely 'depends on sep somewhere'. Correct on "
            "the empty and single-code-word messages, so it is a genuine "
            "partial-domain rival. If it VERIFIES => SPEC-TOO-WEAK (the separator is "
            "unpinned on a sub-domain). Ports nagini's "
            "rival-wrong-separator-first-step."
        ),
        # sep = ['%'], msg = ['1','2'] — exactly the first join, the one position this
        # rival garbles; the two code words differ so the token is observable.
        "witness": _wit("%", "12"),
    },
    {
        "id": "rival-keep-unsupported",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_KEEP_UNSUPPORTED,
        "refinement": (
            "the encoder does not pass over a character the table has no entry for: "
            "it renders it as the empty code word, which still takes a separator "
            "slot. Its faithful real counterpart is an encoder that maps an unknown "
            "character to the empty string instead of skipping it; under it a message "
            "containing an unsupported character emits a doubled separator where the "
            "character sat — e.g. `encode_morse('A%B')` yields '.-||-...' instead of "
            "'.-|-...' — so the exact-string assertion over such a message FAILS. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which renders a word from its "
            "SUPPORTED characters only, so an unsupported character contributes "
            "neither a code word nor a separator. Keeping it inserts an extra "
            "separator the clause does not allow. Attacks the pass-over clause — a "
            "clause of the postcondition no other case reaches. If it VERIFIES => "
            "SPEC-TOO-WEAK (an unsupported character is allowed to leave a mark)."
        ),
        # msg = ['A','%','B'] — a supported pair around one unsupported character
        # (37, printable ASCII, so inside `isModeledChar`); sep = ['#'].
        "witness": _wit("#", "A%B"),
    },
    {
        "id": "rival-keep-empty-words",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_KEEP_EMPTY,
        "refinement": (
            "the encoder keeps a word that retained NO supported character, so that "
            "word contributes an empty rendering and, with it, a doubled separator. "
            "Its faithful real counterpart is an encoder that emits an entry for "
            "every whitespace-delimited token, including one written entirely in "
            "unsupported characters; under it `encode_morse('A % B')` yields "
            "'.-||||-...' instead of '.-||-...', so the exact-string assertion FAILS. "
            "It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, whose `supportedWords` drops "
            "a word that retains nothing — it is absent together with its word break. "
            "Keeping it adds one more doubled separator than the clause allows. "
            "Distinct from rival-keep-unsupported, which keeps the unsupported "
            "CHARACTER inside a word that survives either way; here it is the WORD "
            "that should not appear. If it VERIFIES => SPEC-TOO-WEAK (an "
            "all-unsupported word is allowed to produce a word break)."
        ),
        # msg = ['A',' ','%',' ','B'] — three words, the middle one entirely
        # unsupported, so exactly the dropped-word clause is observable.
        "witness": _wit("#", "A % B"),
    },
    {
        "id": "rival-single-word-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_WORD_SEP,
        "refinement": (
            "the encoder joins WORDS with one copy of the separator instead of two, "
            "collapsing the encoding's two levels into one. Its faithful real "
            "counterpart is an encoder that uses a single separator at both levels; "
            "under it `encode_morse('A B')` yields '.-|-...' instead of '.-||-...', "
            "so the exact-string assertion over any multi-word message FAILS. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which joins the rendered "
            "words by `sep ++ sep` and the code words WITHIN a word by `sep`: using "
            "one copy at both levels makes the result differ as soon as two words are "
            "represented. Attacks the two-level structure — the clause that "
            "distinguishes a word break from a character break — which no other case "
            "reaches. If it VERIFIES => SPEC-TOO-WEAK (a word break is "
            "indistinguishable from a character break)."
        ),
        # msg = ['A',' ','B'] — the minimum two represented words, so exactly the
        # word-level join is observable.
        "witness": _wit("#", "A B"),
    },
    {
        "id": "rival-drop-trailing-break",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DROP_TRAILING,
        "refinement": (
            "the encoder omits the extra doubled separator that a message ending in a "
            "word break contributes. Its faithful real counterpart is an encoder that "
            "strips or ignores a trailing delimiter; under it `encode_morse('A ')` "
            "yields '.-' instead of '.-||', so the exact-string assertion over a "
            "message with a trailing word break FAILS. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the trailing content of the sole postcondition clause, which "
            "appends `sep ++ sep` exactly when the message ends in a word break. This "
            "is the narrowest sub-domain rival in the battery — it is CORRECT on every "
            "message that does not end in a break, which is most of them — so it "
            "tests that the clause is pinned at the one input shape where the trailing "
            "term is observable at all, and it is the only case that probes that term. "
            "If it VERIFIES => SPEC-TOO-WEAK (a trailing word break may be dropped)."
        ),
        # msg = ['A',' '] — one represented word and a trailing break, the only shape
        # at which the trailing term contributes anything.
        "witness": _wit("#", "A "),
    },
    {
        "id": "rival-diverge-argument-independent",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_DIVERGE,
        "refinement": (
            "the encoder never terminates: `spinForever` recurses with no "
            "decreasing measure, so nothing is ever emitted. Its faithful real "
            "counterpart is an encoder whose traversal fails to advance (e.g. a "
            "`while` that never increments its index), which returns no value at "
            "all — so every assertion in the F2P test, `encode_morse('12345') == "
            "'.----|..---|...--|....-|.....'` included, hangs rather than passes. It "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the sole postcondition clause, which pins the result to a "
            "CONCRETE rendering: a non-terminating impl yields an irreducible term "
            "that is not that rendering at any input. This lane is expressible here — "
            "a `partial def` clears variant_scope and keeps the obligation statement "
            "byte-identical — and only a plain measure-free `def` is refused outright "
            "by the termination checker, so recording the class as vacuous understated "
            "the battery (see the LANES note). The witness refutes by FUNCTIONALITY "
            "rather than by evaluation, because the diverging term is irreducible: the "
            "rival returns the SAME term at ['E'] and ['T'], which the clause forces "
            "apart (dot vs dash). If it VERIFIES => SPEC-TOO-WEAK (the spec would "
            "admit an impl that computes nothing). Ports nagini's MustTerminate "
            "obligation lane."
        ),
        "witness": _WIT_DIVERGE,
    },
]


# No @ContractOnly axioms and no opaque callees: the code-word table is modeled
# DEEPLY as `codeMorse`/`codeOf` over the transparent `List Char` carrier, so the
# axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
