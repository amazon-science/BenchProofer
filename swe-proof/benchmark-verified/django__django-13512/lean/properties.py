"""PBT manifest for django__django-13512 (lean backend).

Ported from the nagini sibling's falsification battery. This is a RECORD of
adversarial spec-lane cases the G-PBT gate builds and stamps; it is not itself a
Lean module.

Defended surface (frozen spec in Solution.lean):

  jsonEncodeString (s : List Char) -> (result : List Char)
    (no precondition — the obligation is `∀ s, problem_spec … s (impl s)`)
    Ensures (LOAD-BEARING):
        result = ('"' :: escapeBody s) ++ ['"']

  escapeChar c   = per-character JSON string-literal body: '"' -> ['\\','"'];
                   '\\' -> ['\\','\\']; the five named control chars -> their
                   short escapes; any other char < U+0020 -> ['\\','u','0','0',
                   hex,hex]; EVERY other char (printable ASCII AND every non-ASCII
                   char) -> emitted literally as [c].
  escapeBody s   = front-recursive fold: escapeChar s[0] ++ escapeBody (s.drop 1).

The postcondition is a single top-level equality that fully pins the result to
the input via a transparent, computable fold. There is no opaque callee and no
precondition, so every rival is refutable by `decide` at a concrete input; no
carrier-conditioning is required.

The modeled behavior is the one-character serializer change (ensure_ascii True ->
False) at its smallest observable carrier: the string-leaf renderer. Non-ASCII
text is kept LITERAL rather than expanded to a `\\uXXXX` escape. The whole-
document walk (objects/arrays/numbers/separators/key-quoting) is flag-independent
and unmodeled — the Lean bundle contracts only the purely functional core.

PORTING NOTES (which nagini cases carried over, which did not):
  * nagini (5a) branch-reorder positive -> here as an equivalent CORRECT reshape
    that keeps the load-bearing fold and reproves the obligation honestly
    (pos-control-init-accum). A literal branch reorder is not meaningful on this
    carrier — escapeChar is a single `def`, not an inlined if/elif chain in the
    impl region — so the structural-reshape intent is carried by seeding the
    accumulator with the opening delimiter instead.
  * nagini (5b) split-assembly positive -> pos-control-split-assembly (result
    built via an intermediate `let`, proof unchanged).
  * nagini (6) admissibility self-call -> LANDED as admiss-f2p-inputs (the port
    had dropped it; restored by audit). The port's stated reason — "the Lean
    obligation has no precondition, so there is no admissibility question" — was
    WRONG, and it is the specific reason the audit brief pre-rejects: on a total
    carrier the analogue of PRECOND-TOO-STRONG is the obligation being
    UNSATISFIABLE at an F2P-shaped input, which a positive that discharges the
    spec predicate at those concrete inputs by evaluation tests directly. Landed
    and verified by real build.
  * nagini (1) FRAME-MUTATION rival -> INEXPRESSIBLE here, and the reason is
    demonstrated rather than asserted: the nagini rival's whole mechanism is a
    STORE (`text[i-1] = 97`) through a 1/2-permission reference, and it was
    required to fail for INSUFFICIENT PERMISSION, not for a value mismatch. On this
    carrier `s : List Char` is an immutable value with no aliasing and no
    permission system, so the rejection SOURCE the case exists to exercise does not
    exist. The frame obligation itself is not dropped, though: it re-expresses as
    "no output component is left free", and pos-spec-determinate now PROVES exactly
    that (the spec pins the result uniquely). So the lane's content is carried, by
    the construction this carrier admits.
  * nagini (3a) non-ASCII-escaped -> weak-nonascii-escaped (the pre-patch bug).
  * nagini (3b) quote-not-escaped -> weak-quote-not-escaped.
  * nagini (3c) no-closing-quote -> weak-no-closing-quote.
  * ADDED weak-no-opening-quote: the opening delimiter is the other constant of
    the postcondition equality; the nagini battery only attacked the closing one,
    so this varies the remaining independent output component.
  * nagini AXIOM_TESTS -> dropped (axiom lane is G-AX's job; no consumed axiom
    here — escapeChar/escapeBody are concrete defs).

AUDIT (independent, post-port). Every case was rebuilt with the real verifier.
  * Attack A (statement integrity): all variants keep the `correct_jsonEncodeString`
    STATEMENT byte-identical and pass variant_scope. No neutered obligation.
  * Attack B/B′ (witness discrimination + FORGERY): each reject witness was built
    against the rival (exit 0) and against the frozen solution (exit 1), and then
    a FORGERY differing only in the CLAIM (the `¬` dropped, i.e. asserting the spec
    HOLDS at that input) was built on both sides. The forgery INVERTS the table
    (gold 0, rival 1) for every case, so each gold-side exit code demonstrably
    tracks the claim rather than a tactic accident. Every gold_signature is a plain
    kernel evaluation ("Tactic `decide` proved that the proposition ¬(...) is
    false") — the strongest evidence class, not an unfolding or unification
    failure. No hollow case.
  * Attack C (is the rival wrong, or just different): all six rivals differ from
    gold OBSERVABLY, each demonstrated by the `decide` evaluation above. None is
    definitionally equal to the frozen impl; none is vacuous.
  * Attack D (SPEC-TOO-WEAK probes), six NEW wrong impls not in the battery: the
    backslash clause unescaped; a short escape (tab) rerouted through the generic
    \\u00XX branch; UPPERCASE hex digits in that escape; astral-only (>U+FFFF)
    escaping; a reversed body; and both delimiters dropped. ALL SIX were rejected
    (exit 1) — no spec hole. Two of them exposed real COVERAGE gaps and were landed
    as cases: weak-backslash-not-escaped and weak-body-order-reversed.
  * Attack E (SPEC-TOO-STRONG probes), four NEW correct reshapes: the fold used
    directly; `List.foldl`; `(s.map escapeChar).flatten`; and a delimiter-seeded
    variant. ALL FOUR verify (exit 0). The map/join and foldl shapes are NOT
    definitionally equal to the loop and each needed its own honest accumulator
    lemma, so the spec admits faithful reshapes whose proofs differ from the frozen
    one — it is not merely accepting syntactic clones. No soundness hole.
  * ADDED pos-spec-determinate: PROVES the spec admits at most one result per
    input, so SPEC-TOO-WEAK is structurally unreachable here rather than merely
    unobserved — a stronger statement than "attack D found nothing".
  * The divergence lane is not applicable and is not re-derived here; see
    the corpus-wide termination-semantics finding.
"""
from pathlib import Path

INSTANCE = "django__django-13512"

_DIR = Path(__file__).parent
_BASE = (_DIR / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl / proof regions (each present exactly once).
# ---------------------------------------------------------------------------
_LOOP = ("  let mut acc : List Char := []\n"
         "  for c in s do\n"
         "    acc := acc ++ escapeChar c\n"
         "  return ('\"' :: acc) ++ ['\"']\n")
_PROOF = ("  rw [forIn_escape_eq s []]\n"
          "  simp only [List.nil_append]\n"
          "  rfl\n")
# The obligation's head, up to and including its `intro`. Swapping here lets a
# positive prepend ground `have`s INSIDE the existing tactic body -- no new
# top-level declaration, and the theorem STATEMENT stays byte-identical.
_HEAD = ("theorem correct_jsonEncodeString :\n"
         "    ∀ (s : List Char),\n"
         "      problem_spec_jsonEncodeString s (implementation_jsonEncodeString s) := by\n"
         "  intro s\n")
_HEAD_NO_INTRO = _HEAD.replace("  intro s\n", "")

for _a in (_LOOP, _PROOF, _HEAD):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


# ===========================================================================
# POSITIVE CONTROLS  (expect "verify")  -- correct reshapes that must reprove
# ===========================================================================

# (5a-port) POSITIVE CONTROL -- seed the accumulator with the opening delimiter.
# Instead of building the body and then wrapping it, prime `acc` with the opening
# '"' and append the closing '"' at the end. Semantically identical (the escaped
# body is unchanged; only the two constant delimiters move from the wrap step
# into the accumulator seed and the tail). The obligation is reproven for the new
# shape by instantiating the accumulator lemma at `['"']` instead of `[]`. MUST
# verify; else the postcondition is over-fit to the exact assembly FORM =>
# SPEC-TOO-STRONG.
_POS_INIT = _swap(
    _swap(
        _BASE, _LOOP,
        "  let mut acc : List Char := ['\"']\n"
        "  for c in s do\n"
        "    acc := acc ++ escapeChar c\n"
        "  return acc ++ ['\"']\n",
    ),
    _PROOF,
    "  rw [forIn_escape_eq s ['\"']]\n"
    "  rfl\n",
)

# (5b-port) POSITIVE CONTROL -- split result assembly. The final wrap is built in
# two steps via an intermediate `let` (`opened := '"' :: acc`, then `opened ++
# ['"']`) rather than one expression. Definitionally equal to the one-expression
# form, so the frozen proof body still closes verbatim. MUST verify; else the
# postcondition is over-fit to the one-expression assembly FORM => SPEC-TOO-STRONG.
_POS_SPLIT = _swap(
    _BASE, _LOOP,
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escapeChar c\n"
    "  let opened := '\"' :: acc\n"
    "  return opened ++ ['\"']\n",
)

# (added by audit) ADMISSIBILITY. The frozen obligation carries no precondition,
# so the nagini precondition-admission probe re-expresses on this total carrier as:
# is the obligation actually SATISFIABLE at concrete, F2P-shaped inputs, or is it
# unsatisfiable at exactly the inputs the task cares about? Each `have` discharges
# the spec predicate at one such input BY EVALUATION (`decide`, so the kernel
# really computes both sides), and the frozen tactic body then closes the general
# obligation verbatim. The four inputs are the shapes the F2P assertions key on: a
# plain ASCII scalar, a CJK character, an astral (>U+FFFF) character, and an
# accented Latin letter -- i.e. exactly the non-ASCII-literal points the modeled
# behavior turns on. Nothing is assumed: no new declaration, no axiom, statement
# byte-identical, and the ground instances are `have`s inside the existing body.
_POS_ADMISS = _swap(
    _BASE, _HEAD,
    _HEAD_NO_INTRO
    + "  have _ascii : problem_spec_jsonEncodeString ['a']\n"
      "      (implementation_jsonEncodeString ['a']) := by\n"
      "    unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
      "    decide\n"
      "  have _cjk : problem_spec_jsonEncodeString ['中']\n"
      "      (implementation_jsonEncodeString ['中']) := by\n"
      "    unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
      "    decide\n"
      "  have _astral : problem_spec_jsonEncodeString ['😀']\n"
      "      (implementation_jsonEncodeString ['😀']) := by\n"
      "    unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
      "    decide\n"
      "  have _accent : problem_spec_jsonEncodeString ['ź']\n"
      "      (implementation_jsonEncodeString ['ź']) := by\n"
      "    unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
      "    decide\n"
      "  intro s\n",
)

# (added by audit) DETERMINACY. Proves the spec admits AT MOST ONE result per
# input: the postcondition is a bare equality pinning `result` to a total function
# of `s`, so any two satisfying results are equal. Combined with the frozen
# theorem's existence half, that singleton IS the frozen impl's output -- hence NO
# observably-different impl can satisfy this spec, and SPEC-TOO-WEAK is
# structurally unreachable rather than merely unobserved by the rivals below. This
# is also the frame check (§5): no output component is left free.
_POS_DETERMINATE = _swap(
    _BASE, _HEAD,
    _HEAD_NO_INTRO
    + "  have _det : ∀ (t r1 r2 : List Char),\n"
      "      problem_spec_jsonEncodeString t r1 → problem_spec_jsonEncodeString t r2 →\n"
      "      r1 = r2 := by\n"
      "    intro t r1 r2 h1 h2\n"
      "    rw [h1, h2]\n"
      "  intro s\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes -- expect "reject")
# ===========================================================================

# (3a) PARTIAL-DOMAIN -- non-ASCII escaped (the EXACT pre-patch behavior). Every
# character in the flag-sensitive BMP range U+0080..U+FFFF is emitted as a
# `\uXXXX` escape instead of literally. Diverges ONLY on non-ASCII inputs; correct
# on every all-ASCII input. This is the ensure_ascii=True default the patch turns
# off.
_RIVAL_NONASCII = _swap(
    _BASE, _LOOP,
    "  let escAscii : Char → List Char := fun c =>\n"
    "    let n := c.toNat\n"
    "    if n ≥ 0x80 ∧ n ≤ 0xFFFF then\n"
    "      ['\\\\', 'u', hexDigit ((n / 0x1000) % 16), hexDigit ((n / 0x100) % 16),\n"
    "       hexDigit ((n / 0x10) % 16), hexDigit (n % 16)]\n"
    "    else escapeChar c\n"
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escAscii c\n"
    "  return ('\"' :: acc) ++ ['\"']\n",
)

# (3b) PARTIAL-DOMAIN -- quotation mark NOT escaped. The '"' code point is emitted
# literally as ['"'] instead of the two-character escape ['\\','"']. Diverges ONLY
# on inputs containing a '"'; correct on every quote-free input (incl. all F2P
# strings, none of which contain a literal quote).
_RIVAL_NOQUOTE = _swap(
    _BASE, _LOOP,
    "  let escNoQuote : Char → List Char := fun c =>\n"
    "    if c.toNat = 0x22 then ['\"'] else escapeChar c\n"
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escNoQuote c\n"
    "  return ('\"' :: acc) ++ ['\"']\n",
)

# (3c) STRUCTURAL near-miss -- closing delimiter dropped. The result omits the
# trailing '"'. Diverges on EVERY input (the rendering is missing its closing
# delimiter); attacks the trailing-constant component of the postcondition
# equality.
_RIVAL_NOCLOSE = _swap(
    _BASE, _LOOP,
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escapeChar c\n"
    "  return ('\"' :: acc)\n",
)

# (added) STRUCTURAL near-miss -- opening delimiter dropped. The result omits the
# leading '"'. Attacks the LEADING-constant component of the postcondition
# equality, which the nagini battery never probed independently. Diverges on every
# input.
_RIVAL_NOOPEN = _swap(
    _BASE, _LOOP,
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escapeChar c\n"
    "  return acc ++ ['\"']\n",
)

# (added by audit) PARTIAL-DOMAIN -- the backslash code point NOT escaped. The
# other two-character escape of the rendering (`\` -> ['\\','\\']) is emitted as a
# lone ['\\'] instead. The battery attacked the '"' clause of escapeChar and the
# below-U+0020 clause not at all; this varies the SECOND two-character escape,
# which no other case touches. Diverges ONLY on inputs containing a backslash.
_RIVAL_NOBACKSLASH = _swap(
    _BASE, _LOOP,
    "  let escNoBack : Char → List Char := fun c =>\n"
    "    if c.toNat = 0x5c then ['\\\\'] else escapeChar c\n"
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := acc ++ escNoBack c\n"
    "  return ('\"' :: acc) ++ ['\"']\n",
)

# (added by audit) ORDER attack -- per-character rendering correct, SEQUENCE order
# wrong. Each character's escaping is exactly escapeChar, and on every input of
# length <= 1 the result is byte-identical to gold; the accumulator is prepended
# instead of appended, so the body comes out reversed. Every other rival in this
# battery varies escapeChar's VALUE or a delimiter, so all of them are already
# refuted at a one-character input; nothing here pinned the ORDER of the fold,
# which is the other half of `escapeBody`'s content. Needs a >=2-character witness.
_RIVAL_REVERSED = _swap(
    _BASE, _LOOP,
    "  let mut acc : List Char := []\n"
    "  for c in s do\n"
    "    acc := escapeChar c ++ acc\n"
    "  return ('\"' :: acc) ++ ['\"']\n",
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-init-accum", "kind": "soundness", "expect": "verify",
     "module": _POS_INIT,
     "rationale": "structurally-different but CORRECT impl: the accumulator is "
                  "seeded with the opening delimiter and the closing delimiter is "
                  "appended at the end, moving both constants out of the wrap step. "
                  "The escaped body (the load-bearing fold) is unchanged; the "
                  "obligation is reproven by instantiating the accumulator lemma at "
                  "['\"'] instead of []. Must verify; else the postcondition is "
                  "over-fit to the assembly FORM => SPEC-TOO-STRONG."},
    {"id": "pos-control-split-assembly", "kind": "soundness", "expect": "verify",
     "module": _POS_SPLIT,
     "rationale": "structurally-different final assembly: the wrap is built in two "
                  "steps via an intermediate `let` rather than one expression. "
                  "Definitionally equal to the frozen form, so the frozen proof "
                  "body closes verbatim. Must verify; else the postcondition is "
                  "over-fit to the one-expression assembly FORM => SPEC-TOO-STRONG."},
    {"id": "admiss-f2p-inputs", "kind": "admissibility", "expect": "verify",
     "module": _POS_ADMISS,
     "rationale": "the obligation carries no precondition, so admissibility here "
                  "is SATISFIABILITY at the concrete inputs the task turns on: the "
                  "spec predicate is discharged BY EVALUATION (`decide`, kernel-"
                  "computed on both sides) at a plain ASCII scalar, a CJK "
                  "character, an astral (>U+FFFF) character and an accented Latin "
                  "letter -- the F2P-shaped points -- as ground `have`s, and the "
                  "frozen obligation then closes verbatim. Must verify; a failure "
                  "would mean the modeled behavior is unsatisfiable at exactly a "
                  "normal F2P input, the total-carrier analogue of "
                  "PRECOND-TOO-STRONG. Carries the lane the nagini sibling's "
                  "self-call case covered."},
    {"id": "pos-spec-determinate", "kind": "soundness", "expect": "verify",
     "module": _POS_DETERMINATE,
     "rationale": "proves the spec is FUNCTIONAL: the postcondition is a bare "
                  "equality pinning result to a total function of the input, so any "
                  "two satisfying results are equal. With the frozen theorem's "
                  "existence half that singleton IS the frozen impl's output, so no "
                  "observably-different impl can verify -- SPEC-TOO-WEAK is "
                  "structurally unreachable, not merely unobserved by the rivals "
                  "below, and no output component is left free. Must verify; a "
                  "failure would mean the spec underdetermines the result."},

    # ---- uniqueness rivals (must be REJECTED, each with a discriminating witness) ----
    {"id": "weak-nonascii-escaped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONASCII,
     "refinement": "escaping every U+0080..U+FFFF character to a `\\uXXXX` sequence "
                   "is EXACTLY the pre-patch default (ensure_ascii=True). A faithful "
                   "patch that kept that default renders a CJK text value as its "
                   "escaped ASCII form instead of the literal characters, and the "
                   "admin display path likewise -- it FAILS the F2P assertions that "
                   "pin the literal non-ASCII rendering. So a rival that verified "
                   "here would be a true verify-does-not-resolve break, not an "
                   "artifact.",
     "rationale": "attacks the load-bearing equality result = ('\"' :: escapeBody s) "
                  "++ ['\"'] on its per-character content: escapeBody keeps every "
                  "non-ASCII char literal, so on such a char the rival's escaped "
                  "body cannot equal escapeBody. Correct on all-ASCII inputs, wrong "
                  "on every non-ASCII one. If it verified => SPEC-TOO-WEAK (the "
                  "literal-non-ASCII discriminator hollow).",
     "witness":
        "-- Refutes at the input `中` (U+4E2D, in the flag-sensitive BMP range).\n"
        "-- The rival escapes it to a `\\uXXXX` body; the spec keeps it literal, so\n"
        "-- the rival contradicts the postcondition here. Fails on gold (gold keeps\n"
        "-- `中` literal, so the spec holds and its negation is false).\n"
        "example : ¬ problem_spec_jsonEncodeString ['中'] "
        "(implementation_jsonEncodeString ['中']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
    {"id": "weak-quote-not-escaped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOQUOTE,
     "refinement": "emitting a literal '\"' for the quotation-mark code point "
                   "produces malformed output (an unescaped delimiter) for any text "
                   "containing a '\"'. This is not the standard serializer's "
                   "behavior; a faithful patch shipping it would produce invalid "
                   "JSON on quote-bearing values, so it does not resolve the task. "
                   "verify-does-not-resolve.",
     "rationale": "attacks the per-character content of the equality: escapeChar(34) "
                  "is ['\\','\"'], so on a '\"' the rival's literal-['\"'] body "
                  "cannot equal escapeBody. Correct on every quote-free input (incl. "
                  "all F2P strings). If it verified => SPEC-TOO-WEAK (escaping of "
                  "'\"' not enforced).",
     "witness":
        "-- Refutes at the input `\"` (U+0022). The rival emits it literally; the\n"
        "-- spec demands the two-character escape, so the rival contradicts the\n"
        "-- postcondition here. Fails on gold, which escapes it.\n"
        "example : ¬ problem_spec_jsonEncodeString ['\"'] "
        "(implementation_jsonEncodeString ['\"']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
    {"id": "weak-no-closing-quote", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOCLOSE,
     "refinement": "dropping the trailing delimiter renders every value without its "
                   "closing '\"' -- malformed for EVERY input. A faithful patch "
                   "doing this fails every F2P assertion (which pins fully-delimited "
                   "output). verify-does-not-resolve. (Cheap structural near-miss "
                   "attacking the trailing-constant component of the equality.)",
     "rationale": "attacks the trailing constant of result = ('\"' :: escapeBody s) "
                  "++ ['\"']: the rival returns '\"' :: escapeBody s with no closing "
                  "delimiter, so the equality fails on every input. If it verified "
                  "=> SPEC-TOO-WEAK.",
     "witness":
        "-- Refutes at a trivial ASCII input `a`: the rival returns the body without\n"
        "-- the closing delimiter, so it is shorter than the spec's result and\n"
        "-- cannot equal it. Fails on gold, which appends the closing '\"'.\n"
        "example : ¬ problem_spec_jsonEncodeString ['a'] "
        "(implementation_jsonEncodeString ['a']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
    {"id": "weak-no-opening-quote", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOOPEN,
     "refinement": "dropping the LEADING delimiter renders every value without its "
                   "opening '\"' -- malformed for EVERY input, the mirror of the "
                   "no-closing-quote case. A faithful patch doing this fails every "
                   "F2P assertion. verify-does-not-resolve. Added over the nagini "
                   "battery so both independent constant components of the equality "
                   "are attacked, not just the trailing one.",
     "rationale": "attacks the LEADING constant of result = ('\"' :: escapeBody s) "
                  "++ ['\"']: the rival returns escapeBody s ++ ['\"'] with no "
                  "opening delimiter, so the equality fails on every input. If it "
                  "verified => SPEC-TOO-WEAK (the opening delimiter unconstrained).",
     "witness":
        "-- Refutes at a trivial ASCII input `b`: the rival omits the opening\n"
        "-- delimiter, so its result begins with `b` where the spec begins with '\"'.\n"
        "-- Fails on gold, which prepends the opening '\"'.\n"
        "example : ¬ problem_spec_jsonEncodeString ['b'] "
        "(implementation_jsonEncodeString ['b']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
    {"id": "weak-backslash-not-escaped", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NOBACKSLASH,
     "refinement": "emitting a lone backslash for the backslash code point "
                   "produces malformed output for any text containing one: the "
                   "emitted character then escapes whatever follows it, so the "
                   "value no longer round-trips through a JSON parser. A faithful "
                   "patch shipping this is not the standard serializer and does not "
                   "resolve the task. verify-does-not-resolve.",
     "rationale": "attacks the SECOND two-character escape clause of escapeChar, "
                  "which no other case in this battery varies (the '\"' clause is "
                  "covered by weak-quote-not-escaped; the below-U+0020 clause and "
                  "this one were unattacked). escapeChar(0x5c) is ['\\','\\'], so on "
                  "a backslash the rival's single-character body cannot equal "
                  "escapeBody. Correct on every backslash-free input. If it "
                  "verified => SPEC-TOO-WEAK.",
     "witness":
        "-- Refutes at the input `\\` (U+005C). The rival emits one backslash; the\n"
        "-- spec demands the two-character escape, so the rival contradicts the\n"
        "-- postcondition here. Fails on gold, which doubles it.\n"
        "example : ¬ problem_spec_jsonEncodeString ['\\\\'] "
        "(implementation_jsonEncodeString ['\\\\']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
    {"id": "weak-body-order-reversed", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_REVERSED,
     "refinement": "rendering the characters in reverse order returns a different "
                   "text for every value of length >= 2 -- the serialized form is "
                   "no longer the value that was serialized. A faithful patch doing "
                   "this fails every multi-character F2P assertion. "
                   "verify-does-not-resolve.",
     "rationale": "attacks the ORDER of the load-bearing fold rather than any "
                  "per-character value: this rival applies escapeChar to every "
                  "character exactly as the spec does, and is byte-identical to "
                  "gold on every input of length <= 1, so it is the one rival here "
                  "that a single-character witness CANNOT refute. escapeBody is "
                  "front-recursive, pinning sequence order, so the equality fails "
                  "from length 2 up. If it verified => SPEC-TOO-WEAK (the spec "
                  "would constrain only the multiset of rendered characters, not "
                  "the sequence).",
     "witness":
        "-- Refutes at the two-character input `ab`, the shortest input that\n"
        "-- discriminates: the rival renders the body reversed (`ba`), the spec\n"
        "-- renders it in order. Fails on gold, which preserves the order.\n"
        "example : ¬ problem_spec_jsonEncodeString ['a', 'b'] "
        "(implementation_jsonEncodeString ['a', 'b']) := by\n"
        "  unfold problem_spec_jsonEncodeString implementation_jsonEncodeString\n"
        "  decide"},
]
